# Testing CLI and Data Fetcher

## Build & Setup

```bash
# Install dependencies
npm install

# Build TypeScript to JavaScript
npm run build

# Verify build successful
ls -lh dist/cli/index.js
```

## Test CLI - Interactive Mode

```bash
# Start interactive CLI
npm run dev
```

Opciones en el CLI:
1. Calculate Bond Yields (TIR)
2. Fetch Stock Financial Data
3. Combined Analysis (Bonds + Stock)
4. Exit

Ejemplo de input:
- Tickers: AL30,AL29,GD30
- Format: csv o json
- Output path: data/output.csv (opcional, presionar Enter para default)

---

## Test CLI - Programmatic Mode

```bash
# Test handlers directly (sin interfaz interactiva)
npx tsx test-cli.ts
```

Crea archivo `test-cli.ts`:

```typescript
import path from "path";
import { handleBondYields, handleStockData, handleCombined } from "./src/cli/handler";

async function test() {
  console.log("Testing Bond Yields...");
  await handleBondYields({
    tickers: ["AL30", "AL29"],
    outputFormat: "csv",
    outputPath: "data/bonds.csv",
  });

  console.log("Testing Stock Data...");
  await handleStockData({
    ticker: "VIST",
    period: "annual",
    outputFormat: "csv",
    outputPath: "data/stock.csv",
  });

  console.log("Testing Combined...");
  await handleCombined({
    bondTickers: ["AL30"],
    stockTicker: "VIST",
    stockPeriod: "annual",
    outputFormat: "csv",
    outputPath: "data/combined",
  });

  console.log("✅ All tests passed");
}

test().catch(console.error);
```

---

## Test Data Fetcher - Bond Yields

```bash
npx tsx << 'EOF'
import { BondYieldService } from "./src/services/bondYieldService";

const service = new BondYieldService();
const result = await service.calculateBondYields([
  { ticker: "AL30", price: 68.50, cashflows: [
    { date: new Date("2026-01-01"), amount: 10 },
    { date: new Date("2026-07-01"), amount: 100 }
  ]},
  { ticker: "AL29", price: 72.00, cashflows: [
    { date: new Date("2026-06-01"), amount: 10 },
    { date: new Date("2027-01-01"), amount: 100 }
  ]}
]);

console.log("Bond Yields Result:");
console.log(JSON.stringify(result, null, 2));
EOF
```

---

## Test Data Fetcher - Stock Data

```bash
npx tsx << 'EOF'
import { StockDataService } from "./src/services/stockDataService";

const service = new StockDataService();
const result = await service.fetchStockData({
  ticker: "VIST",
  period: "annual"
});

console.log("Stock Data Result:");
console.log(JSON.stringify(result, null, 2));
EOF
```

---

## Test Data Fetcher - Combined

```bash
npx tsx << 'EOF'
import { FinancialDataOrchestrator } from "./src/services/financialDataOrchestrator";

const orchestrator = new FinancialDataOrchestrator();
const result = await orchestrator.fetchAll(
  [
    { ticker: "AL30", price: 68.50, cashflows: [] },
    { ticker: "AL29", price: 72.00, cashflows: [] }
  ],
  { ticker: "VIST", period: "annual" }
);

console.log("Combined Result:");
console.log(`Bonds: ${result.bondYields?.results.length ?? 0}`);
console.log(`Stock Success: ${result.stockData?.success}`);
console.log(`Execution Time: ${result.executionTime}ms`);
EOF
```

---

## Test Quality Checks

```bash
# Type checking
npm run type-check

# Linting
npm run lint

# Formatting check
npm run format:check

# All checks
npm run check

# Auto-fix issues
npm run fix
```

---

## Full Test Suite

```bash
# Run all unit tests
npm test

# Watch mode (rerun on file changes)
npm run test:watch

# Coverage report
npm run test:coverage
```

---

## Run Production Binary

```bash
# Build first
npm run build

# Run compiled CLI
node dist/cli/index.js

# Or use npm start
npm start
```

---

## Verify Output Files

```bash
# Check generated CSV
cat data/bonds.csv

# Check generated JSON
cat data/stock.json
jq . data/combined/bonds.json  # if jq installed
```

---

## Performance Test

```bash
# Time the combined analysis
time npx tsx << 'EOF'
import { FinancialDataOrchestrator } from "./src/services/financialDataOrchestrator";

const orchestrator = new FinancialDataOrchestrator();
await orchestrator.fetchAll(
  [{ ticker: "AL30", price: 100, cashflows: [] }],
  { ticker: "VIST", period: "annual" }
);
EOF
```

---

## Troubleshooting

### CLI hangs on input
```bash
# Use timeout to prevent hanging
timeout 30 npx tsx test-cli.ts
```

### Check logs
```bash
# Logs are output to stdout with Pino formatting
# To parse as JSON:
npx tsx src/cli/index.ts 2>&1 | jq .
```

### Verify TypeScript compilation
```bash
# Show compilation output
npx tsc --listFiles --noEmit
```

---

## Expected Output

### Bond Yields CSV
```
Ticker,Price,TIR (%),TEM (%),Maturity Date
AL30,68.50,9.05,0.73,2026-01-01
AL29,72.00,8.95,0.72,2026-06-01
```

### Stock Data JSON
```json
{
  "ticker": "VIST",
  "period": "annual",
  "data": [
    {
      "section": "Balance Sheet",
      "period": "2023",
      "values": { ... }
    }
  ]
}
```
