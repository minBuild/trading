import os
from dotenv import load_dotenv


class Config:
    """싱글톤 설정 객체. 최초 접근 시 .env를 로드한다."""

    _instance: "Config | None" = None

    def __new__(cls) -> "Config":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._load()
        return cls._instance

    def _load(self) -> None:
        load_dotenv()

        self.app_key: str = self._require("APP_KEY")
        self.app_secret: str = self._require("APP_SECRET")
        self.account_no: str = self._require("ACCOUNT_NO")
        self.hts_id: str = os.environ.get("HTS_ID", "")
        self.is_paper: bool = os.environ.get("IS_PAPER_TRADING", "true").lower() == "true"

        parts = self.account_no.split("-")
        self.cano: str = parts[0]                              # 계좌번호 앞 8자리
        self.acnt_prdt_cd: str = parts[1] if len(parts) > 1 else "01"  # 계좌상품코드

    @staticmethod
    def _require(key: str) -> str:
        value = os.environ.get(key)
        if not value:
            raise EnvironmentError(f"필수 환경변수 '{key}'가 설정되지 않았습니다.")
        return value


# 모듈 임포트 시 단일 인스턴스 생성
config = Config()
