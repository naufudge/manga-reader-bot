from bs4 import BeautifulSoup
import httpx

class KissManga():
    def __init__(self):
        self.home = "https://kissmanga.org"
        self.timeout = httpx.Timeout(5, read=None)
        self.client = httpx.Client(http2=True, timeout=self.timeout)

    def Search(self, keyword):
        self.search_results = {}
        i = 1
        while True:
            page = self.client.get(f"https://kissmanga.org/manga_list?page={i}&action=search&q={keyword}")
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
                    i += 1
                else:
                    print(f"\npage {i} didn't have any results. Finished Searching!")
                    break
            else:
                print(f"\npage {i} returned: {page}")
                break

        return self.search_results

    def chapters(self, manga_link):
        manga_page = self.client.get(manga_link)
        manga_soup = BeautifulSoup(manga_page, 'html.parser')

        parent_chapter_list = manga_soup.find('div', class_='listing listing8515 full')
        chapter_list = parent_chapter_list.find_all('h3')
        chapters = []
        for each in chapter_list:
            chapter_parent = each.find('a')
            chapter_raw = chapter_parent.text.strip()
            chapter = " ".join(chapter_raw.split())
            chapter_url = chapter_parent['href'].strip()

            chapters.append((chapter, f"{self.home}{chapter_url}"))

        chapters.reverse() # Asscending order
        return chapters

    def read_chap(self, chap_url):
        chapter_page = self.client.get(chap_url)
        chapter_soup = BeautifulSoup(chapter_page.content, 'html.parser')

        parent_page_img = chapter_soup.find('div', id='centerDivVideo')
        page_imgs = parent_page_img.find_all('img')
        pages = [img['src'] for img in page_imgs]

        return pages

