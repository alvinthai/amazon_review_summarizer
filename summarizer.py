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


def print_aspect_summary(aspect_list, polarizer1, polarizer2, line_len=115):
    '''
    INPUT: list(str), Polarizer, Polarizer
    OUTPUT: None

    Prints out a side-by-side comparison of all common aspects for two products
    '''
    big_str = ''

    for aspect in aspect_list:
        p = max(len(polarizer1.aspect_pol_list[aspect]['pos']),
                len(polarizer2.aspect_pol_list[aspect]['pos']))
        m = max(len(polarizer1.aspect_pol_list[aspect]['mixed']),
                len(polarizer2.aspect_pol_list[aspect]['mixed']))
        n = max(len(polarizer1.aspect_pol_list[aspect]['neg']),
                len(polarizer2.aspect_pol_list[aspect]['neg']))
        split = int((line_len - 1) / 2)

        str1 = polarizer1.print_polarity(aspect, max_txt_len=split,
                                         lines_pos=p, lines_mixed=m,
                                         lines_neg=n, printing=False)
        str2 = polarizer2.print_polarity(aspect, max_txt_len=split,
                                         lines_pos=p, lines_mixed=m,
                                         lines_neg=n, printing=False)

        str1 = str1.split('\n')
        str2 = str2.split('\n')

        comb_str = zip(str1, str2)
        comb_str = map(' '.join, comb_str)
        comb_str = '\n'.join(comb_str)

        big_str += comb_str + '\n'

    print big_str
