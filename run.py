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
from functools import wraps
import time
import math

app = Flask(__name__)
app.config["MONGO_URI"] = "mongodb://localhost:27017/pywebboard"
app.config["SECRET_KEY"] = "abcd" # flash함수 사용하기 위해서 반드시 필요 & 실제로는 더 복잡한 값을 줘야함
app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(minutes=30) # 세션 유지 시간 30분
mongo = PyMongo(app) # 이 객체로 mongoDB에 접근할 수 있음

# 유저의 로그인 여부 확인을 위한 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_fucntion(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("member_login", next_url=request.url)) # next_url : 이 데코레이터가 호출된 페이지의 url을 의미
        return f(*args, **kwargs)
    return decorated_fucntion

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

# 글작성
@app.route("/write", methods=["GET", "POST"])
@login_required # 로그인한 회원만 글작성 가능
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
            "writer_id": session.get("id"), # 글,수정 삭제 시에 작성자 본인인지 확인하기 위한 값
            "view" : 0
        }

        x = board.insert_one(post)
        print(x.inserted_id)
        return redirect(url_for("board_view", idx=x.inserted_id))

    else :
        return render_template("write.html")

# 글 상세 보기
@app.route("/view")
@login_required # 로그인한 회원만 글 열람 가능
def board_view() :
    idx = request.args.get("idx")

    page = request.args.get("page")
    search = request.args.get("search")
    keyword = request.args.get("keyword")

    if idx is not None :
        board = mongo.db.board
        data = board.find_one_and_update({"_id": ObjectId(idx)}, {"$inc": {"view": 1}}, return_document=True)
        if data is not None :
            result = {
                "id" : data.get("_id"),
                "name" : data.get("name"),
                "title" : data.get("title"),
                "contents" : data.get("contents"),
                "pubdate" : data.get("pubdate"),
                "view" : data.get("view"),
                "writer_id": data.get("writer_id", "")
            }
            
            return render_template("view.html", result=result, page=page, search=search, keyword=keyword)
    return abort(400)

# 글목록
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

    datas = board.find(query).skip((page-1) * post_num).limit(post_num).sort("pubdate", -1)
    return render_template("list.html", 
                            datas=datas, 
                            post_num=post_num, 
                            page=page, 
                            block_start=block_start, 
                            block_end=block_end,
                            last_page_num=last_page_num,
                            search=search,
                            keyword=keyword)

@app.route("/edit/<idx>", methods=["GET", "POST"])
def board_edit(idx):
    if request.method == "GET":
        board = mongo.db.board
        data = board.find_one({"_id" : ObjectId(idx)})

        if data is None:
            flash("해당 게시물이 존재하지 않습니다.")
            return redirect(url_for("show_list"))
        else:
            if session.get("id") == data.get("writer_id"): # 작성자와 세션아이디가 일치하는지 확인
                return render_template("edit.html", data=data)
            else:
                flash("글 수정 권한이 없습니다.")
                return redirect(url_for("board_view", idx=data.get("_id")))
    else:
        title = request.form.get("title")
        contents = request.form.get("contents")

        board = mongo.db.board
        data = board.find_one({"_id" : ObjectId(idx)})
        if session.get("id") == data.get("writer_id"): # 작성자와 세션아이디가 일치하는지 한 번 더 확인
            board.update_one({"_id" : ObjectId(idx)}, {
                "$set" : {
                    "title": title,
                    "contents": contents,
                }
            })
            flash("수정되었습니다!")
            return redirect(url_for("board_view", idx=idx))
        else:
            flash("글 수정 권한이 없습니다.")
            return redirect(url_for("show_list"))

@app.route("/delete/<idx>")
def board_delete(idx):
    board = mongo.db.board
    data = board.find_one({"_id": ObjectId(idx)})
    if data.get("writer_id") == session.get("id"): # 작성자와 현재 세션 아이디가 일치하는지 확인
        board.delete_one({"_id": ObjectId(idx)})
        flash("삭제 되었습니다.")
    else:
        flash("삭제 권한이 없습니다.")
    return redirect(url_for("show_list"))

# 회원가입
@app.route("/join", methods=["GET", "POST"])
def member_join():
    if request.method == "POST":
        name = request.form.get("name", type=str)
        email = request.form.get("email", type=str)
        pw = request.form.get("pw", type=str)
        pw2= request.form.get("pw2", type=str)

        if name.replace(" ", "") == "" or email.replace(" ", "") == "" or pw.replace(" ", "") == "" or pw2.replace(" ", "") == "":
            flash("입력되지 않은 값이 있습니다.")
            return render_template("join.html")

        if pw != pw2:
            flash("비밀번호가 일치하지 않습니다.")
            return render_template("join.html")
        
        members = mongo.db.members
        cnt = members.find({"email" : email}).count()
        if cnt > 0:
            flash("중복된 이메일 주소입니다.")
            return render_template("join.html")

        current_utc_time = round(datetime.utcnow().timestamp() * 1000)
        
        post = {
            "name": name,
            "email": email,
            "pw": pw,
            "joindate": current_utc_time,
            "logintime": "",
            "logincount": 0,
        }

        members.insert_one(post)
        return ""

    else:
        return render_template("join.html")

@app.route("/login", methods=["GET", "POST"])
def member_login():
    if request.method == "POST":
        email = request.form.get("email")
        pw = request.form.get("pw")
        next_url = request.form.get("next_url")
        
        members = mongo.db.members

        # 이메일 값으로 회원 데이터 찾아옴
        data = members.find_one({"email": email})

        if data is None : # 존재하지 않는 이메일일 경우
            flash("회원 정보가 없습니다!")
            return redirect(url_for("member_login")) # GET방식요청 따라서 아래 else문으로 빠짐
        else:
            if data.get("pw") == pw:
                session["email"] = email
                session["name"] = data.get("name")
                session["id"] = str(data.get("_id")) # mondoDB의 유니크한 id 값을 지정
                session.permanent = True # 세션 유지 시간을 임의로 지정하기 위해 True를 줌
                if next_url is not None:
                    return redirect(next_url)
                else:
                    return redirect(url_for("show_list"))
            else:
                flash("비밀번호가 일치하지 않습니다!")
                return redirect(url_for("member_login"))
    else:
        next_url = request.args.get("next_url", type=str)
        if next_url is not None:
            return render_template("login.html", next_url=next_url)
        else:
            return render_template("login.html")

if __name__ == "__main__":
    app.run(debug=True)