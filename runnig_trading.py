import sys
from os import path
import schedule
import time
from datetime import datetime

app_path = path.abspath(path.join(".."))

if app_path not in sys.path:
    sys.path.append(app_path)

from create_cci_signal import trade_cci
from config import HankookConfig
from hankook_trade_api import TradeHankookAPI

def issue_token(country_code):
    TradeHankookAPI(HankookConfig).issue_access_token(country_code)
    
class BaseRunner:
    def __init__(self):
        pass
    
    def runner(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"Runner START! %s"%str_now)
        schedule.every().days.at("00:01").do(issue_token, country_code="us")
        schedule.every().days.at("00:01").do(issue_token, country_code="kr")
        
        schedule.every().days.at("09:00").do(trade_cci, price_target_market="ETF_KR", target_stock_code="261270", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
        schedule.every().days.at("09:00").do(trade_cci, price_target_market="ETF_KR", target_stock_code="261260", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
        
        schedule.every().days.at("15:20").do(trade_cci, price_target_market="ETF_KR", target_stock_code="261270", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
        schedule.every().days.at("15:20").do(trade_cci, price_target_market="ETF_KR", target_stock_code="261260", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
        
        schedule.every().days.at("22:35").do(trade_cci, price_target_market="ETF_US", target_stock_code="TQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="00")
        schedule.every().days.at("22:35").do(trade_cci, price_target_market="ETF_US", target_stock_code="SQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="00")
        
        schedule.every().days.at("04:30").do(trade_cci, price_target_market="ETF_US", target_stock_code="TQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
        schedule.every().days.at("04:30").do(trade_cci, price_target_market="ETF_US", target_stock_code="SQQQ", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
        schedule.every().days.at("04:30").do(trade_cci, price_target_market="NYSE", target_stock_code="CPNG", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")

if __name__ == "__main__":
    
    BaseRunner().runner()
    while True:
        schedule.run_pending()
        print("Run Schedule!", schedule.get_jobs())
        time.sleep(59)  