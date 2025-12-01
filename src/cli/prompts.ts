import * as readline from "readline";
import { stdin as input, stdout as output } from "process";
import { CliMode, BondYieldsInput, StockDataInput, CombinedInput } from "./types";

class PromptManager {
  private rl: readline.Interface | null = null;
  private isInteractive = true;

  async initialize(): Promise<void> {
    // Clean up any existing interface (for watch mode)
    this.close();

    // Determine if we're running interactively
    this.isInteractive = input.isTTY === true;

    // Create readline interface
    // Use terminal: true for proper line buffering in both TTY and piped mode
    // This allows readline.question() to work correctly with piped input
    this.rl = readline.createInterface({
      input,
      output,
      terminal: true,
    });

    // Handle Ctrl+C gracefully
    this.rl.on("SIGINT", () => {
      this.close();
      process.exit(0);
    });
  }

  private question(prompt: string): Promise<string> {
    if (!this.rl) {
      return Promise.reject(new Error("PromptManager not initialized"));
    }

    const rl = this.rl;

    return new Promise((resolve, reject) => {
      // Only show the prompt in interactive mode
      const displayPrompt = this.isInteractive ? prompt : "";

      rl.question(displayPrompt, (answer) => {
        resolve(answer.trim());
      });

      // Handle errors
      rl.once("error", (err) => {
        reject(err);
      });
    });
  }

  close(): void {
    if (this.rl) {
      this.rl.close();
      this.rl = null;
    }
  }

  // Make methods available on the instance
  async promptMainMenuImpl(): Promise<CliMode> {
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

    let choice = "";
    while (!["1", "2", "3", "4"].includes(choice)) {
      choice = await this.question("Enter your choice (1-4): ");
      if (!["1", "2", "3", "4"].includes(choice)) {
        // eslint-disable-next-line no-console
        console.log("Invalid choice. Please enter 1, 2, 3, or 4.");
      }
    }

    const choices: Record<string, CliMode> = {
      "1": "bond-yields",
      "2": "stock-data",
      "3": "combined",
      "4": "exit",
    };

    // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
    return choices[choice]!;
  }

  async promptBondYieldsImpl(): Promise<BondYieldsInput> {
    const tickers = await this.question(
      "\nEnter bond tickers (comma-separated, e.g. AL30,AL29,GD30): ",
    );
    if (!tickers) {
      throw new Error("Please enter at least one ticker");
    }

    // eslint-disable-next-line no-console
    console.log("\nOutput format:");
    // eslint-disable-next-line no-console
    console.log("  1. CSV");
    // eslint-disable-next-line no-console
    console.log("  2. JSON");

    let formatChoice = "";
    while (!["1", "2"].includes(formatChoice)) {
      formatChoice = await this.question("\nChoose format (1-2): ");
      if (!["1", "2"].includes(formatChoice)) {
        // eslint-disable-next-line no-console
        console.log("Invalid choice. Please enter 1 or 2.");
      }
    }

    const defaultPath = `data/tirs_${new Date().toISOString().split("T")[0]}.csv`;
    const path = await this.question(`\nOutput file path (press Enter for default): `);

    return {
      tickers: tickers.split(",").map((t) => t.trim().toUpperCase()),
      outputFormat: formatChoice === "1" ? "csv" : "json",
      outputPath: path || defaultPath,
    };
  }

