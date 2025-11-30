import { TIRResult } from "../domain";
import { StockDataFromSource } from "../gateway";

export interface SheetRow {
  readonly [key: string]: unknown;
}

export type FormattedSheets = Record<string, readonly SheetRow[]>;

export class SheetsFormatter {
  formatBondYields(results: readonly TIRResult[]): readonly SheetRow[] {
    return results.map((result) => ({
      ticker: result.ticker,
      price: result.price.toFixed(2),
      tir: (result.tir * 100).toFixed(2) + "%",
      tem: result.tem ? (result.tem * 100).toFixed(2) + "%" : "N/A",
      maturity_date: result.maturityDate.toISOString().split("T")[0],
    }));
  }

  formatStockData(data: StockDataFromSource): readonly SheetRow[] {
    const rows: SheetRow[] = [];

    if (data.overview) {
      rows.push({
        section: "Overview",
        ticker: data.overview.ticker,
        name: data.overview.name,
        sector: data.overview.sector || "N/A",
        market_cap: data.overview.marketCap || "N/A",
        pe_ratio: data.overview.peRatio || "N/A",
      });
    }

    if (data.incomeStatement && data.incomeStatement.length > 0) {
      const latestStatement = data.incomeStatement[0];
      rows.push({
        section: "Income Statement",
        ...latestStatement,
      });
    }

    if (data.balanceSheet && data.balanceSheet.length > 0) {
      const latestStatement = data.balanceSheet[0];
      rows.push({
        section: "Balance Sheet",
        ...latestStatement,
      });
    }

    if (data.cashFlow && data.cashFlow.length > 0) {
      const latestStatement = data.cashFlow[0];
      rows.push({
        section: "Cash Flow",
        ...latestStatement,
      });
    }

    if (data.ratios && data.ratios.length > 0) {
      const latestRatios = data.ratios[0];
      rows.push({
        section: "Ratios",
        ...latestRatios,
      });
    }

    return rows;
  }

  formatCombinedReport(
    bondYields: readonly TIRResult[],
    stockData?: StockDataFromSource,
  ): FormattedSheets {
    const sheets: FormattedSheets = {
      "Bond Yields": this.formatBondYields(bondYields),
    };

    if (stockData) {
      sheets["Stock Financials"] = this.formatStockData(stockData);
    }

    return sheets;
  }
}
