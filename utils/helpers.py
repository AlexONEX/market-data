from datetime import datetime
from decimal import Decimal, getcontext, setcontext
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def parse_date(date_str: str) -> datetime | None:
    """
    Parses a date string into a datetime object.
    Handles multiple common date formats.
    """
    formats = [
        "%d/%m/%Y",
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%d",
        "%m/%d/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    logging.warning(f"Could not parse date '{date_str}' with any known format.")
    return None


def calculate_tem_from_tea(tea: Decimal) -> Decimal | None:
    """
    Calculates the Tasa Efectiva Mensual (TEM) from the Tasa Efectiva Anual (TEA).
    Formula: TEM = (1 + TEA)^(1/12) - 1

    Assumes 'tea' is already a Decimal type due to type hinting.
    """
    # Removed the 'if not isinstance(tea, Decimal):' block.
    # The type hint 'tea: Decimal' in the function signature indicates that 'tea'
    # is expected to be a Decimal. Static type checkers will flag calls
    # where 'tea' is not a Decimal.

    one = Decimal("1")
    twelve = Decimal("12")

    base = one + tea

    if base < 0:
        logging.error(
            f"Cannot calculate TEM from TEA={tea}: (1 + TEA) is negative ({base}). Base for fractional power must be non-negative."
        )
        return None

    original_context = getcontext()
    new_context = original_context.copy()
    new_context.prec = 50
    setcontext(new_context)

    try:
        tem_calc = (base ** (one / twelve)) - one
        return tem_calc.normalize()

    except Exception as e:
        logging.error(f"Error calculating TEM from TEA ({tea}): {e}")
        return None
    finally:
        setcontext(original_context)


def calculate_maturity_years(
    expiration_date: datetime,
    current_date: datetime,
) -> Decimal:
    """
    Calculates the years to maturity from an expiration date and current date.
    Assumes expiration_date and current_date are valid datetime objects.
    """
    time_to_maturity = expiration_date - current_date
    return Decimal(time_to_maturity.days) / Decimal("365.25")
