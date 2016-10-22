'''
This script should be executed inside the app folder to run the applicaiton.
Mongo, Celery and Redis-Server are prerequisites to running the app.
See the readme.md for more info on how to install/run Mongo, Celery and
Redis-Server.
'''

from celery import Celery
from flask import Flask, redirect, render_template, request, session, url_for
from pymongo import MongoClient
import datetime
import json
import numpy as np
import os
import requests

from app_preparer import collect
from parsers import ReviewSents
from pipeline import load, summarize
from scraper import Loader

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)   # random cookie
app.config.update(CELERY_BROKER_URL='redis://localhost:6379',
                  CELERY_RESULT_BACKEND='redis://localhost:6379')

celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'],
                broker=app.config['CELERY_BROKER_URL'])

client = MongoClient()
db = client['ars']
tab = db['review_data']

check1 = list(tab.find({'_id': 'B004NBXVFS_0'}))
check2 = list(tab.find({'_id': 'B00J7B8T5Q_0'}))

if not check1 or not check2:
    # adds sample data to mongoDB if it doesn't exist
    from sample_data import store_sample_data
    store_sample_data()


@celery.task
def scraper(url):
    '''parallelizes the load function'''

    try:
        return load(url)
    except:
        raise RuntimeError("Scraping failed")


@celery.task
def aspectize(asin):
    '''paralellizes the sentiment analysis pipeline'''

    product = Loader().extract(asin)
    corpus = ReviewSents(product)
    polarizer = summarize(corpus)
    return product, polarizer


@app.route('/')
def home():
    '''home page'''

    return render_template('home.html')


@app.route('/sample_results')
def sample_results():
    '''sample product comparison results'''

    return render_template('sample_results.html')


@app.route('/compare_home')
def compare_home():
    '''home page for product comparison url input'''

    return render_template('compare_home.html')


@app.route('/compare_scraped', methods=['POST'])
def compare_scraped():
    '''intermediate function for product comparison that scrapes product asin
    and stores cookies'''

    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    url1 = str(request.form['url1'].encode('utf-8'))
    url2 = str(request.form['url2'].encode('utf-8'))

    if not url1 or not url2:
        raise RuntimeError("No url entered")

    try:
        items = [scraper.delay(url) for url in [url1, url2]]
    except RuntimeError:
        return render_template('failed.html')

    asin1 = next(items[0].collect())[1].asin
    asin2 = next(items[1].collect())[1].asin

    session['products'] = [asin1, asin2]

    print "post request completed at " + \
        datetime.datetime.now().time().isoformat()

    return redirect(url_for('compare_results'))


@app.route('/compare_results')
def compare_results():
    '''runs aspect mining, sentiment analysis, and outputs final results for
    product comparison'''

    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    try:
        print session['products']
    except RuntimeError:
        return render_template('failed.html')

    asin1, asin2 = session['products']

    polarizers = [aspectize.delay(asin) for asin in session['products']]
    product1, polarizer1 = next(polarizers[0].collect())[1]
    product2, polarizer2 = next(polarizers[1].collect())[1]

    result = collect(polarizer1, polarizer2)

    if result == "No matches":
        return render_template('no_matches.html')
    else:
        [aspectsf, aspects_pct, en_aspects, ratings, html_str, js_arr,
         img_urls, prices, titles, urls] = result

        print "post request completed at " + \
            datetime.datetime.now().time().isoformat()

    return render_template('compare_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls)


@app.route('/summarize_home')
def summarize_home():
    '''home page for product summarization url input'''

    return render_template('summarize_home.html')


@app.route('/summarize_scraped', methods=['POST'])
def summarize_scraped():
    '''intermediate function for product summarization that scrapes product
    asin and stores cookies. does not involve the use of celery'''

    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    url = str(request.form['url1'].encode('utf-8'))

    if not url:
        raise RuntimeError("No url entered")

    try:
        item = load(url)
    except RuntimeError:
        return render_template('failed.html')

    session['products'] = item.asin

    print "post request completed at " + \
        datetime.datetime.now().time().isoformat()

    return redirect(url_for('summarize_results'))


@app.route('/summarize_results')
def summarize_results():
    '''runs aspect mining, sentiment analysis, and outputs final results for
    product summarization. does not involve the use of celery'''
    print "post request started at " + \
        datetime.datetime.now().time().isoformat()
    
    try:
        print session['products']
    except RuntimeError:
        return render_template('failed.html')

    asin = session['products']
    product = Loader().extract(asin)
    corpus = ReviewSents(product)
    polarizer = summarize(corpus)

    result = collect(polarizer)

    [aspectsf, aspects_pct, en_aspects, ratings, html_str, js_arr,
     img_urls, prices, titles, urls] = result

    print "post request completed at " + \
        datetime.datetime.now().time().isoformat()

    return render_template('summarize_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls)


@app.route('/full_review')
def full_review():
    '''directs user to page of full review details'''

    asin_id = request.args.get('asin')
    review_idx = int(request.args.get('review_idx'))
    data = tab.find({'asin': asin_id, 'review_idx': review_idx})[0]

    auth = data['author']
    head = data['headline']
    rate = data['rating']
    revw = data['review']

    return render_template('full_review.html', author=auth, headline=head,
                           rating=rate, review=revw)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
