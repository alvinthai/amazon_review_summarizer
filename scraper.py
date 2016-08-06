from bs4 import BeautifulSoup
import os
import re


def get_id(url):
    '''
    INPUT: str
    OUTPUT: str

    gets asin identifer for amazon product from a url
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

    extracts the star rating and review text from directory of
    amazon html files
    '''
    ratings = []
    reviews = []

    path = os.getcwd() + '/reviews/com/{}/'.format(asin)
    pages = [file_ for file_ in os.listdir(path) if file_[-5:] == '.html']

    for page in pages:
        html = open(path + page, 'r')
        soup = BeautifulSoup(html, 'html.parser')
        tags = soup.findAll("div", {"class": "a-section review"})

        if not tags:
            print '{} is an invalid page format for scraping'.format(page)
            continue

        for tag in tags:
            rating = int(tag.find('i').text[0])
            review = tag.findAll("span",
                                 {"class": "a-size-base review-text"})[0].text
            ratings.append(rating)
            reviews.append(review)

    return ratings, reviews


class Loader(object):
    '''
    class for scraping a review site on Amazon
    '''
    def __init__(self, name=None):
        self.name = name

    def scrape(self, n_reviews=100, delete=False):
        '''
        INPUT: int
        OUTPUT: None

        scrapes n most helpful amazon reviews and extracts reviews
        if already scraped, extracts reviews
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
