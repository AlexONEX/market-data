export interface TimeSeries {
  readonly date: Date;
  readonly value: number;
}

export interface Cashflow {
  readonly paymentDate: Date;
  readonly totalPayment: number;
  readonly amortization: number;
  readonly interest: number;
}

export interface Bond {
  readonly ticker: string;
  readonly type: BondType;
  readonly price: number;
  readonly currency: Currency;
  readonly maturityDate: Date;
  readonly cashflows: readonly Cashflow[];
}

export interface TIRResult {
  readonly ticker: string;
  readonly tir: number; // decimal: 0.117 = 11.7%
  readonly tem?: number; // tasa efectiva mensual (LECAP/BONCAP)
  readonly price: number;
  readonly maturityDate: Date;
}

export interface StockFinancials {
  readonly ticker: string;
  readonly period: "annual" | "quarterly";
  readonly overview: StockOverview;
  readonly incomeStatement: Record<string, number | string>;
  readonly balanceSheet: Record<string, number | string>;
  readonly cashFlow: Record<string, number | string>;
  readonly ratios: Record<string, number | string>;
  readonly statistics: Record<string, number | string>;
  readonly peers?: readonly string[];
}

export interface StockOverview {
  readonly name: string;
  readonly sector?: string;
  readonly marketCap?: number;
  readonly peRatio?: number;
  readonly eps?: number;
  readonly dividendYield?: number;
}

export enum BondType {
  HardDollarGlobal = "hard_dollar",
  ArgentineLaw = "argentine_law",
  LECAPFixed = "lecap_fixed",
  BONCAPlFixed = "boncap_fixed",
}

export enum Currency {
  ARS = "ARS",
  USD = "USD",
  EUR = "EUR",
}

export enum DataSource {
  StockAnalysis = "stockanalysis",
  YFinance = "yfinance",
  FMP = "fmp",
  BCRA = "bcra",
  Data912 = "data912",
}

export abstract class DomainError extends Error {
  constructor(
    message: string,
    readonly context?: Record<string, unknown>,
  ) {
    super(message);
    this.name = this.constructor.name;
    Object.setPrototypeOf(this, DomainError.prototype);
  }
}

export class TIRCalculationError extends DomainError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(`TIR Calculation Error: ${message}`, context);
    Object.setPrototypeOf(this, TIRCalculationError.prototype);
  }
}

export class DataFetchError extends DomainError {
  constructor(
    readonly source: DataSource,
    message: string,
    context?: Record<string, unknown>,
  ) {
    super(`Data Fetch Error (${source}): ${message}`, context);
    Object.setPrototypeOf(this, DataFetchError.prototype);
  }
}

export class ValidationError extends DomainError {
  constructor(message: string, context?: Record<string, unknown>) {
    super(`Validation Error: ${message}`, context);
    Object.setPrototypeOf(this, ValidationError.prototype);
  }
}

export interface AppConfig {
  readonly nodeEnv: "development" | "production" | "test";
  readonly logLevel: "debug" | "info" | "warn" | "error";
  readonly dataDir: string;
  readonly cacheDir: string;
  readonly apiKeys: {
    readonly fmp?: string;
    readonly googleSheets?: string;
  };
}

export type Result<T, E = DomainError> =
  | { readonly ok: true; readonly value: T }
  | { readonly ok: false; readonly error: E };

export const createOkResult = <T>(value: T): Result<T> => ({
  ok: true,
  value,
});

export const createErrorResult = <E extends DomainError>(error: E): Result<never, E> => ({
  ok: false,
  error,
});

export const unwrapResult = <T>(result: Result<T>): T => {
  if (result.ok) {
    return result.value;
  }
  throw result.error;
};
