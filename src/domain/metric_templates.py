"""
Metric templates for different sectors and asset types.
Defines which metrics to extract and how to organize them for each type of company.
"""

from dataclasses import dataclass

# ============================================================================
# METRIC DEFINITIONS
# ============================================================================


@dataclass
class MetricDefinition:
    """Definition of a single metric."""

    # Display name
    name: str

    # Key path in the data (e.g., "income_statement.total_revenue")
    data_key: str

    # Type of metric for formatting
    metric_type: str  # "currency", "percentage", "ratio", "count", "shares", "string"

    # Alternative keys to try if primary key not found
    alt_keys: list[str] = None

    # Description for documentation
    description: str = ""

    def __post_init__(self):
        if self.alt_keys is None:
            self.alt_keys = []


@dataclass
class MetricCategory:
    """Group of related metrics."""

    name: str  # e.g., "Profitability", "Liquidity"
    metrics: list[MetricDefinition]
    description: str = ""


@dataclass
class SectorTemplate:
    """Template defining metrics for a specific sector."""

    name: str  # e.g., "Technology", "Energy", "Finance"
    sectors: list[str]  # List of sector names this applies to
    categories: dict[str, MetricCategory]  # {category_name: MetricCategory}
    description: str = ""


# ============================================================================
# UNIVERSAL METRICS (apply to all sectors)
# ============================================================================

UNIVERSAL_METRICS = {
    "Overview": MetricCategory(
        name="Overview",
        metrics=[
            MetricDefinition(
                name="Company Name",
                data_key="overview.name",
                metric_type="string",
                alt_keys=["overview.longName"],
                description="Official company name",
            ),
            MetricDefinition(
                name="Sector",
                data_key="overview.sector",
                metric_type="string",
                description="Industry sector",
            ),
            MetricDefinition(
                name="Industry",
                data_key="overview.industry",
                metric_type="string",
                description="Specific industry",
            ),
            MetricDefinition(
                name="Market Cap",
                data_key="overview.marketCap",
                metric_type="currency",
                alt_keys=["overview.market_cap"],
                description="Total market capitalization",
            ),
            MetricDefinition(
                name="Employees",
                data_key="overview.fullTimeEmployees",
                metric_type="count",
                alt_keys=["overview.employees"],
                description="Number of employees",
            ),
        ],
    ),
    "Income Statement": MetricCategory(
        name="Income Statement",
        metrics=[
            MetricDefinition(
                name="Total Revenue",
                data_key="income_statement.Total Revenue",
                metric_type="currency",
                alt_keys=[
                    "income_statement.totalRevenue",
                    "income_statement.Operating Revenue",
                ],
                description="Total company revenue",
            ),
            MetricDefinition(
                name="Cost of Revenue",
                data_key="income_statement.Cost Of Revenue",
                metric_type="currency",
                alt_keys=["income_statement.costOfRevenue"],
                description="Cost of goods sold / Cost of revenue",
            ),
            MetricDefinition(
                name="Gross Profit",
                data_key="income_statement.Gross Profit",
                metric_type="currency",
                alt_keys=["income_statement.grossProfit"],
                description="Revenue minus cost of revenue",
            ),
            MetricDefinition(
                name="Operating Income",
                data_key="income_statement.Operating Income",
                metric_type="currency",
                alt_keys=["income_statement.operatingIncome"],
                description="Income from operations",
            ),
            MetricDefinition(
                name="EBITDA",
                data_key="income_statement.EBITDA",
                metric_type="currency",
                alt_keys=["income_statement.ebitda"],
                description="Earnings before interest, taxes, depreciation, amortization",
            ),
            MetricDefinition(
                name="Net Income",
                data_key="income_statement.Net Income",
                metric_type="currency",
                alt_keys=["income_statement.netIncome"],
                description="Bottom line profit",
            ),
        ],
    ),
    "Balance Sheet": MetricCategory(
        name="Balance Sheet",
        metrics=[
            MetricDefinition(
                name="Total Assets",
                data_key="balance_sheet.Total Assets",
                metric_type="currency",
                alt_keys=["balance_sheet.totalAssets"],
                description="Total company assets",
            ),
            MetricDefinition(
                name="Total Liabilities",
                data_key="balance_sheet.Total Liabilities",
                metric_type="currency",
                alt_keys=["balance_sheet.totalLiabilities"],
                description="Total company liabilities",
            ),
            MetricDefinition(
                name="Total Equity",
                data_key="balance_sheet.Total Equity",
                metric_type="currency",
                alt_keys=[
                    "balance_sheet.totalEquity",
                    "balance_sheet.Stockholders Equity",
                ],
                description="Shareholders' equity",
            ),
            MetricDefinition(
                name="Current Assets",
                data_key="balance_sheet.Current Assets",
                metric_type="currency",
                alt_keys=["balance_sheet.currentAssets"],
                description="Assets expected to be converted to cash within 1 year",
            ),
            MetricDefinition(
                name="Current Liabilities",
                data_key="balance_sheet.Current Liabilities",
                metric_type="currency",
                alt_keys=["balance_sheet.currentLiabilities"],
                description="Liabilities due within 1 year",
            ),
        ],
    ),
    "Valuation": MetricCategory(
        name="Valuation",
        metrics=[
            MetricDefinition(
                name="P/E Ratio",
                data_key="overview.trailingPE",
                metric_type="ratio",
                alt_keys=["overview.peRatio"],
                description="Price to earnings ratio",
            ),
            MetricDefinition(
                name="P/B Ratio",
                data_key="overview.priceToBook",
                metric_type="ratio",
                alt_keys=["overview.pb"],
                description="Price to book ratio",
            ),
            MetricDefinition(
                name="EPS (Trailing)",
                data_key="overview.trailingEps",
                metric_type="currency",
                alt_keys=["overview.eps"],
                description="Earnings per share (trailing 12 months)",
            ),
            MetricDefinition(
                name="Dividend Yield",
                data_key="overview.dividendYield",
                metric_type="percentage",
                alt_keys=["overview.yield"],
                description="Annual dividend yield",
            ),
        ],
    ),
}

