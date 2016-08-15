from collections import defaultdict
from celery import Celery
from flask import Flask, request, render_template, session
from gevent.wsgi import WSGIServer
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
app.config['SECRET_KEY'] = os.urandom(24)
app.config.update(
    CELERY_BROKER_URL='redis://localhost:6379',
    CELERY_RESULT_BACKEND='redis://localhost:6379'
)
celery = Celery(app.name, backend=app.config['CELERY_RESULT_BACKEND'],
                broker=app.config['CELERY_BROKER_URL'])
review_dic = defaultdict(dict)


@celery.task
def scraper(url):
    try:
        return load(url)
    except:
        raise RuntimeError("Scraping failed")


@celery.task
def aspectize(asin):
    product = Loader().extract(asin)
    corpus = ReviewSents(product)
    polarizer = summarize(corpus)
    return product, polarizer


@app.route('/')
def compare_home():
    return render_template('compare_home.html')


@app.route('/compare_scraped', methods=['POST'])
def compare_scraped():
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

    return render_template('compare_scraped.html')


@app.route('/compare_results', methods=['POST'])
def compare_results():
    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    print session['products']

    asin1, asin2 = session['products']

    polarizers = [aspectize.delay(asin) for asin in session['products']]
    product1, polarizer1 = next(polarizers[0].collect())[1]
    product2, polarizer2 = next(polarizers[1].collect())[1]

    result = collect(polarizer1, product1, polarizer2, product2)

    if result == "No matches":
        return render_template('no_matches.html')
    else:
        [aspectsf, aspects_pct, en_aspects, ratings, html_str, js_arr,
         img_urls, prices, titles, urls, authors_lst, headlines_lst,
         ratings_lst, reviews_lst, session_url] = result

        review_dic[session_url]['authors_lst'] = authors_lst
        review_dic[session_url]['headlines_lst'] = headlines_lst
        review_dic[session_url]['ratings_lst'] = ratings_lst
        review_dic[session_url]['reviews_lst'] = reviews_lst

        print "post request completed at " + \
            datetime.datetime.now().time().isoformat()

    return render_template('compare_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls,
                           session=session_url)


@app.route('/summarize_home')
def summarize_home():
    return render_template('summarize_home.html')


@app.route('/summarize_scraped', methods=['POST'])
def summarize_scraped():
    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    url = str(request.form['url1'].encode('utf-8'))

    if not url:
        raise RuntimeError("No url entered")

    try:
        item = scraper.delay(url)
    except RuntimeError:
        return render_template('failed.html')

    asin = next(item.collect())[1].asin

    session['products'] = asin

    print "post request completed at " + \
        datetime.datetime.now().time().isoformat()

    return render_template('summarize_scraped.html')


@app.route('/summarize_results', methods=['POST'])
def summarize_results():
    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    print session['products']

    asin = session['products']
    polarizer = aspectize.delay(asin)
    product, polarizer = next(polarizer.collect())[1]

    result = collect(polarizer, product)

    [aspectsf, aspects_pct, en_aspects, ratings, html_str, js_arr,
     img_urls, prices, titles, urls, authors_lst, headlines_lst,
     ratings_lst, reviews_lst, session_url] = result

    review_dic[session_url]['authors_lst'] = authors_lst
    review_dic[session_url]['headlines_lst'] = headlines_lst
    review_dic[session_url]['ratings_lst'] = ratings_lst
    review_dic[session_url]['reviews_lst'] = reviews_lst

    print "post request completed at " + \
        datetime.datetime.now().time().isoformat()

    return render_template('summarize_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls,
                           session=session_url)


@app.route('/full_review')
def full_review():
    session_url = request.args.get('session')
    product = int(request.args.get('product'))
    review_idx = int(request.args.get('review_idx'))

    auth = review_dic[session_url]['authors_lst'][product][review_idx]
    head = review_dic[session_url]['headlines_lst'][product][review_idx]
    rate = review_dic[session_url]['ratings_lst'][product][review_idx]
    revw = review_dic[session_url]['reviews_lst'][product][review_idx]

    return render_template('full_review.html', author=auth, headline=head,
                           rating=rate, review=revw)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000)
