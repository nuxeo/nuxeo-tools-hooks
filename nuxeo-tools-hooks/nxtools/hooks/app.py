#!/usr/bin/env python
import logging
from api.CustomJSONEncoder import CustomJSONEncoder
from api.providers.leboncoin import LeBonCoinProvider
from flask import json, request
from flask.app import Flask

logging.basicConfig(filename='notify-center.log', level=logging.DEBUG)


app = Flask(__name__)
app.json_encoder = CustomJSONEncoder




if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8888, debug=True)