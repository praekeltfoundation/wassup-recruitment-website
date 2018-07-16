import math
import random
import json
from os import environ

import phonenumbers
from raven.contrib.flask import Sentry
from flask import (Flask, render_template, flash, request)
from wtforms import Form, TextField, validators
from azurewebhook_functions import *


RAPIDPRO_URL = environ.get("RAPIDPRO_URL")
RAPIDPRO_TOKEN = environ.get("RAPIDPRO_TOKEN")
RAPIDPRO_FLOW_UUID = environ.get("RAPIDPRO_FLOW_UUID")

DEBUG = False
app = Flask(__name__)
app.config.from_object(__name__)
sentry = Sentry(app, dsn=environ.get("SENTRY_DSN"))


class ReusableForm(Form):
    name = TextField("Name:", validators=[validators.required()])
    email = TextField(
        "Email:", validators=[validators.required(), validators.Length(min=6, max=35)]
    )
    phone = TextField(
        "Phone:", validators=[validators.required(), validators.Length(min=3, max=35)]
    )


@app.route("/", methods=["GET", "POST"])
def hello():
    bk = Broker()
    bk.read_rapidpro_credentials_file("rapidprocredentials.json")
    form = ReusableForm(request.form)
    print(request.remote_addr)
    print(form.errors)
    if request.method == "POST":
        name = request.form["name"]
        phone = request.form["phone"]
        email = request.form["email"]
        print(name, " ", email, " ", phone)
        try:
            phone = phonenumbers.parse(phone)
        except:
            phone = phonenumbers.parse(phone, "ZA")
        phone = phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)
        rp_phone = "tel:" + phone
        if form.validate():
            # Save the comment here.
            print("form validated " + name)
            flash("Thanks for registration " + name)
            registration_number = math.floor(random.uniform(0, 10000))
            flash("You will receive a whatsapp message")
            flash(
                "Please enter the following number in response "
                + str(registration_number)
            )
            rp_contact = bk.create_rapidpro_contact(name, rp_phone, registration_number)
            print(rp_contact)
        else:
            flash("Error: All the form fields are required. ")

    return render_template("hello.html", form=form)


@app.route("/health/", methods=["GET"])
def health():
    app_id = environ.get('MARATHON_APP_ID', None)
    ver = environ.get('MARATHON_APP_VERSION', None)
    return json.dumps({'id': app_id, 'version': ver})


if __name__ == "__main__":
    app.run(host="0.0.0.0")
