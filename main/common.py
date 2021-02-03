from functools import wraps
from main import redirect, session, url_for, request

# 유저의 로그인 여부 확인을 위한 데코레이터
def login_required(f):
    @wraps(f)
    def decorated_fucntion(*args, **kwargs):
        if session.get("id") is None or session.get("id") == "":
            return redirect(url_for("member_login", next_url=request.url)) # next_url : 이 데코레이터가 호출된 페이지의 url을 의미
        return f(*args, **kwargs)
    return decorated_fucntion