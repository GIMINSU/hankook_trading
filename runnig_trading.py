import sys
from os import path
import schedule
import time
import pause
from datetime import datetime, timedelta
import exchange_calendars as ecals
from threading import Thread, Timer

app_path = path.abspath(path.join(".."))

if app_path not in sys.path:
    sys.path.append(app_path)

from datetime import datetime, timedelta
from create_cci_signal import trade_cci



class BaseRunner:
    def __init__(self):
        pass
    
    def runner(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"runner! %s"%str_now)
        schedule.every().days.at("04:11").do(trade_cci, price_target_market="NASDAQ", target_stock_code="AAL", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
        schedule.every().days.at("15:22").do(trade_cci, price_target_market="KOSPI", target_stock_name="삼성전자우", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")


    def us_trade_runner(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"US_trade_runner! %s"%str_now)
        trade_cci(price_target_market="NASDAQ", target_stock_code="AAL", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
        
        # schedule.every().days.at("04:22").do(trade_cci, price_target_market="NASDAQ", target_stock_code="AAL", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
        
        # while True:
            # t_calendar = ecals.get_calendar("XNYS")
            # us_now = datetime.now() - timedelta(hours=13)
            # us_today_date = us_now.date()
            # open_dummy = t_calendar.is_session(us_now.strftime("%Y-%m-%d"))
            # next_open_timestamp = t_calendar.next_open(datetime.today())  ## type : pandas._libs.tslibs.timestamps.Timestamp
            # next_open_datetime = next_open_timestamp.to_pydatetime() + timedelta(hours=9)

            # trading_signal_time = "15:22"
            # signal_making_time = datetime.strptime(trading_signal_time, "%H:%M").time()
            
            # after_datetime = datetime.combine(us_today_date, signal_making_time) + timedelta(minutes=1)
            # until_datetime = datetime.combine(us_today_date, signal_making_time) - timedelta(minutes=3)

            # run_datetime = datetime.combine(us_today_date, signal_making_time) + timedelta(hours=13)
            
            # hour_str = f"{run_datetime.hour}"
            # minute_str = f"{run_datetime.minute}"
            
            # if run_datetime.hour < 10:
            #     hour_str = f"0{run_datetime.hour}"

            # if run_datetime.minute < 10:
            #     minute_str = f"0{run_datetime.minute}"
            
            # run_time_str = f"{hour_str}:{minute_str}"

            # if open_dummy == True:
            #     if us_now < until_datetime:
            #         print(f"US Pause until_time {until_datetime + timedelta(hours=13)}")  ## 한국 시간으로 Pause time 표시
            #         pause.until(until_datetime + timedelta(hours=13))  ## 한국 시간으로 해야 Pause 걸림
            #     elif us_now > until_datetime and us_now < after_datetime:
            #         schedule.every().days.at(run_time_str).do(trade_cci, price_target_market="NASDAQ", target_stock_code="AAL", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
            #     elif us_now > after_datetime:
            #         print(f"US Pause until_time {next_open_datetime}")
            #         pause.until(next_open_datetime)
            # else:
            #     print(f"US Pause until_time {next_open_datetime}")
            #     pause.until(next_open_datetime)
            
            # schedule.run_pending()
            # print("us", schedule.get_jobs(), datetime.now())
            # time.sleep(10)  

    def kr_trade_runner(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"KR_trade_runner! %s"%str_now)
        trade_cci(trade_cci, price_target_market="KOSPI", target_stock_name="삼성전자우", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")

        # schedule.every().days.at("16:48").do(trade_cci, price_target_market="KOSPI", target_stock_name="삼성전자우", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")

        # while True:
        #     t_calendar = ecals.get_calendar("XKRX")
        #     open_dummy = t_calendar.is_session(datetime.now().strftime("%Y-%m-%d"))
        #     next_open_timestamp = t_calendar.next_open(datetime.today())
        #     next_open_datetime = next_open_timestamp.to_pydatetime() + timedelta(hours=9)

        #     trading_signal_time = "15:22"
        #     signal_making_time = datetime.strptime(trading_signal_time, "%H:%M").time()
        #     after_datetime = datetime.combine(datetime.now().date(), signal_making_time) + timedelta(minutes=1)
        #     until_time = datetime.combine(datetime.now().date(), signal_making_time) - timedelta(minutes=1)

        #     if open_dummy == True:
        #         now = datetime.now()
        #         if now < until_time:
        #             print(f"KR Pause until_time {until_time}")
        #             pause.until(until_time)
        #         elif now > until_time and now < after_datetime:
        #             schedule.every().days.at(trading_signal_time).do(trade_cci, price_target_market="KOSPI", target_stock_name="삼성전자우", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
        #         elif now > after_datetime:
        #             print(f"KR Pause until_time {next_open_datetime}")
        #             pause.until(next_open_datetime)
        #     else:
        #         print(f"KR Pause until_time {next_open_datetime}")
        #         pause.until(next_open_datetime)
            # schedule.run_pending()
            # print("kr", schedule.get_jobs(), datetime.now())
            # time.sleep(10)  

if __name__ == "__main__":
    
    # x = datetime.today()
    # kr_run = x.replace(day=x.day+1, hour=15, minute=22, second=0, microsecond=0) + timedelta(days=1)
    # us_run = x.replace(day=x.day+1, hour=0, minute=1, second=0, microsecond=0) + timedelta(days=1)
    # delta_kr = kr_run - x
    # delta_us = us_run - x

    # """
    # seconds 에 +1을 하는 이유
    # x=datetime.today()를 사용하면 x가 0-999999마이크로초(다른 값과 별도로)를 가질 수 있기 때문입니다. 
    # 그런 다음 xy의 초를 사용하면 예상 날짜보다 0-999999마이크로초 전에 시작되는 결과가 제공됩니다. 
    # +1을 사용하면 함수는 예상 날짜 이후 0-999999마이크로초에서 시작됩니다.
    # """
    # kr_secs = delta_kr.total_seconds() + 1
    # us_secs = delta_us.total_seconds() + 1

    # kr_t = Timer(kr_secs, BaseRunner().kr_trade_runner)
    # us_t = Timer(us_secs, BaseRunner().us_trade_runner)
    # kr_t.start()
    # us_t.start()
    
    BaseRunner().runner()
    while True:
        schedule.run_pending()
        print("sleep", datetime.now())
        print("runner", schedule.get_jobs())
        time.sleep(59)  
    # Thread(target = BaseRunner().runner).start()
    # Thread(target = BaseRunner().kr_trade_runner).start()