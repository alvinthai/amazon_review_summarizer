from bs4 import BeautifulSoup
import os
import re
import requests


def get_id(url):
    '''
    INPUT: str
    OUTPUT: str

    Args:
        url: an Amazon url string

    Gets asin identifer for amazon product from a url
    '''

    # url format: https://www.amazon.com/.../.../id/...
    regex = re.compile(r'(?<=/)[^/]*')
    asin = regex.findall(url)[-2]

    if len(asin) != 10:
        # url format https://www.amazon.com/.../id
        asin = regex.findall(url)[-1][:10]

    return asin


def extract(asin):
    '''
    INPUT: str
    OUTPUT: list(int), list(str)

    Args:
        asin: an Amazon asin str identifier (output from get_id function)

    Extracts the star rating, review text, author name, and review headline
    from directory of amazon html files
    '''
    ratings, reviews, authors, headlines = [], [], [], []

    path = os.getcwd() + '/reviews/com/{}/'.format(asin)
    pages = [file_ for file_ in os.listdir(path) if file_[-5:] == '.html']

    for page in pages:
        with open(path + page, 'r') as f:
            soup = BeautifulSoup(f, 'html.parser')
            tags = soup.findAll("div", {"class": "a-section review"})

            if not tags:
                print '{} is an invalid page format for scraping'.format(page)
                continue

            for tag in tags:
                rev_class = "a-size-base review-text"
                aut_class = "a-size-base a-link-normal author"
                head_class = "a-size-base a-link-normal review-title " \
                    "a-color-base a-text-bold"

                rating = int(tag.find('i').text[0])
                review = tag.findAll("span", {"class": rev_class})[0].text
                author = tag.findAll("a", {"class": aut_class})[0].text
                headline = tag.findAll("a", {"class": head_class})[0].text

                ratings.append(rating)
                reviews.append(review)
                authors.append(author)
                headlines.append(headline)

    return ratings, reviews, authors, headlines


class Loader(object):
    '''
    Class for scraping a review site on Amazon
    '''
    def __init__(self, url, name=None):
        '''
        INPUT: str
        OUTPUT: None

        Attributes:
            authors (list): list of strings or review authors
            asin (str): asin identifier for Amazon product
            headlines (list): list of strings of review headlines
            name (str): custom name for Amazon product
            ratings (list): list of ints of review ratings
            reviews (list): list of strings of review text
            url (str): url of the amazon link to scrape
        '''
        self.authors = None
        self.asin = None
        self.headlines = None
        self.name = name
        self.ratings = None
        self.reviews = None
        self.url = url

    def scrape(self, n_reviews=300, delete=False, retries=0):
        '''
        INPUT: int, bool
        OUTPUT: None

        Args:
            n_reviews: number of reviews to scrape
            delete: option to force delete folder containing cached reviews

        Scrapes n most helpful amazon reviews and extracts reviews
        If already scraped, extracts reviews
        '''
        url = self.url
        asin = get_id(url)
        self.asin = asin

        folder = os.getcwd() + '/reviews/com/' + asin

        if delete:
            path = os.getcwd() + '/reviews/com/{}/'.format(asin)
            pages = [file_ for file_ in os.listdir(path)]

            try:
                for page in pages:
                    os.remove(path + page)
            except:
                print 'No files to delete!'

            try:
                os.rmdir(path)
            except:
                print 'No folder to delete!'

        if not os.path.isdir(folder):
            # Run Amazon scraper
            # Credit to Andrea Esuli
            # https://github.com/aesuli/amadown2py
            os.system('python scripts/amazon_crawler.py '
                                  '-d com {} -m {} -o reviews'
                                  .format(asin, n_reviews))
            last_page = len(os.listdir(folder))
        else:
            last_page = len(os.listdir(folder))

        if retries > 0:
            return retries, last_page

        while last_page == 1 and retries < 5:
            retries += 1
            retries, last_page = self.scrape(n_reviews, delete=True,
                                             retries=retries)

        if last_page == 1 and retries == 5:
            raise RuntimeError("Scraping Failed!")

        self.ratings, self.reviews, self.authors, self.headlines = \
            extract(asin)

        if not self.name:
            f = os.getcwd() + '/reviews/com/{0}/{0}_1.html'.format(asin)
            with open(f, 'r') as html:
                soup = BeautifulSoup(html, 'html.parser')
                self.name = soup.select('.a-link-normal')[0].text
