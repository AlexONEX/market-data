import logging
from typing import Any

import gspread
import pandas as pd

logger = logging.getLogger(__name__)

# Constant for batch writing threshold
BATCH_WRITE_THRESHOLD = 500


class SheetsWriter:
    def __init__(self, credentials_path: str):
        try:
            self.gc = gspread.service_account(filename=credentials_path)
            logger.info("Connected to Google Sheets API")
        except gspread.exceptions.ServiceAccountError as e:
            logger.exception("Failed to connect to Google Sheets: %s", e)
            self.gc = None
        except Exception as e:
            logger.exception("An unexpected error occurred during Google Sheets connection: %s", e)
            self.gc = None

    def get_or_create_spreadsheet(
        self, spreadsheet_name: str, spreadsheet_id: str | None = None
    ) -> Any:
        if not self.gc:
            logger.error("Google Sheets API not initialized")
            return None

        try:
            if spreadsheet_id:
                logger.info("Opening existing spreadsheet (ID: %s)", spreadsheet_id)
                return self.gc.open_by_key(spreadsheet_id)
            logger.info("Creating new spreadsheet: %s", spreadsheet_name)
            return self.gc.create(spreadsheet_name)
        except gspread.exceptions.SpreadsheetNotFound as e:
            logger.exception("Spreadsheet not found: %s", e)
            return None
        except Exception as e:
            logger.exception("Failed to get/create spreadsheet: %s", e)
            return None

    def _get_or_create_worksheet(
        self,
        spreadsheet: Any,
        sheet_name: str,
        overwrite: bool = False,
        default_rows: int = 1000,
        default_cols: int = 26,
    ) -> Any:
        try:
            worksheet = spreadsheet.worksheet(sheet_name)
            if overwrite:
                worksheet.clear()
                logger.info("Cleared worksheet: %s", sheet_name)
            return worksheet
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(
                title=sheet_name, rows=default_rows, cols=default_cols
            )
            logger.info("Created worksheet: %s", sheet_name)
            return worksheet

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
            worksheet = self._get_or_create_worksheet(
                spreadsheet,
                sheet_name,
                overwrite=overwrite,
                default_rows=len(df) + 100,
                default_cols=len(df.columns) + 10,
            )

            # Convert DataFrame to list of lists for gspread
            data = [df.columns.tolist()] + df.to_numpy().tolist()

            # Write data in batches if large
            if len(data) > BATCH_WRITE_THRESHOLD:
                logger.info("Writing %d rows (may take a moment)...", len(data))
                worksheet.batch_clear(["A1:Z10000"])  # Clear large range
                worksheet.append_rows(data, table_range="A1")
            else:
                worksheet.append_rows(data, table_range="A1")

            logger.info("Written %d rows to '%s'", len(df), sheet_name)
            return True

        except Exception as e:
            logger.exception("Failed to write to worksheet: %s", e)
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
            worksheet = self._get_or_create_worksheet(
                spreadsheet, sheet_name, overwrite=overwrite, default_rows=5000, default_cols=50
            )

            # Build combined data with section headers
            all_data = []
            for section_name, df in sections.items():
                if df is None or df.empty:
                    continue

                # Add section header
                all_data.append([f"=== {section_name.upper()} ==="]) # UP031
                all_data.append([])

                # Add column headers
                all_data.append(df.columns.tolist())

                # Add data rows
                for _, row_data in df.iterrows():
                    all_data.append(row_data.tolist())

                # Add spacing
                all_data.append([])
                all_data.append([])

            if all_data:
                worksheet.batch_clear(["A1:Z10000"])
                worksheet.append_rows(all_data, table_range="A1")
                logger.info("Written %d sections to '%s'", len(sections), sheet_name)
                return True
            logger.warning("No data to write to '%s'", sheet_name)
            return False

        except Exception as e:
            logger.exception("Failed to write sections: %s", e)
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
            worksheet = self._get_or_create_worksheet(
                spreadsheet, sheet_name, overwrite=True, default_rows=200, default_cols=20
            )

            # Convert metadata to rows
            data = []
            for key, value_item in metadata.items():
                if isinstance(value_item, (list, dict)):
                    value_item = str(value_item)
                data.append([str(key), str(value_item)])

            worksheet.append_rows(data, table_range="A1")
            logger.info("Written metadata to '%s'", sheet_name)
            return True

        except Exception as e:
            logger.exception("Failed to write metadata: %s", e)
            return False
