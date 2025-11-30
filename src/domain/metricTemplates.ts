export type MetricDataType = "number" | "percentage" | "string" | "currency" | "date";

export interface MetricDefinition {
  readonly key: string;
  readonly label: string;
  readonly dataType: MetricDataType;
  readonly format?: string;
}

export interface MetricCategory {
  readonly name: string;
  readonly metrics: readonly MetricDefinition[];
}

const overviewMetrics: MetricDefinition[] = [
  { key: "marketCap", label: "Market Cap", dataType: "currency" },
  { key: "peRatio", label: "P/E Ratio", dataType: "number" },
  { key: "psRatio", label: "P/S Ratio", dataType: "number" },
  { key: "pbRatio", label: "P/B Ratio", dataType: "number" },
  { key: "dividendYield", label: "Dividend Yield", dataType: "percentage" },
];

const profitabilityMetrics: MetricDefinition[] = [
  { key: "grossMargin", label: "Gross Margin", dataType: "percentage" },
  { key: "operatingMargin", label: "Operating Margin", dataType: "percentage" },
  { key: "netMargin", label: "Net Margin", dataType: "percentage" },
  { key: "roe", label: "Return on Equity", dataType: "percentage" },
  { key: "roa", label: "Return on Assets", dataType: "percentage" },
  { key: "roic", label: "Return on Invested Capital", dataType: "percentage" },
];

const liquidityMetrics: MetricDefinition[] = [
  { key: "currentRatio", label: "Current Ratio", dataType: "number" },
  { key: "quickRatio", label: "Quick Ratio", dataType: "number" },
  { key: "cashRatio", label: "Cash Ratio", dataType: "number" },
  { key: "workingCapital", label: "Working Capital", dataType: "currency" },
];

const solvencyMetrics: MetricDefinition[] = [
  { key: "debtToEquity", label: "Debt to Equity", dataType: "number" },
  { key: "debtToAssets", label: "Debt to Assets", dataType: "percentage" },
  { key: "interestCoverage", label: "Interest Coverage", dataType: "number" },
  { key: "debtRatio", label: "Debt Ratio", dataType: "percentage" },
];

const efficiencyMetrics: MetricDefinition[] = [
  { key: "assetTurnover", label: "Asset Turnover", dataType: "number" },
  { key: "receivableTurnover", label: "Receivable Turnover", dataType: "number" },
  { key: "inventoryTurnover", label: "Inventory Turnover", dataType: "number" },
  { key: "payableTurnover", label: "Payable Turnover", dataType: "number" },
];

const growthMetrics: MetricDefinition[] = [
  { key: "revenueGrowth", label: "Revenue Growth", dataType: "percentage" },
  { key: "earningsGrowth", label: "Earnings Growth", dataType: "percentage" },
  { key: "ebitdaGrowth", label: "EBITDA Growth", dataType: "percentage" },
  { key: "bookValueGrowth", label: "Book Value Growth", dataType: "percentage" },
];

export const metricCategories: readonly MetricCategory[] = [
  { name: "Overview", metrics: overviewMetrics },
  { name: "Profitability", metrics: profitabilityMetrics },
  { name: "Liquidity", metrics: liquidityMetrics },
  { name: "Solvency", metrics: solvencyMetrics },
  { name: "Efficiency", metrics: efficiencyMetrics },
  { name: "Growth", metrics: growthMetrics },
];

export const allMetrics: readonly MetricDefinition[] = metricCategories.flatMap(
  (cat) => cat.metrics,
);

export function getMetricsByCategory(categoryName: string): MetricDefinition[] {
  const category = metricCategories.find((cat) => cat.name === categoryName);
  return category?.metrics ? Array.from(category.metrics) : [];
}

export function getMetricDefinition(metricKey: string): MetricDefinition | undefined {
  return allMetrics.find((m) => m.key === metricKey);
}

export function formatMetricValue(value: unknown, dataType: MetricDataType): string {
  if (value === null || value === undefined) {
    return "N/A";
  }

  if (typeof value === "string") {
    return value;
  }

  if (typeof value !== "number") {
    return String(value);
  }

  const numValue = value;

  switch (dataType) {
    case "percentage":
      return `${(numValue * 100).toFixed(2)}%`;
    case "currency":
      return `$${numValue.toLocaleString("en-US", { maximumFractionDigits: 2 })}`;
    case "number":
      return numValue.toLocaleString("en-US", { maximumFractionDigits: 4 });
    case "date":
      return new Date(numValue).toISOString().split("T")[0] || "N/A";
    case "string":
      return String(numValue);
    default:
      return String(numValue);
  }
}
