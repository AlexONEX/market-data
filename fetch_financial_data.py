#!/usr/bin/env python3
"""
Fetch financial data from multiple sources and save to local JSON + formatted sheets.
Usage:
    python3 fetch_financial_data.py --ticker VIST --period quarterly
    python3 fetch_financial_data.py --ticker AAPL --period annual --fmp-key YOUR_KEY
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import pandas as pd

from src.services.financial_data_service import FinancialDataService
from src.utils.report_formatter import ReportFormatter

logging.basicConfig(
    level=logging.WARNING,
    format="%(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(
        description="Fetch financial data from multiple sources and save locally"
    )

    parser.add_argument(
        "--ticker",
        required=True,
        help="Stock ticker symbol (e.g., VIST, AAPL)",
    )

    parser.add_argument(
        "--period",
        choices=["annual", "quarterly"],
        default="quarterly",
        help="Report period (default: quarterly)",
    )

    parser.add_argument(
        "--fmp-key",
        default=os.getenv("FMP_API_KEY"),
        help="FMP API key for peer data (env: FMP_API_KEY)",
    )

    parser.add_argument(
        "--output-dir",
        default="./data/financial_reports",
        help="Directory to save JSON output (default: ./data/financial_reports)",
    )

    args = parser.parse_args()

    try:
        print(f"Fetching {args.period} data for {args.ticker.upper()}...")

        # Fetch data from multiple sources
        data_service = FinancialDataService(fmp_api_key=args.fmp_key)
        financial_data = data_service.get_company_data(args.ticker, period=args.period)

        # Prepare data for JSON export
        data_to_save = {
            "ticker": financial_data["ticker"],
            "period": financial_data["period"],
            "sources_used": financial_data.get("sources", {}),
        }

        # Add overview
        if financial_data.get("overview"):
            data_to_save["overview"] = financial_data.get("overview")

        # Add income statement
        income_stmt = financial_data.get("income_statement")
        if isinstance(income_stmt, pd.DataFrame) and not income_stmt.empty:
            data_to_save["income_statement"] = income_stmt.to_dict()

        # Add balance sheet
        balance_sheet = financial_data.get("balance_sheet")
        if isinstance(balance_sheet, pd.DataFrame) and not balance_sheet.empty:
            data_to_save["balance_sheet"] = balance_sheet.to_dict()

        # Add cash flow
        cash_flow = financial_data.get("cash_flow")
        if isinstance(cash_flow, pd.DataFrame) and not cash_flow.empty:
            data_to_save["cash_flow"] = cash_flow.to_dict()

        # Add ratios
        ratios = financial_data.get("ratios")
        if isinstance(ratios, pd.DataFrame) and not ratios.empty:
            data_to_save["ratios"] = ratios.to_dict()

        # Add peers
        peers = financial_data.get("peers")
        if peers:
            data_to_save["peers"] = peers

        # Save to JSON
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        output_file = output_dir / f"{args.ticker.lower()}_{args.period}.json"

        with open(output_file, "w") as f:
            json.dump(data_to_save, f, indent=2, default=str)

        print(f"JSON to {output_file.relative_to(Path.cwd())}")

        # Format data for sheets
        formatter = ReportFormatter(financial_data)
        sheets = formatter.generate_all_sheets()

        # Save formatted sheets as CSV for inspection
        sheets_dir = output_dir / "sheets"
        sheets_dir.mkdir(parents=True, exist_ok=True)

        sheet_count = 0
        for sheet_name, df in sheets.items():
            if df is not None and not df.empty:
                sheet_file = (
                    sheets_dir
                    / f"{args.ticker.lower()}_{sheet_name.lower().replace(' ', '_')}.csv"
                )
                df.to_csv(sheet_file, index=False)
                sheet_count += 1

        print(
            f"Generated {sheet_count} sheets in {sheets_dir.relative_to(Path.cwd())}/"
        )
        print(
            f"\nData sources: {', '.join(s for s in financial_data.get('sources', {}).values() if s)}"
        )

        return 0

    except KeyboardInterrupt:
        print("\n✗ Cancelled")
        return 130

    except Exception as e:
        print(f"✗ Error: {e}")
        logger.debug(e, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
