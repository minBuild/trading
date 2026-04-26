from typing import Any, Dict, Optional

from strategies.base import BaseStrategy
from utils.logger import get_logger

logger = get_logger(__name__)


class VolatilityBreakoutStrategy(BaseStrategy):
    """
    래리 윌리엄스 변동성 돌파 전략.

    매수 조건: 당일 현재가 >= 당일 시가 + (전일 고가 - 전일 저가) × k
    매도 조건: 장 마감 임박 시점(is_market_closing=True)에 보유 포지션 청산
    """

    def __init__(self, k: float = 0.5, risk_ratio: float = 0.1) -> None:
        """
        k          : 변동성 돌파 계수 (0 < k < 1, 기본 0.5)
        risk_ratio : 가용 현금 중 1회 투자 비율 (기본 10%)
        """
        self.k = k
        self.risk_ratio = risk_ratio

    # ------------------------------------------------------------------ #
    #  시그널                                                              #
    # ------------------------------------------------------------------ #

    def should_buy(self, ticker: str, market_data: Dict[str, Any]) -> bool:
        target = self._target_price(market_data)
        if target is None:
            return False

        current = float(market_data.get("current_price", 0))
        signal = current >= target
        logger.debug(
            f"[{ticker}] 매수 검토 | 현재가={current:,.0f}  목표가={target:,.0f}  신호={'▲BUY' if signal else '대기'}"
        )
        return signal

    def should_sell(self, ticker: str, market_data: Dict[str, Any]) -> bool:
        # 장 마감 전 일괄 청산 (엔진이 is_market_closing 플래그를 주입)
        return bool(market_data.get("is_market_closing", False))

    # ------------------------------------------------------------------ #
    #  포지션 크기                                                         #
    # ------------------------------------------------------------------ #

    def calculate_quantity(
        self, ticker: str, price: float, available_cash: float
    ) -> int:
        if price <= 0:
            return 0
        invest = available_cash * self.risk_ratio
        qty = int(invest // price)
        logger.debug(
            f"[{ticker}] 수량 계산 | 가용현금={available_cash:,.0f}  "
            f"투자비율={self.risk_ratio:.0%}  단가={price:,.0f}  수량={qty}"
        )
        return qty

    # ------------------------------------------------------------------ #
    #  내부 헬퍼                                                           #
    # ------------------------------------------------------------------ #

    def _target_price(self, market_data: Dict[str, Any]) -> Optional[float]:
        """변동성 돌파 목표가 = 당일 시가 + (전일 고가 - 전일 저가) × k"""
        try:
            today_open = float(market_data["today_open"])
            prev_high  = float(market_data["prev_high"])
            prev_low   = float(market_data["prev_low"])
        except (KeyError, ValueError, TypeError) as exc:
            logger.warning(f"목표가 계산 불가 (데이터 부족): {exc}")
            return None

        return today_open + (prev_high - prev_low) * self.k
