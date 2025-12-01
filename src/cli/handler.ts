import { resolve } from "path";
import { mkdir } from "fs/promises";
import { getLogger } from "../utils/logger";
import { CSVWriter } from "../utils/csvWriter";
import { JSONWriter } from "../utils/jsonWriter";
import { SheetsFormatter } from "../utils/sheetsFormatter";
import { FinancialDataOrchestrator } from "../services/financialDataOrchestrator";
import { StockDataFromSource } from "../gateway";
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

    const outputDir = resolve(
      input.outputPath ||
        `data/stock_${input.ticker.toLowerCase()}_${new Date().toISOString().split("T")[0]}`,
    );

    if (input.outputFormat === "csv") {
      // Generate multiple CSVs like Python version
      await generateStockCSVSheets(result.data, input.ticker, outputDir);
    } else {
      // Generate JSON with full data
      await jsonWriter.write({
        path: `${outputDir}.json`,
        data: {
          ticker: input.ticker,
          period: input.period,
          overview: result.data.overview,
          incomeStatement: result.data.incomeStatement,
          balanceSheet: result.data.balanceSheet,
          cashFlow: result.data.cashFlow,
          ratios: result.data.ratios,
          statistics: result.data.statistics,
        },
      });
    }

    logger.info({ path: outputDir, source: result.source }, "Stock data saved successfully");
  } catch (error) {
    logger.error(
      { error: error instanceof Error ? error.message : String(error) },
      "Failed to fetch stock data",
    );
    throw error;
  }
}

async function generateStockCSVSheets(
  data: StockDataFromSource,
  _ticker: string,
  baseDir: string,
): Promise<void> {
  const dir = resolve(baseDir, "..");
  await mkdir(dir, { recursive: true });

  // Overview Sheet
  if (data.overview) {
    const overviewRows = [
      ["Field", "Value"],
      ["Ticker", data.overview.ticker],
      ["Name", data.overview.name || "N/A"],
      ["Sector", data.overview.sector || "N/A"],
      ["Market Cap", data.overview.marketCap || "N/A"],
      ["P/E Ratio", data.overview.peRatio || "N/A"],
      ["EPS", data.overview.eps || "N/A"],
      ["Dividend Yield", data.overview.dividendYield || "N/A"],
    ];

    await csvWriter.write({
      path: `${baseDir}/overview.csv`,
      headers: ["Field", "Value"],
      rows: overviewRows.slice(1), // Skip header row
    });
  }

  // Income Statement Sheet
  if (data.incomeStatement && data.incomeStatement.length > 0) {
    const headers = Array.from(new Set(data.incomeStatement.flatMap((s) => Object.keys(s))));
    await csvWriter.write({
      path: `${baseDir}/income_statement.csv`,
      headers,
      rows: data.incomeStatement.map((stmt) => headers.map((h) => stmt[h] || "")),
    });
  }

  // Balance Sheet
  if (data.balanceSheet && data.balanceSheet.length > 0) {
    const headers = Array.from(new Set(data.balanceSheet.flatMap((s) => Object.keys(s))));
    await csvWriter.write({
      path: `${baseDir}/balance_sheet.csv`,
      headers,
      rows: data.balanceSheet.map((stmt) => headers.map((h) => stmt[h] || "")),
    });
  }

  // Cash Flow
  if (data.cashFlow && data.cashFlow.length > 0) {
    const headers = Array.from(new Set(data.cashFlow.flatMap((s) => Object.keys(s))));
    await csvWriter.write({
      path: `${baseDir}/cash_flow.csv`,
      headers,
      rows: data.cashFlow.map((stmt) => headers.map((h) => stmt[h] || "")),
    });
  }

  logger.info({ baseDir }, "Generated multiple CSV sheets");
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
