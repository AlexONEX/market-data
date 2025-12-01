export interface Cashflow {
  readonly paymentDate: Date;
  readonly totalPayment: number;
  readonly amortization: number;
  readonly interest: number;
}

export interface Bond {
  readonly ticker: string;
  readonly type: "hard_dollar" | "lecap_boncap";
  readonly price: number;
  readonly maturityDate: Date;
  readonly cashflows: readonly Cashflow[];
}

export interface TIRResult {
  readonly ticker: string;
  readonly tir: number;
  readonly price: number;
  readonly maturityDate: Date;
  readonly duration?: number;
}

export interface FinancialData {
  readonly ticker: string;
  readonly period: "annual" | "quarterly";
  readonly overview?: Record<string, unknown>;
  readonly incomeStatement?: Record<string, unknown>[];
  readonly balanceSheet?: Record<string, unknown>[];
  readonly cashFlow?: Record<string, unknown>[];
  readonly ratios?: Record<string, unknown>[];
  readonly peers?: string[];
}
