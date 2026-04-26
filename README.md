# 🚀 Trading (Automated Trading System)

한국투자증권(KIS) REST API를 활용하여 시장 데이터를 분석하고, 설정된 알고리즘에 따라 자동으로 주식을 매매하는 확장 가능한 파이썬 기반 자동 매매 시스템
초기 버전은 래리 윌리엄스의 '변동성 돌파 전략(Volatility Breakout)'을 기반으로 동작

## ✨ Key Features

### 🧩 Interface-Driven Architecture & DI

- 새로운 매매 전략이나 타 증권사 API를 손쉽게 추가할 수 있도록 BaseStrategy, BaseBroker 추상 클래스(ABC)를 정의
- main.py에서 각 구현체를 생성하고 TradingEngine에 주입(DI)하는 결합도 낮은 구조

### 📈 Volatility Breakout Strategy

- 전일 고가와 저가의 변동폭을 계산하여, 당일 시가 대비 일정 비율(k=0.5) 이상 상승하며 강한 추세를 형성할 때 돌파 매수를 진행하는 알고리즘

### 🔐 Secure & Automated Token Management

- 증권사 API 호출에 필요한 OAuth Access Token의 유효기간(24시간)을 관리하며, 만료 시 자동으로 토큰을 재발급하여 중단 없는 24시간 백그라운드 실행

### 🛡️ Paper Trading & Safe Execution

- .env의 IS_PAPER_TRADING 플래그 하나로 실전 투자와 모의 투자 환경(URL 및 TR_ID)을 즉시 스위칭
- 장 종료 시간(15:15) 도달 시 당일 매수한 모든 종목을 일괄 청산하여 오버나잇 리스크를 방지

### 💼 In-Memory Portfolio Management
- API 호출 과부하를 막기 위해 Portfolio 객체에서 현재 보유 종목과 가용 현금 상태를 인메모리로 관리하며, 주문 전 잔고 검증을 수행

### 🏗 Architecture Overview

```
Client (Terminal / Background Process)
  ↓
┌─ main.py (Dependency Injection) ──────────────────────────┐
│ 1. Initialize KISBroker, VolatilityBreakoutStrategy       │
│ 2. Inject into TradingEngine & Run                        │
└───────────────────────────────────────────────────────────┘
  ↓
┌─ Trading Engine (60s Polling Loop) ───────────────────────┐
│ 3. Fetch current market data (via Broker)                 │
│ 4. Evaluate signals (via Strategy)                        │
│ 5. Calculate target buy quantity (via Portfolio)          │
└───────────────────────────────────────────────────────────┘
  ↓ (BUY / SELL Signal)
┌─ Broker Integration (KIS REST API) ───────────────────────┐
│ 6. Verify Access Token (Auto-refresh if expired)          │
│ 7. Execute Market Order (BUY/SELL)                        │
└───────────────────────────────────────────────────────────┘
  ↓
한국투자증권 (Real / Paper Trading Server)
```

## 🛠 Tech Stack

| Category         | Stack                                             |
|------------------|---------------------------------------------------|
| Language         | Python 3.10+                                      |
| Architecture     | Strategy Pattern, OOP                             |
| API Integration  | HTTP REST Client)                                 |
| Configuration    | python-dotenv (Environment variables management)  |
| Task Scheduling  | schedule                                          |
| Brokerage        | 한국투자증권 Developers REST API                     |

## 🚀 Getting Started

#### 1. 가상환경 세팅 및 패키지 설치
```
Bash

# 가상환경 생성 및 활성화 (Mac/Linux 기준)
python3 -m venv .venv
source .venv/bin/activate

# 의존성 패키지 설치
pip install -r requirements.txt
```

#### 2. 환경변수(.env) 설정

```
Code Snippet

# 한국투자증권 API Keys
APP_KEY=your_app_key_here
APP_SECRET=your_app_secret_here

# 계좌번호 (앞 8자리-뒤 2자리)
ACCOUNT_NO=12345678-01
HTS_ID=your_hts_id_here

# 모의투자 여부 (true: 모의투자, false: 실전투자)
IS_PAPER_TRADING=true
```

#### 3. 애플리케이션 실행

```
Bash

python main.py
```

## ⚠️ 주의사항 (Disclaimer)
- 반드시 IS_PAPER_TRADING=true 상태에서 모의투자 계좌로 충분한 기간 동안 로직을 검증하시기 바랍니다.
- 본 프로그램의 사용으로 인해 발생하는 모든 금전적 손실에 대한 책임은 사용자 본인에게 있습니다.
