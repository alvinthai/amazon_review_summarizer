from parsers import *
from polarizer import *
from scraper import *


def summarize(url, n_reviews=300, delete=False):
    '''
    INPUT: str, int, bool
    OUTPUT: Polarizer, list

    args:
        url (str): url of amazon product
        n_reviews (int): number of reviews to scrape
        delete (bool): whether to delete existing reviews that have been
            scraped (if old reviews exist, no scraping is attempted)

    Master function of repo that scrapes an amazon url, performs aspect mining
    on product, and performs sentiment analysis on review sentences. Outputs
    modeled Polarizer object and list of (author, headline, rating, review_txt)
    data.
    '''
    doc = Loader(url)
    doc.scrape(n_reviews, delete)

    data = [doc.authors, doc.headlines, doc.ratings, doc.reviews]

    corpus = ReviewSents(doc)

    unigramer = Unigramer()
    unigramer.candidate_unigrams(corpus)

    bigramer = Bigramer()
    bigramer.candidate_bigrams(corpus, unigramer)
    unigramer.update_review_count(bigramer)

    polarizer = Polarizer(unigramer, bigramer)
    polarizer.polarize_aspects(corpus)

    return polarizer, data
