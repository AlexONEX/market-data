export interface HttpClientConfig {
  readonly baseURL?: string;
  readonly timeout?: number;
  readonly retryAttempts?: number;
  readonly retryDelay?: number;
}

export interface HttpResponse<T> {
  readonly status: number;
  readonly data: T;
  readonly headers: Record<string, string>;
}

export interface BondPriceData {
  readonly ticker: string;
  readonly price: number;
  readonly currency: string;
  readonly date: Date;
  readonly source: string;
}

export interface StockOverviewData {
  readonly ticker: string;
  readonly name: string;
  readonly sector?: string;
  readonly marketCap?: number;
  readonly peRatio?: number;
  readonly eps?: number;
  readonly dividendYield?: number;
}

export interface FinancialStatementData {
  readonly [key: string]: string | number | undefined;
}

export interface StockDataFromSource {
  readonly overview: StockOverviewData;
  readonly incomeStatement: readonly FinancialStatementData[];
  readonly balanceSheet: readonly FinancialStatementData[];
  readonly cashFlow: readonly FinancialStatementData[];
  readonly ratios?: readonly FinancialStatementData[];
  readonly statistics?: readonly FinancialStatementData[];
  readonly peers?: readonly string[];
}

export interface FetchBondPricesInput {
  readonly tickers: readonly string[];
}

export interface FetchBondPricesOutput {
  readonly prices: readonly BondPriceData[];
  readonly failedTickers: readonly string[];
}

export interface FetchStockDataInput {
  readonly ticker: string;
  readonly period: "annual" | "quarterly";
}

export interface FetchStockDataOutput {
  readonly data: StockDataFromSource;
  readonly source: string;
  readonly fetchedAt: Date;
}

export interface ApiGateway {
  readonly name: string;
  readonly isHealthy: boolean;
  readonly lastError?: Error;
  readonly lastErrorTime?: Date;
  markHealthy(): void;
  markUnhealthy(error: Error): void;
}
