from dataclasses import dataclass, field


@dataclass
class MetricDefinition:
    """Definition of a single metric."""

    name: str
    data_key: str
    metric_type: str
    alt_keys: list[str] = field(default_factory=list)
    description: str = ""


@dataclass
class MetricCategory:
    """Group of related metrics."""

    name: str
    metrics: list[MetricDefinition]
    description: str = ""


@dataclass
class SectorTemplate:
    """Template defining metrics for a specific sector."""

    name: str
    sectors: list[str]
    categories: dict[str, MetricCategory]
    description: str = ""


# ============================================================================
# UNIVERSAL METRICS (apply to all sectors)
# ============================================================================

UNIVERSAL_METRICS = {
    "Overview": MetricCategory(
        name="Overview",
        metrics=[
            MetricDefinition(
                name="Company Name", data_key="overview.name", metric_type="string"
            ),
            MetricDefinition(
                name="Sector", data_key="overview.sector", metric_type="string"
            ),
            MetricDefinition(
                name="Industry", data_key="overview.industry", metric_type="string"
            ),
            MetricDefinition(
                name="Market Cap", data_key="overview.marketCap", metric_type="currency"
            ),
            MetricDefinition(
                name="Employees",
                data_key="overview.fullTimeEmployees",
                metric_type="count",
            ),
        ],
    ),
    "Valuation": MetricCategory(
        name="Valuation",
        metrics=[
            MetricDefinition(
                name="PE Ratio",
                data_key="ratios.pe_ratio",
                metric_type="ratio",
                alt_keys=["overview.peRatio"],
                description="Price-to-Earnings ratio (as on stockanalysis.com)",
            ),
            MetricDefinition(
                name="PS Ratio",
                data_key="ratios.ps_ratio",
                metric_type="ratio",
                description="Price-to-Sales ratio (as on stockanalysis.com)",
            ),
            MetricDefinition(
                name="PB Ratio",
                data_key="ratios.pb_ratio",
                metric_type="ratio",
                alt_keys=["overview.priceToBook"],
                description="Price-to-Book ratio (as on stockanalysis.com)",
            ),
            MetricDefinition(
                name="P/TBV Ratio",
                data_key="ratios.p_tbv_ratio",
                metric_type="ratio",
                description="Price-to-Tangible Book Value ratio",
            ),
            MetricDefinition(
                name="P/FCF Ratio",
                data_key="ratios.p_fcf_ratio",
                metric_type="ratio",
                description="Price-to-Free Cash Flow ratio",
            ),
            MetricDefinition(
                name="Dividend Yield",
                data_key="overview.dividendYield",
                metric_type="percentage",
            ),
        ],
    ),
    "Profitability": MetricCategory(
        name="Profitability",
        metrics=[
            MetricDefinition(
                name="Gross Margin",
                data_key="income_statement.gross_margin",
                metric_type="percentage",
            ),
            MetricDefinition(
                name="Operating Margin",
                data_key="income_statement.operating_margin",
                metric_type="percentage",
            ),
            MetricDefinition(
                name="Profit Margin",
                data_key="income_statement.profit_margin",
                metric_type="percentage",
            ),
            MetricDefinition(
                name="Free Cash Flow Margin",
                data_key="income_statement.free_cash_flow_margin",
                metric_type="percentage",
                description="FCF Margin (as on stockanalysis.com)",
            ),
            MetricDefinition(
                name="EBITDA Margin",
                data_key="income_statement.ebitda_margin",
                metric_type="percentage",
            ),
            MetricDefinition(
                name="EBIT Margin",
                data_key="income_statement.ebit_margin",
                metric_type="percentage",
            ),
        ],
    ),
    "Income Statement": MetricCategory(
        name="Income Statement",
        metrics=[
            MetricDefinition(
                name="Revenue",
                data_key="income_statement.revenue",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Gross Profit",
                data_key="income_statement.gross_profit",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Operating Income",
                data_key="income_statement.operating_income",
                metric_type="currency",
            ),
            MetricDefinition(
                name="EBITDA",
                data_key="income_statement.ebitda",
                metric_type="currency",
            ),
            MetricDefinition(
                name="EBIT", data_key="income_statement.ebit", metric_type="currency"
            ),
            MetricDefinition(
                name="Net Income",
                data_key="income_statement.net_income",
                metric_type="currency",
            ),
            MetricDefinition(
                name="EPS (Basic)",
                data_key="income_statement.eps_basic",
                metric_type="currency",
                description="Earnings Per Share (Basic)",
            ),
            MetricDefinition(
                name="EPS (Diluted)",
                data_key="income_statement.eps_diluted",
                metric_type="currency",
                alt_keys=["overview.eps"],
                description="Earnings Per Share (Diluted)",
            ),
        ],
    ),
    "Balance Sheet": MetricCategory(
        name="Balance Sheet",
        metrics=[
            MetricDefinition(
                name="Total Assets",
                data_key="balance_sheet.total_assets",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Total Liabilities",
                data_key="balance_sheet.total_liabilities",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Total Equity",
                data_key="balance_sheet.shareholders_equity",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Current Assets",
                data_key="balance_sheet.total_current_assets",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Current Liabilities",
                data_key="balance_sheet.total_current_liabilities",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Book Value Per Share",
                data_key="balance_sheet.book_value_per_share",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Tangible Book Value",
                data_key="balance_sheet.tangible_book_value",
                metric_type="currency",
            ),
        ],
    ),
    "Cash Flow": MetricCategory(
        name="Cash Flow",
        metrics=[
            MetricDefinition(
                name="Operating Cash Flow",
                data_key="cash_flow.operating_cash_flow",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Investing Cash Flow",
                data_key="cash_flow.investing_cash_flow",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Financing Cash Flow",
                data_key="cash_flow.financing_cash_flow",
                metric_type="currency",
            ),
            MetricDefinition(
                name="Free Cash Flow",
                data_key="cash_flow.free_cash_flow",
                metric_type="currency",
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
                    data_key="income_statement.revenue_growth_yoy",
                    metric_type="percentage",
                ),
                MetricDefinition(
                    name="EPS Growth",
                    data_key="income_statement.eps_growth",
                    metric_type="percentage",
                ),
            ],
        ),
    },
)

