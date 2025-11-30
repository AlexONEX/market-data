import { resolve } from "path";
import { getLogger } from "../utils/logger";
import { CSVWriter } from "../utils/csvWriter";
import { JSONWriter } from "../utils/jsonWriter";
import { SheetsFormatter } from "../utils/sheetsFormatter";
import { FinancialDataOrchestrator } from "../services/financialDataOrchestrator";
import { BondYieldsInput, StockDataInput, CombinedInput } from "./types";

const logger = getLogger();
const csvWriter = new CSVWriter();
const jsonWriter = new JSONWriter();
const formatter = new SheetsFormatter();
const orchestrator = new FinancialDataOrchestrator();

export async function handleBondYields(input: BondYieldsInput): Promise<void> {
  logger.info({ tickers: input.tickers }, "Fetching bond yields");

  try {
    const bonds = input.tickers.map((ticker) => ({
      ticker,
      price: 100,
      cashflows: [] as const,
    }));

    const yields = await orchestrator.fetchBondYields(bonds);

    if (yields.results.length === 0) {
      logger.warn("No bond yields calculated");
      return;
    }

    const rows = formatter.formatBondYields(yields.results);
    const outputPath = resolve(input.outputPath || `data/tirs.${input.outputFormat}`);

    if (input.outputFormat === "csv") {
      await csvWriter.write({
        path: outputPath,
        headers: ["Ticker", "Price", "TIR (%)", "TEM (%)", "Maturity Date"],
        rows: rows.map((row) => [
          row["ticker"],
          row["price"],
          row["tir"],
          row["tem"],
          row["maturity_date"],
        ]),
      });
    } else {
      await jsonWriter.write({
        path: outputPath,
        data: { yields: yields.results, calculatedAt: new Date() },
      });
    }

    logger.info({ path: outputPath, count: yields.results.length }, "Bond yields saved");
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Failed to fetch bond yields",
    );
    throw error;
  }
}

export async function handleStockData(input: StockDataInput): Promise<void> {
  logger.info({ ticker: input.ticker, period: input.period }, "Fetching stock data");

  try {
    const result = await orchestrator.fetchStockData({
      ticker: input.ticker,
      period: input.period,
    });

    if (!result.success || !result.data) {
      logger.warn("No stock data available");
      return;
    }

    const rows = formatter.formatStockData(result.data);
    const outputPath = resolve(
      input.outputPath || `data/stock_${input.ticker}.${input.outputFormat}`,
    );

    if (input.outputFormat === "csv") {
      await csvWriter.write({
        path: outputPath,
        headers: Array.from(new Set(rows.flatMap((r) => Object.keys(r)))),
        rows: rows.map((r) => Object.values(r)),
      });
    } else {
      await jsonWriter.write({
        path: outputPath,
        data: { ticker: input.ticker, period: input.period, data: rows },
      });
    }

    logger.info({ path: outputPath, sections: rows.length }, "Stock data saved");
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Failed to fetch stock data",
    );
    throw error;
  }
}

export async function handleCombined(input: CombinedInput): Promise<void> {
  logger.info(
    { bondTickers: input.bondTickers, stockTicker: input.stockTicker },
    "Fetching combined analysis",
  );

  try {
    const bonds = input.bondTickers.map((ticker) => ({
      ticker,
      price: 100,
      cashflows: [] as const,
    }));

    const summary = await orchestrator.fetchAll(bonds, {
      ticker: input.stockTicker,
      period: input.stockPeriod,
    });

    const outputDir = resolve(
      input.outputPath || `data/combined_${new Date().toISOString().split("T")[0]}`,
    );

    if (summary.bondYields) {
      const rows = formatter.formatBondYields(summary.bondYields.results);
      const path = `${outputDir}/bonds.${input.outputFormat}`;

      if (input.outputFormat === "csv") {
        await csvWriter.write({
          path,
          headers: ["Ticker", "Price", "TIR (%)", "TEM (%)", "Maturity Date"],
          rows: rows.map((row) => [
            row["ticker"],
            row["price"],
            row["tir"],
            row["tem"],
            row["maturity_date"],
          ]),
        });
      } else {
        await jsonWriter.write({
          path,
          data: summary.bondYields.results,
        });
      }

      logger.info({ path, count: summary.bondYields.results.length }, "Bond yields saved");
    }

    if (summary.stockData?.success && summary.stockData?.data) {
      const rows = formatter.formatStockData(summary.stockData.data);
      const path = `${outputDir}/stock.${input.outputFormat}`;

      if (input.outputFormat === "csv") {
        await csvWriter.write({
          path,
          headers: Array.from(new Set(rows.flatMap((r) => Object.keys(r)))),
          rows: rows.map((r) => Object.values(r)),
        });
      } else {
        await jsonWriter.write({
          path,
          data: rows,
        });
      }

      logger.info({ path, sections: rows.length }, "Stock data saved");
    }

    logger.info({ outputDir, executionTime: summary.executionTime }, "Combined analysis completed");
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Failed to fetch combined analysis",
    );
    throw error;
  }
}
