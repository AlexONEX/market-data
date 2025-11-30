import * as cheerio from "cheerio";

import { DataFetchError, DataSource } from "../domain";
import { HttpClient } from "./httpClient";
import {
  ApiGateway,
  FetchStockDataInput,
  FetchStockDataOutput,
  FinancialStatementData,
  StockDataFromSource,
} from "./types";

export class StockanalysisConnector implements ApiGateway {
  readonly name = "stockanalysis";
  private readonly httpClient: HttpClient;
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;

  constructor() {
    this.httpClient = new HttpClient({
      baseURL: "https://stockanalysis.com",
      timeout: 20000,
      retryAttempts: 2,
    });
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
      const url = `/stocks/${ticker}/${period}/`;
      const response = await this.httpClient.get<string>(url, DataSource.StockAnalysis);

      const stockData = this.parseHtmlResponse(response.data as unknown as string, ticker);
      this.markHealthy();

      return {
        data: stockData,
        source: DataSource.StockAnalysis,
        fetchedAt: new Date(),
      };
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      throw new DataFetchError(
        DataSource.StockAnalysis,
        `Failed to fetch stock data for ${ticker}`,
        { ticker, period: input.period, originalError: err.message },
      );
    }
  }

  private parseHtmlResponse(html: string, ticker: string): StockDataFromSource {
    const $ = cheerio.load(html);

    const marketCapText = this.extractText($, '[data-key="market-cap"]');
    const peRatioText = this.extractText($, '[data-key="pe-ratio"]');
    const epsText = this.extractText($, '[data-key="eps"]');
    const dividendYieldText = this.extractText($, '[data-key="dividend-yield"]');

    return {
      overview: {
        ticker,
        name: this.extractCompanyName($),
        sector: this.extractText($, '[data-key="sector"]'),
        marketCap: marketCapText ? this.parseNumber(marketCapText) : undefined,
        peRatio: peRatioText ? this.parseNumber(peRatioText) : undefined,
        eps: epsText ? this.parseNumber(epsText) : undefined,
        dividendYield: dividendYieldText ? this.parseNumber(dividendYieldText) : undefined,
      },
      incomeStatement: this.extractFinancialTable($, "income-statement"),
      balanceSheet: this.extractFinancialTable($, "balance-sheet"),
      cashFlow: this.extractFinancialTable($, "cash-flow"),
      ratios: this.extractFinancialTable($, "ratios"),
      statistics: this.extractFinancialTable($, "statistics"),
      peers: this.extractPeers($),
    };
  }

  private extractCompanyName($: cheerio.CheerioAPI): string {
    return $("h1").text().trim().split(" ")[0] || "";
  }

  private extractText($: cheerio.CheerioAPI, selector: string): string | undefined {
    const text = $(selector).text().trim();
    return text || undefined;
  }

  private parseNumber(value: string | undefined): number | undefined {
    if (!value) return undefined;

    const multipliers: Record<string, number> = {
      T: 1e12,
      B: 1e9,
      M: 1e6,
      K: 1e3,
    };

    const match = value.match(/^([\d.]+)([TBMK])?/);
    if (!match || !match[1]) return undefined;

    const num = Number.parseFloat(match[1]);
    const multiplier = match[2] ? (multipliers[match[2]] ?? 1) : 1;

    return num * multiplier;
  }

  private extractFinancialTable(
    $: cheerio.CheerioAPI,
    tableId: string,
  ): readonly FinancialStatementData[] {
    const rows: FinancialStatementData[] = [];
    const table = $(`[data-table="${tableId}"] table`);

    table.find("tbody tr").each((_, row) => {
      const cells = $(row).find("td");
      if (cells.length > 0) {
        const rowData: Record<string, string | undefined> = {};
        cells.each((index, cell) => {
          const key = `col${index}`;
          const text = $(cell).text().trim();
          rowData[key] = text || undefined;
        });
        rows.push(rowData as FinancialStatementData);
      }
    });

    return rows;
  }

  private extractPeers($: cheerio.CheerioAPI): string[] | undefined {
    const peersSection = $('[data-section="peers"]');
    if (peersSection.length === 0) return undefined;

    const peers: string[] = [];
    peersSection.find("a[href*='/stocks/']").each((_, link) => {
      const ticker = $(link).text().trim();
      if (ticker) peers.push(ticker);
    });

    return peers.length > 0 ? peers : undefined;
  }
}
