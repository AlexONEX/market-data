import { YahooFinanceConnector, FinancialStatement } from "../gateway/yahooFinanceConnector.js";
import { HttpClient } from "../gateway/httpClient.js";

export interface CompanyOverview {
  currency?: string;
  marketCap?: number;
  trailingPE?: number;
  trailingEps?: number;
  dividendYield?: number;
  fiftyTwoWeekHigh?: number;
  fiftyTwoWeekLow?: number;
  [key: string]: unknown;
}

export interface PeersList {
  peers?: string[];
}

export interface FinancialDataResult {
  readonly ticker: string;
  readonly period: "annual" | "quarterly";
  readonly overview?: CompanyOverview;
  readonly incomeStatement?: FinancialStatement;
  readonly balanceSheet?: FinancialStatement;
  readonly cashFlow?: FinancialStatement;
  readonly peers?: string[];
  readonly sources: {
    readonly overview?: string;
    readonly incomeStatement?: string;
    readonly balanceSheet?: string;
    readonly cashFlow?: string;
    readonly peers?: string;
  };
}

export class FinancialDataOrchestrator {
  private yahooFinance: YahooFinanceConnector;
  private httpClient: HttpClient;
  private fmpApiKey?: string;

  constructor(fmpApiKey?: string) {
    this.yahooFinance = new YahooFinanceConnector();
    this.httpClient = new HttpClient();
    this.fmpApiKey = fmpApiKey;
  }

  async getCompanyData(
    ticker: string,
    period: "annual" | "quarterly" = "quarterly"
  ): Promise<FinancialDataResult> {
    const [overview, incomeStatement, balanceSheet, cashFlow, peers] =
      await Promise.all([
        this.yahooFinance.getQuote(ticker),
        this.yahooFinance.getIncomeStatement(ticker, period),
        this.yahooFinance.getBalanceSheet(ticker, period),
        this.yahooFinance.getCashFlow(ticker, period),
        this.fmpApiKey ? this.getPeersFromFmp(ticker) : Promise.resolve(null),
      ]);

    const result: FinancialDataResult = {
      ticker,
      period,
      overview: overview ?? undefined,
      incomeStatement: incomeStatement ?? undefined,
      balanceSheet: balanceSheet ?? undefined,
      cashFlow: cashFlow ?? undefined,
      peers: peers ?? undefined,
      sources: {
        overview: overview ? "yfinance" : undefined,
        incomeStatement: incomeStatement ? "yfinance" : undefined,
        balanceSheet: balanceSheet ? "yfinance" : undefined,
        cashFlow: cashFlow ? "yfinance" : undefined,
        peers: peers ? "fmp" : undefined,
      },
    };

    return result;
  }

  private async getPeersFromFmp(ticker: string): Promise<string[] | null> {
    if (!this.fmpApiKey) {
      return null;
    }

    try {
      const url = "https://financialmodelingprep.com/stable/stock-peers";
      const response = await this.httpClient.get<PeersList>(url, {
        symbol: ticker,
        apikey: this.fmpApiKey,
      });

      if (response && response.peers && Array.isArray(response.peers)) {
        return response.peers;
      }

      return null;
    } catch {
      return null;
    }
  }
}
