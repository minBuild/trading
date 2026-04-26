import datetime
import time
from typing import Any, Dict, List

from brokers.base import BaseBroker
from core.portfolio import Portfolio
from strategies.base import BaseStrategy
from utils.logger import get_logger

logger = get_logger(__name__)


class TradingEngine:
    """
    매매 루프를 구동하는 엔진.
    Broker / Strategy / Portfolio 는 생성자에서 주입받는다(DI).
    """

    _MARKET_OPEN  = datetime.time(9,  0)
    _MARKET_CLOSE = datetime.time(15, 30)
    _SELL_FROM    = datetime.time(15, 15)   # 마감 전 청산 시작

    def __init__(
        self,
        broker: BaseBroker,
        strategy: BaseStrategy,
        portfolio: Portfolio,
        tickers: List[str],
        poll_interval: int = 60,
    ) -> None:
        self.broker        = broker
        self.strategy      = strategy
        self.portfolio     = portfolio
        self.tickers       = tickers
        self.poll_interval = poll_interval

    # ------------------------------------------------------------------ #
    #  진입점                                                              #
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        logger.info(f"TradingEngine 시작 | 종목: {self.tickers}")
        try:
            while True:
                now = datetime.datetime.now().time()

                if not self._is_market_open(now):
                    logger.debug("장 외 시간 — 대기 중...")
                    time.sleep(self.poll_interval)
                    continue

                self._sync_cash()
                is_closing = now >= self._SELL_FROM

                for ticker in self.tickers:
                    try:
                        self._process(ticker, is_closing)
                    except Exception as exc:
                        logger.error(
                            f"[{ticker}] 처리 중 오류: {exc}", exc_info=True
                        )

                time.sleep(self.poll_interval)

        except KeyboardInterrupt:
            logger.info("사용자 중단 요청 — 엔진 종료.")
        finally:
            logger.info(f"최종 포트폴리오: {self.portfolio.summary()}")

    # ------------------------------------------------------------------ #
    #  종목별 처리                                                         #
    # ------------------------------------------------------------------ #

    def _process(self, ticker: str, is_closing: bool) -> None:
        current_price = self.broker.get_current_price(ticker)
        market_data   = self._build_market_data(ticker, current_price, is_closing)

        if is_closing:
            if self.portfolio.is_holding(ticker):
                self._sell(ticker, current_price)
        else:
            if not self.portfolio.is_holding(ticker):
                if self.strategy.should_buy(ticker, market_data):
                    qty = self.strategy.calculate_quantity(
                        ticker, current_price, self.portfolio.cash
                    )
                    if qty > 0:
                        self._buy(ticker, qty, current_price)

    def _build_market_data(
        self, ticker: str, current_price: float, is_closing: bool
    ) -> Dict[str, Any]:
        today     = datetime.date.today()
        yesterday = today - datetime.timedelta(days=1)

        ohlcv = self.broker.get_daily_ohlcv(
            ticker,
            start=yesterday.strftime("%Y%m%d"),
            end=today.strftime("%Y%m%d"),
        )

        # index 0 = 당일(당일 시가 사용), index 1 = 전일 고저 사용
        today_open = float(ohlcv[0]["stck_oprc"]) if len(ohlcv) > 0 else 0.0
        prev_high  = float(ohlcv[1]["stck_hgpr"]) if len(ohlcv) > 1 else 0.0
        prev_low   = float(ohlcv[1]["stck_lwpr"]) if len(ohlcv) > 1 else 0.0

        return {
            "current_price":    current_price,
            "today_open":       today_open,
            "prev_high":        prev_high,
            "prev_low":         prev_low,
            "is_market_closing": is_closing,
        }

    # ------------------------------------------------------------------ #
    #  주문 실행                                                           #
    # ------------------------------------------------------------------ #

    def _buy(self, ticker: str, quantity: int, price: float) -> None:
        logger.info(f"▲ 매수 실행: {ticker} {quantity}주 @ ~{price:,.0f}원")
        try:
            self.broker.buy_market_order(ticker, quantity)
            self.portfolio.record_buy(ticker, quantity, price)
        except Exception as exc:
            logger.error(f"매수 주문 실패 [{ticker}]: {exc}", exc_info=True)

    def _sell(self, ticker: str, price: float) -> None:
        holding = self.portfolio.get_holding(ticker)
        if not holding:
            return
        quantity = holding["quantity"]
        logger.info(f"▼ 매도 실행: {ticker} {quantity}주 @ ~{price:,.0f}원")
        try:
            self.broker.sell_market_order(ticker, quantity)
            self.portfolio.record_sell(ticker, quantity, price)
        except Exception as exc:
            logger.error(f"매도 주문 실패 [{ticker}]: {exc}", exc_info=True)

    # ------------------------------------------------------------------ #
    #  내부 헬퍼                                                           #
    # ------------------------------------------------------------------ #

    def _is_market_open(self, now: datetime.time) -> bool:
        return self._MARKET_OPEN <= now <= self._MARKET_CLOSE

    def _sync_cash(self) -> None:
        try:
            balance   = self.broker.get_balance()
            available = float(balance.get("ord_psbl_cash", 0))
            self.portfolio.update_cash(available)
        except Exception as exc:
            logger.error(f"현금 잔고 동기화 실패: {exc}", exc_info=True)
