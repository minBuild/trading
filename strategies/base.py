from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseStrategy(ABC):
    """모든 매매 전략이 구현해야 하는 인터페이스."""

    @abstractmethod
    def should_buy(self, ticker: str, market_data: Dict[str, Any]) -> bool:
        """
        매수 신호 여부를 반환한다.

        market_data 필수 키:
          current_price, today_open, prev_high, prev_low, is_market_closing
        """

    @abstractmethod
    def should_sell(self, ticker: str, market_data: Dict[str, Any]) -> bool:
        """매도 신호 여부를 반환한다."""

    @abstractmethod
    def calculate_quantity(
        self, ticker: str, price: float, available_cash: float
    ) -> int:
        """매수 수량을 계산해 반환한다. 잔고 부족 등으로 매수 불가면 0."""
