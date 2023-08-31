import os
from os import path
import sys

app_path = path.abspath(path.join(".."))

if app_path not in sys.path:
    sys.path.append(app_path)

import FinanceDataReader as fdr
import exchange_calendars as ecals
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import csv

from api_config import HankookConfig, SlackConfig, GoogleSpreadseetsConfig

from hankook_trade_api import KisDevelopers
from slack_message import SendMessageSlack


def trade_cci(price_target_market, cci_calculate_days, rate_of_one_order, order_type, target_stock_code=None, target_stock_name=None):
    print("trade_cci", datetime.now())
    
    """
    price_target_market = 'KRX', 'NASDAQ', 'NYSE', 'S&P500', "KOSPI"
    한국 주식 시장 order type
    str 한국 주문 구분 시장가 "01" (00 지정가, 01 시장가, 02 조건부지정가, 05 장전 시간외, 06 장후 시간외)

    미국 주식 시장 order type
    Header tr_id JTTT1002U (미국 매수 주문)]
    00 : 지정가
    32 : LOO(장개시지정가)
    34 : LOC(장마감지정가)

    [Header tr_id JTTT1006U(미국 매도 주문)]
    00 : 지정가
    31 : MOO(장개시시장가)
    32 : LOO(장개시지정가)
    33 : MOC(장마감시장가)
    34 : LOC(장마감지정가)
    """
    stock_name_column_var = "Name"
    stock_code_column_var = "Code"
    
    cci_column_var = f"CCI_{cci_calculate_days}"
    pre_1day_cci_column_var = f"Before_1Day_{cci_column_var}"

    kr_price_market_list = ["KRX", "KOSPI"]
    us_price_market_list = ["NASDAQ", "NYSE", "S&P500"]
    
    open_dummy = 0
    if price_target_market in us_price_market_list:
        stock_code_column_var = "Symbol"
        t_calendar = ecals.get_calendar("XNYS")
        us_now = datetime.now() - timedelta(hours=13)
        open_dummy = t_calendar.is_session(us_now.strftime("%Y-%m-%d"))
    
    elif price_target_market in kr_price_market_list:
        t_calendar = ecals.get_calendar("XKRX")
        open_dummy = t_calendar.is_session(datetime.now().strftime("%Y-%m-%d"))

    if open_dummy == 1:
        try:
            df = fdr.StockListing(price_target_market)
            target_market_stock_name_list = df[stock_name_column_var].values.tolist()
            target_market_stock_code_list = df[stock_code_column_var].values.tolist()

            if target_stock_name != None and target_stock_code != None:
                pass
            elif target_stock_name != None and target_stock_code == None:
                if target_stock_name in target_market_stock_name_list:
                    target_stock_code = df[df[stock_name_column_var] == target_stock_name][stock_code_column_var].iloc[0]
                else:
                    print(f"{target_stock_name} not in {price_target_market}." )
            elif target_stock_name == None and target_stock_code != None:
                if target_stock_code in target_market_stock_code_list:
                    target_stock_name = df[df[stock_code_column_var] == target_stock_code][stock_name_column_var].iloc[0]
                else:
                    print(f"{target_stock_code} not in {price_target_market}." )

            csv_file_name = f"{price_target_market}_{target_stock_name}_{target_stock_code}.csv"

            try:
                edit_df = pd.read_csv(csv_file_name)
            except:
                with open(csv_file_name, "w", newline='') as file:
                    writer = csv.writer(file)
                    try:
                        edit_df = pd.read_csv(csv_file_name)
                    except:
                        edit_df = pd.DataFrame()
            
            edit_df = edit_df.fillna("")
            print("exists csv file data count:", len(edit_df))

        except Exception as e:
            print(e)

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days = cci_calculate_days*2)
            start_date_str = datetime.strftime(start_date, "%Y-%m-%d")
            end_date_str = datetime.strftime(end_date, "%Y-%m-%d")
            price_df = fdr.DataReader(target_stock_code, start_date_str, end_date_str)
            price_df = price_df.reset_index(drop=False)
            price_df["TP"] = (price_df["High"] + price_df["Low"] + price_df["Close"]) / 3
            price_df["sma"] = price_df["TP"].rolling(cci_calculate_days).mean()
            price_df["mad"] = price_df["TP"].rolling(cci_calculate_days).apply(lambda x: pd.Series(x).mad())
            price_df[cci_column_var] = (price_df["TP"] - price_df["sma"]) / (0.015 * price_df["mad"])
            
            price_df[pre_1day_cci_column_var] = price_df[cci_column_var].shift(1)
            price_df["signal_trade"] = None

            # price_df["signal_trade"] = np.where((price_df["pre1day_cci"] >= 100) & (price_df["CCI"] < 100), "sell", price_df["signal_trade"])
            # price_df["signal_trade"] = np.where((price_df["pre1day_cci"] <= -100) & (price_df["CCI"] > -100), "buy", price_df["signal_trade"])

            price_df["signal_trade"] = np.where(price_df[cci_column_var]>=100, "Sell", price_df["signal_trade"])
            price_df["signal_trade"] = np.where(price_df[cci_column_var]<=-100, "Buy", price_df["signal_trade"])
            
            c_df = price_df.iloc[-1]
            current_signal_trade = c_df["signal_trade"]
            current_signal_price = float(round(c_df["Close"],2))

            buy_qty = 0
            sell_qty = 0
            
            order_price = current_signal_price
            order_market = price_target_market
            
            if current_signal_trade == "Buy":
                
                ## 한국 시장일 경우
                if price_target_market in kr_price_market_list:
                    access_token = KisDevelopers(HankookConfig).issue_access_token()

                    ## 국내 예수금 확인
                    check_kr_psbl = KisDevelopers(HankookConfig).kr_inquire_psbl_order(access_token=access_token, stock_code=target_stock_code, order_price=current_signal_price, order_type=order_type)
                    ord_psbl_cash = float(round(int(check_kr_psbl["output"]["ord_psbl_cash"]), 0))

                    ## 국내 시장가 주문 시 주문 가격 "0"으로 변경
                    if order_type == "01":
                        order_price = "0"

                elif price_target_market in us_price_market_list:
                    if price_target_market == "NASDAQ":
                        order_market = "NASD"
                    
                    ## 해외 예수금 확인
                    check_us_psbl = KisDevelopers(HankookConfig).us_inquire_psamount(access_token=access_token, stock_code=target_stock_code, order_market=order_market, price=current_signal_price)
                    ord_psbl_cash = round(float(check_us_psbl["output"]["ord_psbl_frcr_amt"]), 2)

                
                one_order_budget = float(round(ord_psbl_cash * rate_of_one_order, 2))

                buy_qty = one_order_budget // current_signal_price
                if buy_qty >= 2:
                    pass
                elif buy_qty < 2:
                    buy_qty = 1

                buy_qty = str(buy_qty)
                order_price = str(order_price)
                
                if one_order_budget < current_signal_price:
                    if ord_psbl_cash < current_signal_price:
                        message = f"예수금 부족!! {target_stock_name} 1주 주문 가격 : {current_signal_price}, 현재 예수금 : {ord_psbl_cash}"
                        SendMessageSlack(SlackConfig).send_simple_message(message)
                        pass
                    else:        
                        if price_target_market in kr_price_market_list:
                            order_result = KisDevelopers(HankookConfig).kr_order_cash_stock(access_token=access_token, transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price)
                        
                        elif price_target_market in us_price_market_list:
                            if price_target_market == "NASDAQ":
                                order_market = "NASD"
                            order_result = KisDevelopers(HankookConfig).us_order_cash_stock(access_token=access_token, transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price, order_market=order_market)
                        message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}, Trade Price : {order_price} \n{order_result}"
                        SendMessageSlack(SlackConfig).send_simple_message(message)

                else:
                    if price_target_market in kr_price_market_list:
                            order_result = KisDevelopers(HankookConfig).kr_order_cash_stock(access_token=access_token, transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price)
                        
                    elif price_target_market in us_price_market_list:
                        if price_target_market == "NASDAQ":
                            order_market = "NASD"
                        order_result = KisDevelopers(HankookConfig).us_order_cash_stock(access_token=access_token, transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price, order_market=order_market)
                    message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}, Trade Price : {order_price} \n{order_result}"
                    SendMessageSlack(SlackConfig).send_simple_message(message)


            elif current_signal_trade == "Sell":
                access_token = KisDevelopers(HankookConfig).issue_access_token()

                ## 한국 시장일 경우 
                if price_target_market in kr_price_market_list:
                    inquire_balance_result = KisDevelopers(HankookConfig).kr_inquire_balance(access_token=access_token)
                    hold_df = pd.DataFrame(inquire_balance_result["output1"])
                    hold_stock_list = hold_df["pdno"].values.tolist()

                ## 해외 시장일 경우
                elif price_target_market in us_price_market_list:
                    currency_code = "USD"
                    """
                    USD : 미국달러
                    HKD : 홍콩달러
                    CNY : 중국위안화
                    JPY : 일본엔화
                    VND : 베트남동
                    """
                    inquire_balance_result = KisDevelopers(HankookConfig).us_inquire_balance(access_token=access_token, order_market=order_market, currency_code=currency_code)
                    hold_df = pd.DataFrame(inquire_balance_result["output1"])
                    hold_stock_list = hold_df["ovrs_pdno"].values.tolist()
                
                if target_stock_code in hold_stock_list:
                    t_df = hold_df[hold_df["pdno"]==target_stock_code].reset_index(drop=True)
                    current_target_stock_hold_count = int(t_df["ord_psbl_qty"].iloc[0])

                    if current_target_stock_hold_count > 0:
                        sell_qty = int(current_target_stock_hold_count * rate_of_one_order//1)
                        sell_qty = str(sell_qty)
                        order_price = str(order_price)
                        
                        if price_target_market in kr_price_market_list:
                            order_result = KisDevelopers(HankookConfig).kr_order_cash_stock(access_token=access_token, transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=sell_qty, price=order_price)
                        
                        elif price_target_market in us_price_market_list:
                            if price_target_market == "NASDAQ":
                                order_market = "NASD"
                            order_result = KisDevelopers(HankookConfig).us_order_cash_stock(access_token=access_token, transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=sell_qty, price=order_price, order_market=order_market)
                        
                        message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}, Trade Price : {order_price} \n{order_result}"
                        SendMessageSlack(SlackConfig).send_simple_message(message)

            elif current_signal_trade == None:
                message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}"
                SendMessageSlack(SlackConfig).send_simple_message(message)

        except Exception as e:
            print(e)

    else:
        print(f"{price_target_market} is not open today.")