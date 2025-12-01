import { YahooFinanceConnector } from "./gateway/yahooFinanceConnector";

async function testYahooFinance(): Promise<void> {
  const connector = new YahooFinanceConnector();

  console.log("\n=== Testing Yahoo Finance Connector ===\n");

  const ticker = "AAPL";

  console.log(`Testing with ticker: ${ticker}\n`);

  console.log("1. Getting Quote...");
  const quote = await connector.getQuote(ticker);
  console.log("Quote data:", JSON.stringify(quote, null, 2));

  console.log("\n2. Getting Income Statement (Annual)...");
  const incomeAnnual = await connector.getIncomeStatement(ticker, "annual");
  if (incomeAnnual) {
    const dates = Object.keys(incomeAnnual);
    console.log(`Found ${dates.length} income statements`);
    if (dates.length > 0) {
      console.log(`First statement (${dates[0]}):`, JSON.stringify(incomeAnnual[dates[0]], null, 2).substring(0, 300));
    }
  } else {
    console.log("No income statement data");
  }

  console.log("\n3. Getting Balance Sheet (Annual)...");
  const balanceAnnual = await connector.getBalanceSheet(ticker, "annual");
  if (balanceAnnual) {
    const dates = Object.keys(balanceAnnual);
    console.log(`Found ${dates.length} balance sheets`);
    if (dates.length > 0) {
      console.log(`First statement (${dates[0]}):`, JSON.stringify(balanceAnnual[dates[0]], null, 2).substring(0, 300));
    }
  } else {
    console.log("No balance sheet data");
  }

  console.log("\n4. Getting Cash Flow (Annual)...");
  const cashFlowAnnual = await connector.getCashFlow(ticker, "annual");
  if (cashFlowAnnual) {
    const dates = Object.keys(cashFlowAnnual);
    console.log(`Found ${dates.length} cash flow statements`);
    if (dates.length > 0) {
      console.log(`First statement (${dates[0]}):`, JSON.stringify(cashFlowAnnual[dates[0]], null, 2).substring(0, 300));
    }
  } else {
    console.log("No cash flow data");
  }

  console.log("\n5. Getting Income Statement (Quarterly)...");
  const incomeQuarterly = await connector.getIncomeStatement(ticker, "quarterly");
  if (incomeQuarterly) {
    const dates = Object.keys(incomeQuarterly);
    console.log(`Found ${dates.length} quarterly income statements`);
  } else {
    console.log("No quarterly income statement data");
  }
}

testYahooFinance().catch((error) => {
  console.error("Error:", error);
  process.exit(1);
});
