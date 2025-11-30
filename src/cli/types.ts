export type CliMode = "bond-yields" | "stock-data" | "combined" | "exit";

export interface BondYieldsInput {
  readonly tickers: readonly string[];
  readonly outputFormat: "csv" | "json";
  readonly outputPath?: string;
}

export interface StockDataInput {
  readonly ticker: string;
  readonly period: "annual" | "quarterly";
  readonly outputFormat: "csv" | "json";
  readonly outputPath?: string;
}

export interface CombinedInput {
  readonly bondTickers: readonly string[];
  readonly stockTicker: string;
  readonly stockPeriod: "annual" | "quarterly";
  readonly outputFormat: "csv" | "json";
  readonly outputPath?: string;
}

export interface CliConfig {
  readonly dataDir: string;
  readonly cacheDir: string;
}
