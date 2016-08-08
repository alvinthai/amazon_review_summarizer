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

    Extracts the star rating and review text from directory of amazon html
    files
    '''
    ratings = []
    reviews = []

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
                rating = int(tag.find('i').text[0])
                review = tag.findAll("span", {"class": "a-size-base " +
                                              "review-text"})[0].text
                ratings.append(rating)
                reviews.append(review)

    return ratings, reviews


class Loader(object):
    '''
    Class for scraping a review site on Amazon
    '''
    def __init__(self, name=None):
        '''
        INPUT: str
        OUTPUT: None

        Attributes:
            name (str): custom name for Amazon product
            asin (str): asin identifier for Amazon product
        '''
        self.name = name
        self.asin = None

    def scrape(self, n_reviews=300, delete=False):
        '''
        INPUT: int, bool
        OUTPUT: None

        Args:
            n_reviews: number of reviews to scrape
            delete: option to force delete folder containing cached reviews

        Scrapes n most helpful amazon reviews and extracts reviews
        If already scraped, extracts reviews
        '''
        url = raw_input('url of amazon product: ')
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
            last_page = os.system('python amazon_crawler.py '
                                  '-d com {} -m {} -o reviews'
                                  .format(asin, n_reviews))
        else:
            last_page = len(os.listdir(folder))

        if last_page is None:
            print '\nError!\nCheck if captcha is enforced!'
        else:
            ratings, reviews = extract(asin)

            self.ratings = ratings
            self.reviews = reviews

        if not self.name:
            f = os.getcwd() + '/reviews/com/{0}/{0}_1.html'.format(asin)
            with open(f, 'r') as html:
                soup = BeautifulSoup(html, 'html.parser')
                self.name = soup.select('.a-link-normal')[0].text
