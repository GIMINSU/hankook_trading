import sys
from os import path
import schedule
import time
import pause
from datetime import datetime, timedelta
import exchange_calendars as ecals
from threading import Thread

app_path = path.abspath(path.join(".."))

if app_path not in sys.path:
    sys.path.append(app_path)

from datetime import datetime, timedelta
from create_cci_signal import trade_cci



class BaseRunner:
    def __init__(self):
        pass
    
    def us_trade_runner(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"US_trade_runner! %s"%str_now)

        while True:
            t_calendar = ecals.get_calendar("XNYS")
            us_now = datetime.now() - timedelta(hours=13)
            us_today_date = us_now.date()
            open_dummy = t_calendar.is_session(us_now.strftime("%Y-%m-%d"))
            next_open_timestamp = t_calendar.next_open(datetime.today())  ## type : pandas._libs.tslibs.timestamps.Timestamp
            next_open_datetime = next_open_timestamp.to_pydatetime() + timedelta(hours=9)

            trading_signal_time = "15:22"
            signal_making_time = datetime.strptime(trading_signal_time, "%H:%M").time()
            
            after_datetime = datetime.combine(us_today_date, signal_making_time) + timedelta(minutes=1)
            until_time = datetime.combine(us_today_date, signal_making_time) - timedelta(minutes=3)

            if open_dummy == True:
                if us_now < until_time:
                    print(f"US Pause until_time {until_time + timedelta(hours=13)}")  ## 한국 시간으로 Pause time 표시
                    pause.until(until_time + timedelta(hours=13))  ## 한국 시간으로 해야 Pause 걸림
                elif us_now > until_time and us_now < after_datetime:
                    schedule.every().days.at(trading_signal_time).do(trade_cci, price_target_market="NASDAQ", target_stock_code="AAL", cci_calculate_days=20, rate_of_one_order=0.1, order_type="34")
                    time.sleep(58)
                elif us_now > after_datetime:
                    print(f"US Pause until_time {next_open_datetime}")
                    pause.until(next_open_datetime)
            else:
                print(f"US Pause until_time {next_open_datetime}")
                pause.until(next_open_datetime)
            
            schedule.run_pending()
            time.sleep(58)  

    def kr_trade_runner(self):
        str_now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"KR_trade_runner! %s"%str_now)

        while True:
            t_calendar = ecals.get_calendar("XKRX")
            open_dummy = t_calendar.is_session(datetime.now().strftime("%Y-%m-%d"))
            next_open_timestamp = t_calendar.next_open(datetime.today())
            next_open_datetime = next_open_timestamp.to_pydatetime() + timedelta(hours=9)

            trading_signal_time = "15:22"
            signal_making_time = datetime.strptime(trading_signal_time, "%H:%M").time()
            after_datetime = datetime.combine(datetime.now().date(), signal_making_time) + timedelta(minutes=1)
            until_time = datetime.combine(datetime.now().date(), signal_making_time) - timedelta(minutes=1)

            if open_dummy == True:
                now = datetime.now()
                if now < until_time:
                    print(f"KR Pause until_time {until_time}")
                    pause.until(until_time)
                elif now > until_time and now < after_datetime:
                    schedule.every().days.at(trading_signal_time).do(trade_cci, price_target_market="KOSPI", target_stock_name="삼성전자우", cci_calculate_days=20, rate_of_one_order=0.1, order_type="01")
                    time.sleep(59)
                elif now > after_datetime:
                    print(f"KR Pause until_time {next_open_datetime}")
                    pause.until(next_open_datetime)
            else:
                print(f"KR Pause until_time {next_open_datetime}")
                pause.until(next_open_datetime)
            
            schedule.run_pending() 
            time.sleep(58)   

if __name__ == "__main__":
    Thread(target = BaseRunner().us_trade_runner).start()
    Thread(target = BaseRunner().kr_trade_runner).start()