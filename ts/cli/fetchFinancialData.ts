#!/usr/bin/env node

import { program } from "commander";
import { config } from "dotenv";
import { FinancialDataOrchestrator } from "../services/financialDataOrchestrator.js";
import { ExcelWriter } from "../gateway/excelWriter.js";
import { CsvWriter } from "../utils/csvWriter.js";
import * as fs from "fs";
import * as path from "path";

config();

interface Options {
  ticker: string;
  period?: "annual" | "quarterly";
  output?: string;
  format?: "json" | "csv" | "excel";
}

async function fetchFinancialData(options: Options): Promise<void> {
  console.log(`\nFetching ${options.period} financial data for ${options.ticker}...\n`);

  const orchestrator = new FinancialDataOrchestrator(process.env["FMP_API_KEY"]);

  const result = await orchestrator.getCompanyData(
    options.ticker.toUpperCase(),
    options.period ?? "quarterly"
  );

  console.log("Data retrieved successfully!");
  console.log(`\nCompany: ${result.ticker}`);
  console.log(`Period: ${result.period}`);

  if (result.overview) {
    console.log(`\nOverview:`);
    console.log(`  Currency: ${result.overview.currency}`);
    console.log(`  Market Cap: ${result.overview.marketCap}`);
    console.log(`  PE Ratio: ${result.overview.trailingPE}`);
    console.log(`  Dividend Yield: ${result.overview.dividendYield}%`);
  }

  if (result.incomeStatement) {
    const dates = Object.keys(result.incomeStatement);
    console.log(`\nIncome Statements: ${dates.length} periods found`);
  }

  if (result.balanceSheet) {
    const dates = Object.keys(result.balanceSheet);
    console.log(`Balance Sheets: ${dates.length} periods found`);
  }

  if (result.cashFlow) {
    const dates = Object.keys(result.cashFlow);
    console.log(`Cash Flow Statements: ${dates.length} periods found`);
  }

  const outputDir = options.output || "./data/financial_data";
  fs.mkdirSync(outputDir, { recursive: true });

  const format = options.format ?? "json";

  if (format === "json" || format === "csv" || format === "excel") {
    const filename = `${result.ticker}_${result.period}`;
    const fileExt = format === "json" ? "json" : format === "csv" ? "csv" : "xlsx";
    const filePath = path.join(outputDir, `${filename}.${fileExt}`);

    if (format === "json") {
      const jsonData = JSON.stringify(result, null, 2);
      fs.writeFileSync(filePath, jsonData);
      console.log(`\n✅ JSON saved to: ${filePath}`);
    } else if (format === "csv") {
      const csvWriter = new CsvWriter();
      const data: unknown[][] = [];

      data.push(["Financial Data Export"]);
      data.push(["Ticker", result.ticker]);
      data.push(["Period", result.period]);
      data.push([]);

      if (result.overview) {
        data.push(["Overview Data"]);
        data.push(["Currency", String(result.overview.currency)]);
        data.push(["Market Cap", String(result.overview.marketCap)]);
        data.push(["PE Ratio", String(result.overview.trailingPE)]);
        data.push([]);
      }

      if (result.incomeStatement) {
        data.push(["Income Statement"]);
        const dates = Object.keys(result.incomeStatement);
        if (dates.length > 0) {
          const firstDate = dates[0];
          if (firstDate !== undefined) {
            const firstStmt = result.incomeStatement[firstDate];
            if (firstStmt) {
              const keys = Object.keys(firstStmt);
              data.push(["Date", ...keys]);
              for (const date of dates) {
                const stmt = result.incomeStatement[date];
                if (stmt) {
                  data.push([date, ...keys.map((k) => String(stmt[k] ?? ""))]);
              }
            }
          }
        }
      }

      csvWriter.writeFile(filePath, data);
      console.log(`\n✅ CSV saved to: ${filePath}`);
    } else if (format === "excel") {
      const excelWriter = new ExcelWriter();
      const sheets = [];

      const overviewData: unknown[][] = [["Overview Data"]];
      if (result.overview) {
        overviewData.push(["Currency", result.overview.currency]);
        overviewData.push(["Market Cap", result.overview.marketCap]);
        overviewData.push(["PE Ratio", result.overview.trailingPE]);
        overviewData.push(["Dividend Yield", result.overview.dividendYield]);
      }
      sheets.push({ name: "Overview", data: overviewData });

      if (result.incomeStatement) {
        const incomeData: unknown[][] = [["Income Statement"]];
        const dates = Object.keys(result.incomeStatement);
        if (dates.length > 0) {
          const firstStmt = result.incomeStatement[dates[0]];
          if (firstStmt) {
            const keys = Object.keys(firstStmt);
            incomeData.push(["Date", ...keys]);
            for (const date of dates) {
              const stmt = result.incomeStatement[date];
              if (stmt) {
                incomeData.push([date, ...keys.map((k) => stmt[k] ?? "")]);
              }
            }
          }
        }
        sheets.push({ name: "Income", data: incomeData });
      }

      if (result.balanceSheet) {
        const balanceData: unknown[][] = [["Balance Sheet"]];
        const dates = Object.keys(result.balanceSheet);
        if (dates.length > 0) {
          const firstDate = dates[0];
          if (firstDate !== undefined) {
            const firstStmt = result.balanceSheet[firstDate];
            if (firstStmt) {
              const keys = Object.keys(firstStmt);
              balanceData.push(["Date", ...keys]);
              for (const date of dates) {
                const stmt = result.balanceSheet[date];
                if (stmt) {
                  balanceData.push([date, ...keys.map((k) => stmt[k] ?? "")]);
              }
            }
          }
        }
        sheets.push({ name: "Balance", data: balanceData });
      }

      excelWriter.writeFile(filePath, sheets);
      console.log(`\n✅ Excel saved to: ${filePath}`);
    }
  }

  console.log(`\nData sources:`);
  console.log(`  Overview: ${result.sources.overview || "N/A"}`);
  console.log(`  Income Statement: ${result.sources.incomeStatement || "N/A"}`);
  console.log(`  Balance Sheet: ${result.sources.balanceSheet || "N/A"}`);
  console.log(`  Cash Flow: ${result.sources.cashFlow || "N/A"}`);
  console.log(`  Peers: ${result.sources.peers || "N/A"}`);
  console.log("");
}

program
  .name("financial-data")
  .description("Fetch and export financial data from Yahoo Finance")
  .version("1.0.0");

program
  .command("fetch <ticker>")
  .description("Fetch financial data for a company")
  .option("-p, --period <period>", "Period (annual or quarterly)", "quarterly")
  .option("-o, --output <path>", "Output directory", "./data/financial_data")
  .option("-f, --format <format>", "Output format (json, csv, excel)", "json")
  .action(async (ticker: string, options: Record<string, string>) => {
    try {
      await fetchFinancialData({
        ticker,
        period: (options["period"] as "annual" | "quarterly") ?? "quarterly",
        output: options["output"],
        format: (options["format"] as "json" | "csv" | "excel") ?? "json",
      });
    } catch (error) {
      console.error("Error:", error instanceof Error ? error.message : error);
      process.exit(1);
    }
  });

program.parse();
