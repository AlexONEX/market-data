import re


def clean_column_name(col_name: str) -> str:
    """
    Cleans a column name to be a valid Python identifier.

    - Converts to lowercase
    - Handles parentheses content (converts to underscore + content)
    - Replaces spaces, slashes, and hyphens with underscores
    - Removes any non-alphanumeric characters except underscore
    - Removes any trailing or leading underscores

    Examples:
        "Revenue Growth (YoY)" -> "revenue_growth_yoy"
        "Debt / Equity Ratio" -> "debt_equity_ratio"
        "EPS (Basic)" -> "eps_basic"
        "EPS (Diluted)" -> "eps_diluted"

    """
    if not isinstance(col_name, str):
        return ""

    cleaned = col_name.lower()

    # Replace content in parentheses with underscore + content (instead of removing)
    # This ensures EPS (Basic) -> eps_basic and EPS (Diluted) -> eps_diluted
    cleaned = re.sub(r"\s*\((.*?)\)", r"_\1", cleaned)

    # Replace special characters with underscores
    cleaned = re.sub(r"[\s/&-]+", "_", cleaned)

    # Remove any non-alphanumeric characters except underscore
    cleaned = re.sub(r"[^a-z0-9_]", "", cleaned)

    # Remove leading/trailing underscores and return directly
    return cleaned.strip("_")
