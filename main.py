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
app.config['SECRET_KEY'] = 'you-will-never-guess'

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


@app.route('/getProducts', methods = ['POST'])
def get_product_object():
    """
    End point to return the products associated with a phone number
    """
    json_data = request.get_json()
    tf = Transferto() 
    tf.read_transferto_credentials_file("transfertocredentials.json") 
    tf.initiate_rapidpro_json(json_data)
    products = tf.get_msisdn_products()
    return(json.dumps(products))

@app.route('/addData', methods = ['POST'])
def add_data_object():
    """
    End point to actually load data onto a phone number
    """
    json_data = request.get_json()
    tf = Transferto()  
    tf.read_transferto_credentials_file("transfertocredentials.json") 
    tf.initiate_rapidpro_json(json_data)
    tf.get_msisdn_products()
    tf.get_product_id()
    tf.payload_generation()
    services = tf.post_transferto_goods('https://api.transferto.com/v1.1/transactions/fixed_value_recharges')
    return(services.text)

@app.route('/rapidpro', methods = ['POST'])
def add_rapidpro_object():
    """
    End point to actually load data onto a phone number
    """
    json_data = request.form
    print('hehre')
    print(json_data['run'])
    print(json_data['phone'])
    attempts = 0
    status_code = 401
    while (attempts < 3 & status_code != requests.codes.ok):
        attempts = attempts + 1
        tf = Transferto() 
        tf.read_transferto_credentials_file('transfertocredentials.json')
        tf.read_rapidpro_credentials_file('rapidprocredentials.json')
        tf.initiate_rapidpro_json(json_data) 
        fields = tf.get_rapidpro_fields()
        tf.get_msisdn_products()
        tf.get_product_id()
        tf.payload_generation()
        services = tf.post_transferto_goods('https://api.transferto.com/v1.1/transactions/fixed_value_recharges')
        status_code = services.status_code
        #return(services.text)
        print(services.status_code)
        print(json.dumps(services.json()))
    return(json.dumps(services.json()))

if __name__ == '__main__': 
    app.run(host= '0.0.0.0')
