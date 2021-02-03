from datetime import datetime
from main import app, datetime, time

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
