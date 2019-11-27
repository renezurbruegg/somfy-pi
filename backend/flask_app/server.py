# !/usr/bin/env python
# -*- coding: utf-8 -*-
"""Entry point for the server application."""
import threading
import json
import logging
from pylogging import HandlerType, setup_logger
import time
import os
import sys


from flask_cors import CORS
from .config import CONFIG
import traceback
from flask import request, jsonify, current_app, Flask
from flask_jwt_simple import (
    JWTManager, jwt_required, create_jwt, get_jwt_identity
)

from .http_codes import Status
from flask import make_response

from datetime import timedelta, datetime
from functools import update_wrapper


logger = logging.getLogger(__name__)
setup_logger(log_directory='./logs', file_handler_type=HandlerType.ROTATING_FILE_HANDLER, allow_console_logging = True, console_log_level  = logging.DEBUG, max_file_size_bytes = 1000000)


# Create Flask App
app = Flask(__name__)
# Load Configuration for app. Secret key etc.
config_name = os.getenv('FLASK_CONFIGURATION', 'default')
app.config.from_object(CONFIG[config_name])

# Set Cors header. Used to accept connections from browser using XHTTP requests.
CORS(app, headers=['Content-Type'])
jwt = JWTManager(app)



#Pin Code
pinCode = app.config["PIN_CODE"]

""" Path to config file (.json) for frontend """
CONF_FILE = os.path.join(os.path.dirname(__file__), 'conf.json')

@jwt.jwt_data_loader
def add_claims_to_access_token(identity):
    now = datetime.utcnow()
    return {
        'exp': now + current_app.config['JWT_EXPIRES'],
        'iat': now,
        'nbf': now,
        'sub': identity,
        'roles': 'Admin'
    }


def crossdomain(origin=None, methods=None, headers=None, max_age=21600,
                attach_to_all=True, automatic_options=True):
    """Decorator function that allows crossdomain requests.
      Courtesy of
      https://blog.skyred.fi/articles/better-crossdomain-snippet-for-flask.html
    """
    if methods is not None:
        methods = ', '.join(sorted(x.upper() for x in methods))
    # use str instead of basestring if using Python 3.x
    if headers is not None and not isinstance(headers, list):
        headers = ', '.join(x.upper() for x in headers)
    # use str instead of basestring if using Python 3.x
    if not isinstance(origin, list):
        origin = ', '.join(origin)
    if isinstance(max_age, timedelta):
        max_age = max_age.total_seconds()

    def get_methods():
        """ Determines which methods are allowed
        """
        if methods is not None:
            return methods

        options_resp = current_app.make_default_options_response()
        return options_resp.headers['allow']

    def decorator(f):
        """The decorator function
        """
        def wrapped_function(*args, **kwargs):
            """Caries out the actual cross domain code
            """
            if automatic_options and request.method == 'OPTIONS':
                resp = current_app.make_default_options_response()
            else:
                resp = make_response(f(*args, **kwargs))
            if not attach_to_all and request.method != 'OPTIONS':
                return resp

            h = resp.headers
            h['Access-Control-Allow-Origin'] = origin
            h['Access-Control-Allow-Methods'] = get_methods()
            h['Access-Control-Max-Age'] = str(max_age)
            h['Access-Control-Allow-Credentials'] = 'true'
            h['Access-Control-Allow-Headers'] = \
                "Origin, X-Requested-With, Content-Type, Accept, Authorization"
            if headers is not None:
                h['Access-Control-Allow-Headers'] = headers
            return resp

        f.provide_automatic_options = False
        return update_wrapper(wrapped_function, f)
    return decorator



#-------------------------------------------------------------------------------
#                       BEGIN API Functions
#-------------------------------------------------------------------------------
@app.route('/api/hello', methods=['POST', 'GET', 'OPTIONS'])
@crossdomain(origin = '*')
def sayHi():
    return "OK", Status.HTTP_OK_BASIC


def main():
    """Main entry point of the app. <br>
    Starts local server and sets values stored in the conf.json file.
    """

    logger.info("starting server")
    try:
        app.run(debug=False, host= app.config["IP"], port= app.config["PORT"])
        logger.info("Server started. IP: " + str(app.config["IP"]) + " Port: " + str(app.config["PORT"]))
    except Exception as exc:
        logger.error(exc)
        logger.exception(traceback.format_exc())
    finally:
        pass
