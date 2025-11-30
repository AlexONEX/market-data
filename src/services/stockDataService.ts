import { DataSource } from "../domain";
import { FetchStockDataInput, StockanalysisConnector, StockDataFromSource } from "../gateway";
import { getLogger } from "../utils/logger";

export interface StockDataServiceConfig {
  readonly retryAttempts?: number;
}

export interface FetchStockResult {
  readonly success: boolean;
  readonly data?: StockDataFromSource;
  readonly source?: DataSource;
  readonly error?: string;
  readonly fetchedAt: Date;
}

export class StockDataService {
  private readonly stockanalysisConnector: StockanalysisConnector;
  private readonly logger = getLogger();
  private readonly config: Required<StockDataServiceConfig>;

  constructor(config: StockDataServiceConfig = {}) {
    this.stockanalysisConnector = new StockanalysisConnector();
    this.config = {
      retryAttempts: config.retryAttempts ?? 3,
    };
  }

  async fetchStockData(input: FetchStockDataInput): Promise<FetchStockResult> {
    const { ticker, period } = input;
    this.logger.info({ ticker, period }, "Fetching stock data");

    for (let attempt = 1; attempt <= this.config.retryAttempts; attempt++) {
      try {
        const output = await this.stockanalysisConnector.fetchStockData(input);

        this.logger.info(
          { ticker, source: output.source, attempt },
          "Successfully fetched stock data",
        );

        return {
          success: true,
          data: output.data,
          source: output.source as DataSource,
          fetchedAt: output.fetchedAt,
        };
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);

        this.logger.warn({ ticker, attempt, error: errorMessage }, "Attempt failed, retrying");

        if (attempt === this.config.retryAttempts) {
          this.logger.error(
            { ticker, totalAttempts: this.config.retryAttempts, error: errorMessage },
            "Failed to fetch stock data after all retry attempts",
          );

          return {
            success: false,
            error: errorMessage,
            fetchedAt: new Date(),
          };
        }

        await this.delayBeforeRetry(attempt);
      }
    }

    return {
      success: false,
      error: "Unknown error",
      fetchedAt: new Date(),
    };
  }

  private async delayBeforeRetry(attempt: number): Promise<void> {
    const delayMs = 1000 * attempt;
    await new Promise((resolve) => setTimeout(resolve, delayMs));
  }
}
