"""
Generic metric extractor that extracts data based on templates.
Handles nested data structures and provides fallbacks.
"""

import logging
from typing import Any

import pandas as pd

from src.domain.metric_templates import (
    MetricDefinition,
    SectorTemplate,
    get_template_for_sector,
)

logger = logging.getLogger(__name__)


class MetricExtractor:
    """Extracts metrics from financial data using templates."""

    def __init__(self, data: dict[str, Any], sector: str = None):
        """Initialize the extractor.

        Args:
            data: Dictionary with financial data (overview, income_statement, etc)
            sector: Company sector for template selection
        """
        self.data = data
        self.sector = sector or data.get("overview", {}).get("sector", "")
        self.template = get_template_for_sector(self.sector)
        logger.info(f"Using template: {self.template.name}")

    def extract_category(self, category_name: str) -> dict[str, Any]:
        """Extract all metrics from a category.

        Args:
            category_name: Name of the category to extract

        Returns:
            Dictionary with {metric_name: (value, metric_type)}
        """
        if category_name not in self.template.categories:
            logger.warning(f"Category '{category_name}' not found in template")
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
        """Extract all metrics from all categories.

        Returns:
            Dictionary with {category_name: {metric_name: (value, type)}}
        """
        results = {}

        for category_name in self.template.categories.keys():
            results[category_name] = self.extract_category(category_name)

        return results

    def _extract_metric(self, metric_def: MetricDefinition) -> Any:
        """Extract a single metric value using fallback keys.

        Args:
            metric_def: MetricDefinition to extract

        Returns:
            Extracted value or None if not found
        """
        # Try primary key
        value = self._get_nested_value(metric_def.data_key)
        if value is not None:
            return value

        # Try alternative keys
        for alt_key in metric_def.alt_keys:
            value = self._get_nested_value(alt_key)
            if value is not None:
                return value

        # Not found
        logger.debug(f"Metric '{metric_def.name}' not found with keys: {metric_def.data_key}, {metric_def.alt_keys}")
        return None

    def _get_nested_value(self, key_path: str) -> Any:
        """Get value from nested dictionary using dot notation.

        Examples:
            "overview.name" → data["overview"]["name"]
            "income_statement.Total Revenue" → data["income_statement"]["Total Revenue"]

        Args:
            key_path: Dot-separated path to the value

        Returns:
            Value or None if not found
        """
        parts = key_path.split(".")
        current = self.data

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, pd.DataFrame):
                # For DataFrames, the part is the row name
                try:
                    current = current.loc[part]
                except KeyError:
                    return None
            else:
                return None

            if current is None:
                return None

        return current

    def format_value(self, value: Any, metric_type: str) -> str:
        """Format a value for display based on metric type.

        Args:
            value: Value to format
            metric_type: Type of metric (currency, percentage, ratio, etc)

        Returns:
            Formatted string
        """
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return "N/A"

        try:
            if metric_type == "currency":
                # Convert millions to billions if needed
                if isinstance(value, (int, float)):
                    if abs(value) >= 1_000_000_000:
                        return f"${value / 1_000_000_000:.2f}B"
                    elif abs(value) >= 1_000_000:
                        return f"${value / 1_000_000:.2f}M"
                    else:
                        return f"${value:,.0f}"

            elif metric_type == "percentage":
                if isinstance(value, (int, float)):
                    # If value is 0-1 scale, multiply by 100
                    if abs(value) <= 1:
                        return f"{value * 100:.2f}%"
                    else:
                        return f"{value:.2f}%"

            elif metric_type == "ratio":
                if isinstance(value, (int, float)):
                    return f"{value:.4f}"

            elif metric_type == "count":
                if isinstance(value, (int, float)):
                    return f"{int(value):,}"

            elif metric_type == "shares":
                if isinstance(value, (int, float)):
                    return f"{int(value):,} shares"

            return str(value)

        except Exception as e:
            logger.warning(f"Failed to format value {value} as {metric_type}: {e}")
            return str(value)

    def get_metric_table(self, category_name: str) -> pd.DataFrame:
        """Get a metric category as a formatted DataFrame.

        Args:
            category_name: Name of the category

        Returns:
            DataFrame with columns: [Metric, Value, Type]
        """
        metrics = self.extract_category(category_name)

        if not metrics:
            return pd.DataFrame()

        rows = []
        for metric_name, metric_data in metrics.items():
            value = metric_data["value"]
            metric_type = metric_data["type"]
            formatted = self.format_value(value, metric_type)

            rows.append(
                {
                    "Metric": metric_name,
                    "Value": formatted,
                    "Type": metric_type,
                }
            )

        return pd.DataFrame(rows)
