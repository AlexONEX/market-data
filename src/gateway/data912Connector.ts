import { DataFetchError, DataSource } from "../domain";
import { HttpClient } from "./httpClient";
import { ApiGateway, BondPriceData, FetchBondPricesOutput } from "./types";

interface Data912Response {
  readonly ticker: string;
  readonly price: number;
  readonly currency?: string;
  readonly date?: string;
  readonly bid?: number;
  readonly ask?: number;
}

export class Data912Connector implements ApiGateway {
  readonly name = "data912";
  private readonly httpClient: HttpClient;
  private isHealthyFlag = true;
  private lastErrorValue?: Error;
  private lastErrorTimeValue?: Date;

  constructor() {
    this.httpClient = new HttpClient({
      baseURL: "https://data912.com/live",
      timeout: 15000,
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

  async fetchHardDollarBonds(tickers: readonly string[]): Promise<FetchBondPricesOutput> {
    return this.fetchBondsByEndpoint(tickers, "/arg_bonds");
  }

  async fetchNotes(tickers: readonly string[]): Promise<FetchBondPricesOutput> {
    return this.fetchBondsByEndpoint(tickers, "/arg_notes");
  }

  private async fetchBondsByEndpoint(
    tickers: readonly string[],
    endpoint: string,
  ): Promise<FetchBondPricesOutput> {
    const prices: BondPriceData[] = [];
    const failedTickers: string[] = [];

    try {
      const response = await this.httpClient.get<readonly Data912Response[]>(
        endpoint,
        DataSource.Data912,
      );

      const responseData = Array.isArray(response.data) ? response.data : [response.data];

      for (const ticker of tickers) {
        const data = responseData.find((item) => item.ticker === ticker);

        if (data) {
          prices.push({
            ticker: data.ticker,
            price: data.price,
            currency: data.currency ?? "ARS",
            date: data.date ? new Date(data.date) : new Date(),
            source: DataSource.Data912,
          });
        } else {
          failedTickers.push(ticker);
        }
      }

      this.markHealthy();
    } catch (error) {
      const err = error instanceof Error ? error : new Error(String(error));
      this.markUnhealthy(err);
      throw new DataFetchError(DataSource.Data912, `Failed to fetch bond prices from ${endpoint}`, {
        tickers,
        endpoint,
        originalError: err.message,
      });
    }

    return { prices, failedTickers };
  }
}
