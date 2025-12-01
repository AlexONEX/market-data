import { FinancialDataOrchestrator } from "./services/financialDataOrchestrator.js";

async function testFinancialData(): Promise<void> {
  const orchestrator = new FinancialDataOrchestrator();

  console.log("\n=== Testing Financial Data Orchestrator ===\n");

  const ticker = "AAPL";

  console.log(`Fetching data for ${ticker}...\n`);

  const result = await orchestrator.getCompanyData(ticker, "annual");

  console.log("Result structure:");
  console.log(`  ticker: ${result.ticker}`);
  console.log(`  period: ${result.period}`);

  console.log("\nOverview data:");
  if (result.overview) {
    console.log(`  currency: ${result.overview.currency}`);
    console.log(`  marketCap: ${result.overview.marketCap}`);
    console.log(`  trailingPE: ${result.overview.trailingPE}`);
    console.log(`  dividendYield: ${result.overview.dividendYield}`);
  } else {
    console.log("  No overview data");
  }

  console.log("\nIncome Statement:");
  if (result.incomeStatement) {
    const dates = Object.keys(result.incomeStatement);
    console.log(`  Found ${dates.length} statements`);
    if (dates.length > 0) {
      const firstDate = dates[0];
      if (firstDate !== undefined) {
        const firstStmt = result.incomeStatement[firstDate];
        console.log(`  First date: ${firstDate}`);
        console.log(`  Total Revenue: ${firstStmt?.["totalRevenue"]}`);
        console.log(`  Net Income: ${firstStmt?.["netIncome"]}`);
      }
    }
  } else {
    console.log("  No income statement data");
  }

  console.log("\nBalance Sheet:");
  if (result.balanceSheet) {
    const dates = Object.keys(result.balanceSheet);
    console.log(`  Found ${dates.length} statements`);
  } else {
    console.log("  No balance sheet data");
  }

  console.log("\nCash Flow:");
  if (result.cashFlow) {
    const dates = Object.keys(result.cashFlow);
    console.log(`  Found ${dates.length} statements`);
  } else {
    console.log("  No cash flow data");
  }

  console.log("\nData Sources:");
  console.log(`  overview: ${result.sources.overview || "N/A"}`);
  console.log(`  incomeStatement: ${result.sources.incomeStatement || "N/A"}`);
  console.log(`  balanceSheet: ${result.sources.balanceSheet || "N/A"}`);
  console.log(`  cashFlow: ${result.sources.cashFlow || "N/A"}`);
  console.log(`  peers: ${result.sources.peers || "N/A"}`);

  console.log("\n✅ Test completed successfully\n");
}

testFinancialData().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
