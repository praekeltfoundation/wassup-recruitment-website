from os import getenv, path
from dotenv import load_dotenv

dotenv_path = path.join(path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

import math
import random
import json
import phonenumbers
import requests
from raven.contrib.flask import Sentry
from flask import (Flask, render_template, flash, request)
from wtforms import Form, TextField, validators
from temba_client.exceptions import TembaBadRequestError
from temba_client.v2 import TembaClient

RAPIDPRO_URL = getenv("RAPIDPRO_URL", None)
RAPIDPRO_TOKEN = getenv("RAPIDPRO_TOKEN", None)
RAPIDPRO_FLOW_UUID = getenv("RAPIDPRO_FLOW_UUID", None)
RAPIDPRO_GROUP = getenv("RAPIDPRO_GROUP", None)
RAPIDPRO_FIELD = getenv("RAPIDPRO_FIELD", None)
APP_SECRET_KEY = getenv("APP_SECRET_KEY", None)

if (
    None in [
        RAPIDPRO_URL,
        RAPIDPRO_TOKEN,
        RAPIDPRO_FLOW_UUID,
        RAPIDPRO_GROUP,
        RAPIDPRO_FIELD,
        APP_SECRET_KEY,
    ]
):
    raise Exception("Improperly Configured Application")

DEBUG = getenv("DEBUG", False)
app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
sentry = Sentry(app, dsn=getenv("SENTRY_DSN"))


class ReusableForm(Form):
    name = TextField("Name:", validators=[validators.required()])
    email = TextField(
        "Email:", validators=[validators.required(), validators.Length(min=6, max=35)]
    )
    phone = TextField(
        "Phone:", validators=[validators.required(), validators.Length(min=3, max=35)]
    )


def process_number(num):
    try:
        phone = phonenumbers.parse(num)
    except Exception:
        phone = phonenumbers.parse(num, "ZA")
    return (phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164))


@app.route("/", methods=["GET", "POST"])
def index():
    form = ReusableForm(request.form)
    if request.method == "POST":
        if form.validate():
            name = request.form["name"]
            phone_number = request.form["phone"]

            # TODO: include this in validation of phone number as well
            processed_phone_number = process_number(phone_number)
            formatted_rapidpro_number = "tel:{}".format(processed_phone_number)

            registration_pin = math.floor(random.uniform(10000, 99999))
            fields = {}
            fields[RAPIDPRO_FIELD] = registration_pin

            try:
                client = TembaClient(RAPIDPRO_URL, RAPIDPRO_TOKEN)
                contact = client.create_contact(
                    name=name,
                    urns=[formatted_rapidpro_number],
                    groups=[RAPIDPRO_GROUP],
                    fields=fields,
                )
                try:
                    print("RAPIDPRO_FLOW_UUID:")
                    print(RAPIDPRO_FLOW_UUID)
                    client.create_flow_start(
                        RAPIDPRO_FLOW_UUID,
                        urns=[formatted_rapidpro_number],
                        restart_participants=True,
                        extra=None,
                    )
                    flash("Thanks for registration " + name)
                    flash("You will receive a whatsapp message")
                    flash(
                        "Please enter the following number in response: {}".format(
                            registration_pin
                        )
                    )
                except Exception as e:
                    # try and delete the number so that they can start again if they want to
                    try:
                        client.delete_contact(contact)
                    except Exception as e:
                        print("unable to delete the contact")
                    flash("Apologies, something went wrong, please try again.")

            except TembaBadRequestError as e:
                print(e)
                flash("That number has already been submitted")
        else:
            flash("Error: All the form fields are required. ")

    return render_template("index.html", form=form)


@app.route("/health/", methods=["GET"])
def health():
    app_id = getenv("MARATHON_APP_ID", None)
    ver = getenv("MARATHON_APP_VERSION", None)
    return (json.dumps({"id": app_id, "version": ver}))


if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0")
