import os
from os import path
import sys

app_path = path.abspath(path.join(".."))

if app_path not in sys.path:
    sys.path.append(app_path)

import FinanceDataReader as fdr
import financedatabase as fd

import exchange_calendars as ecals
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from tabulate import tabulate

import csv
import traceback

from config import HankookConfig, SlackConfig, GoogleSpreadseetsConfig

from hankook_trade_api import TradeHankookAPI
from slack_message import SendMessageSlack

def check_open_market(country_code):
    open_dummy = 0
    if country_code == "us":
        t_calendar = ecals.get_calendar("XNYS")
        us_now = datetime.now() - timedelta(hours=13)
        open_dummy = t_calendar.is_session(us_now.strftime("%Y-%m-%d"))
    
    elif country_code == "kr":
        t_calendar = ecals.get_calendar("XKRX")
        open_dummy = t_calendar.is_session(datetime.now().strftime("%Y-%m-%d"))
            
    return open_dummy
    
def trade_cci(price_target_market, order_type, target_stock_code=None, target_stock_name=None, cci_calculate_days=20, rate_of_one_order=0.1):
    """
    price_target_market (str) = 'KRX', 'KOSPI', 'ETF_KR', 'NASDAQ', 'NYSE', 'S&P500', 'AMEX', 'ETF_US
    cci_caclulate_days (int) = default 20
    rate_of_one_order (float) = default 0.1
    order type
    한국 주문 구분 시장가 (str) = default "01" (00 지정가, 01 시장가, 02 조건부지정가, 05 장전 시간외, 06 장후 시간외)

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
    print(f"Start Trade CCI {target_stock_code}!", datetime.now())
    
    stock_name_column_var = "Name"
    stock_code_column_var = "Code"
    
    cci_column_var = f"CCI_{cci_calculate_days}"
    pre_1day_cci_column_var = f"Before_1Day_{cci_column_var}"

    kr_price_market_list = ["KRX", "KOSPI", "ETF_KR"]
    us_price_market_list = ["NASDAQ", "NYSE", "S&P500", 'AMEX', "ETF_US"]
    
    us_etf_order_dict = {
        "AMEX" : ["JEPI", ""],
        "NASDAQ" : ["TQQQ", "SQQQ"]
    }
    
    us_etf_order_df = pd.DataFrame(us_etf_order_dict)
    country_code = None
    if price_target_market in us_price_market_list:
        country_code = "us"
        stock_code_column_var = "Symbol"
        if price_target_market == "ETF_US":
            stock_code_column_var = "symbol"
            stock_name_column_var = "name"
    
    elif price_target_market in kr_price_market_list:
        country_code = "kr"
        if price_target_market == "ETF_KR":
            stock_code_column_var = "Symbol"

    open_dummy = check_open_market(country_code)
    
    if open_dummy == 1:
        try:
            if price_target_market == "ETF_KR":
                df = fdr.StockListing("ETF/KR")
            elif price_target_market == "ETF_US":
                df = fd.ETFs().search(currency="USD").reset_index()
            else:
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

        except:
            print(traceback.format_exc())

        try:
            end_date = datetime.now()
            start_date = end_date - timedelta(days = cci_calculate_days*2)
            start_date_str = datetime.strftime(start_date, "%Y-%m-%d")
            end_date_str = datetime.strftime(end_date, "%Y-%m-%d")
            price_df = fdr.DataReader(target_stock_code, start_date_str, end_date_str)
            price_df = price_df.reset_index(drop=False)
            price_df["TP"] = (price_df["High"] + price_df["Low"] + price_df["Close"]) / 3
            price_df["sma"] = price_df["TP"].rolling(cci_calculate_days).mean()
            price_df["mad"] = price_df["TP"].rolling(cci_calculate_days).apply(lambda x: abs(x - pd.Series(x).mean()).sum() / cci_calculate_days)
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
            
            target_stock_name = target_stock_name.strip()
            csv_file_name = f"{price_target_market}_{target_stock_name}_{target_stock_code}.csv"
            price_df.to_csv(csv_file_name, index=False, encoding="utf-8-sig")
            
            if current_signal_trade == "Buy":
                
                ## 한국 시장일 경우
                if price_target_market in kr_price_market_list:
                    ## 국내 예수금 확인
                    check_kr_psbl = TradeHankookAPI(HankookConfig).kr_inquire_psbl_order(stock_code=target_stock_code, order_price=current_signal_price, order_type=order_type)
                    ord_psbl_cash = float(round(int(check_kr_psbl["output"]["ord_psbl_cash"]), 0))

                    ## 국내 시장가 주문 시 주문 가격 "0"으로 변경
                    if order_type == "01":
                        order_price = "0"
                    else:
                        order_price = int(current_signal_price)

                ## 미국 시장일 경우
                elif price_target_market in us_price_market_list:
                        
                    if price_target_market == "NASDAQ":
                        order_market = "NASD"
                            
                    if price_target_market == "ETF_US":
                        if target_stock_code in us_etf_order_df["AMEX"].values.tolist():
                            order_market = "AMEX"
                        elif target_stock_code in us_etf_order_df["NASDAQ"].values.tolist():
                            order_market = "NASD"
                        
                    order_price = float(round(current_signal_price, 2))
                    
                    ## 해외 예수금 확인
                    check_us_psbl = TradeHankookAPI(HankookConfig).us_inquire_psamount(stock_code=target_stock_code, order_market=order_market, price=current_signal_price)
                    ord_psbl_cash = round(float(check_us_psbl["output"]["frcr_ord_psbl_amt1"]), 2)

                
                one_order_budget = float(round(ord_psbl_cash * rate_of_one_order, 2))

                buy_qty = one_order_budget // current_signal_price
                if buy_qty >= 2:
                    pass
                elif buy_qty < 2:
                    buy_qty = 1

                buy_qty = str(int(buy_qty))
                
                if one_order_budget < current_signal_price:
                    if ord_psbl_cash < current_signal_price:
                        message = f"예수금 부족!! {target_stock_name} 1주 주문 가격 : {current_signal_price}, 현재 예수금 : {ord_psbl_cash}"
                        SendMessageSlack(SlackConfig).send_simple_message(message)
                        pass
                    else:        
                        if price_target_market in kr_price_market_list:
                            order_price = str(order_price)
                            order_result = TradeHankookAPI(HankookConfig).kr_order_cash_stock(transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price)
                        
                        elif price_target_market in us_price_market_list:
                            if price_target_market == "NASDAQ":
                                order_market = "NASD"
                            order_price = str(order_price)
                            order_result = TradeHankookAPI(HankookConfig).us_order_cash_stock(transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price, order_market=order_market)
                        # message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}, Trade Price : {order_price} \n{order_result}"
                        # SendMessageSlack(SlackConfig).send_simple_message(message)

                else:
                    if price_target_market in kr_price_market_list:
                        order_result = TradeHankookAPI(HankookConfig).kr_order_cash_stock(transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price)
                        
                    elif price_target_market in us_price_market_list:
                        if price_target_market == "NASDAQ":
                            order_market = "NASD"
                        order_price = str(order_price)
                        order_result = TradeHankookAPI(HankookConfig).us_order_cash_stock(transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=buy_qty, price=order_price, order_market=order_market)
                    # message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}, Trade Price : {order_price} \n{order_result}"
                    # SendMessageSlack(SlackConfig).send_simple_message(message)


            elif current_signal_trade == "Sell":

                ## 한국 시장일 경우 
                if price_target_market in kr_price_market_list:
                    inquire_balance_result = TradeHankookAPI(HankookConfig).kr_inquire_balance()
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
                    try:
                        inquire_balance_result = TradeHankookAPI(HankookConfig).us_inquire_balance(order_market=order_market, currency_code=currency_code)
                        hold_df = pd.DataFrame(inquire_balance_result["output1"])
                        hold_stock_list = hold_df["ovrs_pdno"].values.tolist()
                    except:
                        message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade} \n But {target_stock_code} not in hold_stock_list!"
                        SendMessageSlack(SlackConfig).send_simple_message(message)
                        print(traceback.format_exc())
                        pass
                
                if target_stock_code in hold_stock_list:
                    try:
                        t_df = hold_df[hold_df["pdno"]==target_stock_code].reset_index(drop=True)
                        current_target_stock_hold_count = int(t_df["ord_psbl_qty"].iloc[0])

                        if current_target_stock_hold_count > 0:
                            sell_qty = int(current_target_stock_hold_count * rate_of_one_order//1)
                            sell_qty = str(sell_qty)
                            order_price = str(order_price)
                            
                            if price_target_market in kr_price_market_list:
                                order_result = TradeHankookAPI(HankookConfig).kr_order_cash_stock(transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=sell_qty, price=order_price)
                            
                            elif price_target_market in us_price_market_list:
                                if price_target_market == "NASDAQ":
                                    order_market = "NASD"
                                order_result = TradeHankookAPI(HankookConfig).us_order_cash_stock(transaction=current_signal_trade, stock_code=target_stock_code, order_type=order_type, quantity=sell_qty, price=order_price, order_market=order_market)
                            
                            message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}, Trade Price : {order_price} \n{order_result}"
                            SendMessageSlack(SlackConfig).send_simple_message(message)
                    except:
                        print(traceback.format_exc())
                        message = "Check the code! create_cci_signal.py line 241"
                        SendMessageSlack(SlackConfig).send_simple_message(message)
                        pass

            elif current_signal_trade == None:
                message = f"Stock :{target_stock_name}, Trade Signal : {current_signal_trade}"
                print(message, datetime.now().strftime("%Y-%m-%d, %H:%M:%S"))
                # SendMessageSlack(SlackConfig).send_simple_message(message)
                pass
                
                

        except:
            print(traceback.format_exc())

    else:
        print(f"{price_target_market} is not open today.")
        
        
def search_trading_history(country_code, start_date_str=None, end_date_str=None):
    
    r_df = pd.DataFrame()
    open_dummy = check_open_market(country_code)
    if open_dummy == 1:
        if country_code == "kr":
            if start_date_str == None:
                start_date_str = datetime.today().date().strftime("%Y%m%d")
            if end_date_str == None:
                end_date_str = datetime.today().date().strftime("%Y%m%d")
            r_json = TradeHankookAPI(HankookConfig).kr_inquire_daily_ccld(start_date_str, end_date_str)
            return_data = r_json["output1"]
            
        elif country_code == "us":
            if start_date_str == None:
                start_date_str = (datetime.today() - timedelta(days=1)).date().strftime("%Y%m%d")
            if end_date_str == None:
                end_date_str = (datetime.today() - timedelta(days=1)).date().strftime("%Y%m%d")
            r_json = TradeHankookAPI(HankookConfig).us_inquire_ccnl(start_date_str, end_date_str)
            return_data = r_json["output"]
            
        if len(return_data) > 0:
            df = pd.DataFrame(return_data)
            if country_code == "kr":
                r_df = df[["ord_dt", "sll_buy_dvsn_cd_name", "pdno", "prdt_name", "tot_ccld_qty", "tot_ccld_amt", "avg_prvs"]]
            elif country_code == "us":
                r_df = df[["ord_dt", "sll_buy_dvsn_cd_name", "pdno", "prdt_name", "ft_ccld_qty", "ft_ccld_unpr3", "ft_ccld_amt3", "prcs_stat_name"]]
                
            p_r_df = tabulate(r_df, tablefmt="pretty")
            message = f"**오늘 체결 내역** \n {p_r_df}"
            SendMessageSlack(SlackConfig).send_simple_message(message)
        else:
            message = f"{start_date_str}, There are no {country_code} trades histroy."
            SendMessageSlack(SlackConfig).send_simple_message(message)
    else:
        print(f"{country_code} is not open today.")