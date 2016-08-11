from flask import Flask, request, render_template
from scripts.app_preparer import collect
import cPickle
import json
import numpy as np
import requests


app = Flask(__name__)

# with open('data/polarizer3.pkl', 'rb') as f:
#     pol1 = cPickle.load(f)
# with open('data/polarizer4.pkl', 'rb') as f:
#     pol2 = cPickle.load(f)
# with open('data/sample_authors.pkl', 'rb') as f:
#     authors_lst = cPickle.load(f)
# with open('data/sample_headlines.pkl', 'rb') as f:
#     headlines_lst = cPickle.load(f)
# with open('data/sample_ratings.pkl', 'rb') as f:
#     ratings_lst = cPickle.load(f)
# with open('data/sample_reviews.pkl', 'rb') as f:
#     reviews_lst = cPickle.load(f)

# title1, title2 = pol1.name, pol2.name
# url1, url2 = "", ""
# price1, price2 = "$1", "$1"
# img_url1 = "https://images-na.ssl-images-amazon.com/" \
#     "images/I/71rHYqOkvNL._SX466_.jpg"
# img_url2 = "https://images-na.ssl-images-amazon.com/" \
#     "images/I/91L30nswRuL._SY450_.jpg"


@app.route('/')
def home():
    return render_template('compare_home.html')


@app.route('/compare_results', methods=['POST'])
def compare_results():
    url1 = str(request.form['url1'].encode('utf-8'))
    url2 = str(request.form['url2'].encode('utf-8'))
    output_dic = collect(url1, url2)
    globals().update(output_dic)
    return render_template('compare_results.html', aspects=en_aspects,
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
    app.run(host='0.0.0.0', port=8080, debug=True)
