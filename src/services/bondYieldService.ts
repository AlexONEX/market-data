import { calculateTIRNewtonRaphson, Cashflow, TIRResult } from "../domain";
import { BondPriceData, Data912Connector } from "../gateway";
import { getLogger } from "../utils/logger";

export interface BondWithPrice {
  readonly ticker: string;
  readonly price: number;
  readonly cashflows: readonly Cashflow[];
}

export interface BondYieldOutput {
  readonly results: readonly TIRResult[];
  readonly failedTickers: readonly string[];
  readonly processedAt: Date;
}

export class BondYieldService {
  private readonly data912Connector: Data912Connector;
  private readonly logger = getLogger();

  constructor() {
    this.data912Connector = new Data912Connector();
  }

  async calculateBondYields(bonds: readonly BondWithPrice[]): Promise<BondYieldOutput> {
    const results: TIRResult[] = [];
    const failedTickers: string[] = [];

    for (const bond of bonds) {
      try {
        if (bond.cashflows.length === 0) {
          this.logger.warn({ ticker: bond.ticker }, "No cashflows for bond");
          failedTickers.push(bond.ticker);
          continue;
        }

        const tir = calculateTIRNewtonRaphson(bond.cashflows, bond.price, new Date());

        const lastCashflow = bond.cashflows.at(-1);
        if (!lastCashflow) {
          this.logger.warn({ ticker: bond.ticker }, "Could not get last cashflow");
          failedTickers.push(bond.ticker);
          continue;
        }

        results.push({
          ticker: bond.ticker,
          tir,
          price: bond.price,
          maturityDate: lastCashflow.paymentDate,
        });

        this.logger.info({ ticker: bond.ticker, tir }, "Calculated TIR");
      } catch (error) {
        this.logger.error(
          { ticker: bond.ticker, error: error instanceof Error ? error.message : String(error) },
          "Failed to calculate TIR",
        );
        failedTickers.push(bond.ticker);
      }
    }

    return {
      results,
      failedTickers,
      processedAt: new Date(),
    };
  }

  async fetchBondPrices(tickers: readonly string[]): Promise<readonly BondPriceData[]> {
    this.logger.info({ tickerCount: tickers.length }, "Fetching bond prices");

    try {
      const output = await this.data912Connector.fetchHardDollarBonds(tickers);

      if (output.failedTickers.length > 0) {
        this.logger.warn({ failed: output.failedTickers }, "Some bond prices failed to fetch");
      }

      return output.prices;
    } catch (error) {
      this.logger.error(
        { error: error instanceof Error ? error.message : String(error) },
        "Failed to fetch bond prices",
      );
      throw error;
    }
  }
}
