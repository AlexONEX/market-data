import YahooFinanceType from "yahoo-finance2";

export interface YFinanceQuote {
  currency?: string;
  marketCap?: number;
  trailingPE?: number;
  trailingEps?: number;
  dividendYield?: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
  [key: string]: unknown;
}

export interface FinancialStatement {
  [date: string]: Record<string, number | string>;
}

export class YahooFinanceConnector {
  private yahooFinance: InstanceType<typeof YahooFinanceType>;

  constructor() {
    this.yahooFinance = new YahooFinanceType();
  }

  async getQuote(ticker: string): Promise<YFinanceQuote | null> {
    try {
      const quote = (await this.yahooFinance.quote(ticker)) as Record<
        string,
        unknown
      > | null;
      if (!quote) {
        return null;
      }

      return {
        currency: quote["currency"] as string | undefined,
        marketCap: quote["marketCap"] as number | undefined,
        trailingPE: quote["trailingPE"] as number | undefined,
        trailingEps: quote["trailingEps"] as number | undefined,
        dividendYield: quote["dividendYield"] as number | undefined,
        fiftyTwoWeekHigh: quote["fiftyTwoWeekHigh"] as number | undefined,
        fiftyTwoWeekLow: quote["fiftyTwoWeekLow"] as number | undefined,
      };
    } catch {
      return null;
    }
  }

  async getIncomeStatement(
    ticker: string,
    period: "annual" | "quarterly" = "annual"
  ): Promise<FinancialStatement | null> {
    try {
      const module =
        period === "annual" ? "incomeStatementHistory" : "incomeStatementHistoryQuarterly";

      const quoteSummary = (await this.yahooFinance.quoteSummary(ticker, {
        modules: [module as never],
      })) as Record<string, unknown> | null;

      if (!quoteSummary) {
        return null;
      }

      const historyData = quoteSummary[module] as Record<string, unknown> | undefined;
      const statements = historyData?.["incomeStatementHistory"] as
        | Array<Record<string, unknown>>
        | undefined;

      if (!statements || !Array.isArray(statements)) {
        return null;
      }

      const result: FinancialStatement = {};
      for (const stmt of statements) {
        const endDate = stmt["endDate"] as string | undefined;
        if (endDate) {
          result[endDate] = this.flattenStatement(stmt);
        }
      }

      return Object.keys(result).length > 0 ? result : null;
    } catch {
      return null;
    }
  }

  async getBalanceSheet(
    ticker: string,
    period: "annual" | "quarterly" = "annual"
  ): Promise<FinancialStatement | null> {
    try {
      const module =
        period === "annual" ? "balanceSheetHistory" : "balanceSheetHistoryQuarterly";

      const quoteSummary = (await this.yahooFinance.quoteSummary(ticker, {
        modules: [module as never],
      })) as Record<string, unknown> | null;

      if (!quoteSummary) {
        return null;
      }

      const historyData = quoteSummary[module] as Record<string, unknown> | undefined;
      const statements = historyData?.["balanceSheetStatements"] as
        | Array<Record<string, unknown>>
        | undefined;

      if (!statements || !Array.isArray(statements)) {
        return null;
      }

      const result: FinancialStatement = {};
      for (const stmt of statements) {
        const endDate = stmt["endDate"] as string | undefined;
        if (endDate) {
          result[endDate] = this.flattenStatement(stmt);
        }
      }

      return Object.keys(result).length > 0 ? result : null;
    } catch {
      return null;
    }
  }

  async getCashFlow(
    ticker: string,
    period: "annual" | "quarterly" = "annual"
  ): Promise<FinancialStatement | null> {
    try {
      const module =
        period === "annual" ? "cashflowStatementHistory" : "cashflowStatementHistoryQuarterly";

      const quoteSummary = (await this.yahooFinance.quoteSummary(ticker, {
        modules: [module as never],
      })) as Record<string, unknown> | null;

      if (!quoteSummary) {
        return null;
      }

      const historyData = quoteSummary[module] as Record<string, unknown> | undefined;
      const statements = historyData?.["cashflowStatements"] as
        | Array<Record<string, unknown>>
        | undefined;

      if (!statements || !Array.isArray(statements)) {
        return null;
      }

      const result: FinancialStatement = {};
      for (const stmt of statements) {
        const endDate = stmt["endDate"] as string | undefined;
        if (endDate) {
          result[endDate] = this.flattenStatement(stmt);
        }
      }

      return Object.keys(result).length > 0 ? result : null;
    } catch {
      return null;
    }
  }

  private flattenStatement(stmt: Record<string, unknown>): Record<string, number | string> {
    const result: Record<string, number | string> = {};

    for (const [key, value] of Object.entries(stmt)) {
      if (value === null || value === undefined) {
        continue;
      }

      if (typeof value === "object") {
        const obj = value as Record<string, unknown>;
        if ("raw" in obj && typeof obj["raw"] === "number") {
          result[key] = obj["raw"] as number;
        } else if ("longFmt" in obj) {
          result[key] = obj["longFmt"] as string;
        } else {
          result[key] = String(value);
        }
      } else if (typeof value === "number" || typeof value === "string") {
        result[key] = value;
      }
    }

    return result;
  }
}
