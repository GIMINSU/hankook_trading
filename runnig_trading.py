import sys
from os import path
import schedule
import time
from datetime import datetime, timedelta

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

sched = BackgroundScheduler(daemon=True)
sched.start()

trigger_kr_start = CronTrigger(year="*", month="*", day="*", hour="9", minute="00", second="2")
trigger_kr_end = CronTrigger(year="*", month="*", day="*", hour="15", minute="21", second="0")
trigger_kr_history = CronTrigger(year="*", month="*", day="*", hour="15", minute="31", second="0")

trigger_us_start = CronTrigger(year="*", month="*", day="*", hour="23", minute="30", second="2")  ## 서머타임 3월 두번째 일요일 오전 2시, 그리고 11월 첫 일요일 오전 2시
trigger_us_end = CronTrigger(year="*", month="*", day="*", hour="5", minute="39", second="0")  ## LOC 주문 제한 시간 종료 전 20분
trigger_us_history = CronTrigger(year="*", month="*", day="*", hour="6", minute="1", second="0")


sched.add_job(trade_cci, trigger=trigger_kr_start, args=["ETF_KR", "01", "261270"])
sched.add_job(trade_cci, trigger=trigger_kr_end, args=["ETF_KR", "01", "261270"])
sched.add_job(trade_cci, trigger=trigger_kr_start, args=["KOSPI", "01", "005935"])
sched.add_job(trade_cci, trigger=trigger_kr_end, args=["KOSPI", "01", "005935"])
sched.add_job(search_trading_history, trigger=trigger_kr_history, args= ["kr"])

sched.add_job(trade_cci, trigger=trigger_us_start, args=["ETF_US", "01", "TQQQ"])
sched.add_job(trade_cci, trigger=trigger_us_end, args=["ETF_US", "01", "TQQQ"])
sched.add_job(trade_cci, trigger=trigger_us_start, args=["ETF_US", "34", "SQQQ"])
sched.add_job(trade_cci, trigger=trigger_us_end, args=["ETF_US", "34", "SQQQ"])

sched.add_job(trade_cci, trigger=trigger_us_end, args=["NYSE", "34", "CPNG"])
sched.add_job(search_trading_history, trigger=trigger_us_history, args= ["us"])
# class BaseRunner:
#     def __init__(self):
#         pass
    
#     def runner(self):
#         str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
#         print(f"Runner START! %s"%str_now)
        
#         schedule.every().days.at("09:00").do(trade_cci, price_target_market="ETF_KR", target_stock_code="261270", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
#         schedule.every().days.at("15:20").do(trade_cci, price_target_market="ETF_KR", target_stock_code="261270", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
#         schedule.every().days.at("09:00").do(trade_cci, price_target_market="KOSPI", target_stock_code="005935", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
#         schedule.every().days.at("15:20").do(trade_cci, price_target_market="KOSPI", target_stock_code="005935", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
        
#         schedule.every().days.at("22:35").do(trade_cci, price_target_market="ETF_US", target_stock_code="TQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="00")
#         schedule.every().days.at("22:35").do(trade_cci, price_target_market="ETF_US", target_stock_code="SQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="00")
        
#         schedule.every().days.at("04:30").do(trade_cci, price_target_market="ETF_US", target_stock_code="TQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
#         schedule.every().days.at("04:30").do(trade_cci, price_target_market="ETF_US", target_stock_code="SQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
#         schedule.every().days.at("04:30").do(trade_cci, price_target_market="NYSE", target_stock_code="CPNG", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")

# if __name__ == "__main__":
    
#     BaseRunner().runner()
#     while True:
#         schedule.run_pending()
#         print("Run Schedule!", schedule.get_jobs())
#         time.sleep(59)  

app = Flask(__name__)


if __name__ == "__main__":
    app.run(host="localhost", port=5501, debug=False, use_reloader=False)