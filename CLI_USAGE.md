# Market Data Analysis CLI - TypeScript Version

Interactive CLI tool for analyzing bond yields and stock financial data.

## Installation

```bash
npm install
npm run build
```

## Running the CLI

### Development Mode (with hot reload)
```bash
npm run dev
```

### Production Mode
```bash
npm start
# or
node dist/cli/index.js
```

### As npm bin command (after install -g)
```bash
npm install -g .
market-data
```

## Features

### 1. Bond Yields Analysis (TIR Calculation)
Calculate Time-to-Maturity Internal Rates (TIR) for bonds using bisection method with Decimal.js (50-digit precision).

**Inputs:**
- Bond tickers (comma-separated, e.g., AL30,AL29,GD30)
- Output format (CSV or JSON)
- Output file path (optional)

**Output:**
- Ticker, Price, TIR (%), TEM (%), Maturity Date

### 2. Stock Financial Data
Fetch financial statements (balance sheet, income statement, cash flow) from stockanalysis.com with retry logic.

**Inputs:**
- Stock ticker (e.g., VIST, AAPL)
- Report period (annual or quarterly)
- Output format (CSV or JSON)
- Output file path (optional)

**Output:**
- Financial data sections formatted as structured tables

### 3. Combined Analysis
Run both bond yields and stock data analysis simultaneously, saving results to organized directory structure.

**Inputs:**
- Bond tickers (comma-separated)
- Stock ticker
- Stock report period
- Output format (CSV or JSON)
- Output directory (optional)

**Output:**
- Directory structure with `bonds.csv/json` and `stock.csv/json`

## Architecture

### Project Structure
```
src/
├── cli/                          # CLI interface layer
│   ├── index.ts                 # Entry point with event loop
│   ├── prompts.ts               # Interactive inquirer prompts
│   ├── handler.ts               # Business logic handlers
│   ├── types.ts                 # Type definitions
│   └── index.exports.ts         # Barrel export
├── services/                     # Orchestration & business logic
│   ├── bondYieldService.ts      # TIR calculation logic
│   ├── stockDataService.ts      # Stock data fetching
│   └── financialDataOrchestrator.ts
├── gateway/                      # External API integration
│   ├── httpClient.ts            # HTTP client with retry logic
│   ├── data912Connector.ts      # Bond data API
│   ├── stockanalysisConnector.ts # Stock financial data scraper
│   └── googleSheetsClient.ts    # Google Sheets integration
├── domain/                       # Pure business logic & math
│   ├── financialMath.ts         # TIR/TEM calculation (bisection)
│   ├── validators.ts            # Input validation
│   ├── types.ts                 # Domain types (Result<T,E> pattern)
│   └── models.ts                # Bond, Stock, Financial data models
└── utils/                        # Utilities
    ├── csvWriter.ts             # CSV output with escaping
    ├── jsonWriter.ts            # JSON output formatting
    ├── sheetsFormatter.ts       # Data formatting for reports
    ├── logger.ts                # Pino logging
    └── config.ts                # Configuration management
```

### Key Technologies
- **Language:** TypeScript with strict mode (`noImplicitAny`, `strictNullChecks`)
- **Runtime:** Node.js 18+ with ESM modules
- **CLI:** Inquirer.js for interactive prompts
- **Logging:** Pino for structured logging
- **Math:** Decimal.js for financial calculations (50-digit precision)
- **HTTP:** Axios with exponential backoff retry logic
- **Scraping:** Cheerio for HTML parsing
- **Quality:** ESLint + Prettier + TypeScript strict compiler

## Financial Calculations

### TIR (Time-to-Maturity Internal Rate)
- Algorithm: Bisection method with sign change detection
- Precision: 50-digit with Decimal.js
- Formula: NPV = Σ(cashflow / (1 + rate)^years) = 0
- Settlement date: Current date (November 2025)
- Input: Bond tickers, prices (per 100 nominal), future cashflows

### TEM (Monthly Equivalent Rate)
- Derived from annualized TIR
- Formula: TEM = (1 + TIR)^(1/12) - 1

## Data Sources
- **Bonds:** data912.com API (Argentine bonds)
- **Stocks:** stockanalysis.com (web scraping with Cheerio)
- **Google Sheets:** Integration for data export

## Error Handling
- Graceful degradation: Continues processing on partial failures
- Retry logic: Exponential backoff (3 attempts, 2-8 second waits)
- Result pattern: `Result<T, Error>` instead of exceptions
- Structured logging: All operations logged with context

## Development

### Quality Checks
```bash
npm run type-check    # TypeScript strict validation
npm run lint          # ESLint rules
npm run format:check  # Prettier formatting
npm run fix           # Auto-fix lint and format issues
```

### Building
```bash
npm run build         # Compile TypeScript → dist/
```

### Testing
```bash
npm test              # Run all tests
npm run test:watch   # Watch mode
npm run test:coverage # Coverage report
```

## Example Usage

### Interactive CLI
```bash
npm run dev

📊 Market Data Analysis Tool

? What would you like to do?
❯ Calculate Bond Yields (TIR)
  Fetch Stock Financial Data
  Combined Analysis (Bonds + Stock)
  Exit
```

### CLI Output Examples

**CSV Output (Bonds):**
```
Ticker,Price,TIR (%),TEM (%),Maturity Date
AL30,68.50,9.05,0.73,2026-01-01
AL29,72.00,8.95,0.72,2026-06-01
```

**JSON Output (Stocks):**
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

## Performance
- Bond yield calculation: < 100ms per bond
- Stock data fetch: 3-10s (includes retries, API latency)
- Combined analysis: ~10-15s (parallel processing where possible)

## Troubleshooting

### CLI hangs
Ensure stdin/stdout are properly connected. For automated inputs, use the programmatic API directly instead of interactive mode.

### Stock data not available
Check API availability at stockanalysis.com. Some tickers may not have data. The tool will retry 3 times before failing gracefully.

### Bond yield calculation errors
Verify cashflows are provided for the settlement date (today). Bonds without future cashflows are skipped with warning logs.

## License
MIT
