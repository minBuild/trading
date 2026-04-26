from brokers.kis_api import KISBroker
from core.engine import TradingEngine
from core.portfolio import Portfolio
from strategies.volatility import VolatilityBreakoutStrategy
from utils.logger import get_logger

logger = get_logger(__name__)

# ── 매매 대상 종목 (종목코드) ──────────────────────────────────────────
TICKERS = [
    "005930",   # 삼성전자
    "000660",   # SK하이닉스
    "035720",   # 카카오
]

# ── 전략 파라미터 ─────────────────────────────────────────────────────
K            = 0.5    # 변동성 돌파 계수
RISK_RATIO   = 0.1    # 1회 투자 비율 (가용 현금의 10%)

# ── 엔진 파라미터 ─────────────────────────────────────────────────────
POLL_INTERVAL = 60    # 종목 조회 주기 (초)


def main() -> None:
    logger.info("=" * 60)
    logger.info("변동성 돌파 전략 자동 매매 시작")
    logger.info("=" * 60)

    # ── 의존성 주입(DI) ────────────────────────────────────────────────
    broker    = KISBroker()
    strategy  = VolatilityBreakoutStrategy(k=K, risk_ratio=RISK_RATIO)
    portfolio = Portfolio(initial_cash=0.0)   # 실 잔고는 장 시작 후 동기화

    engine = TradingEngine(
        broker=broker,
        strategy=strategy,
        portfolio=portfolio,
        tickers=TICKERS,
        poll_interval=POLL_INTERVAL,
    )

    engine.run()


if __name__ == "__main__":
    main()
