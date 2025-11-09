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
    def __init__(self, data: dict[str, Any], sector: str | None = None):
        self.data = data
        self.sector = sector or data.get("overview", {}).get("sector", "")
        self.template = get_template_for_sector(self.sector)
        logger.info("Using template: %s", self.template.name)

    def extract_category(self, category_name: str) -> dict[str, Any]:
        if category_name not in self.template.categories:
            logger.warning("Category '%s' not found in template", category_name)
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

        for category_name in self.template.categories:
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
            "Metric '%s' not found with keys: %s, %s",
            metric_def.name,
            metric_def.data_key,
            metric_def.alt_keys,
        )
        return None

    def _get_nested_value(self, key_path: str) -> Any:
        """
        Get value from data structure.
        - For "overview.marketCap", gets data['overview']['marketCap']
        - For "income_statement.revenue", finds the 'revenue' row and gets the first value.
        """
        parts = key_path.split(".")
        if len(parts) != NESTED_KEY_PARTS:
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

    def get_metric_table(self, category_name: str) -> pd.DataFrame:
        metrics = self.extract_category(category_name)

        if not metrics:
            return pd.DataFrame()

        rows = []
        for metric_name, metric_data in metrics.items():
            value = metric_data["value"]
            metric_type = metric_data["type"]

            rows.append(
                {
                    "Metric": metric_name,
                    "Value": value,  # Pass raw value
                    "Type": metric_type,
                }
            )

        return pd.DataFrame(rows)
