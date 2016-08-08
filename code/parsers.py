from __future__ import division
from collections import Counter, defaultdict
from sklearn.feature_extraction.text import CountVectorizer
from spacy.en import English
from textblob import TextBlob
from wordsets import com_dep, com_tag, noun_tag, nonaspects
import numpy as np
import re

parser = English()


class SentCustomProperties(object):
    '''
    Adds properties to spacy sentences
    '''

    def __init__(self, review_idx, rating, sent_idx, sent):
        '''
        INPUT: int, int, int, spacy sentence (spacy.tokens.span.Span)
        OUTPUT: None

        Attribures:
            review_idx (int): index of review where sentence originated
            review_rate (int): customer review rating
            sent (spacy.tokens.span.Span): spacy Span object
            sent_idx (int): index of sentence within review corpus
            start_idx (int): index of first token in sentence within review
            words (int): num of words in sentences
        '''
        self.review_idx = review_idx
        self.review_rate = rating
        self.sent = sent
        self.sent_idx = sent_idx
        self.start_idx = sent[0].i
        self.words = len(sent)


class ReviewSents(object):
    '''
    Takes a list of unicode reviews and stores the sentences
    (with additional properties) in the returned object
    '''

    def __init__(self, product):
        '''
        INPUT: Loader
        OUTPUT: None

        Attribures:
            n_reviews (int): total number of reviews for product
            n_sent (int): total number of sentences in all reviews for product
            name (str): name of product
            ratings (list): list of customer review ratings for product
            reviews (list): list of customer review text for product
            sentences (list): list of SentCustomProperties objects
        '''
        self.name = product.name
        self.ratings = product.ratings
        self.reviews = product.reviews
        self.n_reviews, self.n_sent, self.sentences = self._parse_sentences()

    def _parse_sentences(self):
        '''
        INPUT: None
        OUTPUT: int, int, list(SentCustomProperties)

        Uses spacy to parse and split the sentences
        Return number of reviews, sentences, and list of spacy objects
        '''
        regex = re.compile(r'\.\.\.\.+')

        n_sent, n_reviews = 0, 0
        sentences = []

        for i, review in enumerate(self.reviews):
            try:
                review = regex.sub(u'...', review)
                review = parser(review)
                n_reviews += 1
            except AssertionError:
                print 'parser for review #{} failed'.format(i)
                continue

            for sent in review.sents:
                if sent.string:
                    sentences.append(SentCustomProperties(i, self.ratings[i],
                                                          n_sent, sent))
                    n_sent += 1

        return n_reviews, n_sent, sentences


