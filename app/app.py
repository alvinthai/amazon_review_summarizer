from __future__ import division
from scripts.polarizer import *
from scripts.summarizer import *
from flask import Flask, request, render_template
import cPickle
import numpy as np

app = Flask(__name__)

with open('data/polarizer1.pkl', 'rb') as f:
    pol1 = cPickle.load(f)

[aspects1, aspects1f] = pol1.top_asps
aspects1, aspects1f = aspects1[0:10], aspects1f[0:10]
en_aspects1 = [[x[0], x[1]] for x in enumerate(aspects1)]

aspects1_pct = np.array([pol1.aspect_pct[x] for x in aspects1])
aspects1_pct_vis = np.apply_along_axis(lambda x: 5 + x / sum(x) * 85, 1,
                                       aspects1_pct)

aspects1_pct = np.hstack([aspects1_pct, aspects1_pct_vis]).tolist()
ratings1 = [np.mean(pol1.ratings[x]) for x in aspects1]

test_str, test_arr = flask_output_iter(aspects1, pol1)

# Form page to submit
@app.route('/')
def index():
    return render_template('app_results.html', aspects=en_aspects1,
                           aspects_f=aspects1f, aspects_pct=aspects1_pct,
                           ratings=ratings1, js_str=test_str,
                           review_txt=test_arr)

# My word counte app
# @app.route('/predict', methods=['POST'] )
# def prediction_page():
#     text = str(request.form['user_input'].encode('utf-8'))
#     X = vectorizer.transform([text])
#     page = 'The predicted category is {}'.format(model.predict(X)[0])
#     return render_template('index.html', clicked=True, text=page)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
