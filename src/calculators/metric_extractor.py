import logging
from typing import Any

import pandas as pd

from src.domain.metric_templates import (
    MetricDefinition,
    get_template_for_sector,
)

logger = logging.getLogger(__name__)

# Constants for magic values
BILLION = 1_000_000_000
MILLION = 1_000_000
NESTED_KEY_PARTS = 2


class MetricExtractor:
    def __init__(self, data: dict[str, Any], sector: str = None):
        self.data = data
        self.sector = sector or data.get("overview", {}).get("sector", "")
        self.template = get_template_for_sector(self.sector)
        logger.info("Using template: %s", self.template.name) # G004

    def extract_category(self, category_name: str) -> dict[str, Any]:
        if category_name not in self.template.categories: # SIM118
            logger.warning("Category '%s' not found in template", category_name) # G004
            return {}

        category = self.template.categories[category_name]
        results = {}

        for metric_def in category.metrics:
            value = self._extract_metric(metric_def)
            if value is not None:
                results[metric_def.name] = {
                    "value": value,
                    "type": metric_def.metric_type,
                    "description": metric_def.description,
                }

        return results

    def extract_all_categories(self) -> dict[str, dict[str, Any]]:
        results = {}

        for category_name in self.template.categories: # SIM118
            results[category_name] = self.extract_category(category_name)

        return results

    def _extract_metric(self, metric_def: MetricDefinition) -> Any:
        value = self._get_nested_value(metric_def.data_key)
        if value is not None:
            return value

        for alt_key in metric_def.alt_keys:
            value = self._get_nested_value(alt_key)
            if value is not None:
                return value

        logger.debug(
            "Metric '%s' not found with keys: %s, %s", metric_def.name, metric_def.data_key, metric_def.alt_keys # G004
        )
        return None

    def _get_nested_value(self, key_path: str) -> Any:
        """
        Get value from data structure.
        - For "overview.marketCap", gets data['overview']['marketCap']
        - For "income_statement.revenue", finds the 'revenue' row and gets the first value.
        """
        parts = key_path.split(".")
        if len(parts) != NESTED_KEY_PARTS: # PLR2004
            return None

        section_name, metric_key = parts
        section_data = self.data.get(section_name)

        if section_data is None:
            return None

        # Handle the overview dictionary
        if isinstance(section_data, dict):
            return section_data.get(metric_key)

        # Handle the financial DataFrames (metrics are in the index)
        if isinstance(section_data, pd.DataFrame):
            if metric_key in section_data.index:
                series = section_data.loc[metric_key]
                if not series.empty:
                    # Return the first value (most recent period)
                    return series.iloc[0]
            return None

        return None

    # Removed _format_value as it's now handled by ReportFormatter
    # def _format_value(self, value: Any, metric_type: str) -> str:
    #     if value is None or (isinstance(value, float) and pd.isna(value)):
    #         return "N/A"

    #     try:
    #         if metric_type == "currency":
    #             if isinstance(value, (int, float)):
    #                 if abs(value) >= BILLION: # PLR2004
    #                     return f"${value / BILLION:.2f}B"
    #                 if abs(value) >= MILLION: # PLR2004
    #                     return f"${value / MILLION:.2f}M"
    #                 return f"${value:,.0f}"

    #         elif metric_type == "percentage":
    #             if isinstance(value, (int, float)):
    #                 if abs(value) <= 1:
    #                     return f"{value * 100:.2f}%"
    #                 return f"{value:.2f}%"

    #         elif metric_type == "ratio":
    #             if isinstance(value, (int, float)):
    #                 return f"{value:.4f}"

    #         elif metric_type == "count":
    #             if isinstance(value, (int, float)):
    #                 return f"{int(value):,}"

    #         elif metric_type == "shares":
    #             if isinstance(value, (int, float)): # SIM102
    #                 return f"{int(value):,} shares"

    #         return str(value)

    #     except Exception as e: # BLE001
    #         logger.warning("Failed to format value %s as %s: %s", value, metric_type, e) # G004
    #         return str(value)

    def get_metric_table(self, category_name: str) -> pd.DataFrame:
        metrics = self.extract_category(category_name)

        if not metrics:
            return pd.DataFrame()

        rows = []
        for metric_name, metric_data in metrics.items():
            value = metric_data["value"]
            metric_type = metric_data["type"]
            # The formatting is now handled by ReportFormatter, so we just pass the raw value
            # formatted = self._format_value(value, metric_type)

            rows.append(
                {
                    "Metric": metric_name,
                    "Value": value, # Pass raw value
                    "Type": metric_type,
                }
            )

        return pd.DataFrame(rows)