# ============================================================================
# SECTOR-SPECIFIC TEMPLATES
# ============================================================================

TECHNOLOGY_TEMPLATE = SectorTemplate(
    name="Technology",
    sectors=["Technology", "Communication Services"],
    description="Template for tech companies - focus on growth, user metrics, R&D",
    categories={
        **UNIVERSAL_METRICS,
        "Growth Metrics": MetricCategory(
            name="Growth Metrics",
            metrics=[
                MetricDefinition(
                    name="Revenue Growth (YoY)",
                    data_key="ratios.Revenue Growth (YoY)",
                    metric_type="percentage",
                    alt_keys=["ratios.revenueGrowth"],
                    description="Year-over-year revenue growth",
                ),
                MetricDefinition(
                    name="Operating Margin",
                    data_key="ratios.Operating Margin",
                    metric_type="percentage",
                    alt_keys=["ratios.operatingMargin"],
                    description="Operating income / revenue",
                ),
                MetricDefinition(
                    name="Net Margin",
                    data_key="ratios.Net Margin",
                    metric_type="percentage",
                    alt_keys=["ratios.netMargin"],
                    description="Net income / revenue",
                ),
            ],
        ),
        "R&D & Innovation": MetricCategory(
            name="R&D & Innovation",
            metrics=[
                MetricDefinition(
                    name="R&D Expense",
                    data_key="income_statement.Research And Development",
                    metric_type="currency",
                    alt_keys=["income_statement.rdExpense"],
                    description="Research and development spending",
                ),
                MetricDefinition(
                    name="R&D % of Revenue",
                    data_key="ratios.R&D % of Revenue",
                    metric_type="percentage",
                    description="R&D spending as % of revenue",
                ),
            ],
        ),
    },
)

