from os import getenv, path
from dotenv import load_dotenv

dotenv_path = path.join(path.dirname(__file__), ".env")
load_dotenv(dotenv_path)

import logging
import math
import random
import json
import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException

from raven.contrib.flask import Sentry
from flask import Flask, render_template, flash, request, redirect, url_for

from flask_wtf import FlaskForm
from wtforms import TextField, SubmitField
from wtforms.fields.html5 import EmailField
from wtforms.validators import DataRequired, Length, Email, ValidationError

from temba_client.exceptions import TembaBadRequestError
from temba_client.v2 import TembaClient

RAPIDPRO_URL = getenv("RAPIDPRO_URL", None)
RAPIDPRO_TOKEN = getenv("RAPIDPRO_TOKEN", None)
RAPIDPRO_FLOW_UUID = getenv("RAPIDPRO_FLOW_UUID", None)
RAPIDPRO_GROUP = getenv("RAPIDPRO_GROUP", None)
RAPIDPRO_FIELD = getenv("RAPIDPRO_FIELD", None)
APP_SECRET_KEY = getenv("APP_SECRET_KEY", None)

if None in [
    RAPIDPRO_URL,
    RAPIDPRO_TOKEN,
    RAPIDPRO_FLOW_UUID,
    RAPIDPRO_GROUP,
    RAPIDPRO_FIELD,
    APP_SECRET_KEY,
]:
    raise Exception("Improperly Configured Application")

DEBUG = getenv("DEBUG", False)
app = Flask(__name__)
app.secret_key = APP_SECRET_KEY
sentry = Sentry(app, dsn=getenv("SENTRY_DSN"))


class PhoneEmailSignUpForm(FlaskForm):
    name = TextField("Name:", validators=[DataRequired()])
    email = EmailField("Email:", validators=[DataRequired(), Email()])
    phone = TextField("Phone:", validators=[DataRequired(), Length(min=8, max=35)])
    submit = SubmitField("Submit")

    def validate_phone(form, field):
        if len(field.data) > 16:
            raise ValidationError(
                '"Please enter a valid South African cellphone number."'
            )

        input_number = phonenumbers.parse(field.data, "ZA")
        if not (phonenumbers.is_valid_number(input_number)):
            raise ValidationError(
                '"Please enter a valid South African cellphone number."'
            )


def process_number(num):
    phone = phonenumbers.parse(num, "ZA")
    return phonenumbers.format_number(phone, phonenumbers.PhoneNumberFormat.E164)


@app.route("/", methods=["GET", "POST"])
def index():
    form = PhoneEmailSignUpForm(request.form)
    if request.method == "POST":
        if form.validate():
            app.logger.debug("Form Validated")
            name = request.form["name"]
            phone_number = request.form["phone"]

            # TODO: include this in validation of phone number as well
            processed_phone_number = process_number(phone_number)
            formatted_rapidpro_number = "tel:{}".format(processed_phone_number)

            registration_pin = math.floor(random.uniform(10000, 99999))
            fields = {}
            fields[RAPIDPRO_FIELD] = registration_pin
            try:
                app.logger.debug("Creating Client")
                client = TembaClient(RAPIDPRO_URL, RAPIDPRO_TOKEN)
                app.logger.debug("Creating Contact")
                client.create_contact(
                    name=name,
                    urns=[formatted_rapidpro_number],
                    groups=[RAPIDPRO_GROUP],
                    fields=fields,
                )
                try:
                    app.logger.debug("Starting Flow")
                    client.create_flow_start(
                        RAPIDPRO_FLOW_UUID,
                        urns=[formatted_rapidpro_number],
                        restart_participants=True,
                        extra=None,
                    )
                    return redirect(
                        url_for("success", registration_pin=registration_pin, name=name)
                    )

                except Exception as e_1:
                    # try and delete the number so that they can start again if they want to
                    try:
                        app.logger.error("Flow Start Failed\n{}".format(e_1))
                        client.delete_contact(formatted_rapidpro_number)
                    except Exception as e_2:
                        app.logger.error("Unable to delete contact\n{}".format(e_2))
                    flash("Apologies, something went wrong, please try again.")

            except TembaBadRequestError:
                flash("That number has already been submitted")

    return render_template("index.html", form=form)


@app.route("/success/", methods=["GET"])
def success():
    return render_template(
        "success.html",
        registration_pin=request.args.get("registration_pin"),
        name=request.args.get("name"),
    )


@app.route("/health/", methods=["GET"])
def health():
    app_id = getenv("MARATHON_APP_ID", None)
    ver = getenv("MARATHON_APP_VERSION", None)
    return json.dumps({"id": app_id, "version": ver})


if __name__ == "__main__":
    app.run(debug=DEBUG, host="0.0.0.0")


if __name__ != "__main__":
    gunicorn_logger = logging.getLogger("gunicorn.error")
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