  async promptStockDataImpl(): Promise<StockDataInput> {
    const ticker = await this.question("\nEnter stock ticker (e.g., AAPL, VIST): ");
    if (!ticker) {
      throw new Error("Please enter a ticker");
    }

    // eslint-disable-next-line no-console
    console.log("\nReport period:");
    // eslint-disable-next-line no-console
    console.log("  1. Annual");
    // eslint-disable-next-line no-console
    console.log("  2. Quarterly");

    let periodChoice = "";
    while (!["1", "2"].includes(periodChoice)) {
      periodChoice = await this.question("\nChoose period (1-2): ");
      if (!["1", "2"].includes(periodChoice)) {
        // eslint-disable-next-line no-console
        console.log("Invalid choice. Please enter 1 or 2.");
      }
    }

    // eslint-disable-next-line no-console
    console.log("\nOutput format:");
    // eslint-disable-next-line no-console
    console.log("  1. CSV");
    // eslint-disable-next-line no-console
    console.log("  2. JSON");

    let formatChoice = "";
    while (!["1", "2"].includes(formatChoice)) {
      formatChoice = await this.question("\nChoose format (1-2): ");
      if (!["1", "2"].includes(formatChoice)) {
        // eslint-disable-next-line no-console
        console.log("Invalid choice. Please enter 1 or 2.");
      }
    }

    const defaultPath = `data/stock_${ticker.toLowerCase()}_${
      new Date().toISOString().split("T")[0]
    }.csv`;
    const filePath = await this.question(`\nOutput file path (press Enter for default): `);

    return {
      ticker: ticker.toUpperCase(),
      period: periodChoice === "1" ? "annual" : "quarterly",
      outputFormat: formatChoice === "1" ? "csv" : "json",
      outputPath: filePath || defaultPath,
    };
  }

  async promptCombinedImpl(): Promise<CombinedInput> {
    const bondTickers = await this.question("\nEnter bond tickers (comma-separated): ");
    if (!bondTickers) {
      throw new Error("Please enter at least one bond ticker");
    }

    const stockTicker = await this.question("Enter stock ticker: ");
    if (!stockTicker) {
      throw new Error("Please enter a stock ticker");
    }

    // eslint-disable-next-line no-console
    console.log("\nStock report period:");
    // eslint-disable-next-line no-console
    console.log("  1. Annual");
    // eslint-disable-next-line no-console
    console.log("  2. Quarterly");

    let periodChoice = "";
    while (!["1", "2"].includes(periodChoice)) {
      periodChoice = await this.question("\nChoose period (1-2): ");
      if (!["1", "2"].includes(periodChoice)) {
        // eslint-disable-next-line no-console
        console.log("Invalid choice. Please enter 1 or 2.");
      }
    }

    // eslint-disable-next-line no-console
    console.log("\nOutput format:");
    // eslint-disable-next-line no-console
    console.log("  1. CSV");
    // eslint-disable-next-line no-console
    console.log("  2. JSON");

    let formatChoice = "";
    while (!["1", "2"].includes(formatChoice)) {
      formatChoice = await this.question("\nChoose format (1-2): ");
      if (!["1", "2"].includes(formatChoice)) {
        // eslint-disable-next-line no-console
        console.log("Invalid choice. Please enter 1 or 2.");
      }
    }

    const defaultPath = `data/combined_${new Date().toISOString().split("T")[0]}`;
    const dirPath = await this.question(`\nOutput directory (press Enter for default): `);

    return {
      bondTickers: bondTickers.split(",").map((t) => t.trim().toUpperCase()),
      stockTicker: stockTicker.toUpperCase(),
      stockPeriod: periodChoice === "1" ? "annual" : "quarterly",
      outputFormat: formatChoice === "1" ? "csv" : "json",
      outputPath: dirPath || defaultPath,
    };
  }

  async promptContinueImpl(): Promise<boolean> {
    // If not interactive (piped input), auto-continue
    if (!this.isInteractive) {
      return true;
    }

    try {
      const answer = await this.question("\nContinue? (y/n): ");
      return ["y", "yes"].includes(answer.toLowerCase());
    } catch (error) {
      // If readline is closed or error occurs, exit gracefully
      return false;
    }
  }
}

// Singleton instance
const manager = new PromptManager();

// Export functions that use the singleton
export async function initializeInput(): Promise<void> {
  return manager.initialize();
}

export async function promptMainMenu(): Promise<CliMode> {
  return manager.promptMainMenuImpl();
}

export async function promptBondYields(): Promise<BondYieldsInput> {
  return manager.promptBondYieldsImpl();
}

export async function promptStockData(): Promise<StockDataInput> {
  return manager.promptStockDataImpl();
}

export async function promptCombined(): Promise<CombinedInput> {
  return manager.promptCombinedImpl();
}

export async function promptContinue(): Promise<boolean> {
  return manager.promptContinueImpl();
}

export function closePrompts(): void {
  manager.close();
}
