from flask import Flask, render_template, flash, request, abort, request, logging, jsonify
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
import logging
import json
import requests
from urllib.parse import parse_qs
import urllib 
from azurewebhook_functions import *
import phonenumbers
import math
import random

# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)

class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()])
    email = TextField('Email:', validators=[validators.required(), validators.Length(min=6, max=35)])
    phone = TextField('Phone:', validators=[validators.required(), validators.Length(min=3, max=35)])
    

@app.route("/", methods=['GET', 'POST'])
def hello():
    bk = Broker()
    bk.read_rapidpro_credentials_file('rapidprocredentials.json')
    form = ReusableForm(request.form)
    print(request.remote_addr)
    print(form.errors)
    if request.method == 'POST':
        name=request.form['name']
        phone=request.form['phone']
        email=request.form['email']
        print(name, " ", email, " ", phone)
        try:
            phone = phonenumbers.parse(phone)
        except:
            phone = phonenumbers.parse(phone,'ZA')
        phone = phonenumbers.format_number(phone,phonenumbers.PhoneNumberFormat.E164)
        rp_phone = 'tel:'+phone
        if form.validate():
            # Save the comment here.
            print('form validated ' + name)
            flash('Thanks for registration ' + name)
            registration_number = math.floor(random.uniform(0,10000))
            flash('You will receive a whatsapp message')
            flash('Please enter the following number in response ' + str(registration_number))
            rp_contact = bk.create_rapidpro_contact(name,rp_phone,registration_number)
            print(rp_contact)
        else:
            flash('Error: All the form fields are required. ')
 
    return render_template('hello.html', form=form)


if __name__ == '__main__': 
    app.run(host= '0.0.0.0')
