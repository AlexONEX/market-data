import { BondYieldService, type BondWithPrice, type BondYieldOutput } from "./bondYieldService";
import { StockDataService, type FetchStockResult } from "./stockDataService";
import { getLogger } from "../utils/logger";
import { FetchStockDataInput } from "../gateway";

export interface OrchestratorConfig {
  readonly bondYieldEnabled?: boolean;
  readonly stockDataEnabled?: boolean;
  readonly stockDataRetries?: number;
}

export interface FinancialDataSummary {
  readonly bondYields?: BondYieldOutput;
  readonly stockData?: FetchStockResult;
  readonly executionTime: number;
  readonly timestamp: Date;
}

export class FinancialDataOrchestrator {
  private readonly bondYieldService: BondYieldService;
  private readonly stockDataService: StockDataService;
  private readonly logger = getLogger();
  private readonly config: Required<OrchestratorConfig>;

  constructor(config: OrchestratorConfig = {}) {
    this.bondYieldService = new BondYieldService();
    this.stockDataService = new StockDataService({
      retryAttempts: config.stockDataRetries,
    });
    this.config = {
      bondYieldEnabled: config.bondYieldEnabled ?? true,
      stockDataEnabled: config.stockDataEnabled ?? true,
      stockDataRetries: config.stockDataRetries ?? 3,
    };
  }

  async fetchBondYields(bonds: readonly BondWithPrice[]): Promise<BondYieldOutput> {
    const startTime = Date.now();

    this.logger.info({ bondCount: bonds.length }, "Starting bond yield calculation");

    try {
      const results = await this.bondYieldService.calculateBondYields(bonds);
      const duration = Date.now() - startTime;

      this.logger.info(
        {
          successCount: results.results.length,
          failedCount: results.failedTickers.length,
          durationMs: duration,
        },
        "Bond yield calculation completed",
      );

      return results;
    } catch (error) {
      const duration = Date.now() - startTime;
      this.logger.error(
        { error: error instanceof Error ? error.message : String(error), durationMs: duration },
        "Bond yield calculation failed",
      );
      throw error;
    }
  }

  async fetchStockData(input: FetchStockDataInput): Promise<FetchStockResult> {
    const startTime = Date.now();

    this.logger.info({ ticker: input.ticker, period: input.period }, "Starting stock data fetch");

    try {
      const result = await this.stockDataService.fetchStockData(input);
      const duration = Date.now() - startTime;

      this.logger.info(
        { success: result.success, durationMs: duration },
        "Stock data fetch completed",
      );

      return result;
    } catch (error) {
      const duration = Date.now() - startTime;
      this.logger.error(
        { error: error instanceof Error ? error.message : String(error), durationMs: duration },
        "Stock data fetch failed",
      );
      throw error;
    }
  }

  async fetchAll(
    bonds: readonly BondWithPrice[],
    stockInput: FetchStockDataInput,
  ): Promise<FinancialDataSummary> {
    const startTime = Date.now();
    let bondYields: BondYieldOutput | undefined;
    let stockData: FetchStockResult | undefined;

    try {
      if (this.config.bondYieldEnabled && bonds.length > 0) {
        this.logger.info("Fetching bond yields");
        bondYields = await this.fetchBondYields(bonds);
      }

      if (this.config.stockDataEnabled) {
        this.logger.info("Fetching stock data");
        stockData = await this.fetchStockData(stockInput);
      }

      const executionTime = Date.now() - startTime;
      this.logger.info(
        { executionTimeMs: executionTime },
        "All financial data fetched successfully",
      );

      return {
        bondYields,
        stockData,
        executionTime,
        timestamp: new Date(),
      };
    } catch (error) {
      const executionTime = Date.now() - startTime;
      this.logger.error(
        {
          error: error instanceof Error ? error.message : String(error),
          durationMs: executionTime,
        },
        "Financial data fetch failed",
      );
      throw error;
    }
  }
}
