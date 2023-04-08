from bs4 import BeautifulSoup
import httpx
import asyncio
from difflib import SequenceMatcher

def no_cap_dict(d):
    """
    Returns a new dictionary with lower case key values of the inputted dictionary.
    """
    new_d = {}
    for x,y in d.items():
        new_d[x.lower()] = y
    return new_d

def similar(a, b):
    """
    Similarity check between ``a`` and ``b``. Returns a ratio (Float).
    """
    return SequenceMatcher(None, a, b).ratio()

class Async_KissManga():
    def __init__(self):
        self.home = "https://kissmanga.org"
        self.timeout = httpx.Timeout(5, read=None)
        self.client = httpx.Client(http2=True, timeout=self.timeout)
        self.search_results = {}
        self.chapters = []

    async def search_page_loader(self, client, url, page_num):
        """
        Scrapes the search result page.
        ### Parameters
        ``client``: httpx.Client
            The httpx client that you are using.
        ``url``: str
            The URL of the search result page.
        ``page_num``: int
            The search result page number.
        """
        page = await client.get(url)
        if page.status_code < 400:
            page_soup = BeautifulSoup(page.content, 'html.parser')
            parent_results = page_soup.find('div', class_="listing full")
            results = parent_results.find_all('div', class_="item_movies_in_cat")
            if results != []:
                # print(f"\non page: {i} \n")
                for result in results:
                    parent_title = result.find('a', class_="item_movies_link")
                    title = parent_title.text.strip()
                    if title.lower().find('duplicate') == -1:
                        link = parent_title['href'].strip()
                        self.search_results[title] = f"{self.home}{link}"
            else:
                print(f"\npage {page_num} didn't have any results. Finished Searching!")
                return 1
        else:
            print(f"\npage {page_num} returned: {page}")
            return 2
        return

    async def Search(self, keyword):
        """
        Search for any manga that you want.\n
        ### Parameters
        ``keyword``: str
            The name of the manga you want to search \n
        This function will return a dictionary of the results containing the name of the manga as key and the link as the value.
        """
        test_p, page_urls, tasks = 10, [], []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for j in range(1, test_p):
                page_url = f"https://kissmanga.org/manga_list?page={j}&action=search&q={keyword}"
                page_urls.append(page_url)
                tasks.append(asyncio.create_task(self.search_page_loader(client, page_url, j)))

            tests = await asyncio.gather(*tasks)
        return self.search_results

    def search_results_sorter(self, search_results, keyword):
        """
        Sorts the search results based on the similarity between it and the keyword.
        ### Parameters
        ``search_results``: sequence
            A non-empty sequence of search results. \n
        ``keyword``: str
            The name of the manga you searched. \n
        Returns the sorted list.
        """
        temp_listed_results = []
        for result in search_results:
            x = similar(keyword, result)
            temp_listed_results.append((x, result))

        temp_listed_results.sort(reverse=True)
        sorted_results = [x[1] for x in temp_listed_results]

        return sorted_results

    def load_managa_page(self, manga_link):
        """
        Loads up the specific manga page. Returns manga page's HTML source code.
        """
        manga_page = self.client.get(manga_link)
        soup = BeautifulSoup(manga_page, 'html.parser')
        return soup

    def Chapters(self, manga_link):
        """
        Find the all the chapters of a specific manga.\n
        ### Parameters
        ``manga_link``: str
            The link of the manga \n
        This function will return a list of tuples, where the first value of the tuple is the name of the chapter and the second value of the tuple is the link of the chapter.
        """
        manga_soup = self.load_managa_page(manga_link)

        parent_chapter_list = manga_soup.find('div', class_='listing listing8515 full')
        chapter_list = parent_chapter_list.find_all('h3')

        for each in chapter_list:
            chapter_parent = each.find('a')
            chapter_raw = chapter_parent.text.strip()
            chapter = " ".join(chapter_raw.split())
            chapter_url = chapter_parent['href'].strip()

            self.chapters.append((chapter, f"{self.home}{chapter_url}"))

        self.chapters.reverse() # Changes to asscending order
        return self.chapters

    def mangaInfo(self, manga_link):
        """
        Find the basic info of a specific manga.
        ### Parameters
        ``manga_link``: str
            The link of the manga \n
        This function will return a dictionary with the 'title', 'other name', 'authors', 'summary' and 'cover' of the manga.
        """
        manga_soup = self.load_managa_page(manga_link)
        info = {}
        main_window = manga_soup.find('div', class_='barContent full')
        details = main_window.find('div', class_='full')
        other_info = details.find_all('p', class_='info')

        manga_cover_parent = manga_soup.find('div', class_='barContent cover_anime full')
        manga_cover = manga_cover_parent.find('img')['src']

        info['title'] = details.find('h2').text.strip()
        for each in other_info:
            span = each.find('span').text.strip().lower()
            if span != 'genres:':
                a = each.find('a').text.strip()
                info[span.replace(':', '')] = a
        info['summary'] = details.find('div', class_='summary').text.strip()
        info['cover'] = f"{self.home}{manga_cover}"

        return info

    def read_chap(self, chap_url):
        """
        Find the images of the pages of a specific chapter.
        ### Parameters
        ``chap_url``: str
            URL of the chapter.
        This function returns a list of image URLs in order.
        """
        chapter_page = self.client.get(chap_url)
        chapter_soup = BeautifulSoup(chapter_page.content, 'html.parser')

        parent_page_img = chapter_soup.find('div', id='centerDivVideo')
        page_imgs = parent_page_img.find_all('img')
        pages = [img['src'] for img in page_imgs]

        return pages