class Unigramer(object):
    '''
    Class of functions for extracting Unigrams
    '''

    def __init__(self):
        '''
        Attribures:
            cnt_dict (dict):      dictionary with word as key and count of how
                                  frequently such word appears in all review
                                  for products as value
            dep_dict (dict):      dictionary with word as key and list of every
                                  dependency type that corresponding with the
                                  word element as value
            n_reviews (int):      total number of reviews for product
            rev_dict (dict):      dictionary with word as key and set of review
                                  indexes containg word as value
            sent_dict (dict):     dictionary with word as key and list of
                                  sentence indexes containg word as value
            unigrams (set):       set of unigrams obtained with
                                  candidate_unigrams function
            word_pos_dict (dict): dictionary with word as key and list of
                                  token index of word within spacy sentence as
                                  value
        '''
        self.cnt_dict = defaultdict(int)
        self.dep_dict = defaultdict(list)
        self.n_reviews = None
        # self.pol_dict = defaultdict(list)
        self.rev_dict = defaultdict(set)
        self.sent_dict = defaultdict(list)
        self.unigrams = None
        self.word_pos_dict = defaultdict(list)

    def _iter_nouns(self, sent):
        '''
        INPUT: SentCustomProperties
        OUTPUT: str

        Iterates through each token of spacy sentence and collects
        lemmas of all nouns into a set.
        '''
        wordset = set()

        for token in sent.sent:
            self.cnt_dict[token.lemma_] += 1
            self.dep_dict[token.head.lemma_].append(token.dep_)
            root = parser.vocab[token.lemma].prob

            # filter to only consider nouns, valid aspects, and uncommon words
            if token.tag_ in noun_tag and (root < -7.5 and
                                           token.lemma_ not in nonaspects):
                wordset.add(token.lemma_)
                self.rev_dict[token.lemma_].add(sent.review_idx)

                if sent.sent_idx not in self.sent_dict[token.lemma_]:
                    i = token.i - sent.start_idx
                    self.word_pos_dict[token.lemma_].append(i)
                    self.sent_dict[token.lemma_].append(sent.sent_idx)

            # if token.dep_ == 'amod':
            #     pol = abs(TextBlob(token.string).sentiment.polarity) > 0
            #     self.pol_dict[token.head.lemma_].append(pol)

        return " ".join(wordset)

    def candidate_unigrams(self, corpus, min_pct=0.01, amod_pct=0.094):
        '''
        INPUT: ReviewSents, float, float
        OUTPUT: set

        Args:
            min_pct: percentage of sentences unigram must appear in
            amod_pct: minimum percentage where word element has a corresponding
                      'amod' dependency

        Obtains a set of candidate unigrams
        Each candidate unigram must be a noun
        '''
        count_X = []
        self.n_reviews = corpus.n_reviews

        for sent in corpus.sentences:
            count_X.append(self._iter_nouns(sent))

        cnt_vec = CountVectorizer()
        freq = cnt_vec.fit_transform(count_X)

        total_count = freq.toarray().sum(axis=0)
        filter_ = total_count >= min_pct * corpus.n_sent

        # filter for aspect appearing in min_pct of sentences
        features = np.array(cnt_vec.get_feature_names())
        unigrams = set(features[filter_])

        # filter for percentage of time aspect is modified by amod
        for word in unigrams.copy():
            arr = np.array(self.dep_dict[word]) == 'amod'

            if np.mean(arr) < amod_pct:
                unigrams.remove(word)

        self.unigrams = unigrams

        return unigrams

    def update_review_count(self, bigramer):
        '''
        IMPUT: Bigramer
        OUTPUT: none

        Updates Unigramer rev_dict so that reviews aren't double counted for
        unigram words appearing in bigrams.
        '''
        update_queue = self.unigrams & bigramer.bigram_words

        for unigram in update_queue:
            for bigram in bigramer.bigrams:
                if unigram in bigram:
                    self.rev_dict[unigram] -= bigramer.rev_dict[bigram]


