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
import math

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
    # 페이지 번호 (기본값 : 1)
    page = request.args.get("page", 1, type=int)
    # 한 페이지당 보여질 게시물 수
    post_num = 10
    # # 한 페이지당 보여질 게시물 수 (기본값 : 10)
    # limit = request.args.get("limit", 10, type=int)

    search = request.args.get("search", -1, type=int)
    keyword = request.args.get("keyword", "", type=str) # 기본값 지정안해주면 None
    
    # 최종적으로 완성된 쿼리를 만들 변수
    query = {}
    # 검색어 상태를 추가할 리스트 변수
    search_list = []

    if search == 0:
        search_list.append({"title" : {"$regex":keyword}}) # keyword가 포함된 모든 title
    elif search == 1:
        search_list.append({"contents" : {"$regex":keyword}})
    elif search == 2:
        search_list.append({"title" : {"$regex":keyword}})
        search_list.append({"contents" : {"$regex":keyword}})
    elif search == 3:
        search_list.append({"name" : {"$regex":keyword}})
    
    # 검색어가 하나라도 있는 경우 query 변수에 $or 리스트를 쿼리
    if len(search_list) > 0 :
        query = {"$or": search_list}

    board = mongo.db.board
    # 게시물 총 개수
    tot_count = board.find(query).count()
    # 마지막 페이지
    last_page_num = math.ceil(tot_count / post_num)
    # 한 블럭 당 페이지 5개씩 표기
    block_size = 5
    # 현재 보고 있는 페이지의 블럭이 몇 번째 블럭인지(0번째부터)
    block_num = int((page - 1) / block_size)
    # 현재 블럭의 맨 앞 페이지 번호
    block_start = int((block_size * block_num) + 1)
    # 현재 블럭의 맨 끝 페이지 번호
    block_end = (block_start + block_size) - 1

    datas = board.find(query).skip((page-1) * post_num).limit(post_num)
    return render_template("list.html", 
                            datas=datas, 
                            post_num=post_num, 
                            page=page, 
                            block_start=block_start, 
                            block_end=block_end,
                            last_page_num=last_page_num,
                            search=search,
                            keyword=keyword)

if __name__ == "__main__":
    app.run(debug=True)