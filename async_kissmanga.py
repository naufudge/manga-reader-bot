from bs4 import BeautifulSoup
import httpx
import asyncio

def no_cap_dict(d):
    """
    Returns a new dictionary with lower case key values of the inputted dictionary.
    """
    new_d = {}
    for x,y in d.items():
        new_d[x.lower()] = y
    return new_d

class Async_KissManga():
    def __init__(self):
        self.home = "https://kissmanga.org"
        self.timeout = httpx.Timeout(5, read=None)
        self.client = httpx.Client(http2=True, timeout=self.timeout)
        self.search_results = {}
        self.chapters = []

    async def search_page_loader(self, client, url, page_num):
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
        test_p, page_urls, tasks = 10, [], []
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for j in range(1, test_p):
                page_url = f"https://kissmanga.org/manga_list?page={j}&action=search&q={keyword}"
                page_urls.append(page_url)
                tasks.append(asyncio.create_task(self.search_page_loader(client, page_url, j)))

            tests = await asyncio.gather(*tasks)
        return self.search_results

    def Chapters(self, manga_link):
        manga_page = self.client.get(manga_link)
        manga_soup = BeautifulSoup(manga_page, 'html.parser')

        parent_chapter_list = manga_soup.find('div', class_='listing listing8515 full')
        chapter_list = parent_chapter_list.find_all('h3')

        for each in chapter_list:
            chapter_parent = each.find('a')
            chapter_raw = chapter_parent.text.strip()
            chapter = " ".join(chapter_raw.split())
            chapter_url = chapter_parent['href'].strip()

            self.chapters.append((chapter, f"{self.home}{chapter_url}"))

        self.chapters.reverse() # Asscending order
        return self.chapters

    def read_chap(self, chap_url):
        chapter_page = self.client.get(chap_url)
        chapter_soup = BeautifulSoup(chapter_page.content, 'html.parser')

        parent_page_img = chapter_soup.find('div', id='centerDivVideo')
        page_imgs = parent_page_img.find_all('img')
        pages = [img['src'] for img in page_imgs]

        return pages

