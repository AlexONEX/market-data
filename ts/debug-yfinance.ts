import YahooFinanceType from "yahoo-finance2";

async function debugYahooFinance(): Promise<void> {
  const yf = new YahooFinanceType();

  console.log("Attempting quote fetch...");

  try {
    const quote = await yf.quote("AAPL");
    console.log("Quote type:", typeof quote);
    console.log("Quote is null:", quote === null);
    console.log("Quote keys:", quote ? Object.keys(quote).slice(0, 20) : "N/A");
    console.log("Full quote:", JSON.stringify(quote, null, 2).substring(0, 500));
  } catch (error) {
    console.error("Error fetching quote:", error instanceof Error ? error.message : error);
  }

  console.log("\nAttempting quoteSummary with incomeStatementHistory...");
  try {
    const summary = await yf.quoteSummary("AAPL", {
      modules: ["incomeStatementHistory" as never],
    });
    console.log("Summary type:", typeof summary);
    console.log("Summary is null:", summary === null);
    const summaryObj = summary as Record<string, unknown>;
    console.log("Summary keys:", Object.keys(summaryObj).slice(0, 10));
    const incomeHistory = summaryObj["incomeStatementHistory"] as Record<string, unknown> | undefined;
    if (incomeHistory) {
      console.log("Income history keys:", Object.keys(incomeHistory));
      const statements = incomeHistory["incomeStatementHistory"] as Array<unknown> | undefined;
      if (Array.isArray(statements) && statements.length > 0) {
        console.log(`Found ${statements.length} statements`);
        console.log("First statement:", JSON.stringify(statements[0], null, 2).substring(0, 300));
      }
    }
  } catch (error) {
    console.error("Error fetching quoteSummary:", error instanceof Error ? error.message : error);
  }
}

debugYahooFinance().catch((error) => {
  console.error("Fatal error:", error);
  process.exit(1);
});
