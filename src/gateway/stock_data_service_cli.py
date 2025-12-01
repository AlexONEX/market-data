#!/usr/bin/env python3
"""
CLI for fetching stock data via FinancialDataService.
Called from TypeScript via child_process.

Usage:
    python stock_data_service_cli.py <ticker> <period> [fmp_api_key]

Output: JSON to stdout
"""
import json
import logging
import sys
from typing import Any

import pandas as pd

from src.services.financial_data_service import FinancialDataService

# Configure logging to stderr only
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger(__name__)


def convert_to_serializable(obj: Any) -> Any:
    """Convert pandas DataFrames and other non-serializable objects to JSON-compatible format."""
    # Handle NaN/None first
    try:
        if pd.isna(obj):
            return None
    except (TypeError, ValueError):
        pass

    if isinstance(obj, pd.DataFrame):
        # Convert DataFrame and recursively handle NaN values
        result = obj.to_dict(orient="split")
        return convert_to_serializable(result)
    elif isinstance(obj, pd.Series):
        return convert_to_serializable(obj.to_dict())
    elif isinstance(obj, dict):
        return {k: convert_to_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [convert_to_serializable(item) for item in obj]
    elif isinstance(obj, float):
        # Check for NaN/Inf
        if pd.isna(obj) or obj != obj:  # NaN check
            return None
        if not pd.isna(obj) and pd.isnull(obj):
            return None
        return obj
    return obj


def main():
    """Main entry point."""
    if len(sys.argv) < 3:
        print(
            json.dumps(
                {
                    "error": "Missing required arguments",
                    "usage": "python stock_data_service_cli.py <ticker> <period> [fmp_api_key]",
                }
            )
        )
        sys.exit(1)

    ticker = sys.argv[1]
    period = sys.argv[2]
    fmp_api_key = sys.argv[3] if len(sys.argv) > 3 else None

    try:
        service = FinancialDataService(fmp_api_key=fmp_api_key)
        data = service.get_company_data(ticker, period)

        # Convert DataFrames to JSON-serializable format
        serializable_data = convert_to_serializable(data)

        # Output JSON to stdout
        print(json.dumps(serializable_data))
        sys.exit(0)

    except Exception as e:
        logger.exception("Error fetching stock data for %s", ticker)
        print(
            json.dumps(
                {
                    "error": str(e),
                    "ticker": ticker,
                    "period": period,
                }
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
