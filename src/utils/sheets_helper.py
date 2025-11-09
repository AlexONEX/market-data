import logging
from typing import Any

import gspread
import pandas as pd

logger = logging.getLogger(__name__)


class SheetsWriter:
    def __init__(self, credentials_path: str):
        try:
            self.gc = gspread.service_account(filename=credentials_path)
            logger.info("✓ Connected to Google Sheets API")
        except Exception as e:
            logger.error(f"Failed to connect to Google Sheets: {e}")
            self.gc = None

    def get_or_create_spreadsheet(
        self, spreadsheet_name: str, spreadsheet_id: str | None = None
    ) -> Any:
        if not self.gc:
            logger.error("Google Sheets API not initialized")
            return None

        try:
            if spreadsheet_id:
                logger.info(f"Opening existing spreadsheet (ID: {spreadsheet_id})")
                return self.gc.open_by_key(spreadsheet_id)
            else:
                logger.info(f"Creating new spreadsheet: {spreadsheet_name}")
                return self.gc.create(spreadsheet_name)
        except Exception as e:
            logger.error(f"Failed to get/create spreadsheet: {e}")
            return None

    def write_dataframe(
        self,
        spreadsheet: Any,
        sheet_name: str,
        df: pd.DataFrame,
        overwrite: bool = True,
    ) -> bool:
        if not spreadsheet:
            logger.error("No spreadsheet provided")
            return False

        try:
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                if overwrite:
                    worksheet.clear()
                    logger.info(f"Cleared worksheet: {sheet_name}")
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name, rows=len(df) + 100, cols=len(df.columns) + 10
                )
                logger.info(f"Created worksheet: {sheet_name}")

            # Convert DataFrame to list of lists for gspread
            data = [df.columns.tolist()] + df.values.tolist()

            # Write data in batches if large
            if len(data) > 500:
                logger.info(f"Writing {len(data)} rows (may take a moment)...")
                worksheet.batch_clear(["A1:Z10000"])  # Clear large range
                worksheet.append_rows(data, table_range="A1")
            else:
                worksheet.append_rows(data, table_range="A1")

            logger.info(f"✓ Written {len(df)} rows to '{sheet_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to write to worksheet: {e}")
            return False

    def write_sections(
        self,
        spreadsheet: Any,
        sheet_name: str,
        sections: dict[str, pd.DataFrame],
        overwrite: bool = True,
    ) -> bool:
        if not spreadsheet:
            logger.error("No spreadsheet provided")
            return False

        try:
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                if overwrite:
                    worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name, rows=5000, cols=50
                )

            # Build combined data with section headers
            all_data = []
            for section_name, df in sections.items():
                if df is None or df.empty:
                    continue

                # Add section header
                all_data.append([f"=== {section_name.upper()} ==="])
                all_data.append([])

                # Add column headers
                all_data.append(df.columns.tolist())

                # Add data rows
                for _, row in df.iterrows():
                    all_data.append(row.tolist())

                # Add spacing
                all_data.append([])
                all_data.append([])

            if all_data:
                worksheet.batch_clear(["A1:Z10000"])
                worksheet.append_rows(all_data, table_range="A1")
                logger.info(f"✓ Written {len(sections)} sections to '{sheet_name}'")
                return True
            else:
                logger.warning(f"No data to write to '{sheet_name}'")
                return False

        except Exception as e:
            logger.error(f"Failed to write sections: {e}")
            return False

    def write_metadata(
        self,
        spreadsheet: Any,
        sheet_name: str,
        metadata: dict[str, Any],
    ) -> bool:
        if not spreadsheet:
            logger.error("No spreadsheet provided")
            return False

        try:
            # Get or create worksheet
            try:
                worksheet = spreadsheet.worksheet(sheet_name)
                worksheet.clear()
            except gspread.exceptions.WorksheetNotFound:
                worksheet = spreadsheet.add_worksheet(
                    title=sheet_name, rows=200, cols=20
                )

            # Convert metadata to rows
            data = []
            for key, value in metadata.items():
                if isinstance(value, (list, dict)):
                    value = str(value)
                data.append([str(key), str(value)])

            worksheet.append_rows(data, table_range="A1")
            logger.info(f"✓ Written metadata to '{sheet_name}'")
            return True

        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
            return False
