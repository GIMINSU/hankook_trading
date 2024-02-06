import sys
from os import path

app_path = path.abspath(path.join(".."))
if app_path not in sys.path:
    sys.path.append(app_path)
    
    
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from create_cci_signal import trade_cci, search_trading_history
from config import HankookConfig
from hankook_trade_api import TradeHankookAPI

def issue_token(country_code):
    TradeHankookAPI(HankookConfig).issue_access_token(country_code)
    
import logging
logging.basicConfig(filename='./running_trading.log', level=logging.ERROR)

kr_sched = BackgroundScheduler({'apscheduler.timezone': 'Asia/Seoul'}, daemon=True)
us_sched = BackgroundScheduler({'apscheduler.timezone': 'US/Eastern'}, daemon=True)
kr_sched.start()
us_sched.start()

trigger_kr_start = CronTrigger(year="*", month="*", day="*", hour="9", minute="00", second="2")
trigger_kr_end = CronTrigger(year="*", month="*", day="*", hour="15", minute="21", second="0")
trigger_kr_history = CronTrigger(year="*", month="*", day="*", hour="15", minute="31", second="0")

trigger_us_start = CronTrigger(year="*", month="*", day="*", hour="9", minute="30", second="2", timezone="US/Eastern")  ## 서머타임 3월 두번째 일요일 오전 2시, 그리고 11월 첫 일요일 오전 2시
trigger_us_end = CronTrigger(year="*", month="*", day="*", hour="15", minute="39", second="0", timezone="US/Eastern")  ## LOC 주문 제한 시간 종료 전 20분
trigger_us_history = CronTrigger(year="*", month="*", day="*", hour="16", minute="01", second="0", timezone="US/Eastern")


kr_sched.add_job(trade_cci, trigger=trigger_kr_start, args=["ETF_KR", "01", "261270"])
kr_sched.add_job(trade_cci, trigger=trigger_kr_end, args=["ETF_KR", "01", "261270"])
kr_sched.add_job(trade_cci, trigger=trigger_kr_start, args=["KOSPI", "01", "005935"])
kr_sched.add_job(trade_cci, trigger=trigger_kr_end, args=["KOSPI", "01", "005935"])
kr_sched.add_job(search_trading_history, trigger=trigger_kr_history, args= ["kr"])

us_sched.add_job(trade_cci, trigger=trigger_us_start, args=["ETF_US", "01", "TQQQ"])
us_sched.add_job(trade_cci, trigger=trigger_us_end, args=["ETF_US", "01", "TQQQ"])
us_sched.add_job(trade_cci, trigger=trigger_us_start, args=["ETF_US", "34", "SQQQ"])
us_sched.add_job(trade_cci, trigger=trigger_us_end, args=["ETF_US", "34", "SQQQ"])

us_sched.add_job(trade_cci, trigger=trigger_us_end, args=["NYSE", "34", "CPNG"])
us_sched.add_job(search_trading_history, trigger=trigger_us_history, args= ["us"])

app = Flask(__name__)


if __name__ == "__main__":
    app.run(host="localhost", port=5501, debug=False, use_reloader=False)