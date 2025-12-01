import YahooFinance from "yahoo-finance2";

import { DataFetchError, DataSource } from "../domain";
import {
  ApiGateway,
  FetchStockDataInput,
  FetchStockDataOutput,
  FinancialStatementData,
  StockDataFromSource,
} from "./types";

export class YahooFinanceConnector implements ApiGateway {
  readonly name = "yahoo-finance";
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  private yf: any;

  constructor() {
    this.yf = new YahooFinance({ suppressNotices: ["yahooSurvey"] });
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

  async fetchStockData(input: FetchStockDataInput): Promise<FetchStockDataOutput> {
    const { ticker, period } = input;

    try {
      const quoteSummary = await this.yf.quoteSummary(ticker, {
        modules: [
          "summaryProfile",
          "financialData",
          "incomeStatementHistory",
          "balanceSheetHistory",
          "cashflowStatementHistory",
          "incomeStatementHistoryQuarterly",
          "balanceSheetHistoryQuarterly",
          "cashflowStatementHistoryQuarterly",
        ],
      });

      if (!quoteSummary) {
        throw new Error(`No data found for ticker ${ticker}`);
      }

      const stockData = this.buildStockData(ticker, period, quoteSummary);
      this.markHealthy();

      return {
        data: stockData,
        source: DataSource.YFinance,
        fetchedAt: new Date(),
      };
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      throw new DataFetchError(DataSource.YFinance, `Failed to fetch stock data for ${ticker}`, {
        ticker,
        period,
        originalError: err.message,
      });
    }
  }

  private buildStockData(
    ticker: string,
    period: "annual" | "quarterly",
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    quoteSummary: any,
  ): StockDataFromSource {
    const summaryProfile = quoteSummary.summaryProfile || {};
    const financialData = quoteSummary.financialData || {};

    const overview: StockDataFromSource["overview"] = {
      ticker,
      name: (summaryProfile.longName as string) || (summaryProfile.shortName as string) || "",
      sector: (summaryProfile.sector as string) || undefined,
      marketCap: (financialData.marketCap as number) || undefined,
      peRatio: (financialData.trailingPE as number) || undefined,
      eps: (financialData.trailingEps as number) || undefined,
      dividendYield: (financialData.dividendYield as number) || undefined,
    };

    const incomeStatements = this.extractStatementsAsTable(quoteSummary, period, "income");
    const balanceSheets = this.extractStatementsAsTable(quoteSummary, period, "balance");
    const cashFlows = this.extractStatementsAsTable(quoteSummary, period, "cashflow");

    return {
      overview,
      incomeStatement: incomeStatements,
      balanceSheet: balanceSheets,
      cashFlow: cashFlows,
      ratios: [],
      statistics: [],
      peers: undefined,
    };
  }

  private extractStatementsAsTable(
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    quoteSummary: any,
    period: "annual" | "quarterly",
    statementType: "income" | "balance" | "cashflow",
  ): readonly FinancialStatementData[] {
    const moduleNames = {
      income: {
        annual: "incomeStatementHistory",
        quarterly: "incomeStatementHistoryQuarterly",
      },
      balance: {
        annual: "balanceSheetHistory",
        quarterly: "balanceSheetHistoryQuarterly",
      },
      cashflow: {
        annual: "cashflowStatementHistory",
        quarterly: "cashflowStatementHistoryQuarterly",
      },
    };

    const moduleName = moduleNames[statementType][period];
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const module = quoteSummary[moduleName];

    if (!module) {
      return [];
    }

    const statementsKey =
      statementType === "income"
        ? "incomeStatementHistory"
        : statementType === "balance"
          ? "balanceSheetStatements"
          : "cashflowStatements";

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const statements: any[] = module[statementsKey] || [];

    if (statements.length === 0) {
      return [];
    }

    // Convertir a formato: cada fila es un período, columnas son métricas
    const result: FinancialStatementData[] = statements.map((stmt) => {
      const data: Record<string, string | undefined> = {};
      for (const [key, value] of Object.entries(stmt)) {
        if (value === null || value === undefined) {
          data[key] = undefined;
        } else if (typeof value === "object") {
          data[key] = String(value);
        } else {
          data[key] = String(value);
        }
      }
      return data as FinancialStatementData;
    });

    return result;
  }
}
