import os 
currentpath = os.getcwd()
import schedule
import time
import pause
from datetime import datetime, timezone, timedelta
import exchange_calendars as ecals
import pandas as pd

class BaseRunner():
    def __init__(self, contry_code):
        self.contry_code = contry_code
    
    def check_time(self):
        print(datetime.now())
        print("오늘 영업합니다..")

    def main(self):
        str_now = datetime.now().strftime('%m-%d-%y %H:%M:%S')
        print(f"Trading signal generation algorithm running! %s"%str_now)


        while True:
            if self.contry_code == "kr":
                t_calendar = ecals.get_calendar("XKRX")
                open_dummy = t_calendar.is_session(datetime.now().strftime("%Y-%m-%d"))
                next_open_date = t_calendar.next_open(datetime.now()).date()
                next_open_datetime = datetime.combine(next_open_date, datetime.strptime("1500", "%H%M").time())
                
            elif self.contry_code == "us":
                t_calendar = ecals.get_calendar("XNYS")
                open_dummy = t_calendar.is_session(datetime.now().strftime("%Y-%m-%d"))
                next_open_date = t_calendar.next_open(datetime.today()).date()
                next_open_datetime = datetime.combine(next_open_date, datetime.strptime("2359", "%H%M").time())
            
            if open_dummy == True:
                schedule.every().days.at("23:21").do(self.check_time)
            sleep_seconds = (next_open_datetime - datetime.now()).seconds
            print(f"sleep until : {next_open_datetime}")
            time.sleep(sleep_seconds)
            
            schedule.run_pending()    
            time.sleep(59)

if __name__ == "__main__":
    BaseRunner(contry_code = "us").main()