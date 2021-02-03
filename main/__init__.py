from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo
from datetime import datetime
from datetime import timedelta
from bson.objectid import ObjectId
from flask import abort
from flask import redirect
from flask import url_for
from flask import flash
from flask import session
import time
import math

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/pywebboard"
app.config["SECRET_KEY"] = "abcd" # flash함수 사용하기 위해서 반드시 필요 & 실제로는 더 복잡한 값을 줘야함
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30) # 세션 유지 시간 30분
mongo = PyMongo(app) # 이 객체로 mongoDB에 접근할 수 있음

from .common import login_required
from .filter import formate_datetime
from . import board
from . import member