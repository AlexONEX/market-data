import { DataFetchError, DataSource } from "../domain";
import { ApiGateway } from "./types";

export interface GoogleSheetsConfig {
  readonly credentialsPath: string;
  readonly spreadsheetId?: string;
}

export interface SheetData {
  readonly title: string;
  readonly headers: readonly string[];
  readonly rows: readonly (readonly unknown[])[];
}

export interface WriteSheetInput {
  readonly sheetId: string;
  readonly sheetTitle: string;
  readonly data: SheetData;
  readonly clearFirst?: boolean;
}

export class GoogleSheetsClient implements ApiGateway {
  readonly name = "google-sheets";
  private readonly config: GoogleSheetsConfig;
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;

  constructor(config: GoogleSheetsConfig) {
    this.config = config;
  }

  get isHealthy(): boolean {
    return this.isHealthyFlag;
  }

  get lastError(): Error | undefined {
    return this.lastErrorValue;
  }

  get lastErrorTime(): Date | undefined {
    return this.lastErrorTimeValue;
  }

  markHealthy(): void {
    this.isHealthyFlag = true;
    this.lastErrorValue = undefined;
    this.lastErrorTimeValue = undefined;
  }

  markUnhealthy(error: Error): void {
    this.isHealthyFlag = false;
    this.lastErrorValue = error;
    this.lastErrorTimeValue = new Date();
  }

  async writeSheet(input: WriteSheetInput): Promise<void> {
    try {
      if (!this.config.spreadsheetId) {
        throw new Error("Spreadsheet ID not configured");
      }

      // TODO: Implement actual Google Sheets API integration
      // This is a placeholder for the API call
      this.validateSheetData(input.data);
      this.markHealthy();
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      throw new DataFetchError(
        DataSource.StockAnalysis,
        `Failed to write to Google Sheets: ${err.message}`,
        {
          sheetId: input.sheetId,
          sheetTitle: input.sheetTitle,
        },
      );
    }
  }

  async appendRows(sheetId: string, rows: readonly (readonly unknown[])[]): Promise<void> {
    try {
      if (!this.config.spreadsheetId) {
        throw new Error("Spreadsheet ID not configured");
      }

      if (!Array.isArray(rows) || rows.length === 0) {
        throw new Error("Rows must be a non-empty array");
      }

      // TODO: Implement actual Google Sheets API integration
      this.markHealthy();
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      throw new DataFetchError(
        DataSource.StockAnalysis,
        `Failed to append rows to Google Sheets: ${err.message}`,
        { sheetId },
      );
    }
  }

  private validateSheetData(data: SheetData): void {
    if (!data.title || data.title.trim().length === 0) {
      throw new Error("Sheet title cannot be empty");
    }

    if (!Array.isArray(data.headers) || data.headers.length === 0) {
      throw new Error("Headers must be a non-empty array");
    }

    if (!Array.isArray(data.rows)) {
      throw new Error("Rows must be an array");
    }

    for (const row of data.rows) {
      if (!Array.isArray(row)) {
        throw new Error("Each row must be an array");
      }

      if (row.length !== data.headers.length) {
        throw new Error(
          `Row length (${row.length}) does not match headers length (${data.headers.length})`,
        );
      }
    }
  }
}
