import logging
from typing import Any

import pandas as pd
import yfinance as yf

from src.gateway.stockanalysis_connector import StockanalysisConnector

logger = logging.getLogger(__name__)


class FinancialDataService:
    def __init__(self, fmp_api_key: str | None = None):
        self.fmp_api_key = fmp_api_key

    def get_company_data(
        self, ticker: str, period: str = "quarterly"
    ) -> dict[str, Any]:
        result = {
            "ticker": ticker,
            "period": period,
            "sources": {
                "overview": None,
                "income_statement": None,
                "balance_sheet": None,
                "cash_flow": None,
                "ratios": None,
                "peers": None,
            },
        }

        sa_data = self._get_from_stockanalysis(ticker, period)
        yf_data = self._get_from_yfinance(ticker, period)

        result["overview"] = sa_data.get("overview") or yf_data.get("overview")

        sa_income = sa_data.get("income_statement")
        result["income_statement"] = (
            sa_income
            if (sa_income is not None and not sa_income.empty)
            else yf_data.get("income_statement")
        )

        sa_balance = sa_data.get("balance_sheet")
        result["balance_sheet"] = (
            sa_balance
            if (sa_balance is not None and not sa_balance.empty)
            else yf_data.get("balance_sheet")
        )

        sa_cashflow = sa_data.get("cash_flow")
        result["cash_flow"] = (
            sa_cashflow
            if (sa_cashflow is not None and not sa_cashflow.empty)
            else yf_data.get("cash_flow")
        )

        result["ratios"] = sa_data.get("ratios")

        if self.fmp_api_key:
            result["peers"] = self._get_peers_from_fmp(ticker)

        result["sources"]["overview"] = (
            "stockanalysis" if sa_data.get("overview") else "yfinance"
        )
        result["sources"]["income_statement"] = (
            "stockanalysis"
            if sa_data.get("income_statement") is not None
            else "yfinance"
        )
        result["sources"]["balance_sheet"] = (
            "stockanalysis" if sa_data.get("balance_sheet") is not None else "yfinance"
        )
        result["sources"]["cash_flow"] = (
            "stockanalysis" if sa_data.get("cash_flow") is not None else "yfinance"
        )
        ratios_data = sa_data.get("ratios")
        result["sources"]["ratios"] = (
            "stockanalysis"
            if (
                ratios_data is not None
                and isinstance(ratios_data, pd.DataFrame)
                and not ratios_data.empty
            )
            else None
        )

        result["sources"]["peers"] = "fmp" if result.get("peers") else None

        return result

    def _get_from_stockanalysis(self, ticker: str, period: str) -> dict[str, Any]:
        try:
            connector = StockanalysisConnector(ticker)
            data = connector.get_all_data(period=period)
            return data
        except Exception as e:
            logger.debug(f"Failed to fetch from stockanalysis.com: {e}")
            return {}

    def _get_from_yfinance(self, ticker: str, period: str) -> dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            overview = {}
            try:
                if hasattr(stock, "info"):
                    overview = stock.info if isinstance(stock.info, dict) else {}
            except Exception:
                pass

            income_stmt = None
            try:
                if period == "annual" and hasattr(stock, "income_stmt"):
                    income_stmt = stock.income_stmt
                elif period == "quarterly" and hasattr(stock, "quarterly_income_stmt"):
                    income_stmt = stock.quarterly_income_stmt
            except Exception:
                pass

            balance_sheet = None
            try:
                if period == "annual" and hasattr(stock, "balance_sheet"):
                    balance_sheet = stock.balance_sheet
                elif period == "quarterly" and hasattr(
                    stock, "quarterly_balance_sheet"
                ):
                    balance_sheet = stock.quarterly_balance_sheet
            except Exception:
                pass

            cash_flow = None
            try:
                if period == "annual" and hasattr(stock, "cashflow"):
                    cash_flow = stock.cashflow
                elif period == "quarterly" and hasattr(stock, "quarterly_cashflow"):
                    cash_flow = stock.quarterly_cashflow
            except Exception:
                pass

            data = {
                "overview": overview,
                "income_statement": income_stmt,
                "balance_sheet": balance_sheet,
                "cash_flow": cash_flow,
                "ratios": None,
            }

            return data

        except Exception as e:
            logger.debug(f"Failed to fetch from yfinance: {e}")
            return {}

    def _get_peers_from_fmp(self, ticker: str) -> list[str] | None:
        if not self.fmp_api_key:
            return None

        try:
            import requests

            url = "https://financialmodelingprep.com/api/v4/stock_peers"
            params = {"symbol": ticker, "apikey": self.fmp_api_key}

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            peers_data = response.json()
            if isinstance(peers_data, dict) and "peersList" in peers_data:
                return peers_data["peersList"]

            return None

        except Exception as e:
            logger.debug(f"Failed to fetch peers from FMP: {e}")
            return None
