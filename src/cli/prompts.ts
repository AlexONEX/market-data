import inquirer from "inquirer";
import { CliMode, BondYieldsInput, StockDataInput, CombinedInput } from "./types";

const prompt = inquirer.prompt;

export async function promptMainMenu(): Promise<CliMode> {
  const answers = await prompt([
    {
      type: "list",
      name: "mode",
      message: "What would you like to do?",
      choices: [
        {
          name: "Calculate Bond Yields (TIR)",
          value: "bond-yields",
        },
        {
          name: "Fetch Stock Financial Data",
          value: "stock-data",
        },
        {
          name: "Combined Analysis (Bonds + Stock)",
          value: "combined",
        },
        {
          name: "Exit",
          value: "exit",
        },
      ],
    },
  ]);

  return answers.mode as CliMode;
}

export async function promptBondYields(): Promise<BondYieldsInput> {
  const answers = await prompt([
    {
      type: "input",
      name: "tickers",
      message: "Enter bond tickers (comma-separated, e.g. AL30,AL29,GD30):",
      validate: (input: string) => {
        if (!input || input.trim().length === 0) {
          return "Please enter at least one ticker";
        }
        return true;
      },
    },
    {
      type: "list",
      name: "outputFormat",
      message: "Output format:",
      choices: ["csv", "json"],
    },
    {
      type: "input",
      name: "outputPath",
      message: "Output file path (optional, press Enter to skip):",
      default: `data/tirs_${new Date().toISOString().split("T")[0]}.csv`,
    },
  ]);

  return {
    tickers: answers.tickers.split(",").map((t: string) => t.trim().toUpperCase()),
    outputFormat: answers.outputFormat,
    outputPath: answers.outputPath,
  };
}

export async function promptStockData(): Promise<StockDataInput> {
  const answers = await prompt([
    {
      type: "input",
      name: "ticker",
      message: "Enter stock ticker (e.g., AAPL, VIST):",
      validate: (input: string) => {
        if (!input || input.trim().length === 0) {
          return "Please enter a ticker";
        }
        return true;
      },
    },
    {
      type: "list",
      name: "period",
      message: "Report period:",
      choices: ["annual", "quarterly"],
    },
    {
      type: "list",
      name: "outputFormat",
      message: "Output format:",
      choices: ["csv", "json"],
    },
    {
      type: "input",
      name: "outputPath",
      message: "Output file path (optional, press Enter to skip):",
      default: `data/stock_PLACEHOLDER_${new Date().toISOString().split("T")[0]}.csv`,
    },
  ]);

  return {
    ticker: answers.ticker.toUpperCase(),
    period: answers.period,
    outputFormat: answers.outputFormat,
    outputPath:
      answers.outputPath ||
      `data/stock_${answers.ticker.toLowerCase()}_${new Date().toISOString().split("T")[0]}.csv`,
  };
}

export async function promptCombined(): Promise<CombinedInput> {
  const answers = await prompt([
    {
      type: "input",
      name: "bondTickers",
      message: "Enter bond tickers (comma-separated):",
      validate: (input: string) => {
        if (!input || input.trim().length === 0) {
          return "Please enter at least one bond ticker";
        }
        return true;
      },
    },
    {
      type: "input",
      name: "stockTicker",
      message: "Enter stock ticker:",
      validate: (input: string) => {
        if (!input || input.trim().length === 0) {
          return "Please enter a stock ticker";
        }
        return true;
      },
    },
    {
      type: "list",
      name: "stockPeriod",
      message: "Stock report period:",
      choices: ["annual", "quarterly"],
    },
    {
      type: "list",
      name: "outputFormat",
      message: "Output format:",
      choices: ["csv", "json"],
    },
    {
      type: "input",
      name: "outputPath",
      message: "Output directory (optional, press Enter to skip):",
      default: `data/combined_${new Date().toISOString().split("T")[0]}`,
    },
  ]);

  return {
    bondTickers: answers.bondTickers.split(",").map((t: string) => t.trim().toUpperCase()),
    stockTicker: answers.stockTicker.toUpperCase(),
    stockPeriod: answers.stockPeriod,
    outputFormat: answers.outputFormat,
    outputPath: answers.outputPath,
  };
}

export async function promptContinue(): Promise<boolean> {
  const answers = await prompt([
    {
      type: "confirm",
      name: "continue",
      message: "Continue?",
      default: true,
    },
  ]);

  return answers.continue;
}
