import { config } from "dotenv";
import { existsSync, mkdirSync } from "node:fs";
import { resolve } from "node:path";

import { AppConfig } from "../domain";

config();

function getEnvironmentString(key: string, defaultValue?: string): string {
  const value = process.env[key];
  if (!value && !defaultValue) {
    throw new Error(`Missing required env var: ${key}`);
  }
  return value ?? defaultValue ?? "";
}

function ensureDirectoryExists(directoryPath: string): void {
  if (!existsSync(directoryPath)) {
    mkdirSync(directoryPath, { recursive: true });
  }
}

export function loadConfig(): AppConfig {
  const nodeEnv = getEnvironmentString("NODE_ENV", "development") as
    | "development"
    | "production"
    | "test";
  const logLevel = getEnvironmentString("LOG_LEVEL", "info") as "debug" | "info" | "warn" | "error";
  const dataDir = resolve(getEnvironmentString("DATA_DIR", resolve(process.cwd(), "data")));
  const cacheDir = resolve(getEnvironmentString("CACHE_DIR", resolve(process.cwd(), ".cache")));

  ensureDirectoryExists(dataDir);
  ensureDirectoryExists(cacheDir);

  const applicationConfig: AppConfig = {
    nodeEnv,
    logLevel,
    dataDir,
    cacheDir,
    apiKeys: {
      fmp: process.env["FMP_API_KEY"],
      googleSheets: process.env["GOOGLE_SHEETS_CREDENTIALS"],
    },
  };

  return applicationConfig;
}

export const appConfig = loadConfig();
