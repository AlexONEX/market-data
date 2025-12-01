import yahooFinance from "yahoo-finance2";

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
  async getQuote(ticker: string): Promise<YFinanceQuote | null> {
    try {
      const quote = await yahooFinance.quote(ticker);
      if (!quote) {
        return null;
      }

      return {
        currency: quote.currency as string | undefined,
        marketCap: quote.marketCap as number | undefined,
        trailingPE: quote.trailingPE as number | undefined,
        trailingEps: quote.trailingEps as number | undefined,
        dividendYield: quote.dividendYield as number | undefined,
        fiftyTwoWeekHigh: quote.fiftyTwoWeekHigh as number | undefined,
        fiftyTwoWeekLow: quote.fiftyTwoWeekLow as number | undefined,
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
      const quoteSummary = await yahooFinance.quoteSummary(ticker, {
        modules: [
          period === "annual"
            ? "incomeStatementHistory"
            : "incomeStatementHistoryQuarterly",
        ],
      });

      if (!quoteSummary) {
        return null;
      }

      const statements =
        period === "annual"
          ? quoteSummary.incomeStatementHistory?.incomeStatementHistory
          : quoteSummary.incomeStatementHistoryQuarterly
              ?.incomeStatementHistory;

      if (!statements || !Array.isArray(statements)) {
        return null;
      }

      const result: FinancialStatement = {};
      for (const stmt of statements) {
        const endDate = stmt.endDate as string | undefined;
        if (endDate) {
          result[endDate] = this.flattenStatement(stmt);
        }
      }

      return result;
    } catch {
      return null;
    }
  }

  async getBalanceSheet(
    ticker: string,
    period: "annual" | "quarterly" = "annual"
  ): Promise<FinancialStatement | null> {
    try {
      const quoteSummary = await yahooFinance.quoteSummary(ticker, {
        modules: [
          period === "annual" ? "balanceSheetHistory" : "balanceSheetHistoryQuarterly",
        ],
      });

      if (!quoteSummary) {
        return null;
      }

      const statements =
        period === "annual"
          ? quoteSummary.balanceSheetHistory?.balanceSheetStatements
          : quoteSummary.balanceSheetHistoryQuarterly?.balanceSheetStatements;

      if (!statements || !Array.isArray(statements)) {
        return null;
      }

      const result: FinancialStatement = {};
      for (const stmt of statements) {
        const endDate = stmt.endDate as string | undefined;
        if (endDate) {
          result[endDate] = this.flattenStatement(stmt);
        }
      }

      return result;
    } catch {
      return null;
    }
  }

  async getCashFlow(
    ticker: string,
    period: "annual" | "quarterly" = "annual"
  ): Promise<FinancialStatement | null> {
    try {
      const quoteSummary = await yahooFinance.quoteSummary(ticker, {
        modules: [
          period === "annual"
            ? "cashflowStatementHistory"
            : "cashflowStatementHistoryQuarterly",
        ],
      });

      if (!quoteSummary) {
        return null;
      }

      const statements =
        period === "annual"
          ? quoteSummary.cashflowStatementHistory?.cashflowStatements
          : quoteSummary.cashflowStatementHistoryQuarterly?.cashflowStatements;

      if (!statements || !Array.isArray(statements)) {
        return null;
      }

      const result: FinancialStatement = {};
      for (const stmt of statements) {
        const endDate = stmt.endDate as string | undefined;
        if (endDate) {
          result[endDate] = this.flattenStatement(stmt);
        }
      }

      return result;
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
        if ("raw" in value && typeof (value as Record<string, unknown>).raw === "number") {
          result[key] = ((value as Record<string, unknown>).raw as number);
        } else if ("longFmt" in value) {
          result[key] = ((value as Record<string, unknown>).longFmt as string);
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
