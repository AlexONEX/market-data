import re


def clean_column_name(col_name: str) -> str:
    """
    Cleans a column name to be a valid Python identifier.

    - Converts to lowercase
    - Removes parentheses and percentage signs
    - Replaces spaces, slashes, and hyphens with underscores
    - Removes any trailing or leading underscores

    Example:
        "Revenue Growth (YoY)" -> "revenue_growth_yoy"
        "Debt / Equity Ratio" -> "debt_equity_ratio"
    """
    if not isinstance(col_name, str):
        return ""

    # Convert to lowercase
    cleaned = col_name.lower()

    # Remove content in parentheses and the parentheses themselves
    cleaned = re.sub(r"\(.*?\)", "", cleaned)

    # Replace special characters with underscores
    cleaned = re.sub(r"[\s/&-]+", "_", cleaned)

    # Remove any non-alphanumeric characters except underscore
    cleaned = re.sub(r"[^a-z0-9_]", "", cleaned)

    # Remove leading/trailing underscores
    cleaned = cleaned.strip("_")

    return cleaned
