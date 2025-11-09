import logging
import re
from typing import Any, ClassVar  # Added ClassVar for RUF012

import pandas as pd
import requests  # Moved to top as per PLC0415
from bs4 import BeautifulSoup
from requests.exceptions import RequestException

from src.utils.helpers import clean_column_name

logger = logging.getLogger(__name__)


class StockanalysisConnector:
    BASE_URL: ClassVar[str] = "https://stockanalysis.com/stocks"
    HEADERS: ClassVar[dict[str, str]] = {"User-Agent": "Mozilla/5.0"}

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.base_url = f"{self.BASE_URL}/{self.ticker.lower()}"

    def _parse_number(self, text: str) -> float | str:
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

    def _get_cleaned_financial_table(self, url: str) -> pd.DataFrame | None:
        """
        Fetches a financial table from a URL, cleans its index, and returns the DataFrame.
        """
        try:
            tables = pd.read_html(url, storage_options=self.HEADERS)
            if not tables:
                return None

            df = tables[0].copy()

            # Flatten MultiIndex columns if they exist by taking the first level
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # Set the first column as the index
            df = df.set_index(df.columns[0])

            # Clean the index names (which are the metric names)
            df.index = [clean_column_name(name) for name in df.index]

            return df
        except RequestException as e: # BLE001
            logger.debug("Failed to get or clean table from %s: %s", url, e) # G004
            return None
        except Exception as e: # Catch any other unexpected exceptions
            logger.debug("An unexpected error occurred while getting/cleaning table from %s: %s", url, e)
            return None

    def get_overview(self) -> dict[str, Any]:
        url = f"{self.base_url}/"
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, "html.parser")
        except RequestException as e:
            logger.debug("Failed to fetch overview page %s: %s", url, e)
            return {"ticker": self.ticker}

        overview_data = {"ticker": self.ticker, "url": url}
        try:
            script_tag = soup.find("script", string=re.compile(r"__sveltekit_"))
            if not script_tag or not script_tag.string:
                logger.debug("Could not find SvelteKit data script tag.")
                return overview_data
            script_content = script_tag.string
            patterns = {
                "marketCap": r'marketCap:"(.*?)"',
                "peRatio": r'peRatio:"(.*?)"',
                "eps": r'eps:"(.*?)"',
                "dividendYield": r'dividend:"(.*?)"',
                "priceToBook": r'pbRatio:"(.*?)"',
                "sector": r'\{t:"Sector",v:"(.*?)"\}',
                "industry": r'\{t:"Industry",v:"(.*?)"\}',
                "fullTimeEmployees": r'\{t:"Employees",v:"(.*?)"\}',
                "name": r'name:"(.*?)"',
            }
            for key, pattern in patterns.items():
                match = re.search(pattern, script_content)
                if match:
                    value = match.group(1)
                    overview_data[key] = self._parse_number(value)
        except Exception as e: # BLE001
            logger.debug("Error extracting overview data with regex: %s", e) # G004
        return overview_data

    def get_income_statement(self, period: str = "quarterly") -> pd.DataFrame | None:
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/?p={period_param}"
        return self._get_cleaned_financial_table(url)

    def get_balance_sheet(self, period: str = "quarterly") -> pd.DataFrame | None:
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/balance-sheet/?p={period_param}"
        return self._get_cleaned_financial_table(url)

    def get_cash_flow_statement(self, period: str = "quarterly") -> pd.DataFrame | None:
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/cash-flow-statement/?p={period_param}"
        return self._get_cleaned_financial_table(url)

    def get_ratios(self, period: str = "quarterly") -> pd.DataFrame | None:
        period_param = "yearly" if period == "annual" else "quarterly"
        url = f"{self.base_url}/financials/ratios/?p={period_param}"
        return self._get_cleaned_financial_table(url)

    def get_statistics(self) -> pd.DataFrame | None:
        url = f"{self.base_url}/statistics/"
        return self._get_cleaned_financial_table(url)

    def get_dividends(self) -> pd.DataFrame | None:
        url = f"{self.base_url}/dividends/"
        try:
            tables = pd.read_html(url, storage_options=self.HEADERS)
            return tables[0] if tables else None
        except RequestException as e: # BLE001
            logger.debug("Failed to get dividends from %s: %s", url, e) # G004
            return None
        except Exception as e: # Catch any other unexpected exceptions
            logger.debug("An unexpected error occurred while getting dividends from %s: %s", url, e)
            return None

    def get_all_data(self, period: str = "quarterly") -> dict[str, Any]:
        return {
            "overview": self.get_overview(),
            "income_statement": self.get_income_statement(period),
            "balance_sheet": self.get_balance_sheet(period),
            "cash_flow": self.get_cash_flow_statement(period),
            "ratios": self.get_ratios(period),
            "statistics": self.get_statistics(),
            "dividends": self.get_dividends(),
        }
