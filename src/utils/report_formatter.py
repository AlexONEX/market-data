import logging
from typing import Any

import pandas as pd

from src.calculators.metric_extractor import MetricExtractor
from src.domain.metric_templates import MetricType  # Import MetricType

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
                {
                    "Error": [f"No {sheet_name.replace('_', ' ')} data available"]
                }  # UP031 - converted f-string
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
            ["Market Cap", self.format_currency(overview.get("marketCap"))],
            ["P/E Ratio", self.format_number(overview.get("peRatio"))],
            ["EPS", self.format_currency(overview.get("eps"))],
            ["Dividend Yield", self.format_percentage(overview.get("dividendYield"))],
            ["Employees", self.format_number(overview.get("fullTimeEmployees"))],
        ]
        return pd.DataFrame(rows, columns=["Metric", "Value"])

    def _format_metric_value(self, value: Any, metric_type: MetricType) -> str:
        """
        Formats a single metric value based on its type.
        This logic is moved from MetricExtractor._format_value.
        """
        if value is None:
            return "N/A"

        if metric_type == MetricType.CURRENCY:
            return self.format_currency(value)
        if metric_type == MetricType.PERCENTAGE:
            return self.format_percentage(value)
        if metric_type == MetricType.NUMBER:
            return self.format_number(value)
        return str(value)

    def generate_metrics_sheet(self) -> pd.DataFrame:
        all_metrics = self.extractor.extract_all_categories()
        rows = []
        for category_name, metrics in all_metrics.items():
            if not metrics:
                continue
            rows.append(
                [f"=== {category_name.upper()} ==="]
            )  # UP031 - converted f-string
            for metric_name, metric_data in metrics.items():
                value = metric_data["value"]
                metric_type = metric_data["type"]
                formatted = self._format_metric_value(
                    value, metric_type
                )  # SLF001 fixed: call ReportFormatter's own method
                rows.append(
                    [metric_name, formatted, metric_type.value]
                )  # .value to get string representation
            rows.append([])
        if rows:
            return pd.DataFrame(rows, columns=["Metric", "Value", "Type"])
        return pd.DataFrame({"Error": ["No metrics extracted"]})

    def generate_all_sheets(self) -> dict[str, pd.DataFrame]:
        """
        Generates all sheets, returning the raw, unfiltered data for the main financial tables.
        """
        return {  # RET504 fixed: removed 'sheets ='
            "Overview": self.generate_overview_sheet(),
            "Metrics": self.generate_metrics_sheet(),
            "Income_Statement": self._get_raw_sheet("income_statement"),
            "Balance_Sheet": self._get_raw_sheet("balance_sheet"),
            "Cash_Flow": self._get_raw_sheet("cash_flow"),
            "Ratios": self._get_raw_sheet("ratios"),
            "Statistics": self._get_raw_sheet("statistics"),
        }

    def format_currency(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"
        try:
            value = float(value)
            return f"${value:,.2f}"  # UP031 - converted f-string
        except (ValueError, TypeError):
            return str(value)

    def format_percentage(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"
        try:
            value = float(value)
            return f"{value:.2%}"  # UP031 - converted f-string
        except (ValueError, TypeError):
            return str(value)

    def format_number(self, value: Any) -> str:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"
        try:
            value = float(value)
            if value == int(value):
                return f"{int(value):,}"  # UP031 - converted f-string
            return f"{value:,.2f}"  # UP031 - converted f-string
        except (ValueError, TypeError):
            return str(value)
