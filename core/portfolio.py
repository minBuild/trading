from typing import Any, Dict, Optional

from utils.logger import get_logger

logger = get_logger(__name__)


class Portfolio:
    """보유 종목 및 현금 상태를 인메모리로 관리한다."""

    def __init__(self, initial_cash: float = 0.0) -> None:
        self.cash: float = initial_cash
        # ticker -> {"quantity": int, "avg_price": float}
        self._holdings: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------ #
    #  현금                                                                #
    # ------------------------------------------------------------------ #

    def update_cash(self, amount: float) -> None:
        self.cash = amount
        logger.info(f"현금 잔고 갱신: {self.cash:,.0f}원")

    # ------------------------------------------------------------------ #
    #  매매 기록                                                           #
    # ------------------------------------------------------------------ #

    def record_buy(self, ticker: str, quantity: int, price: float) -> None:
        cost = quantity * price
        if ticker in self._holdings:
            prev_qty   = self._holdings[ticker]["quantity"]
            prev_avg   = self._holdings[ticker]["avg_price"]
            total_qty  = prev_qty + quantity
            new_avg    = (prev_qty * prev_avg + cost) / total_qty
            self._holdings[ticker] = {"quantity": total_qty, "avg_price": new_avg}
        else:
            self._holdings[ticker] = {"quantity": quantity, "avg_price": price}

        self.cash -= cost
        logger.info(
            f"[매수 기록] {ticker} {quantity}주 @ {price:,.0f}원  "
            f"(잔여현금 {self.cash:,.0f}원)"
        )

    def record_sell(self, ticker: str, quantity: int, price: float) -> None:
        if not self.is_holding(ticker):
            logger.warning(f"[매도 기록 오류] {ticker}는 보유 중이 아닙니다.")
            return

        self._holdings[ticker]["quantity"] -= quantity
        if self._holdings[ticker]["quantity"] <= 0:
            del self._holdings[ticker]

        self.cash += quantity * price
        logger.info(
            f"[매도 기록] {ticker} {quantity}주 @ {price:,.0f}원  "
            f"(잔여현금 {self.cash:,.0f}원)"
        )

    # ------------------------------------------------------------------ #
    #  조회                                                                #
    # ------------------------------------------------------------------ #

    def is_holding(self, ticker: str) -> bool:
        holding = self._holdings.get(ticker)
        return holding is not None and holding.get("quantity", 0) > 0

    def get_holding(self, ticker: str) -> Optional[Dict[str, Any]]:
        return self._holdings.get(ticker)

    def summary(self) -> Dict[str, Any]:
        return {"cash": self.cash, "holdings": dict(self._holdings)}
