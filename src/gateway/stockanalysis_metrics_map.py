"""
Mapping of metric names from stockanalysis.com pages to normalized data keys.

This file documents the exact metric names as they appear on the website
and provides mapping to normalized keys that are used internally.

Generated from: https://stockanalysis.com/stocks/vist/financials/
"""

# ============================================================================
# FINANCIALS PAGE (Income Statement & Profitability)
# ============================================================================

FINANCIALS_METRICS = {
    # Revenue & Cost Section
    "Revenue": "revenue",
    "Revenue Growth (YoY)": "revenue_growth_yoy",
    "Cost of Revenue": "cost_of_revenue",
    "Gross Profit": "gross_profit",
    # Operating Section
    "Selling, General & Admin": "selling_general_admin",
    "Other Operating Expenses": "other_operating_expenses",
    "Operating Expenses": "operating_expenses",
    "Operating Income": "operating_income",
    # Non-Operating Items
    "Interest Expense": "interest_expense",
    "Interest & Investment Income": "interest_investment_income",
    "Currency Exchange Gain (Loss)": "currency_exchange_gain_loss",
    "Other Non Operating Income (Expenses)": "other_non_operating_income_expenses",
    # EBIT & Unusual Items
    "EBT Excluding Unusual Items": "ebt_excluding_unusual_items",
    "Merger & Restructuring Charges": "merger_restructuring_charges",
    "Impairment of Goodwill": "impairment_of_goodwill",
    "Gain (Loss) on Sale of Investments": "gain_loss_on_sale_of_investments",
    "Gain (Loss) on Sale of Assets": "gain_loss_on_sale_of_assets",
    "Asset Writedown": "asset_writedown",
    "Legal Settlements": "legal_settlements",
    "Other Unusual Items": "other_unusual_items",
    # Income Section
    "Pretax Income": "pretax_income",
    "Income Tax Expense": "income_tax_expense",
    "Net Income": "net_income",
    "Net Income to Common": "net_income_to_common",
    "Net Income Growth": "net_income_growth",
    # Per-Share Metrics
    "Shares Outstanding (Basic)": "shares_outstanding_basic",
    "Shares Outstanding (Diluted)": "shares_outstanding_diluted",
    "Shares Change (YoY)": "shares_change_yoy",
    "EPS (Basic)": "eps_basic",
    "EPS (Diluted)": "eps_diluted",
    "EPS Growth": "eps_growth",
    "Free Cash Flow Per Share": "free_cash_flow_per_share",
    # Profitability & Efficiency Margins
    "Gross Margin": "gross_margin",
    "Operating Margin": "operating_margin",
    "Profit Margin": "profit_margin",
    "Free Cash Flow Margin": "free_cash_flow_margin",
    "EBITDA": "ebitda",
    "EBITDA Margin": "ebitda_margin",
    "D&A For EBITDA": "da_for_ebitda",
    "EBIT": "ebit",
    "EBIT Margin": "ebit_margin",
    "Effective Tax Rate": "effective_tax_rate",
    "Free Cash Flow": "free_cash_flow",
    "Advertising Expenses": "advertising_expenses",
}

# ============================================================================
# RATIOS PAGE
# ============================================================================

RATIOS_METRICS = {
    # Valuation Ratios
    "Market Capitalization": "market_capitalization",
    "Market Cap Growth": "market_cap_growth",
    "Enterprise Value": "enterprise_value",
    "Last Close Price": "last_close_price",
    "PE Ratio": "pe_ratio",  # Note: NOT "P/E Ratio"
    "PS Ratio": "ps_ratio",  # Note: NOT "P/S Ratio"
    "PB Ratio": "pb_ratio",  # Note: NOT "P/B Ratio"
    "P/TBV Ratio": "p_tbv_ratio",
    "P/FCF Ratio": "p_fcf_ratio",
    "P/OCF Ratio": "p_ocf_ratio",
    "EV/Sales Ratio": "ev_sales_ratio",
    "EV/EBITDA Ratio": "ev_ebitda_ratio",
    "EV/EBIT Ratio": "ev_ebit_ratio",
    "EV/FCF Ratio": "ev_fcf_ratio",
    # Leverage Ratios
    "Debt / Equity Ratio": "debt_equity_ratio",
    "Debt / EBITDA Ratio": "debt_ebitda_ratio",
    "Debt / FCF Ratio": "debt_fcf_ratio",
    # Efficiency Ratios
    "Asset Turnover": "asset_turnover",
    "Inventory Turnover": "inventory_turnover",
    "Quick Ratio": "quick_ratio",
    "Current Ratio": "current_ratio",
    "Working Capital Ratio": "working_capital_ratio",
    "Cash Ratio": "cash_ratio",
    "Days Sales Outstanding": "days_sales_outstanding",
    "Days Inventory Outstanding": "days_inventory_outstanding",
    "Days Payable Outstanding": "days_payable_outstanding",
    "Cash Conversion Cycle": "cash_conversion_cycle",
}

# ============================================================================
# STATISTICS PAGE (Market Data, Dividend Info, Share Info)
# ============================================================================

STATISTICS_METRICS = {
    # Market Data (Use stats_ prefix to avoid collision with ratios/financials)
    "Market Cap": "stats_market_cap",
    "Enterprise Value": "stats_enterprise_value",
    "Last Close Price": "stats_last_close_price",
    # Dividend & Earnings Data
    "Earnings Date": "earnings_date",
    "Ex-Dividend Date": "ex_dividend_date",
    # Share Information
    "Current Share Class": "current_share_class",
    "Shares Outstanding": "stats_shares_outstanding",
    "Shares Change (YoY)": "stats_shares_change_yoy",
    "Shares Change (QoQ)": "shares_change_qoq",
    "Owned by Insiders (%)": "owned_by_insiders_percent",
    "Owned by Institutions (%)": "owned_by_institutions_percent",
    "Float": "float",
}

# ============================================================================
# REVERSE MAPPING (for lookups)
# ============================================================================

# Create reverse mappings for easy lookup by normalized key
_all_metrics = {**FINANCIALS_METRICS, **RATIOS_METRICS, **STATISTICS_METRICS}
REVERSE_METRICS_MAP = {v: k for k, v in _all_metrics.items()}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_page_name(normalized_key: str) -> str | None:
    """
    Get the original page metric name from a normalized key.

    Args:
        normalized_key: The normalized metric key (e.g., 'pe_ratio')

    Returns:
        The original metric name as it appears on the website, or None if not found

    """
    return REVERSE_METRICS_MAP.get(normalized_key)


def get_normalized_key(page_name: str) -> str | None:
    """
    Get the normalized key from a page metric name.

    Args:
        page_name: The metric name as it appears on the website

    Returns:
        The normalized metric key, or None if not found

    """
    return _all_metrics.get(page_name)


def is_available_metric(page_name: str) -> bool:
    """Check if a metric name is available on stockanalysis.com"""
    return page_name in _all_metrics
