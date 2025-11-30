import { BondType, Cashflow, Currency } from "./types";

export interface BondMetadata {
  readonly ticker: string;
  readonly type: BondType;
  readonly currency: Currency;
  readonly maturityDate: Date;
  readonly isin?: string;
  readonly issuer?: string;
}

export interface BondPricing {
  readonly price: number;
  readonly priceDate: Date;
  readonly source: string;
}

export interface Bond {
  readonly metadata: BondMetadata;
  readonly pricing: BondPricing;
  readonly cashflows: readonly Cashflow[];
}

export interface StockMetadata {
  readonly ticker: string;
  readonly name: string;
  readonly sector?: string;
  readonly industry?: string;
  readonly country?: string;
}

export interface FinancialStatement {
  readonly fiscalYear: string;
  readonly [key: string]: string | number;
}

export interface StockFinancialData {
  readonly ticker: string;
  readonly period: "annual" | "quarterly";
  readonly metadata: StockMetadata;
  readonly incomeStatement: readonly FinancialStatement[];
  readonly balanceSheet: readonly FinancialStatement[];
  readonly cashFlow: readonly FinancialStatement[];
}

export interface StockKeyMetrics {
  readonly marketCap?: number;
  readonly peRatio?: number;
  readonly psRatio?: number;
  readonly pbRatio?: number;
  readonly eps?: number;
  readonly roe?: number;
  readonly roa?: number;
  readonly dividendYield?: number;
  readonly debtToEquity?: number;
  readonly currentRatio?: number;
  readonly quickRatio?: number;
}

export interface StockData {
  readonly ticker: string;
  readonly metadata: StockMetadata;
  readonly keyMetrics: StockKeyMetrics;
  readonly financialData: StockFinancialData;
  readonly peers?: readonly string[];
}

export interface TimePeriod {
  readonly start: Date;
  readonly end: Date;
}

export interface DataFetchRequest {
  readonly ticker: string;
  readonly period?: "annual" | "quarterly";
  readonly includeHistorical?: boolean;
}

export interface DataFetchResult<T> {
  readonly data: T;
  readonly fetchedAt: Date;
  readonly source: string;
}
