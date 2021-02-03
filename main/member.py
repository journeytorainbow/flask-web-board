from main import *

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