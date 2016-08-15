from parsers import *
from polarizer import *
from scraper import *


def load(url, n_reviews=300, delete=False):
    '''
    INPUT: str, int, bool
    OUTPUT: Loader

    Args:
        url: url of amazon product
        n_reviews: number of reviews to scrape
        delete: whether to delete existing reviews that have been
            scraped (if old reviews exist, no scraping is attempted)

    Scrapes an amazon url and returns the scraped product.
    '''
    product = Loader(url)
    product.scrape(300)

    return product


def parse(product):
    '''
    INPUT: Loader
    OUTPUT: ReviewSents

    Args:
        doc: a scrpaed Loader object from the load function

    Uses spacy to tokenize sentences in review and returns custom class of
    review data for later processing
    '''
    product.extract(product.asin)
    return ReviewSents(product)


def summarize(corpus):
    '''
    INPUT: ReviewSents
    OUTPUT: Polarizer

    Args:
        doc: a ReviewSents object from the parse function

    Master function of repo that performs aspect mining on product and
    sentiment analysis on review sentences. Outputs modeled Polarizer object.
    '''

    unigramer = Unigramer()
    unigramer.candidate_unigrams(corpus)

    bigramer = Bigramer(unigramer)
    bigramer.candidate_bigrams(corpus)

    trigramer = Trigramer(bigramer)
    trigramer.candidate_trigrams(corpus)

    bigramer.pop_bigrams(trigramer)
    unigramer.update_review_count(bigramer, trigramer)

    polarizer = Polarizer(unigramer, bigramer, trigramer)
    polarizer.polarize_aspects(corpus)

    return polarizer
