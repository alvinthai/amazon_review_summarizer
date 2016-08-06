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
    adds properties to spacy sentence that tracks:
        index of review where sentence originated
        customer review rating
        spacy Span object
        index of sentence within review corpus
        index of first token in sentence within review
        num of words in sentences
    '''

    def __init__(self, review_idx, rating, sent_idx, sent):
        '''
        INPUT: int, int, spacy sentence (spacy.tokens.span.Span)
        OUTPUT: None
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
        '''
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
        self.dep_dict = defaultdict(list)
        self.cnt_dict = defaultdict(int)
        self.rev_dict = defaultdict(set)
        self.pol_dict = defaultdict(list)

    def _iter_nouns(self, sent):
        '''
        INPUT: SentCustomProperties
        OUTPUT: set

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

            if token.dep_ == 'amod':
                pol = abs(TextBlob(token.string).sentiment.polarity)
                self.pol_dict[token.head.lemma_].append(pol)

        return " ".join(wordset)

    def candidate_unigrams(self, corpus, min_pct=0.01, amod_pct=0.075):
        '''
        INPUT: ReviewSents, float, float
        OUTPUT: set, dict

        obtains a set of candidate unigrams

        each candidate unigram must be a noun and must appear in at least
            a percentage of the sentences specified by min_pct with the unigram
            being modified by an amod dependency at least amod_pct of the time
        '''
        count_X = []

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

        return unigrams, self.cnt_dict


class Bigramer(object):
    '''
    Class of functions for extracting Bigrams
    '''
    def __init__(self):
        self.avg_dist = defaultdict(float)
        self.distances = defaultdict(list)
        self.pmi = defaultdict(float)
        self.rev_dict = defaultdict(set)

    def _get_compactness_feat(self, corpus):
        '''
        INPUT: ReviewSents
        OUTPUT: generator(tuples(unicode))

        outputs generator of tuples (in alphabetical order) consisting of:
            at least one noun
            a second word within +/- 3 words of noun
        excludes dependencies and tags not likely to be a feature word
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
                            tup = tuple(sorted([item.lemma_, token.lemma_]))
                            dist = abs(item.i - token.i)
                            self.distances[tup].append(dist)
                            self.rev_dict[tup].add(sent.review_idx)
                            output.add(tup)

            if output:
                for element in output:
                    yield element

    def candidate_bigrams(self, corpus, cnt_dict, min_pct=0.005,
                          pmi_pct=0.000):
        '''
        INPUT: ReviewSents, cnt_dict, float
        OUTPUT: set(tuples), set(str)

        outputs set of tuples and set of words within tuples from
            _get_compactness_feat function appearing at least
            min_cnt times

        cnt_dict output from candidate_unigrams is the input for the second
            argument of this function
        '''
        bigrams = set()
        bigram_words = set()

        feats = Counter(self._get_compactness_feat(corpus))

        for (key, val) in feats.iteritems():
            pmi = round(val / (cnt_dict[key[0]] * cnt_dict[key[1]]), 4)

            if val >= max(2, min_pct * corpus.n_sent) and pmi >= pmi_pct:
                avg_dist = round(np.mean(self.distances[key]), 2)
                self.avg_dist[key] = avg_dist
                self.pmi[key] = pmi

                bigrams.add(key)
                bigram_words.update(set(key))

        return bigrams, bigram_words
