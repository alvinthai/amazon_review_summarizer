'''
Adds sample data from the sample_results.html page to MongoDB.
'''
from pymongo import MongoClient
import cPickle


def store_sample_data():
    '''
    Opens up the sample_data.pkl file and stores data into MongoDB
    '''
    client = MongoClient()
    db = client['ars']
    tab = db['review_data']

    with open('../data/sample_data.pkl', 'rb') as f:
        sample_data = cPickle.load(f)

    for asin in sample_data:
        for i, (auth, head, rate, revw) in enumerate(sample_data[asin]):
            _id = '{}_{}'.format(asin, i)

            data = {'asin': asin, 'review_idx': i, 'rating': rate,
                    'review': revw, 'author': auth, 'headline': head}

            tab.update_one({'_id': _id}, {'$set': data}, upsert=True)