class Bigramer(object):
    '''
    Class of functions for extracting Bigrams
    '''
    def __init__(self):
        '''
        Attribures:
            avg_dist (dict):      dictionary with word as key and count of how
                                  frequently such word appears in all review
                                  for products as value
            bigrams (set):        set of bigrams obtained with
                                  candidate_bigrams function
            bigram_words (set):   set of words used in bigrams
            distances (dict):     dictionary with bigram as key and list of
                                  absolute word spacing difference betweeen
                                  words of bigram as values
            ordering (dict):      dictionary with bigram as key and list of
                                  which word in bigram appears first in
                                  sentence as value
            pmi (dict):           dictionary with bigram as key and float
                                  describing Pointwise Mutual Information
                                  between words in bigram as value
            rev_dict (dict):      dictionary with word as key and set of review
                                  indexes containg word as value
            sent_dict (dict):     dictionary with word as key and list of
                                  sentence indexes containg word as value
            word_pos_dict (dict): dictionary with word as key and list of
                                  token index of word within spacy sentence as
                                  value
        '''
        self.avg_dist = defaultdict(float)
        self.bigrams = None
        self.bigram_words = None
        self.distances = defaultdict(list)
        self.ordering = defaultdict(list)
        self.pmi = defaultdict(float)
        self.rev_dict = defaultdict(set)
        self.sent_dict = defaultdict(list)
        self.word_pos_dict = defaultdict(list)

    def _reverse_key(self, key, new_key):
        '''
        INPUT: str, str
        OUTPUT: None

        Args:
            key: bigram with words seperated by space
            new_key: bigram with words reversed and seperated by space

        Reverses the word order for the key in the class dictionaries
        '''
        self.avg_dist[new_key] = self.avg_dist.pop(key)
        self.distances[new_key] = self.distances.pop(key)
        self.ordering[new_key] = self.ordering.pop(key)
        self.pmi[new_key] = self.pmi.pop(key)
        self.rev_dict[new_key] = self.rev_dict.pop(key)
        self.sent_dict[new_key] = self.sent_dict.pop(key)
        self.word_pos_dict[new_key] = self.word_pos_dict.pop(key)

    def _get_compactness_feat(self, corpus):
        '''
        INPUT: ReviewSents
        OUTPUT: generator(tuples(unicode))

        Outputs generator of tuples (in alphabetical order) consisting of:
            at least one noun
            a second word within +/- 3 words of noun
        Excludes dependencies and tags not likely to be a feature word
        '''

        for sent in corpus.sentences:
            output = set()

            for i, token in enumerate(sent.sent):
                # one word in bigram must be noun
                if token.tag_ in noun_tag and token.lemma_ not in nonaspects:
                    arr = sent.sent[max(0, i - 3):min(i + 4, sent.words)]
                    arr = np.array(arr)
                    arr = arr[arr != token]

                    for item in arr:
                        root = parser.vocab[item.lemma].prob
                        # filter out unlikely features
                        if root < -7.5 and (item.dep_ not in com_dep and
                                            item.tag_ not in com_tag and
                                            item.lemma_ not in nonaspects):
                            bigrm = " ".join(sorted([item.lemma_,
                                                     token.lemma_]))
                            dist = item.i - token.i
                            word_sort = item.lemma_ < token.lemma_

                            if not self.ordering[bigrm]:
                                self.ordering[bigrm] = [0, 0]

                            self.distances[bigrm].append(abs(dist))
                            self.rev_dict[bigrm].add(sent.review_idx)
                            self.ordering[bigrm][word_sort == (dist > 0)] += 1

                            if sent.sent_idx not in self.sent_dict[bigrm]:
                                i = token.i - sent.start_idx
                                self.word_pos_dict[bigrm].append(i)
                                self.sent_dict[bigrm].append(sent.sent_idx)

                            output.add(bigrm)

            if output:
                for element in output:
                    yield element

    def candidate_bigrams(self, corpus, unigramer, min_pct=0.005,
                          pmi_pct=1/2500, max_avg_dist=2):
        '''
        INPUT: ReviewSents, Unigramer, float, float, float
        OUTPUT: set(str)

        Args:
            min_pct: percentage of sentences bigram must appear in
            pmi_pct: minimum PMI value for bigram to be considered valid
            max_avg_dist: maximum average word spacing distance for bigram to
                          be considered valud

        Outputs set of bigram strings with words in bigram seperated by space
        '''
        bigrams = set()
        bigram_words = set()
        cnt_dict = unigramer.cnt_dict

        feats = Counter(self._get_compactness_feat(corpus))

        for (key, val) in feats.iteritems():
            order = sorted(key.split(" "),
                           reverse=self.ordering[key][1] >
                           self.ordering[key][0])
            new_key = " ".join(order)

            pmi = round(val / (cnt_dict[order[0]] * cnt_dict[order[1]]), 4)
            avg_dist = round(np.mean(self.distances[key]), 2)

            if pmi >= pmi_pct and (avg_dist < max_avg_dist and
                                   val >= max(2, min_pct * corpus.n_sent)):
                self.avg_dist[key] = avg_dist
                self.pmi[key] = pmi

                bigrams.add(new_key)
                bigram_words.update(set(order))

                if key != new_key:
                    self._reverse_key(key, new_key)

        self.bigrams = bigrams
        self.bigram_words = bigram_words

        return bigrams
