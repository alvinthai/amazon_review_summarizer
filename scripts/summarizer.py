from __future__ import division
import numpy as np
import pandas as pd


def common_features(polarizer1, polarizer2, min_pct=0.03, n=10, printing=True):
    '''
    INPUT: Polarizer, Polarizer, float, int, bool
    OUTPUT: np.array([aspect, freq1, freq2]), list

    Args:
        min_pct: percentage of reviews aspect must appear in
        n: number of reviews to print
        printing: option to print top n results

    Finds the common aspects between two products and outputs a list of these
    aspects with review frequency and a list of these aspects without review
    frequency.

    Results of output are sorted by f1 score like calculation using the
    frequencies the aspect appears in product1 and product2
    '''
    unigramer1, unigramer2 = polarizer1.unigramer, polarizer2.unigramer

    df1 = pd.concat([pd.Series(polarizer1.top_asps[0], name='aspect'),
                     pd.Series(polarizer1.top_asps[1], name='freq')], axis=1)
    df2 = pd.concat([pd.Series(polarizer2.top_asps[0], name='aspect'),
                     pd.Series(polarizer2.top_asps[1], name='freq')], axis=1)

    comm_aspects = pd.merge(df1, df2, on='aspect', suffixes=('1', '2'))

    comm_aspects['pct1'] = comm_aspects['freq1'] / unigramer1.n_reviews
    comm_aspects['pct2'] = comm_aspects['freq2'] / unigramer2.n_reviews

    comm_aspects = comm_aspects[(comm_aspects['pct1'] >= min_pct) &
                                (comm_aspects['pct2'] >= min_pct)]

    comm_aspects['sort'] = (comm_aspects['pct1'] * comm_aspects['pct2'] /
                            (comm_aspects['pct1'] + comm_aspects['pct2']))

    comm_aspects.sort_values('sort', ascending=False, inplace=True)
    output = comm_aspects.values[:, 0:3]

    if printing:
        print output[0:n]

    return output[:, 0:3], output[:, 0].tolist()


def print_aspect_summary(aspect_list, polarizer1, polarizer2, line_len=115):
    '''
    INPUT: list(str), Polarizer, Polarizer, int
    OUTPUT: None

    Args:
        aspect_list: list of aspects to compare
        line_len: line length to print out for side-by-side comparison

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


def _html_coder(ai, pi, ci, cat, dic, max_txt_len, curr_str):
    '''
    INPUT: int, int, int, str, dict, int, str
    OUTPUT: str, list

    Args:
        ai: aspect index
        pi: product index
        ci: polarity class index (0: 'pos', 1: 'mixed', 2: 'neg')
        cat: label for polarity class
        dic: dictionary to extract review text from with cat keys
        max_txt_len: max length for each printed line
        curr_str: current html string to be modified

    Appends review text data to an existing html string
    '''
    txt_list = []

    for ri, (txt, asp_idx, _, _) in enumerate(dic[cat]):
        reach, frag = 10, txt

        while len(frag) > max_txt_len:
            chars = txt.split(" ")

            lst = map(len, chars)
            lst = np.hstack([0, np.cumsum(lst)])
            lst = np.arange(lst.shape[0]) + lst

            where = np.searchsorted(lst, asp_idx)
            start = lst[max(0, where - reach)]
            end = lst[min(where + reach + 1, len(lst) - 1)]

            frag = txt[start:end]
            reach -= 1

        if frag:
            curr_str += '''<hr>'''
            curr_str += '''<div class="row">'''
            curr_str += '''<div class="col-md-12">'''
            curr_str += '''<p id="asp{0}_prd{1}_{2}_{3}">'''\
                .format(ai, pi, ci, ri)
            curr_str += '''{}'''.format(frag)
            curr_str += '''<p style="float:right">'''
            curr_str += '''<a style="color:#337ab7" '''
            curr_str += '''onclick="snippet(review_txt, {0}, {1}, {2}, {3})'''\
                .format(ai, pi, ci, ri)
            curr_str += '''">Expand Snippet</a></p>'''
            curr_str += '''</p>'''
            curr_str += '''</div>'''
            curr_str += '''</div>'''
            txt_list.append([frag.strip(), txt])

    return curr_str, txt_list


def flask_output(ai, aspect, polarizer1, polarizer2=None, max_txt_len=80):
    '''
    INPUT: int, str, Polarizer, Polarizer, int
    OUTPUT: str, list

    Args:
        ai: aspect index
        aspect: aspect to print result for
        max_txt_len: max length for each printed line

    Outputs a string of html/javascript and a three-dimensional array of review
    text for input into flask/jinja
    '''
    dic1 = polarizer1.aspect_pol_list[aspect]
    big_str, js_arr, cats = "", [], ['pos', 'mixed', 'neg']
    html_panel = ['''<div id="home" class="tab-pane fade in active">''',
                  '''<div id="menu1" class="tab-pane fade">''',
                  '''<div id="menu2" class="tab-pane fade">''']

    for ci, cat in enumerate(cats):
        big_str += html_panel[ci]
        big_str += '''<div class="col-md-75" '''
        big_str += '''style="width:37.5%; padding-right:0.6%">'''
        big_str += '''<div class="well">'''

        big_str, txt_list = _html_coder(ai, 0, ci, cat, dic1, max_txt_len,
                                        big_str)

        big_str += '''</div></div></div>'''
        js_arr.append(txt_list)

    return big_str, js_arr


def flask_output_iter(aspect_list, polarizer1, polarizer2=None, max_txt_len=80):
    '''
    INPUT: list, Polarizer, Polarizer, int
    OUTPUT: list, list

    Args:
        aspect_list: list of aspects to print result for
        max_txt_len: max length for each printed line

    Repeats flask_output for a list of array. Outputs a list of html strings
    and a five-dimensional array of review text for input into flask/jinfa
    '''
    html_strs, js_arrs = [], []

    for ai, aspect in enumerate(aspect_list):
        big_str, js_arr = flask_output(ai, aspect, polarizer1, polarizer2,
                                       max_txt_len)
        js_arr = [js_arr]

        html_strs.append(big_str)
        js_arrs.append(js_arr)

    return html_strs, js_arrs