ENERGY_TEMPLATE = SectorTemplate(
    name="Energy",
    sectors=["Energy", "Oil & Gas", "Oil & Gas Exploration & Production"],
    description="Template for energy/oil companies - focus on production, reserves, margins",
    categories={
        **UNIVERSAL_METRICS,
        "Financial Health": MetricCategory(
            name="Financial Health",
            metrics=[
                MetricDefinition(
                    name="Debt / Equity Ratio",
                    data_key="ratios.debt_equity_ratio",
                    metric_type="ratio",
                ),
                MetricDefinition(
                    name="Current Ratio",
                    data_key="ratios.current_ratio",
                    metric_type="ratio",
                ),
                MetricDefinition(
                    name="Debt / EBITDA Ratio",
                    data_key="ratios.debt_ebitda_ratio",
                    metric_type="ratio",
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
                    data_key="ratios.return_on_equity_roe",
                    metric_type="percentage",
                ),
                MetricDefinition(
                    name="ROA (Return on Assets)",
                    data_key="ratios.return_on_assets_roa",
                    metric_type="percentage",
                ),
                MetricDefinition(
                    name="Net Interest Margin",
                    data_key="ratios.net_interest_margin",
                    metric_type="percentage",
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

DEFAULT_TEMPLATE = SectorTemplate(
    name="Default",
    sectors=["*"],
    description="Default template for any sector",
    categories=UNIVERSAL_METRICS,
)


def get_template_for_sector(sector: str) -> SectorTemplate:
    if not sector:
        return DEFAULT_TEMPLATE
    sector_lower = sector.lower()
    for template_sector, template in SECTOR_TEMPLATES.items():
        if (
            sector_lower in template_sector.lower()
            or template_sector.lower() in sector_lower
        ):
            return template
    return DEFAULT_TEMPLATE
