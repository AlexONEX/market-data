"""
Formats extracted metrics into sheets-ready format.
Generates organized sheets with proper structure and styling information.
"""

import logging
from typing import Any

import pandas as pd

from src.calculators.metric_extractor import MetricExtractor

logger = logging.getLogger(__name__)


class ReportFormatter:
    """Formats financial data into structured reports for Google Sheets."""

    def __init__(self, financial_data: dict[str, Any]):
        """Initialize the formatter.

        Args:
            financial_data: Dictionary with financial data from multi-source fetcher
        """
        self.financial_data = financial_data
        self.ticker = financial_data.get("ticker", "")
        self.period = financial_data.get("period", "quarterly")
        self.sector = financial_data.get("overview", {}).get("sector", "")

        self.extractor = MetricExtractor(financial_data)

    def generate_overview_sheet(self) -> pd.DataFrame:
        """Generate Overview sheet with company info and key metrics.

        Returns:
            DataFrame with overview information
        """
        overview = self.financial_data.get("overview", {})

        rows = [
            ["Company Information"],
            ["Field", "Value"],
            ["Ticker", self.ticker],
            ["Name", overview.get("name", "N/A")],
            ["Sector", overview.get("sector", "N/A")],
            ["Industry", overview.get("industry", "N/A")],
            ["Employees", f"{overview.get('fullTimeEmployees', 'N/A'):,}"],
            ["Website", overview.get("website", "N/A")],
            [],
            ["Key Metrics"],
            ["Field", "Value"],
            ["Market Cap", self._format_currency(overview.get("marketCap"))],
            ["Price", f"${overview.get('currentPrice', 'N/A')}"],
            ["P/E Ratio", self._format_number(overview.get("trailingPE"))],
            ["52W High", f"${overview.get('fiftyTwoWeekHigh', 'N/A')}"],
            ["52W Low", f"${overview.get('fiftyTwoWeekLow', 'N/A')}"],
            ["Dividend Yield", self._format_percentage(overview.get("dividendYield"))],
        ]

        return pd.DataFrame(rows)

    def generate_income_statement_sheet(self) -> pd.DataFrame:
        """Generate Income Statement sheet with key profitability metrics.

        Returns:
            DataFrame with income statement data
        """
        income_stmt = self.financial_data.get("income_statement")

        if income_stmt is None or income_stmt.empty:
            return pd.DataFrame({"Error": ["No income statement data available"]})

        # Select key metrics
        key_metrics = [
            "Total Revenue",
            "Cost Of Revenue",
            "Gross Profit",
            "Operating Income",
            "EBITDA",
            "Net Income",
        ]

        filtered_data = income_stmt.loc[
            income_stmt.index.isin(key_metrics), :
        ].copy()

        # Format the data
        for col in filtered_data.columns:
            filtered_data[col] = filtered_data[col].apply(self._format_currency)

        return filtered_data.reset_index().rename(columns={"index": "Metric"})

    def generate_balance_sheet_sheet(self) -> pd.DataFrame:
        """Generate Balance Sheet sheet with key financial position metrics.

        Returns:
            DataFrame with balance sheet data
        """
        balance_sheet = self.financial_data.get("balance_sheet")

        if balance_sheet is None or balance_sheet.empty:
            return pd.DataFrame({"Error": ["No balance sheet data available"]})

        # Select key metrics
        key_metrics = [
            "Total Assets",
            "Current Assets",
            "Total Liabilities",
            "Current Liabilities",
            "Total Equity",
            "Stockholders Equity",
        ]

        filtered_data = balance_sheet.loc[
            balance_sheet.index.isin(key_metrics), :
        ].copy()

        # Format the data
        for col in filtered_data.columns:
            filtered_data[col] = filtered_data[col].apply(self._format_currency)

        return filtered_data.reset_index().rename(columns={"index": "Metric"})

    def generate_cash_flow_sheet(self) -> pd.DataFrame:
        """Generate Cash Flow sheet with cash flow metrics.

        Returns:
            DataFrame with cash flow data
        """
        cash_flow = self.financial_data.get("cash_flow")

        if cash_flow is None or cash_flow.empty:
            return pd.DataFrame({"Error": ["No cash flow data available"]})

        # Select key metrics
        key_metrics = [
            "Operating Cash Flow",
            "Investing Cash Flow",
            "Financing Cash Flow",
            "Free Cash Flow",
        ]

        filtered_data = cash_flow.loc[
            cash_flow.index.isin(key_metrics), :
        ].copy()

        # Format the data
        for col in filtered_data.columns:
            filtered_data[col] = filtered_data[col].apply(self._format_currency)

        return filtered_data.reset_index().rename(columns={"index": "Metric"})

    def generate_metrics_sheet(self) -> pd.DataFrame:
        """Generate Metrics sheet using template-based extraction.

        Returns:
            DataFrame with key metrics organized by template
        """
        all_metrics = self.extractor.extract_all_categories()

        rows = []
        for category_name, metrics in all_metrics.items():
            if not metrics:
                continue

            # Add category header
            rows.append([f"=== {category_name.upper()} ==="])

            # Add metrics
            for metric_name, metric_data in metrics.items():
                value = metric_data["value"]
                metric_type = metric_data["type"]
                formatted = self.extractor.format_value(value, metric_type)

                rows.append([metric_name, formatted, metric_type])

            rows.append([])  # Spacing

        if rows:
            return pd.DataFrame(rows, columns=["Metric", "Value", "Type"])
        else:
            return pd.DataFrame({"Error": ["No metrics extracted"]})

    def generate_all_sheets(self) -> dict[str, pd.DataFrame]:
        """Generate all sheets at once.

        Returns:
            Dictionary of {sheet_name: DataFrame}
        """
        sheets = {
            "Overview": self.generate_overview_sheet(),
            "Income Statement": self.generate_income_statement_sheet(),
            "Balance Sheet": self.generate_balance_sheet_sheet(),
            "Cash Flow": self.generate_cash_flow_sheet(),
            "Metrics": self.generate_metrics_sheet(),
        }

        return sheets

    # ========================================================================
    # FORMATTING HELPERS
    # ========================================================================

    def _format_currency(self, value: Any) -> str:
        """Format value as currency.

        Args:
            value: Value to format

        Returns:
            Formatted currency string
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"

        try:
            value = float(value)
            if value >= 1_000_000_000:
                return f"${value / 1_000_000_000:.2f}B"
            elif value >= 1_000_000:
                return f"${value / 1_000_000:.2f}M"
            elif value >= 1_000:
                return f"${value / 1_000:.2f}K"
            else:
                return f"${value:.2f}"
        except (ValueError, TypeError):
            return str(value)

    def _format_percentage(self, value: Any) -> str:
        """Format value as percentage.

        Args:
            value: Value to format (0-1 or 0-100 scale)

        Returns:
            Formatted percentage string
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"

        try:
            value = float(value)
            if abs(value) <= 1:
                return f"{value * 100:.2f}%"
            else:
                return f"{value:.2f}%"
        except (ValueError, TypeError):
            return str(value)

    def _format_number(self, value: Any) -> str:
        """Format value as regular number.

        Args:
            value: Value to format

        Returns:
            Formatted number string
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"

        try:
            value = float(value)
            if value == int(value):
                return f"{int(value):,}"
            else:
                return f"{value:.2f}"
        except (ValueError, TypeError):
            return str(value)
