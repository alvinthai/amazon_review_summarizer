from __future__ import division
from afinn import Afinn
from collections import defaultdict
from textblob import TextBlob
import numpy as np

afinn = Afinn()


class Polarizer(object):
    '''
    Class of functions for determing polarity of reviews
    '''

    def __init__(self, unigramer, bigramer):
        '''
        INPUT: Unigramer, Bigramer
        OUTPUT: None

        Attributes:
            aspect_dict (dict):     dictionary with aspect as key and review
                                    number as subkey. combines sentences
                                    containing aspects from the same review
                                    into a single text, tracks the first
                                    occurance of the aspect within text block,
                                    and stores customer rating of review
            aspect_pct (dict):      dictionary with aspect as key and list of
                                    floats [pos, mixed, neg] representing
                                    polarity class proportion within aspect
                                    as value
            aspect_pol_list (dict): dictionary with aspect as key and polarity
                                    class (pos, mixed, neg) as subkey. values
                                    are lists containing info on
                                    (review_txt, aspect_idx, rating, pol_blob)
            bigramer (Bigramer):    stores Bigramer class
            name (str):             name of product
            ratings (dict):         dictionary with aspect as key and customer
                                    ratings for reviews containing aspect as
                                    values
            unigramer (Unigramer):  stores Unigramer class
        '''
        self.aspect_dict = dict()
        self.aspect_pct = dict()
        self.aspect_pol_list = defaultdict(dict)
        self.bigramer = bigramer
        self.name = None
        self.ratings = defaultdict(list)
        self.unigramer = unigramer

    def _aspect_review_dict(self, corpus, aspect):
        '''
        INPUT: ReviewSents, str
        OUTPUT: None

        Args:
            aspect: aspect to create dictionary for

        Creates a dictionary for the aspect position, customer rating, and
        sentences associated with the specified aspect.
        '''
        prev_sent = -1

        if " " not in aspect:
            # aspect is a unigram
            rev_idx = self.unigramer.rev_dict[aspect]
            sent_idx = self.unigramer.sent_dict[aspect]
            word_pos_idx = self.unigramer.word_pos_dict[aspect]
        else:
            # aspect is a bigram
            rev_idx = self.bigramer.rev_dict[aspect]
            sent_idx = self.bigramer.sent_dict[aspect]
            word_pos_idx = self.bigramer.word_pos_dict[aspect]

        review_dict = defaultdict(dict)

        for s, w in zip(sent_idx, word_pos_idx):
            review = corpus.sentences[s].review_idx

            if review not in rev_idx:
                continue

            if review not in review_dict:
                review_dict[review]['sentences'] = ''
                review_dict[review]['first_aspect_idx'] = None

            if s == prev_sent:
                continue
            else:
                rating = corpus.sentences[s].review_rate
                sentence = corpus.sentences[s].sent.string
                self.ratings[aspect].append(rating)

                review_dict[review]['rating'] = rating
                review_dict[review]['sentences'] += sentence

                if not review_dict[review]['first_aspect_idx']:
                    i = len(corpus.sentences[s].sent[0:w].string)
                    review_dict[review]['first_aspect_idx'] = i

        self.aspect_dict[aspect] = review_dict

    def _polarity_class(self, aspect, review):
        '''
        INPUT: str, int
        OUTPUT: None

        Args:
            aspect: aspect dictionary to use
            review: review to score polarity on

        Function that determines polarity of a review.

        Assigns positive/negative polarity class to polarity according to the
        following custom rules:

            pol_blob = polarity score from TextBlob
            pol_afin = polarity score from Afinn

            POS:      rating == 5 AND pol_blob > 0.1
                   OR rating == 4 AND pol_blob > 0.45
                   OR rating == 4 AND pol_blob > 0.2 and pol_afin >= 4
                   OR rating == 3 AND pol_blob > 0.7
            NEG:      rating == 1 AND pol_blob < 0
                   OR rating == 1 AND pol_blob <= 0.2 AND pol_afin < 0
                   OR rating == 2 AND pol_blob < 0
                   OR rating == 2 AND pol_blob <= 0.175 AND pol_afin < 0
                   OR rating == 3 AND pol_blob < 0
            MIXED:    all other cases

        Adds tuple of (review_txt, aspect_idx, rating, pol_blob) to
        self.aspect_pol_list object.
        '''
        aspect_idx = self.aspect_dict[aspect][review]['first_aspect_idx']
        rating = self.aspect_dict[aspect][review]['rating']
        review_txt = self.aspect_dict[aspect][review]['sentences']

        pol_blob = round(TextBlob(review_txt).sentiment.polarity, 3)

        if rating == 5 and pol_blob > 0.1:
            result = 'pos'
        elif rating == 4 and pol_blob > 0.45:
            result = 'pos'
        elif rating == 4 and pol_blob > 0.2:
            pol_afin = afinn.score(review_txt)
            result = 'pos' if pol_afin >= 4 else 'mixed'
        elif rating == 3 and pol_blob > 0.7:
            result = 'pos'
        elif rating == 3 and pol_blob < 0:
            result = 'neg'
        elif rating == 2 and pol_blob < 0:
            result = 'neg'
        elif rating == 2 and pol_blob <= 0.175:
            pol_afin = afinn.score(review_txt)
            result = 'neg' if pol_afin < 0 else 'mixed'
        elif rating == 1 and pol_blob < 0:
            result = 'neg'
        elif rating == 1 and pol_blob <= 0.2:
            pol_afin = afinn.score(review_txt)
            result = 'neg' if pol_afin < 0 else 'mixed'
        else:
            result = 'mixed'

        output = (review_txt, aspect_idx, rating, pol_blob)

        self.aspect_dict[aspect][review]['pol_val'] = pol_blob
        self.aspect_pol_list[aspect][result].append(output)

    def _sort_polarity(self, aspect):
        '''
        INPUT: str
        OUTPUT: None

        Sorts self.aspect_pol_list object by polarity score
        '''
        dic = self.aspect_pol_list[aspect]

        for category in dic:
            dic[category] = sorted(dic[category], key=lambda x: x[3],
                                   reverse=category != 'neg')

    def _get_pol_class_pct(self, aspect):
        '''
        INPUT: str
        OUTPUT: None

        Args:
            aspect: aspect to calculate polarity class percentage for

        Calculates percentage of results belonging to each polarity class
        '''
        dic = self.aspect_pol_list[aspect]

        pos = len(dic['pos'])
        mixed = len(dic['mixed'])
        neg = len(dic['neg'])
        total = pos + mixed + neg

        pos = round(pos / total, 3) * 100
        mixed = round(mixed / total, 3) * 100
        neg = round(neg / total, 3) * 100

        self.aspect_pct[aspect] = [pos, mixed, neg]

    def polarize_aspects(self, corpus, aspect_list):
        '''
        INPUT: ReviewSents, list(str)
        OUTPUT: None

        Args:
            aspect_list: list of aspects to pass through pipeline

        Master function of class that creates dictionary of polarity scores and
        list of review text within respective polarity class for each aspect in
        aspect_list
        '''
        self.name = corpus.name

        for aspect in aspect_list:
            self._aspect_review_dict(corpus, aspect)

            self.aspect_pol_list[aspect]['pos'] = []
            self.aspect_pol_list[aspect]['mixed'] = []
            self.aspect_pol_list[aspect]['neg'] = []

            for review in self.aspect_dict[aspect]:
                self._polarity_class(aspect, review)

            self._sort_polarity(aspect)
            self._get_pol_class_pct(aspect)

    def print_polarity(self, aspect, max_txt_len=80, lines_pos=0,
                       lines_mixed=0, lines_neg=0, printing=True):
        '''
        INPUT: str, int, int, int, int, bool
        OUTPUT: str if printing=False

        Args:
            aspect: aspect to print result for
            max_txt_len: max length for each printed line
            lines_pos: if > 0, number of lines to print for positive sentiment
            lines_mixed: if > 0, number of lines to print for mixed sentiment
            lines_neg: if > 0, number of lines to print for negative sentiment
            printing: option to permit or supress printing

        Prints out the polarity and full text sentences for reviews containing
        aspect
        '''
        dic = self.aspect_pol_list[aspect]
        categories = [('pos', 'Positive Sentiment', lines_pos),
                      ('mixed', 'Mixed Sentiment', lines_mixed),
                      ('neg', 'Negative Sentiment', lines_neg)]

        big_str = ('-' * (max_txt_len - 2)).ljust(max_txt_len) + '\n'
        big_str += self.name[0:max_txt_len - 2].ljust(max_txt_len) + '\n'
        big_str += ('-' * (max_txt_len - 2)).ljust(max_txt_len) + '\n\n'

        big_str += ('-' * 39).ljust(max_txt_len) + '\n'
        big_str += aspect.ljust(max_txt_len) + '\n'
        big_str += ('-' * 39).ljust(max_txt_len) + '\n\n'

        good, mixed, bad = self.aspect_pct[aspect]

        big_str += 'average rating: {}'.format(np.mean(self.ratings[aspect])) \
                   .ljust(max_txt_len) + '\n'
        big_str += 'positive: {}%'.format(good).ljust(max_txt_len) + '\n'
        big_str += 'mixed: {}%'.format(mixed).ljust(max_txt_len) + '\n'
        big_str += 'negative: {}%'.format(bad).ljust(max_txt_len) + '\n\n'

        for category, label, total_lines in categories:
            big_str += label.ljust(max_txt_len) + '\n'
            big_str += ('-' * 28).ljust(max_txt_len) + '\n'

            for txt, asp_idx, _, _ in dic[category]:
                reach = 10
                frag = txt

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
                    big_str += frag.strip().ljust(max_txt_len) + '\n'
                    if total_lines:
                        total_lines -= 1

            big_str += (' ' * max_txt_len + '\n') * (total_lines + 1)

        if printing:
            print big_str
        else:
            return big_str

    def flask_output(self, aspect, pol_class, max_txt_len=80):
        '''
        INPUT: str, str, int
        OUTPUT: str

        Args:
            aspect: aspect to print result for
            pol_class: 'pos', 'mixed', or 'neg' sentiment
            max_txt_len: max length for each printed line

        Outputs a string of html/javascript code for input into flask/jinja
        '''
        arr = self.aspect_pol_list[aspect][pol_class]
        big_str = ""

        for txt, asp_idx, _, _ in arr:
            reach = 10
            frag = txt

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
                big_str += '''<hr>'''
                big_str += '''<div class="row">'''
                big_str += '''<div class="col-md-12">'''
                big_str += frag.strip().ljust(max_txt_len)
                big_str += '''</div>'''
                big_str += '''</div>'''

        return big_str
