import prompts from "prompts";
import { CliMode, BondYieldsInput, StockDataInput, CombinedInput } from "./types";

export async function promptMainMenu(): Promise<CliMode> {
  // eslint-disable-next-line no-console
  console.log("\nSelect an option:");
  // eslint-disable-next-line no-console
  console.log("  1. Calculate Bond Yields (TIR)");
  // eslint-disable-next-line no-console
  console.log("  2. Fetch Stock Financial Data");
  // eslint-disable-next-line no-console
  console.log("  3. Combined Analysis (Bonds + Stock)");
  // eslint-disable-next-line no-console
  console.log("  4. Exit\n");

  const response = await prompts({
    type: "text",
    name: "choice",
    message: "Enter your choice (1-4):",
    validate: (input: string) =>
      ["1", "2", "3", "4"].includes(input) || "Please enter 1, 2, 3, or 4",
  });

  const choices: Record<string, CliMode> = {
    "1": "bond-yields",
    "2": "stock-data",
    "3": "combined",
    "4": "exit",
  };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  return choices[response.choice]!;
}

export async function promptBondYields(): Promise<BondYieldsInput> {
  const tickersRes = await prompts({
    type: "text",
    name: "tickers",
    message: "Enter bond tickers (comma-separated, e.g. AL30,AL29,GD30):",
    validate: (input: string) => input.trim().length > 0 || "Please enter at least one ticker",
  });

  // eslint-disable-next-line no-console
  console.log("\nOutput format:");
  // eslint-disable-next-line no-console
  console.log("  1. CSV");
  // eslint-disable-next-line no-console
  console.log("  2. JSON\n");

  const formatRes = await prompts({
    type: "text",
    name: "format",
    message: "Choose format (1-2):",
    validate: (input: string) => ["1", "2"].includes(input) || "Please enter 1 or 2",
  });

  const pathRes = await prompts({
    type: "text",
    name: "path",
    message: "Output file path (press Enter to use default):",
    initial: `data/tirs_${new Date().toISOString().split("T")[0]}.csv`,
  });

  const formatMap: Record<string, "csv" | "json"> = { "1": "csv", "2": "json" };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const format = formatMap[formatRes.format]!;

  return {
    tickers: tickersRes.tickers.split(",").map((t: string) => t.trim().toUpperCase()),
    outputFormat: format,
    outputPath: pathRes.path,
  };
}

export async function promptStockData(): Promise<StockDataInput> {
  const tickerRes = await prompts({
    type: "text",
    name: "ticker",
    message: "Enter stock ticker (e.g., AAPL, VIST):",
    validate: (input: string) => input.trim().length > 0 || "Please enter a ticker",
  });

  // eslint-disable-next-line no-console
  console.log("\nReport period:");
  // eslint-disable-next-line no-console
  console.log("  1. Annual");
  // eslint-disable-next-line no-console
  console.log("  2. Quarterly\n");

  const periodRes = await prompts({
    type: "text",
    name: "period",
    message: "Choose period (1-2):",
    validate: (input: string) => ["1", "2"].includes(input) || "Please enter 1 or 2",
  });

  // eslint-disable-next-line no-console
  console.log("\nOutput format:");
  // eslint-disable-next-line no-console
  console.log("  1. CSV");
  // eslint-disable-next-line no-console
  console.log("  2. JSON\n");

  const formatRes = await prompts({
    type: "text",
    name: "format",
    message: "Choose format (1-2):",
    validate: (input: string) => ["1", "2"].includes(input) || "Please enter 1 or 2",
  });

  const pathRes = await prompts({
    type: "text",
    name: "path",
    message: "Output file path (press Enter to use default):",
    initial: `data/stock_${tickerRes.ticker.toLowerCase()}_${new Date().toISOString().split("T")[0]}.csv`,
  });

  const periodMap: Record<string, "annual" | "quarterly"> = { "1": "annual", "2": "quarterly" };
  const formatMap: Record<string, "csv" | "json"> = { "1": "csv", "2": "json" };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const period = periodMap[periodRes.period]!;
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const format = formatMap[formatRes.format]!;

  return {
    ticker: tickerRes.ticker.toUpperCase(),
    period,
    outputFormat: format,
    outputPath: pathRes.path,
  };
}

export async function promptCombined(): Promise<CombinedInput> {
  const bondTickersRes = await prompts({
    type: "text",
    name: "tickers",
    message: "Enter bond tickers (comma-separated):",
    validate: (input: string) => input.trim().length > 0 || "Please enter at least one bond ticker",
  });

  const stockTickerRes = await prompts({
    type: "text",
    name: "ticker",
    message: "Enter stock ticker:",
    validate: (input: string) => input.trim().length > 0 || "Please enter a stock ticker",
  });

  // eslint-disable-next-line no-console
  console.log("\nStock report period:");
  // eslint-disable-next-line no-console
  console.log("  1. Annual");
  // eslint-disable-next-line no-console
  console.log("  2. Quarterly\n");

  const periodRes = await prompts({
    type: "text",
    name: "period",
    message: "Choose period (1-2):",
    validate: (input: string) => ["1", "2"].includes(input) || "Please enter 1 or 2",
  });

  // eslint-disable-next-line no-console
  console.log("\nOutput format:");
  // eslint-disable-next-line no-console
  console.log("  1. CSV");
  // eslint-disable-next-line no-console
  console.log("  2. JSON\n");

  const formatRes = await prompts({
    type: "text",
    name: "format",
    message: "Choose format (1-2):",
    validate: (input: string) => ["1", "2"].includes(input) || "Please enter 1 or 2",
  });

  const pathRes = await prompts({
    type: "text",
    name: "path",
    message: "Output directory (press Enter to use default):",
    initial: `data/combined_${new Date().toISOString().split("T")[0]}`,
  });

  const periodMap: Record<string, "annual" | "quarterly"> = { "1": "annual", "2": "quarterly" };
  const formatMap: Record<string, "csv" | "json"> = { "1": "csv", "2": "json" };

  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const period = periodMap[periodRes.period]!;
  // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
  const format = formatMap[formatRes.format]!;

  return {
    bondTickers: bondTickersRes.tickers.split(",").map((t: string) => t.trim().toUpperCase()),
    stockTicker: stockTickerRes.ticker.toUpperCase(),
    stockPeriod: period,
    outputFormat: format,
    outputPath: pathRes.path,
  };
}

export async function promptContinue(): Promise<boolean> {
  const response = await prompts({
    type: "text",
    name: "continue",
    message: "Continue? (y/n):",
    validate: (input: string) =>
      ["y", "n", "yes", "no"].includes(input.toLowerCase()) || "Please enter y or n",
  });

  return ["y", "yes"].includes(response.continue.toLowerCase());
}
