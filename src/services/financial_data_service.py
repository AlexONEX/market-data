import logging
from typing import Any

import pandas as pd
import requests  # Moved to top as per PLC0415
import yfinance as yf
from requests.exceptions import HTTPError, RequestException

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
            return connector.get_all_data(period=period)
        except (ValueError, TypeError, AttributeError, KeyError) as e:
            logger.debug("Failed to fetch from stockanalysis.com: %s", e)
            return {}

    def _get_yfinance_overview(self, stock) -> dict:
        """Get overview data from yfinance."""
        try:
            if hasattr(stock, "info"):
                return stock.info if isinstance(stock.info, dict) else {}
        except (AttributeError, TypeError, KeyError) as e:
            logger.debug("Failed to get overview from yfinance: %s", e)
        return {}

    def _get_yfinance_statement(self, stock, period: str, stmt_type: str):
        """Get financial statement from yfinance based on period and type."""
        try:
            attr_map = {
                ("annual", "income"): "income_stmt",
                ("quarterly", "income"): "quarterly_income_stmt",
                ("annual", "balance"): "balance_sheet",
                ("quarterly", "balance"): "quarterly_balance_sheet",
                ("annual", "cashflow"): "cashflow",
                ("quarterly", "cashflow"): "quarterly_cashflow",
            }
            attr_name = attr_map.get((period, stmt_type))
            if attr_name and hasattr(stock, attr_name):
                return getattr(stock, attr_name)
        except (AttributeError, TypeError, KeyError) as e:
            logger.debug("Failed to get %s statement from yfinance: %s", stmt_type, e)
        return None

    def _get_from_yfinance(self, ticker: str, period: str) -> dict[str, Any]:
        try:
            stock = yf.Ticker(ticker)
            overview = self._get_yfinance_overview(stock)
            income_stmt = self._get_yfinance_statement(stock, period, "income")
            balance_sheet = self._get_yfinance_statement(stock, period, "balance")
            cash_flow = self._get_yfinance_statement(stock, period, "cashflow")

        except (ValueError, TypeError, AttributeError, KeyError) as e:
            logger.debug("Failed to fetch from yfinance: %s", e)
            return {}
        else:
            return {
                "overview": overview,
                "income_statement": income_stmt,
                "balance_sheet": balance_sheet,
                "cash_flow": cash_flow,
                "ratios": None,
            }

    def _get_peers_from_fmp(self, ticker: str) -> list[str] | None:
        if not self.fmp_api_key:
            return None

        try:
            url = "https://financialmodelingprep.com/stable/stock-peers"
            params = {"symbol": ticker, "apikey": self.fmp_api_key}

            response = requests.get(url, params=params, timeout=5)
            response.raise_for_status()

            peers_data = response.json()
            if isinstance(peers_data, dict) and "peersList" in peers_data:
                return peers_data["peersList"]

        except (RequestException, HTTPError) as e:
            logger.debug("Failed to fetch peers from FMP: %s", e)
            return None
        except ValueError as e:  # For JSON decoding errors
            logger.debug("Failed to decode FMP peers JSON: %s", e)
            return None
        except (TypeError, KeyError, AttributeError) as e:
            logger.debug("An unexpected error occurred while fetching FMP peers: %s", e)
            return None
        else:
            # TRY300
            return None
