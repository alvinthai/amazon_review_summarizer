from parsers import *
from polarizer import *
from scraper import *


def load(url, n_reviews=300, delete=False):
    '''
    INPUT: str, int, bool
    OUTPUT: Loader, list

    Args:
        url: url of amazon product
        n_reviews: number of reviews to scrape
        delete: whether to delete existing reviews that have been
            scraped (if old reviews exist, no scraping is attempted)

    Scrapes an amazon url and returns the scraped object and a list of lists
    of the product's review data.
    '''
    doc = Loader(url)
    doc.scrape(300)
    data = [doc.authors, doc.headlines, doc.ratings, doc.reviews]

    return doc, data


def parse(doc):
    '''
    INPUT: Loader
    OUTPUT: ReviewSents

    Args:
        doc: a scrpaed Loader object from the load function

    Uses spacy to tokenize sentences in review and returns custom class of
    review data for later processing
    '''
    return ReviewSents(doc)


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
