
# import library Start
from __future__ import unicode_literals
from flask import Flask, request, abort, render_template, url_for, redirect, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user


import os
import sys
import json
import pprint
import requests
import base64
import time
import random
import tensorflow as tf
from flask import *
import numpy
import pandas as pd
numpy.random.seed(10)
import fileinput
import xlrd

new_model = tf.keras.models.load_model('spec.h5')
milk_model = tf.keras.models.load_model('spectrum_milk_freshness_detection_0919v1.h5')
# import library end

#flask initiallize
app = Flask(__name__)
app.secret_key = 'abcd123'

#login system
users = {'lab321': {'password': 'spectrum'}}

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.session_protection = "strong"
login_manager.login_view = 'login'
login_manager.login_message = '請證明你是阿春的人'


class User(UserMixin):
    pass


@login_manager.user_loader
def user_loader(user_id):
    if user_id not in users:
        return

    user = User()
    user.id = user_id
    return user


@login_manager.request_loader
def request_loader(request):
    user_id = request.form.get('user_id')
    if user_id not in users:
        return

    user = User()
    user.id = user_id

    # DO NOT ever store passwords in plaintext and always compare password
    # hashes using constant-time comparison!
    user.is_authenticated = request.form['password'] == users[user_id]['password']

    return user
#login system end

#route

@app.route("/", methods=['GET'])
def home():
    return render_template("home.html")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template("login.html")
    
    user_id = request.form['user_id']
    if (user_id in users) and (request.form['password'] == users[user_id]['password']):
        user = User()
        user.id = user_id
        login_user(user)
        flash(f'{user_id}！歡迎你來查看光譜資料！')
        return redirect(url_for('spectrum'))

    flash('登入失敗了...')
    return redirect(url_for('login'))


    
@app.route('/logout')
def logout():
    user_id = current_user.get_id()
    logout_user()
    flash(f'{user_id}！歡迎下次再來！')
    return render_template('login.html') 
    
@app.route("/from_start")
def from_start():
    return render_template("from_start.html")

#color spectrum detection

@app.route("/spectrum", methods=['GET', 'POST'])
@login_required
def spectrum():
     return render_template('spectrum.html', **locals())

@app.route('/predict', methods=['GET', 'POST'])
def predict():
     if request.method == 'POST':
             file = request.files['inputfile']
             test_df = pd.read_excel(file)
             test_df=test_df.values
             test_df = numpy.array(test_df, dtype=numpy.float32)
             predictions = new_model.predict(test_df)
             if (predictions[0][0]>predictions[0][1])&(predictions[0][0]>predictions[0][2])&(predictions[0][0]>predictions[0][3]):
                 results='Red'
             if (predictions[0][1]>predictions[0][0])&(predictions[0][1]>predictions[0][2])&(predictions[0][1]>predictions[0][3]):
                 results='Green'
             if (predictions[0][2]>predictions[0][0])&(predictions[0][2]>predictions[0][1])&(predictions[0][2]>predictions[0][3]):
                 results='Blue'
             if (predictions[0][3]>predictions[0][0])&(predictions[0][3]>predictions[0][1])&(predictions[0][3]>predictions[0][2]):
                 results='White'
             spec_df=test_df.tolist()
     return render_template('spectrum.html',results=results,data=json.dumps(spec_df))

#milk spectrum detection 

df=pd.read_excel("test_data.xlsx")
df1=df.values

@app.route('/milk')
@login_required
def index():
    return render_template('milk.html', **locals())

@app.route('/milk_predict', methods=['GET', 'POST'])
def milkpredict():
     if request.method == 'POST':
             files = request.files['inputfile']
             userdata = pd.read_csv(files)
             userdata1=userdata.values
             inputdata=numpy.vstack([df1,userdata1])
             x_max=inputdata.max(axis=0)
             x_min=inputdata.min(axis=0)
             userdata1=numpy.reshape(userdata1,(121))
             for i in range(121):
                 std_data=(userdata1[i]-x_min[i])/(x_max[i]-x_min[i])
                 userdata1[i]=std_data
             userdata1=numpy.reshape(userdata1,(1,121))
             prediction = new_model.predict(userdata1)
             if (prediction[0][0]>0.5): 
                 result='fresh'
             else:
                 result='unfresh'
             milk_df=userdata.values.tolist()
     return render_template('milk.html',result=result,data=json.dumps(milk_df))

if __name__ == "__main__":
    app.run()