ENERGY_TEMPLATE = SectorTemplate(
    name="Energy",
    sectors=["Energy", "Oil & Gas"],
    description="Template for energy/oil companies - focus on production, reserves, margins",
    categories={
        **UNIVERSAL_METRICS,
        "Production & Operations": MetricCategory(
            name="Production & Operations",
            metrics=[
                MetricDefinition(
                    name="Operating Margin",
                    data_key="ratios.Operating Margin",
                    metric_type="percentage",
                    alt_keys=["ratios.operatingMargin"],
                    description="Operating income / revenue",
                ),
                MetricDefinition(
                    name="EBITDA Margin",
                    data_key="ratios.EBITDA Margin",
                    metric_type="percentage",
                    alt_keys=["ratios.ebitdaMargin"],
                    description="EBITDA / revenue",
                ),
            ],
        ),
        "Financial Health": MetricCategory(
            name="Financial Health",
            metrics=[
                MetricDefinition(
                    name="Debt to Equity",
                    data_key="ratios.Debt to Equity",
                    metric_type="ratio",
                    alt_keys=["ratios.debtToEquity"],
                    description="Total debt / total equity",
                ),
                MetricDefinition(
                    name="Current Ratio",
                    data_key="ratios.Current Ratio",
                    metric_type="ratio",
                    alt_keys=["ratios.currentRatio"],
                    description="Current assets / current liabilities",
                ),
                MetricDefinition(
                    name="Free Cash Flow",
                    data_key="cash_flow.Free Cash Flow",
                    metric_type="currency",
                    alt_keys=["cash_flow.freeCashFlow"],
                    description="Operating cash flow minus capex",
                ),
            ],
        ),
    },
)

FINANCE_TEMPLATE = SectorTemplate(
    name="Finance",
    sectors=["Financial Services", "Finance"],
    description="Template for financial institutions - focus on profitability, capital ratios",
    categories={
        **UNIVERSAL_METRICS,
        "Profitability": MetricCategory(
            name="Profitability",
            metrics=[
                MetricDefinition(
                    name="ROE (Return on Equity)",
                    data_key="ratios.Return on Equity",
                    metric_type="percentage",
                    alt_keys=["ratios.roe"],
                    description="Net income / shareholders' equity",
                ),
                MetricDefinition(
                    name="ROA (Return on Assets)",
                    data_key="ratios.Return on Assets",
                    metric_type="percentage",
                    alt_keys=["ratios.roa"],
                    description="Net income / total assets",
                ),
                MetricDefinition(
                    name="Net Interest Margin",
                    data_key="ratios.Net Interest Margin",
                    metric_type="percentage",
                    alt_keys=["ratios.nim"],
                    description="Net interest income / earning assets",
                ),
            ],
        ),
        "Capital & Risk": MetricCategory(
            name="Capital & Risk",
            metrics=[
                MetricDefinition(
                    name="Capital Ratio",
                    data_key="ratios.Capital Ratio",
                    metric_type="percentage",
                    alt_keys=["ratios.tier1Ratio"],
                    description="Capital / total assets",
                ),
                MetricDefinition(
                    name="Loan Loss Reserve",
                    data_key="balance_sheet.Loan Loss Reserve",
                    metric_type="currency",
                    description="Reserve for potentially bad loans",
                ),
            ],
        ),
    },
)

# ============================================================================
# TEMPLATE REGISTRY
# ============================================================================

SECTOR_TEMPLATES = {
    "Technology": TECHNOLOGY_TEMPLATE,
    "Communication Services": TECHNOLOGY_TEMPLATE,
    "Energy": ENERGY_TEMPLATE,
    "Oil & Gas": ENERGY_TEMPLATE,
    "Oil & Gas Exploration & Production": ENERGY_TEMPLATE,
    "Financial Services": FINANCE_TEMPLATE,
    "Finance": FINANCE_TEMPLATE,
}

# Default template if sector not recognized
DEFAULT_TEMPLATE = SectorTemplate(
    name="Default",
    sectors=["*"],
    description="Default template for any sector",
    categories=UNIVERSAL_METRICS,
)


def get_template_for_sector(sector: str) -> SectorTemplate:
    """Get the appropriate template for a given sector.

    Args:
        sector: Sector name from company info

    Returns:
        SectorTemplate for that sector, or DEFAULT_TEMPLATE if not found
    """
    if not sector:
        return DEFAULT_TEMPLATE

    # Exact match
    if sector in SECTOR_TEMPLATES:
        return SECTOR_TEMPLATES[sector]

    # Partial match (case-insensitive)
    sector_lower = sector.lower()
    for template_sector, template in SECTOR_TEMPLATES.items():
        if (
            sector_lower in template_sector.lower()
            or template_sector.lower() in sector_lower
        ):
            return template

    return DEFAULT_TEMPLATE
