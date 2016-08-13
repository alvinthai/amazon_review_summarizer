from collections import defaultdict
from flask import Flask, request, render_template
import datetime
import json
import numpy as np
import requests

try:
    from scripts.app_preparer import collect
except:
    from app_preparer import collect

app = Flask(__name__)


@app.route('/')
def compare_home():
    return render_template('compare_home.html')


@app.route('/summarize_home')
def summarize_home():
    return render_template('summarize_home.html')


@app.route('/compare_results', methods=['POST'])
def compare_results():
    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    url1 = str(request.form['url1'].encode('utf-8'))
    url2 = str(request.form['url2'].encode('utf-8'))

    if not url1 or not url2:
        raise RuntimeError("No url entered")

    result = collect(url1, url2)

    if result == "No matches":
        return render_template('no_matches.html')
    elif result == "Scraping failed":
        return render_template('failed.html')
    else:
        [aspectsf, aspects_pct, en_aspects, ratings, html_str, js_arr,
         img_urls, prices, titles, urls, authors_lst, headlines_lst,
         ratings_lst, reviews_lst, session] = result

        review_dic[session]['authors_lst'] = authors_lst
        review_dic[session]['headlines_lst'] = headlines_lst
        review_dic[session]['ratings_lst'] = ratings_lst
        review_dic[session]['reviews_lst'] = reviews_lst

        print "post request completed at " + \
            datetime.datetime.now().time().isoformat()

    return render_template('compare_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls,
                           session=session)


@app.route('/summarize_results', methods=['POST'])
def summarize_results():
    print "post request started at " + \
        datetime.datetime.now().time().isoformat()

    url1 = str(request.form['url1'].encode('utf-8'))

    if not url1:
        raise RuntimeError("No url entered")

    result = collect(url1)

    if result == "Scraping failed":
        return render_template('failed.html')
    else:
        [aspectsf, aspects_pct, en_aspects, ratings, html_str, js_arr,
         img_urls, prices, titles, urls, authors_lst, headlines_lst,
         ratings_lst, reviews_lst, session] = result

        review_dic[session]['authors_lst'] = authors_lst
        review_dic[session]['headlines_lst'] = headlines_lst
        review_dic[session]['ratings_lst'] = ratings_lst
        review_dic[session]['reviews_lst'] = reviews_lst

        print "post request completed at " + \
            datetime.datetime.now().time().isoformat()

    return render_template('summarize_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls,
                           session=session)


@app.route('/full_review')
def full_review():
    session = request.args.get('session')
    product = int(request.args.get('product'))
    review_idx = int(request.args.get('review_idx'))

    auth = review_dic[session]['authors_lst'][product][review_idx]
    head = review_dic[session]['headlines_lst'][product][review_idx]
    rate = review_dic[session]['ratings_lst'][product][review_idx]
    revw = review_dic[session]['reviews_lst'][product][review_idx]

    return render_template('full_review.html', author=auth, headline=head,
                           rating=rate, review=revw)


if __name__ == '__main__':
    review_dic = defaultdict(dict)
    app.run(host='0.0.0.0', port=8000)
