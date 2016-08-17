'''
This file stores variables of items to filter out during the execution of the
functions inside the parsers.py script
'''

# list of dependencies not likely to be words found in features
com_dep = set(['det', 'aux', 'cc', 'punct', 'mark', '', 'neg', 'nummod',
               'prt', 'auxpass', 'case', 'expl', 'preconj', 'intj',
               'predet', 'meta', 'quantmod', 'agent'])

# list of POS tags not likely to be words found in features
com_tag = set(['IN', 'PRP', 'PRP$', 'DT', 'HYPH', 'TO', ',', '.', 'CC',
               'SP', 'CD', 'MD', 'WDT', 'RP', 'WRB', '-LRB-', '-RRB-',
               ':', 'WP', 'POS', '``', "''", 'SYM', 'EX', 'PDT', 'UH',
               'NFP', 'XX'])

# list of POS tag belonging to nouns
noun_tag = set(['NN', 'NNP', 'NNS'])

# stopword aspects to filter out
nonaspects = set(['product', 'price', 'device', 'review', 'item',
                  'amazon', 'everything', 'company', 'brand',
                  'buy', 'purchase', 'cost', 'year', 'month', 'day',
                  'week', 'hour', 'problem', 'issue', 'give'])

# stopword adjectives to filter out
nonadj = set(['other', 'first', 'second', 'third', 'much'])
