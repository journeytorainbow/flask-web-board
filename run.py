from flask import Flask
from flask import request
from flask import render_template
from flask_pymongo import PyMongo
from datetime import datetime
from bson.objectid import ObjectId
from flask import abort
from flask import redirect
from flask import url_for
import time

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/pywebboard"
mongo = PyMongo(app) # 이 객체로 mongoDB에 접근할 수 있음

@app.template_filter("formatdatetime")
def formate_datetime(value) :
    if value is None :
        return ""

    now_timestamp = time.time() # 클라이언트의 현재 시간에 대한 타임스탬프값
    # 우리나라 기준으로 offset값은 9
    offset = datetime.fromtimestamp(now_timestamp) - datetime.utcfromtimestamp(now_timestamp)
    # db에 저장된 utc시간 + 시간차 = 현재 로컬 시간
    value = datetime.fromtimestamp(int(value) / 1000) + offset
    return value.strftime('%Y-%m-%d %H:%M:%S')

@app.route("/write", methods=["GET", "POST"])
def board_write():
    if request.method == "POST" :
        name = request.form.get("name")
        title = request.form.get("title")
        contents = request.form.get("contents")

        current_utc_time = round(datetime.utcnow().timestamp() * 1000) # 가공하기 쉬운 형태로 현재 시간 구하기 (sec)

        board = mongo.db.board
        post = {
            "name" : name,
            "title" : title,
            "contents" : contents,
            "pubdate" : current_utc_time, # 작성 시간
            "view" : 0
        }

        x = board.insert_one(post)
        print(x.inserted_id)
        return redirect(url_for("board_view", idx=x.inserted_id))

    else :
        return render_template("write.html")
    return "헬로 파이썬"

@app.route("/view")
def board_view() :
    idx = request.args.get("idx")
    if idx is not None :
        board = mongo.db.board
        data = board.find_one({"_id" : ObjectId(idx)})

        if data is not None :
            result = {
                "id" : data.get("_id"),
                "name" : data.get("name"),
                "title" : data.get("title"),
                "contents" : data.get("contents"),
                "pubdate" : data.get("pubdate"),
                "view" : data.get("view")
            }
            
            return render_template("view.html", result=result)
    return abort(400)

@app.route("/list")
def show_list() :
    board = mongo.db.board
    datas = board.find({}).skip(page-1)
    return render_template("list.html", datas=datas)

if __name__ == "__main__":
    app.run(debug=True)