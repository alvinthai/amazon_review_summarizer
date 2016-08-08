from __future__ import division
from pprint import pprint
import pandas as pd


def get_top_aspects(corpus, unigramer, bigramer, n=10, printing=True):
    '''
    INPUT: ReviewSents, Unigramer, Bigramer, int, bool
    OUTPUT: list(tuple)

    Returns a list of the top appearing aspects across all reviews
    Prints out top n aspects
    '''
    aspects = list(unigramer.unigrams)
    bigrams = list(bigramer.bigrams)

    aspects_rev_f = [len(unigramer.rev_dict[unigram]) for unigram in aspects]
    bigrams_rev_f = [len(bigramer.rev_dict[bigram]) for bigram in bigrams]

    aspects.extend(bigrams)
    aspects_rev_f.extend(bigrams_rev_f)

    top_aspects = sorted(zip(aspects, aspects_rev_f),
                         key=lambda x: x[1], reverse=True)

    if printing:
        pprint(top_aspects[0:n])

    return top_aspects


def common_features(aspects1, aspects2, corpus1, corpus2, min_pct=0.03,
                    n=10, printing=True):
    '''
    INPUT: list(tuples), list(tuples), ReviewSents, ReviewSents, float,
           int, bool
    OUTPUT: np.array([aspect, freq1, freq2]), list

    Outputs a list of the common aspects between two products.

    List returned from sort_aspect_frequency is the input for the first and
        second arguments of this function

    Results of output are sorted by f1 score like calculation using the
        frequencies the aspect appears in product1 and product2.
    '''
    comm_aspects = pd.merge(pd.DataFrame(aspects1, columns=['aspect', 'freq']),
                            pd.DataFrame(aspects2, columns=['aspect', 'freq']),
                            on='aspect', suffixes=('1', '2'))

    comm_aspects['pct1'] = comm_aspects['freq1'] / corpus1.n_reviews
    comm_aspects['pct2'] = comm_aspects['freq2'] / corpus2.n_reviews

    comm_aspects = comm_aspects[(comm_aspects['pct1'] >= min_pct) &
                                (comm_aspects['pct2'] >= min_pct)]

    comm_aspects['sort'] = (comm_aspects['pct1'] * comm_aspects['pct2'] /
                            (comm_aspects['pct1'] + comm_aspects['pct2']))

    comm_aspects.sort_values('sort', ascending=False, inplace=True)
    output = comm_aspects.values[:, 0:3]

    if printing:
        pprint(output[0:n])

    return output[:, 0:3], output[:, 0].tolist()
