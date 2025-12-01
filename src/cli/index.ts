#!/usr/bin/env node

import { initializeLogger } from "../utils/logger";
import { loadConfig } from "../utils/config";
import {
  promptMainMenu,
  promptBondYields,
  promptStockData,
  promptCombined,
  promptContinue,
  closePrompts,
  initializeInput,
} from "./prompts";
import { handleBondYields, handleStockData, handleCombined } from "./handler";

const config = loadConfig();
initializeLogger(config);

async function main(): Promise<number> {
  try {
    await initializeInput();
    // eslint-disable-next-line no-console
    console.log("\n📊 Market Data Analysis Tool\n");

    let continueLoop = true;

    while (continueLoop) {
      const mode = await promptMainMenu();

      switch (mode) {
        case "bond-yields": {
          const input = await promptBondYields();
          await handleBondYields(input);
          break;
        }

        case "stock-data": {
          const input = await promptStockData();
          await handleStockData(input);
          break;
        }

        case "combined": {
          const input = await promptCombined();
          await handleCombined(input);
          break;
        }

        case "exit": {
          continueLoop = false;
          // eslint-disable-next-line no-console
          console.log("\n👋 Goodbye!\n");
          break;
        }
      }

      if (continueLoop && mode !== "exit") {
        try {
          continueLoop = await promptContinue();
        } catch {
          // If prompt fails (e.g., stdin closed), exit gracefully
          continueLoop = false;
          // eslint-disable-next-line no-console
          console.log("\n👋 Goodbye!\n");
        }
      }
    }

    closePrompts();
    return 0;
  } catch (error) {
    closePrompts();
    console.error("\n❌ Error:", error instanceof Error ? error.message : String(error), "\n");
    return 1;
  }
}

main()
  .then((code) => process.exit(code))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
