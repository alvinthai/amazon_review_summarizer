from flask import Flask, request, render_template
from scripts.app_preparer import collect
import cPickle
import json
import numpy as np
import requests


app = Flask(__name__)


@app.route('/')
def compare_home():
    return render_template('compare_home.html')


@app.route('/summarize_home')
def summarize_home():
    return render_template('summarize_home.html')


@app.route('/compare_results', methods=['POST'])
def compare_results():
    url1 = str(request.form['url1'].encode('utf-8'))
    url2 = str(request.form['url2'].encode('utf-8'))

    if not url1 or not url2:
        raise RuntimeError("No url entered")

    output_dic = collect(url1, url2)

    if output_dic == "No matches":
        return render_template('no_matches.html')
    elif output_dic == "Scraping failed":
        return render_template('failed.html')
    else:
        globals().update(output_dic)

    return render_template('compare_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls)


@app.route('/summarize_results', methods=['POST'])
def summarize_results():
    url1 = str(request.form['url1'].encode('utf-8'))

    if not url1:
        raise RuntimeError("No url entered")

    output_dic = collect(url1)

    if output_dic == "Scraping failed":
        return render_template('failed.html')
    else:
        globals().update(output_dic)

    return render_template('summarize_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr, img_urls=img_urls,
                           titles=titles, prices=prices, urls=urls)


@app.route('/full_review')
def full_review():
    product = int(request.args.get('product'))
    review_idx = int(request.args.get('review_idx'))

    auth = authors_lst[product][review_idx]
    head = headlines_lst[product][review_idx]
    rate = ratings_lst[product][review_idx]
    revw = reviews_lst[product][review_idx]

    return render_template('full_review.html', author=auth, headline=head,
                           rating=rate, review=revw)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)
