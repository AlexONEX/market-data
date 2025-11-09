"""
Connector for fetching financial data from stockanalysis.com.
Scrapes income statement, balance sheet, cash flow, ratios, and overview data.
"""

import logging
import re
from typing import Any

import pandas as pd
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class StockanalysisConnector:
    """Connector for extracting financial data from stockanalysis.com."""

    BASE_URL = "https://stockanalysis.com/stocks"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }

    def __init__(self, ticker: str):
        """Initialize connector with a stock ticker.

        Args:
            ticker: Stock ticker symbol (e.g., 'VIST', 'AAPL')
        """
        self.ticker = ticker.upper()
        self.base_url = f"{self.BASE_URL}/{self.ticker.lower()}"

    def _fetch_page(self, url: str) -> BeautifulSoup | None:
        """Fetch and parse a page from stockanalysis.com.

        Args:
            url: Full URL to fetch

        Returns:
            BeautifulSoup object or None if fetch fails
        """
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, "html.parser")
        except requests.RequestException as e:
            logger.debug(f"Failed to fetch {url}: {e}")
            return None

    def _parse_number(self, text: str) -> float | str:
        """Parse text to number, handling various formats (1,234.56M, 52.72%, etc)."""
        if not isinstance(text, str):
            return text

        try:
            is_percentage = "%" in text
            text = text.replace("%", "").strip()

            multiplier = 1
            if text.endswith("M"):
                multiplier = 1_000_000
                text = text[:-1]
            elif text.endswith("B"):
                multiplier = 1_000_000_000
                text = text[:-1]
            elif text.endswith("K"):
                multiplier = 1_000
                text = text[:-1]

            text = text.replace(",", "")
            value = float(text) * multiplier

            if is_percentage:
                return value / 100 if value > 1 else value

            return value
        except (ValueError, AttributeError):
            return text

    def _extract_table_data(self, soup: BeautifulSoup) -> pd.DataFrame | None:
        """Extract financial table from HTML."""
        try:
            table = soup.find("table")
            if not table:
                return None

            headers = []
            header_row = table.find("tr")
            if header_row:
                for th in header_row.find_all(["th", "td"]):
                    headers.append(th.get_text(strip=True))

            if not headers:
                return None

            rows = []
            for tr in table.find_all("tr")[1:]:
                row_data = []
                for td in tr.find_all("td"):
                    text = td.get_text(strip=True)
                    text = self._parse_number(text)
                    row_data.append(text)
                if row_data and len(row_data) == len(headers):
                    rows.append(row_data)

            if not rows:
                return None

            return pd.DataFrame(rows, columns=headers)

        except Exception as e:
            logger.debug(f"Failed to extract table data: {e}")
            return None

    def get_overview(self) -> dict[str, Any]:
        """Get company overview and key metrics."""
        url = f"{self.base_url}/"
        soup = self._fetch_page(url)

        if not soup:
            return {"ticker": self.ticker}

        overview_data = {"ticker": self.ticker, "url": url}

        try:
            company_name = soup.find("h1")
            if company_name:
                overview_data["name"] = company_name.get_text(strip=True)

            page_text = soup.get_text()

            patterns = {
                "price": r"Price[:\s]+\$?([\d,]+\.?\d*)",
                "market_cap": r"Market Cap[:\s]+\$?([\d,]+[MBK]?)",
                "pe_ratio": r"P\/E Ratio[:\s]+([\d,]+\.?\d*)",
            }

            for key, pattern in patterns.items():
                match = re.search(pattern, page_text, re.IGNORECASE)
                if match:
                    overview_data[key] = self._parse_number(match.group(1))

        except Exception as e:
            logger.debug(f"Error extracting overview data: {e}")

        return overview_data

    def get_income_statement(self, period: str = "quarterly") -> pd.DataFrame | None:
        """Get income statement data."""
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/?p={period_param}"

        soup = self._fetch_page(url)
        if not soup:
            return None

        df = self._extract_table_data(soup)
        return df.set_index(df.columns[0]) if (df is not None and len(df) > 0) else None

    def get_balance_sheet(self, period: str = "quarterly") -> pd.DataFrame | None:
        """Get balance sheet data."""
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/balance-sheet/?p={period_param}"

        soup = self._fetch_page(url)
        if not soup:
            return None

        df = self._extract_table_data(soup)
        return df.set_index(df.columns[0]) if (df is not None and len(df) > 0) else None

    def get_cash_flow_statement(self, period: str = "quarterly") -> pd.DataFrame | None:
        """Get cash flow statement data."""
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/cash-flow-statement/?p={period_param}"

        soup = self._fetch_page(url)
        if not soup:
            return None

        df = self._extract_table_data(soup)
        return df.set_index(df.columns[0]) if (df is not None and len(df) > 0) else None

    def get_ratios(self, period: str = "quarterly") -> pd.DataFrame | None:
        """Get financial ratios data."""
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/ratios/?p={period_param}"

        soup = self._fetch_page(url)
        if not soup:
            return None

        df = self._extract_table_data(soup)
        return df.set_index(df.columns[0]) if (df is not None and len(df) > 0) else None

    def get_all_data(self, period: str = "quarterly") -> dict[str, Any]:
        """Get all financial data in one call."""
        return {
            "overview": self.get_overview(),
            "income_statement": self.get_income_statement(period),
            "balance_sheet": self.get_balance_sheet(period),
            "cash_flow": self.get_cash_flow_statement(period),
            "ratios": self.get_ratios(period),
        }
