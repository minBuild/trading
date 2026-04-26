from abc import ABC, abstractmethod
from typing import Any, Dict, List


class BaseBroker(ABC):
    """모든 증권사 연동 클래스가 구현해야 하는 인터페이스."""

    @abstractmethod
    def get_access_token(self) -> str:
        """OAuth 액세스 토큰을 반환한다. 만료 시 자동 재발급."""

    @abstractmethod
    def get_current_price(self, ticker: str) -> float:
        """주어진 종목의 현재가(원)를 반환한다."""

    @abstractmethod
    def get_daily_ohlcv(
        self, ticker: str, start: str, end: str
    ) -> List[Dict[str, Any]]:
        """
        일봉 OHLCV 리스트를 반환한다 (최신순).
        start / end 형식: "YYYYMMDD"
        """

    @abstractmethod
    def buy_market_order(self, ticker: str, quantity: int) -> Dict[str, Any]:
        """시장가 매수 주문을 제출하고 응답을 반환한다."""

    @abstractmethod
    def sell_market_order(self, ticker: str, quantity: int) -> Dict[str, Any]:
        """시장가 매도 주문을 제출하고 응답을 반환한다."""

    @abstractmethod
    def get_balance(self) -> Dict[str, Any]:
        """주문 가능 현금 등 잔고 정보를 반환한다."""
