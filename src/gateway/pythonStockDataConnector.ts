import { execFile as execFileCallback } from "child_process";
import { promisify } from "util";
import { resolve } from "path";
import { getLogger } from "../utils/logger";
import {
  ApiGateway,
  FetchStockDataInput,
  FetchStockDataOutput,
  StockDataFromSource,
  FinancialStatementData,
} from "./types";
import { DataFetchError, DataSource } from "../domain";

const execFile = promisify(execFileCallback);

const logger = getLogger();

interface PythonStockDataResult {
  ticker: string;
  period: string;
  overview?: Record<string, unknown>;
  income_statement?: unknown;
  balance_sheet?: unknown;
  cash_flow?: unknown;
  ratios?: unknown;
  sources?: Record<string, string | null>;
  error?: string;
}

export class PythonStockDataConnector implements ApiGateway {
  readonly name = "python-stock-data";
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;

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

  async fetchStockData(input: FetchStockDataInput): Promise<FetchStockDataOutput> {
    const { ticker, period } = input;

    try {
      const result = await this.executePythonService(ticker, period);

      if (result.error) {
        throw new Error(result.error);
      }

      const stockData = this.convertPythonResponse(result);
      this.markHealthy();

      return {
        data: stockData,
        source: DataSource.YFinance, // Can be stockanalysis or yfinance depending on fallback
        fetchedAt: new Date(),
      };
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      throw new DataFetchError(DataSource.YFinance, `Failed to fetch stock data for ${ticker}`, {
        ticker,
        period: input.period,
        originalError: err.message,
      });
    }
  }

  private async executePythonService(
    ticker: string,
    period: string,
  ): Promise<PythonStockDataResult> {
    // Path to Python script in src directory (not dist)
    const scriptPath = resolve(
      __dirname,
      "..",
      "..",
      "src",
      "gateway",
      "stock_data_service_cli.py",
    );

    try {
      const { stdout } = await (
        execFile as (
          file: string,
          args: string[],
          options: {
            timeout: number;
            maxBuffer: number;
            env: NodeJS.ProcessEnv;
            cwd: string;
          },
        ) => Promise<{ stdout: string; stderr: string }>
      )("uv", ["run", "python", scriptPath, ticker, period], {
        timeout: 180000, // 3 minutes for stockanalysis scraping
        maxBuffer: 10 * 1024 * 1024,
        cwd: resolve(__dirname, "..", ".."),
        env: {
          ...process.env,
          PYTHONPATH: resolve(__dirname, "..", ".."),
        },
      });

      const result = JSON.parse(stdout) as PythonStockDataResult;
      return result;
    } catch (error) {
      logger.error(
        { ticker, error: error instanceof Error ? error.message : String(error) },
        "Python service execution failed",
      );
      throw error;
    }
  }

  private convertPythonResponse(pythonData: PythonStockDataResult): StockDataFromSource {
    const overview = pythonData.overview || {};

    // Convert income_statement from various formats
    const incomeStatement = this.convertFinancialData(
      pythonData.income_statement,
    ) as FinancialStatementData[];
    const balanceSheet = this.convertFinancialData(
      pythonData.balance_sheet,
    ) as FinancialStatementData[];
    const cashFlow = this.convertFinancialData(pythonData.cash_flow) as FinancialStatementData[];
    const ratios = this.convertFinancialData(pythonData.ratios) as FinancialStatementData[];

    return {
      overview: {
        ticker: pythonData.ticker,
        name: String(overview["name"] || ""),
        sector: overview["sector"] ? String(overview["sector"]) : undefined,
        marketCap: overview["marketCap"] ? Number(overview["marketCap"]) : undefined,
        peRatio: overview["peRatio"] ? Number(overview["peRatio"]) : undefined,
        eps: overview["eps"] ? Number(overview["eps"]) : undefined,
        dividendYield: overview["dividendYield"] ? Number(overview["dividendYield"]) : undefined,
      },
      incomeStatement,
      balanceSheet,
      cashFlow,
      ratios,
    };
  }

  private convertFinancialData(data: unknown): readonly Record<string, unknown>[] {
    if (!data) return [];

    // If it's already an array, return as is
    if (Array.isArray(data)) {
      return data as readonly Record<string, unknown>[];
    }

    // If pandas DataFrame converted to dict with 'split' orient
    if (
      typeof data === "object" &&
      data !== null &&
      "index" in data &&
      "columns" in data &&
      "data" in data
    ) {
      const dfData = data as {
        index: unknown[];
        columns: string[];
        data: unknown[][];
      };
      return dfData.data.map((row, idx) => {
        const record: Record<string, unknown> = { _index: dfData.index[idx] };
        dfData.columns.forEach((col, colIdx) => {
          record[col] = row[colIdx];
        });
        return record;
      });
    }

    // If it's a dict/object, convert to array with keys
    if (typeof data === "object" && !Array.isArray(data)) {
      return [data as Record<string, unknown>];
    }

    return [];
  }
}
