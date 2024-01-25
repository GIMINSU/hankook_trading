
## related to config
from os import path
import sys

config_path = path.abspath(path.join(".."))
if config_path not in sys.path:
    sys.path.append(config_path)

from config import HankookConfig

## related to API
import requests
import json

import pandas as pd

class TradeHankookAPI(HankookConfig):
    def __init__(self, HankookConfig):
        self.kr_key = HankookConfig.kr_key
        self.kr_secret = HankookConfig.kr_secret
        self.us_key = HankookConfig.us_key
        self.us_secret = HankookConfig.us_secret
        self.url_base = "https://openapi.koreainvestment.com:9443"
        self.kr_account_number = HankookConfig.kr_account_number
        self.us_account_number = HankookConfig.us_account_number
        
    def issue_access_token(self, country_code):
        """
        country_code = kr, us
        """
        app_key = None
        app_secret = None
        csv_file_name = f"{country_code}_token.csv"
        
        if country_code == "kr":
            app_key = self.kr_key
            app_secret = self.kr_secret
            
        elif country_code == "us":
            app_key = self.us_key
            app_secret = self.us_secret
        
        url_base = "https://openapi.koreainvestment.com:9443"
        url = "oauth2/tokenP"  ## KIS DEVELOPERS > API 문서 > 각 항목 > 기본정보 > URL 을 의미함
        
        final_url = f"{url_base}/{url}"
        
        headers = {"content-type" : "application/json"}
        body = {
            "grant_type" : "client_credentials",
            "appkey" : app_key,
            "appsecret" : app_secret
            }
        
        r = requests.post(final_url, headers = headers, data = json.dumps(body))
        r_code = r.status_code
        
        access_token = None
        
        if r_code == 200:
            access_token = r.json()["access_token"]
            return_dict = {f"{country_code}_token" : access_token}
            df = pd.DataFrame([return_dict])
            df.to_csv(csv_file_name, index=False, encoding="utf-8-sig")
            
            print("Success Issue Access Token.")
        else:
            print("Fail Issue Access Token.")
            print("response :", r_code)
            print("response headers :", r.headers)
            print("resopnse text :", r.text)
            pass

    def issue_hashkey(self, country_code, account_type="01"):
        """
        INPUT : 
            account_number : string 계좌번호
            account_type : string 계좌상품코드(통장종류) defualt 01(위탁종합인듯)
        OUTPUT :
            hashkey : 거래시 사용되는 HASHKEY
        """
        account_number = None
        if country_code == "kr":
            account_number = self.kr_account_number

        elif country_code == "us":
            account_number = self.us_account_number
            
        url = "/uapi/hashkey"
        final_url = f"{self.url_base}/{url}"
        headers = {
            "appkey" : self.app_key,
            "appsecret" : self.app_secret,
            "content_Type" : "application/json"
        }

        body = {
            "CANO" : account_number,
            "ACNT_PRDT_CD" : account_type,
            "OVRS_EXCG_CD" : 'SHAA'  ## KIS DEVELOPERS 문서 안내 상 고정 값
        }

        r = requests.post(final_url, headers = headers, data = json.dumps(body))
        r_code = r.status_code
        
        hashkey = None
        if r_code == 200:
            hashkey = r.json()["HASH"]
            print("Success Issue HASHKEY.")
        else:
            print("Fail Issue HASHKEY.")
            print("response :", r_code)
            print("response headers :", r.headers)
            print("resopnse text :", r.text)
            pass

        return hashkey

    def kr_order_cash_stock(self, transaction, stock_code, order_type, quantity, price, account_type="01"):
        """
        transaction : str "Buy", "Sell" 입력
        stock_code : str 종목코드 6자리
        order_type : str 주문 구분 시장가 "01" (00 지정가, 01 시장가, 02 조건부지정가, 05 장전 시간외, 06 장후 시간외)
        quantity : str 주문 수량
        price : str 1주당 주문 가격, 시장가 주문의 경우 "0" 입력
        account_number : str 계좌번호 앞8자리, 입력안하면 config 기본 계좌번호
        account_type : str 계좌번호 뒤2자리, 입력 안하면 "01" 기본 입력 
        tr_cont : str 연속 거래 조회 여부, "" 공백 초기 조회, N 다음 데이터 조회
        """
        app_key = self.kr_key
        app_secret = self.kr_secret

        access_token = pd.read_csv("kr_token.csv")["kr_token"][0]

        url = "/uapi/domestic-stock/v1/trading/order-cash"
        final_url = f"{self.url_base}/{url}"
        
        tr_id = None
        if transaction == "Buy":
            tr_id = "TTTC0802U"  ## 한국 매수 주문
        elif transaction == "Sell":
            tr_id = "TTTC0801U"  ## 한국 매도 주문
        
        account_number = self.kr_account_number

        headers = {
                "Content-Type" : "application/json",
                "authorization" : f"Bearer {access_token}",
                "appkey" : app_key,
                "appsecret" : app_secret,
                "tr_id" : tr_id,
                "custtype" : "P",  ## 개인
                # "hashkey" : HASH
        }

        body = {
            "CANO": account_number,
            "ACNT_PRDT_CD": account_type,
            "PDNO": stock_code,
            "ORD_DVSN": order_type,
            "ORD_QTY": quantity,
            "ORD_UNPR": price
        }
        res = requests.post(final_url, headers = headers, data = json.dumps(body))
        return res.json()


    def us_order_cash_stock(self, transaction, price, order_type, stock_code, order_market, quantity, account_type="01"):
        """
        transaction : str "Buy", "Sell"
        OVRS_EXCG_CD : 
        NASD : 나스닥
        NYSE : 뉴욕
        AMEX : 아멕스
        SEHK : 홍콩
        SHAA : 중국상해
        SZAA : 중국심천
        TKSE : 일본
        HASE : 베트남 하노이
        VNSE : 베트남 호치민

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

        [Header tr_id JTTT1006U (홍콩 매도 주문)]
        00 : 지정가
        05 : 단주지정가 셋팅
        """
    
        url = "/uapi/overseas-stock/v1/trading/order"
        final_url = f"{self.url_base}/{url}"

        tr_id = None
        if transaction == "Buy":
            tr_id = "JTTT1002U"
        elif transaction == "Sell":
            tr_id = "JTTT1006U"

        app_key = self.us_key
        app_secret = self.us_secret

        access_token = pd.read_csv("us_token.csv")["us_token"][0]
        account_number = self.us_account_number

        headers = {
                "Content-Type" : "application/json",
                "authorization" : f"Bearer {access_token}",
                "appkey" : app_key,
                "appsecret" : app_secret,
                "tr_id" : tr_id,
                "custtype" : "P"
                }

        datas = {
            "CANO": account_number,
            "ACNT_PRDT_CD": account_type,
            "OVRS_EXCG_CD": order_market, 
            "PDNO": stock_code,
            "ORD_QTY": quantity,
            "OVRS_ORD_UNPR": price,
            "CTAC_TLNO": "",  ## 연락 전화번호
            "MGCO_APTM_ODNO": "",
            "ORD_SVR_DVSN_CD": "0",  ## 주문서버구분코드 default "0"
            "ORD_DVSN": order_type
            }
        
        res = requests.post(final_url, headers = headers, data = json.dumps(datas))
        return res.json()
    
    def us_cancel_cash_stock(self, order_market, stock_code, orgn_odno, rvse_cncl_dvsn_cd, qty, price, account_type = "01"):
        url = "/uapi/overseas-stock/v1/trading/order-rvsecncl"
        final_url = f"{self.url_base}/{url}"

        app_key = self.us_key
        app_secret = self.us_secret

        access_token = pd.read_csv("us_token.csv")["us_token"][0]
        account_number = self.us_account_number

        tr_id = "TTTT1004U"

        headers = {
                "Content-Type" : "application/json",
                "authorization" : f"Bearer {access_token}",
                "appkey" : app_key,
                "appsecret" : app_secret,
                "tr_id" : tr_id,
                "custtype" : "P"
                }
        
        datas = {
            "CANO": account_number, ## 종합계좌번호
            "ACNT_PRDT_CD": account_type,  ## 계좌상품코드
            "OVRS_EXCG_CD": order_market,   ## 해외거래소코드
            "PDNO": stock_code,  ## 상품번호
            "ORGN_ODNO": orgn_odno,  ## 원주문번호
            "RVSE_CNCL_DVSN_CD": rvse_cncl_dvsn_cd,  ## 정정취소구분코드 01 : 정정 02 : 취소
            "ORD_QTY": qty,  ## 주문수량
            "OVRS_ORD_UNPR": price,  ## 해외주문단가
            "CTAC_TLNO":"",
            "MGCO_APTM_ODNO": "",  ## 운용사지정주문번호 not required
            "ORD_SVR_DVSN_CD": "0" ## 주문서버구분코드  not required defaul 0
        }

        res = requests.post(final_url, headers = headers, data = json.dumps(datas))
        return res.json()

    def kr_inquire_psbl_order(self, stock_code, order_price, order_type, account_type = "01"):
        url = "/uapi/domestic-stock/v1/trading/inquire-psbl-order"
        final_url = f"{self.url_base}/{url}"

        app_key = self.kr_key
        app_secret = self.kr_secret

        access_token = pd.read_csv("kr_token.csv")["kr_token"][0]
        account_number = self.kr_account_number

        tr_id = "TTTC8908R"  ## 실전투자, 모의투자 : VTTC8908R 
        headers = {
            "authorization" : f"Bearer {access_token}",
            "appkey" : app_key,
            "appsecret" : app_secret,
            "tr_id" : tr_id
            }
        datas = {
            "CANO": account_number,
            "ACNT_PRDT_CD": account_type,
            "PDNO": stock_code,
            "ORD_UNPR": order_price,
            "ORD_DVSN": order_type,
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "OVRS_ICLD_YN": "N"
        }
        res = requests.get(final_url, headers= headers, params = datas)
        return res.json()
        
    def kr_inquire_balance(self, account_type = "01", AFHR_FLPR_YN="N", OFL_YN="", INQR_DVSN="02", UNPR_DVSN="01", FUND_STTL_ICLD_YN="N", FNCG_AMT_AUTO_RDPT_YN ="N", PRCS_DVSN="00", CTX_AREA_FK100="", CTX_AREA_NK100=""):
        ## AFHR_FLPR_YN : 시간외 단일가 여부 N : 기본값, Y : 시간외단일가
        ## OFL_YN : 오프라인여부 공란: 기본값
        ## INQR_DVSN : 조회구분  01: 대출일별, 02: 종목별
        ## UNPR_DVSN : 단가구분 01: 기본값
        ## FUND_STTL_ICLD_YN : 펀드결제 포함여부 N: 포함하지 않음, Y: 포함
        ## FNCG_AMT_AUTO_RDPT_YN : 융자금액 자동 상환 여부 N: 기본값
        ## PRCS_DVSN : 처리구분  00 : 전일매매포함 01 : 전일매매미포함
        ## CTX_AREA_FK100 : 연속조회검색조건100 공란 : 최초 조회시, 이전 조회 Output CTX_AREA_FK100 값 : 다음페이지 조회시(2번째부터)
        ## CTX_AREA_NK100 : 연속조회키100 공란 : 최초 조회시, 이전 조회 Output CTX_AREA_NK100 값 : 다음페이지 조회시(2번째부터)

        url = "/uapi/domestic-stock/v1/trading/inquire-balance"
        final_url = f"{self.url_base}/{url}"

        app_key = self.kr_key
        app_secret = self.kr_secret

        access_token = pd.read_csv("kr_token.csv")["kr_token"][0]
        account_number = self.kr_account_number

        tr_id = "TTTC8434R"

        headers = {
            "authorization" : f"Bearer {access_token}",
            "appkey" : app_key,
            "appsecret" : app_secret,
            "tr_id" : tr_id
            }

        datas = {
            "CANO": account_number,
            "ACNT_PRDT_CD": account_type,
            "AFHR_FLPR_YN": AFHR_FLPR_YN,
            "OFL_YN": OFL_YN,
            "INQR_DVSN": INQR_DVSN,
            "UNPR_DVSN": UNPR_DVSN,
            "FUND_STTL_ICLD_YN": FUND_STTL_ICLD_YN,
            "FNCG_AMT_AUTO_RDPT_YN": FNCG_AMT_AUTO_RDPT_YN,
            "PRCS_DVSN": PRCS_DVSN,
            "CTX_AREA_FK100": CTX_AREA_FK100,
            "CTX_AREA_NK100": CTX_AREA_NK100
        }
        res = requests.get(final_url, headers=headers, params = datas)
        return res.json()

    def us_inquire_psamount(self, stock_code, order_market, price, account_type = "01"):
    
        url = "/uapi/overseas-stock/v1/trading/inquire-psamount"
        final_url = f"{self.url_base}/{url}"

        app_key = self.us_key
        app_secret = self.us_secret

        access_token = pd.read_csv("us_token.csv")["us_token"][0]
        account_number = self.us_account_number

        tr_id = "JTTT3007R"

        headers = {
            "authorization" : f"Bearer {access_token}",
            "appkey" : app_key,
            "appsecret" : app_secret,
            "tr_id" : tr_id
        }

        datas = {
            "ACNT_PRDT_CD": account_type,
            "CANO": account_number,
            "ITEM_CD": stock_code,  ## 종목코드
            "OVRS_EXCG_CD": order_market,
            "OVRS_ORD_UNPR": price
        }

        res = requests.get(final_url, headers=headers, params = datas)
        return res.json()


    def us_inquire_balance(self, order_market, currency_code, account_type = "01", CTX_AREA_FK200="", CTX_AREA_NK200=""):
        url = "/uapi/overseas-stock/v1/trading/inquire-balance"
        final_url = f"{self.url_base}/{url}"
        
        app_key = self.us_key
        app_secret = self.us_secret

        access_token = pd.read_csv("us_token.csv")["us_token"][0]
        account_number = self.us_account_number

        tr_id = "JTTT3012R"

        headers = {
            "authorization" : f"Bearer {access_token}",
            "appkey" : app_key,
            "appsecret" : app_secret,
            "tr_id" : tr_id
        }

        datas = {
            "CANO": account_number,
            "ACNT_PRDT_CD": account_type,
            "OVRS_EXCG_CD": order_market,
            "TR_CRCY_CD": currency_code,
            "CTX_AREA_FK200": CTX_AREA_FK200,
            "CTX_AREA_NK200": CTX_AREA_NK200
        }
        res = requests.get(final_url, headers=headers, params = datas)
        return res.json()

    def kr_inquire_daily_ccld(self, INQR_STRT_DT, INQR_END_DT, account_type="01", SLL_BUY_DVSN_CD="00", INQR_DVSN="00", PDNO="", CCLD_DVSN="01", CTX_AREA_FK100="", CTX_AREA_NK100=""):
        url = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"
        final_url = f"{self.url_base}/{url}"

        app_key = self.kr_key
        app_secret = self.kr_secret

        access_token = pd.read_csv("kr_token.csv")["kr_token"][0]
        account_number = self.kr_account_number
        tr_id = "TTTC8001R"  ## 주식 일별 주문 체결 조회 3개월 이내, 3개월 이상은 CTSC9115R

        headers = {
            "authorization" : f"Bearer {access_token}",
            "appkey" : app_key,
            "appsecret" : app_secret,
            "tr_id" : tr_id
        }

        datas = {
            "CANO": account_number,  ## 계좌번호 체계(8-2)의 앞 8자리
            "ACNT_PRDT_CD": account_type,  ## 계좌번호 체계(8-2)의 뒤 2자리
            "INQR_STRT_DT": INQR_STRT_DT,  ## YYYYMMDD
            "INQR_END_DT": INQR_END_DT,  ## YYYYMMDD
            "SLL_BUY_DVSN_CD": SLL_BUY_DVSN_CD,  ## 00 : 전체 01 : 매도 02 : 매수
            "INQR_DVSN": INQR_DVSN,  ## 	00 : 역순 01 : 정순
            "PDNO": PDNO,  ## 종목번호(6자리) 공란 : 전체 조회
            "CCLD_DVSN": CCLD_DVSN,  ## 00 : 전체 01 : 체결 02 : 미체결
            "ORD_GNO_BRNO": "",  ## 
            "ODNO": "",  ## 
            "INQR_DVSN_3": "",  ## 00 : 전체 01 : 현금 02 : 융자 03 : 대출 04 : 대주
            "INQR_DVSN_1": "",  ## 공란 : 전체 1 : ELW 2 : 프리보드
            "CTX_AREA_FK100": CTX_AREA_FK100,  ## 
            "CTX_AREA_NK100": CTX_AREA_NK100  ## 
        }

        res = requests.get(final_url, headers=headers, params = datas)
        return res.json()