import time
from typing import Any, Dict, List, Optional

import requests

from brokers.base import BaseBroker
from utils.config import config
from utils.logger import get_logger

logger = get_logger(__name__)


class KISBroker(BaseBroker):
    """한국투자증권(KIS) REST API 브로커."""

    _REAL_URL = "https://openapi.koreainvestment.com:9443"
    _PAPER_URL = "https://openapivts.koreainvestment.com:29443"

    # 토큰 유효 시간(초). KIS 기본 발급 주기는 1일
    _TOKEN_TTL = 86_400.0

    def __init__(self) -> None:
        self.base_url = self._PAPER_URL if config.is_paper else self._REAL_URL
        self._access_token: Optional[str] = None
        self._token_issued_at: float = 0.0

    # ------------------------------------------------------------------ #
    #  Token                                                               #
    # ------------------------------------------------------------------ #

    def get_access_token(self) -> str:
        if self._access_token and (time.time() - self._token_issued_at) < self._TOKEN_TTL:
            return self._access_token

        url = f"{self.base_url}/oauth2/tokenP"
        payload = {
            "grant_type": "client_credentials",
            "appkey": config.app_key,
            "appsecret": config.app_secret,
        }

        logger.info("액세스 토큰 발급 요청 중...")
        resp = requests.post(url, json=payload, timeout=10)
        resp.raise_for_status()

        data = resp.json()
        self._access_token = data["access_token"]
        self._token_issued_at = time.time()
        logger.info("액세스 토큰 발급 완료.")
        return self._access_token

    def _headers(self, tr_id: str, extra: Optional[Dict] = None) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.get_access_token()}",
            "appkey": config.app_key,
            "appsecret": config.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }
        if extra:
            headers.update(extra)
        return headers

    # ------------------------------------------------------------------ #
    #  시세 조회                                                           #
    # ------------------------------------------------------------------ #

    def get_current_price(self, ticker: str) -> float:
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
        }

        logger.debug(f"현재가 조회: {ticker}")
        resp = requests.get(
            url, headers=self._headers("FHKST01010100"), params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self._check_rt(data, ticker)

        price = float(data["output"]["stck_prpr"])
        logger.debug(f"{ticker} 현재가: {price:,.0f}원")
        return price

    def get_daily_ohlcv(
        self, ticker: str, start: str, end: str
    ) -> List[Dict[str, Any]]:
        """일봉 데이터 조회. 반환 리스트는 최신 날짜가 index 0."""
        url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",
            "FID_INPUT_ISCD": ticker,
            "FID_PERIOD_DIV_CODE": "D",
            "FID_ORG_ADJ_PRC": "0",
            "FID_INPUT_DATE_1": start,
            "FID_INPUT_DATE_2": end,
        }

        logger.debug(f"일봉 조회: {ticker} ({start}~{end})")
        resp = requests.get(
            url, headers=self._headers("FHKST01010400"), params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self._check_rt(data, ticker)
        return data.get("output", [])

    # ------------------------------------------------------------------ #
    #  주문                                                                #
    # ------------------------------------------------------------------ #

    def buy_market_order(self, ticker: str, quantity: int) -> Dict[str, Any]:
        return self._place_order(ticker, quantity, side="buy")

    def sell_market_order(self, ticker: str, quantity: int) -> Dict[str, Any]:
        return self._place_order(ticker, quantity, side="sell")

    def _place_order(self, ticker: str, quantity: int, side: str) -> Dict[str, Any]:
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"

        # 모의/실전 × 매수/매도별 tr_id
        tr_map = {
            (True,  "buy"):  "VTTC0802U",
            (True,  "sell"): "VTTC0801U",
            (False, "buy"):  "TTTC0802U",
            (False, "sell"): "TTTC0801U",
        }
        tr_id = tr_map[(config.is_paper, side)]

        payload = {
            "CANO": config.cano,
            "ACNT_PRDT_CD": config.acnt_prdt_cd,
            "PDNO": ticker,
            "ORD_DVSN": "01",       # 01 = 시장가
            "ORD_QTY": str(quantity),
            "ORD_UNPR": "0",        # 시장가 주문은 단가 0
        }

        label = side.upper()
        logger.info(f"{label} 주문 전송: {ticker} x {quantity}주 (시장가)")
        resp = requests.post(
            url, headers=self._headers(tr_id), json=payload, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self._check_rt(data, ticker)

        odno = data["output"].get("ODNO", "-")
        logger.info(f"{label} 주문 접수 완료: {ticker} x {quantity}주, 주문번호={odno}")
        return data

    # ------------------------------------------------------------------ #
    #  잔고 조회                                                           #
    # ------------------------------------------------------------------ #

    def get_balance(self) -> Dict[str, Any]:
        url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-psbl-order"
        tr_id = "VTTC8908R" if config.is_paper else "TTTC8908R"
        params = {
            "CANO": config.cano,
            "ACNT_PRDT_CD": config.acnt_prdt_cd,
            "PDNO": "",
            "ORD_UNPR": "0",
            "ORD_DVSN": "01",
            "CMA_EVLU_AMT_ICLD_YN": "N",
            "OVRS_ICLD_YN": "N",
        }

        logger.debug("주문가능 잔고 조회")
        resp = requests.get(
            url, headers=self._headers(tr_id), params=params, timeout=10
        )
        resp.raise_for_status()
        data = resp.json()
        self._check_rt(data, "balance")
        return data.get("output", {})

    # ------------------------------------------------------------------ #
    #  내부 헬퍼                                                           #
    # ------------------------------------------------------------------ #

    @staticmethod
    def _check_rt(data: Dict[str, Any], label: str) -> None:
        if data.get("rt_cd") != "0":
            raise RuntimeError(f"KIS API 오류 [{label}]: {data.get('msg1')}")
