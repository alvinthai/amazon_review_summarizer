from __future__ import division
from scripts.polarizer import *
from flask import Flask, request, render_template
import numpy as np
import pickle

app = Flask(__name__)

with open('data/polarizer1.p', 'rb') as f:
    polarizer = pickle.load(f)


# Form page to submit
@app.route('/')
def index():
    return render_template('app_results.html')

# My word counte app
# @app.route('/predict', methods=['POST'] )
# def prediction_page():
#     text = str(request.form['user_input'].encode('utf-8'))
#     X = vectorizer.transform([text])
#     page = 'The predicted category is {}'.format(model.predict(X)[0])
#     return render_template('index.html', clicked=True, text=page)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
