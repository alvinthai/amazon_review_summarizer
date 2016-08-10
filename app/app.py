from __future__ import division
from scripts.polarizer import *
from scripts.summarizer import *
from flask import Flask, request, render_template
import cPickle
import numpy as np

app = Flask(__name__)

with open('data/polarizer1.pkl', 'rb') as f:
    pol1 = cPickle.load(f)
with open('data/polarizer2.pkl', 'rb') as f:
    pol2 = cPickle.load(f)

aspectsf, aspects = common_features(pol1, pol2, printing=False)
aspectsf, aspects = aspectsf[0:10, 1:].tolist(), aspects[0:10]
en_aspects = [[x[0], x[1]] for x in enumerate(aspects)]

aspects1_pct = np.array([pol1.aspect_pct[x] for x in aspects])
aspects1_pct_vis = np.apply_along_axis(lambda x: 5 + x / sum(x) * 85, 1,
                                       aspects1_pct)
aspects2_pct = np.array([pol2.aspect_pct[x] for x in aspects])
aspects2_pct_vis = np.apply_along_axis(lambda x: 5 + x / sum(x) * 85, 1,
                                       aspects2_pct)

aspects1_pct = np.hstack([aspects1_pct, aspects1_pct_vis]).tolist()
aspects2_pct = np.hstack([aspects2_pct, aspects2_pct_vis]).tolist()
aspects_pct = [aspects1_pct, aspects2_pct]

ratings1 = [np.mean(pol1.ratings[x]) for x in aspects]
ratings2 = [np.mean(pol2.ratings[x]) for x in aspects]
ratings = [ratings1, ratings2]

html_str, js_arr = flask_output_iter(aspects, pol1, pol2)

# Form page to submit
@app.route('/')
def index():
    return render_template('app_results.html', aspects=en_aspects,
                           aspects_f=aspectsf, aspects_pct=aspects_pct,
                           ratings=ratings, html_str=html_str,
                           review_txt=js_arr)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
