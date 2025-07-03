import os
import json
import logging
from datetime import datetime
from decimal import Decimal
from typing import cast, Any  # Import cast and Any

from ppi_client.models.estimate_bonds import EstimateBonds
from dotenv import load_dotenv

# Import the refactored PPIAPIConnector
from gateway.ppi_api_connector import PPIAPIConnector

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PPIService:
    """
    Provides business logic for interacting with the PPI API,
    using PPIAPIConnector for the underlying API calls.
    Manages data caching.
    """

    def __init__(self):
        load_dotenv()  # Ensure .env is loaded here, as PPIService is often the first to need it.
        # PPIAPIConnector also needs it, so loading it once here is fine.

        # Get the authenticated PPI client instance from the connector
        self.ppi = PPIAPIConnector().get_client()

        self.cached_prices = {"cedears": {}, "bonds": {}, "stocks": {}}
        self._load_cache()

    def _load_cache(self):
        """Loads cached prices from a JSON file."""
        cache_file = "data/price_cache.json"
        try:
            if os.path.exists(cache_file):
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)
                    for ticker, price in cache_data.get("cedears", {}).items():
                        self.cached_prices["cedears"][ticker] = Decimal(str(price))
                    for ticker, price in cache_data.get("bonds", {}).items():
                        self.cached_prices["bonds"][ticker] = Decimal(str(price))
                    for ticker, price in cache_data.get("stocks", {}).items():
                        self.cached_prices["stocks"][ticker] = Decimal(str(price))
        except Exception as e:
            logger.error(f"Error loading price cache: {str(e)}")

    def _save_cache(self):
        """Saves current prices to a JSON cache file."""
        cache_file = "data/price_cache.json"
        try:
            os.makedirs(os.path.dirname(cache_file), exist_ok=True)
            cache_data = {
                "cedears": {
                    ticker: float(price)  # Storing as float for JSON serialization
                    for ticker, price in self.cached_prices["cedears"].items()
                },
                "bonds": {
                    ticker: float(price)  # Storing as float for JSON serialization
                    for ticker, price in self.cached_prices["bonds"].items()
                },
                "stocks": {
                    ticker: float(price)  # Storing as float for JSON serialization
                    for ticker, price in self.cached_prices["stocks"].items()
                },
                "last_updated": datetime.now().isoformat(),
            }
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving price cache: {str(e)}")

    def get_price(
        self, ticker: str, instrument_type: str, settlement: str = "INMEDIATA"
    ) -> dict:
        """Fetches the current price and TIR for a given instrument."""
        cache_key = {
            "CEDEARS": "cedears",
            "BONOS": "bonds",
            "ACCIONES": "stocks",
            "LETRAS": "bonds",
        }.get(instrument_type, "other")
        try:
            data = self.ppi.marketdata.current(ticker, instrument_type, settlement)

            if data:
                price = (
                    Decimal(str(data["price"]))
                    if data.get("price") is not None
                    else None
                )
                tir = Decimal(str(data["tir"])) if data.get("tir") is not None else None

                if price is not None and cache_key in self.cached_prices:
                    self.cached_prices[cache_key][ticker] = price

                return {"price": price, "tir": tir}

            if (
                cache_key in self.cached_prices
                and ticker in self.cached_prices[cache_key]
            ):
                logger.warning(f"No API data for {ticker}. Using cached price.")
                return {"price": self.cached_prices[cache_key][ticker], "tir": None}

            logger.warning(
                f"No price/TIR for {ticker} ({instrument_type}) from API or cache."
            )
            return {"price": None, "tir": None}
        except Exception as e:
            logger.warning(
                f"Error getting price/TIR for {ticker} ({instrument_type}): {str(e)}"
            )
            if (
                cache_key in self.cached_prices
                and ticker in self.cached_prices[cache_key]
            ):
                logger.warning(f"Using cached price for {ticker}.")
                return {"price": self.cached_prices[cache_key][ticker], "tir": None}
            logger.error(
                f"Failed to get price/TIR for {ticker} ({instrument_type}) even from cache."
            )
            raise  # Re-raise if completely failed, or return None if graceful fallback is intended

    def get_bond_estimation_details(
        self,
        ticker: str,
        quantity_type: str,
        quantity: Decimal,
        amount_of_money: Decimal,
        price: Decimal,
    ) -> dict | None:
        """
        Obtains bond estimation details from the PPI API.
        Uses typing.cast(Any, ...) to work around incorrect type hints in the ppi_client library's EstimateBonds model.
        """
        if quantity_type == "PAPELES":
            estimate_quantity = quantity
            estimate_amount_of_money = Decimal("0.0")
        else:
            estimate_quantity = Decimal("0.0")
            estimate_amount_of_money = amount_of_money

        current_date = datetime.now()

        # Use typing.cast(Any, ...) for each parameter that's causing a type error due to the library's
        # incorrect 'decimal' module type hint instead of 'decimal.Decimal' class.
        # PPI library sucks ass
        params_model = EstimateBonds(
            ticker=ticker,
            date=current_date,
            quantityType=quantity_type,
            quantity=cast(Any, estimate_quantity),
            amountOfMoney=cast(Any, estimate_amount_of_money),
            price=cast(Any, price),
            exchangeRate=cast(Any, Decimal("1.0")),
            equityRate=cast(Any, Decimal("1.0")),
            exchangeRateAmortization=cast(Any, Decimal("0.0")),
            rateAdjustmentAmortization=cast(Any, Decimal("0.0")),
        )

        try:
            response = self.ppi.marketdata.estimate_bonds(params_model)

            if response:
                if isinstance(response, list) and len(response) > 0:
                    return response[0]
                elif isinstance(response, dict):
                    return response

            logger.warning(
                f"Bonds/Estimate returned no valid data for {ticker}. Response: {response}"
            )
            return None
        except Exception as e:
            logger.error(f"Error calling Bonds/Estimate for {ticker}: {e}")
            raise  # Re-raise if this is a critical failure

    def get_cedear_price(self, ticker: str) -> dict:
        return self.get_price(ticker, "CEDEARS")

    def get_bond_price(self, ticker: str) -> dict:
        return self.get_price(ticker, "BONOS")

    def get_stock_price(self, ticker: str) -> dict:
        return self.get_price(ticker, "ACCIONES")

    def save_cache(self):
        self._save_cache()

    def search_instrument(
        self, ticker: str, instrument_name: str, market: str, instrument_type: str
    ) -> list[dict] | None:
        """Searches for instruments based on provided criteria."""
        try:
            return self.ppi.marketdata.search_instrument(
                ticker=ticker,
                instrument_name=instrument_name,
                market=market,
                instrument_type=instrument_type,
            )
        except Exception as e:
            logger.error(
                f"Error calling search_instrument for {ticker} ({instrument_type}): {e}"
            )
            raise  # Re-raise if search is critical

    def get_instrument_details(
        self, ticker: str, preferred_instrument_type: str
    ) -> dict | None:
        """
        Attempts to retrieve detailed information for an instrument,
        trying different instrument types if the preferred one fails.
        """
        instrument_types_to_try = [
            preferred_instrument_type,
            "LETRAS",
            "BONOS",
            "FCI",
        ]
        instrument_types_to_try = list(dict.fromkeys(instrument_types_to_try))

        for inst_type in instrument_types_to_try:
            try:
                details = self.search_instrument(
                    ticker=ticker,
                    instrument_name=ticker,
                    market="BYMA",
                    instrument_type=inst_type,
                )
                if details and len(details) > 0:
                    result_details = details[0]
                    result_details["actual_instrument_type"] = inst_type
                    return result_details
            except Exception as e:
                logger.debug(
                    f"Error for {ticker} with type {inst_type} using search_instrument: {e}"
                )

        logger.warning(
            f"Failed to retrieve descriptive details for {ticker} after trying all instrument types."
        )
        return None
