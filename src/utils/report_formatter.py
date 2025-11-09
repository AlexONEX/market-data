import logging
from typing import Any

import pandas as pd

from src.calculators.metric_extractor import MetricExtractor

logger = logging.getLogger(__name__)


class ReportFormatter:
    def __init__(self, financial_data: dict[str, Any]):
        self.financial_data = financial_data
        self.extractor = MetricExtractor(financial_data)

    def _get_raw_sheet(self, sheet_name: str) -> pd.DataFrame:
        """
        Gets the raw DataFrame for a given sheet name, resets the index,
        and renames the index column to 'Metric'.
        """
        df = self.financial_data.get(sheet_name)

        if df is None or not isinstance(df, pd.DataFrame) or df.empty:
            return pd.DataFrame(
                {"Error": [f"No {sheet_name.replace('_', ' ')} data available"]}
            )

        # The first column is the index, so we reset it to make it a regular column
        return df.reset_index().rename(columns={"index": "Metric"})

    def generate_overview_sheet(self) -> pd.DataFrame:
        overview = self.financial_data.get("overview", {})
        rows = [
            ["Field", "Value"],
            ["Ticker", overview.get("ticker", "N/A")],
            ["Name", overview.get("name", "N/A")],
            ["Sector", overview.get("sector", "N/A")],
            ["Industry", overview.get("industry", "N/A")],
            ["Market Cap", self._format_currency(overview.get("marketCap"))],
            ["P/E Ratio", self._format_number(overview.get("peRatio"))],
            ["EPS", self._format_currency(overview.get("eps"))],
            ["Dividend Yield", self._format_percentage(overview.get("dividendYield"))],
            ["Employees", self._format_number(overview.get("fullTimeEmployees"))],
        ]
        return pd.DataFrame(rows, columns=["Metric", "Value"])

    def generate_metrics_sheet(self) -> pd.DataFrame:
        all_metrics = self.extractor.extract_all_categories()
        rows = []
        for category_name, metrics in all_metrics.items():
            if not metrics:
                continue
            rows.append([f"=== {category_name.upper()} ==="])
            for metric_name, metric_data in metrics.items():
                value = metric_data["value"]
                metric_type = metric_data["type"]
                formatted = self.extractor._format_value(value, metric_type)
                rows.append([metric_name, formatted, metric_type])
            rows.append([])
        if rows:
            return pd.DataFrame(rows, columns=["Metric", "Value", "Type"])
        return pd.DataFrame({"Error": ["No metrics extracted"]})

    def generate_all_sheets(self) -> dict[str, pd.DataFrame]:
        """
        Generates all sheets, returning the raw, unfiltered data for the main financial tables.
        """
        sheets = {
            "Overview": self.generate_overview_sheet(),
            "Metrics": self.generate_metrics_sheet(),
            "Income_Statement": self._get_raw_sheet("income_statement"),
            "Balance_Sheet": self._get_raw_sheet("balance_sheet"),
            "Cash_Flow": self._get_raw_sheet("cash_flow"),
            "Ratios": self._get_raw_sheet("ratios"),
            "Statistics": self._get_raw_sheet("statistics"),
        }
        return sheets

    # Formatting helpers (can be removed if raw numbers are preferred)
    def _format_currency(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"
        try:
            value = float(value)
            return f"${value:,.2f}"
        except (ValueError, TypeError):
            return str(value)

    def _format_percentage(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"
        try:
            value = float(value)
            return f"{value:.2%}"
        except (ValueError, TypeError):
            return str(value)

    def _format_number(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"
        try:
            value = float(value)
            if value == int(value):
                return f"{int(value):,}"
            return f"{value:,.2f}"
        except (ValueError, TypeError):
            return str(value)
