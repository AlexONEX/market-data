import os
import json
import logging
from services.ppi_service import PPIService
from domain.asset_types import FixedIncomeAssetType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class AssetLister:
    """Manages fetching, categorizing, and storing fixed-income asset lists."""

    def __init__(self):
        self.ppi_service = PPIService()
        self.data_dir = "data"
        os.makedirs(self.data_dir, exist_ok=True)
        self.instrument_type_mapping_file = os.path.join(
            self.data_dir, "instrument_types_mapping.json"
        )

        # Ensure default_instrument_type is always initialized
        self.default_instrument_type = "BONOS"

        self.successful_instrument_types = (
            self._load_instrument_types_mapping()
        )  # Load existing mapping

    def _load_tickers_from_file(self, filename: str) -> list[str]:
        """Loads tickers from a specified text file."""
        filepath = os.path.join(self.data_dir, filename)
        tickers = []
        if os.path.exists(filepath):
            with open(filepath, "r") as f:
                for line in f:
                    ticker = line.strip()
                    if ticker:
                        tickers.append(ticker)
            logger.info(f"Loaded {len(tickers)} tickers from {filepath}")
        else:
            logger.warning(
                f"Ticker file not found: {filepath}. No assets will be loaded for this category."
            )
        return tickers

    def _load_instrument_types_mapping(self) -> dict:
        """Loads the saved ticker -> instrument_type mapping."""
        if os.path.exists(self.instrument_type_mapping_file):
            try:
                with open(self.instrument_type_mapping_file, "r") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(
                    f"Error loading instrument type mapping from {self.instrument_type_mapping_file}: {e}"
                )
                return {}
        return {}

    def _save_assets_to_file(
        self, asset_type: FixedIncomeAssetType, assets: list[dict]
    ):
        """Saves a list of assets to a JSON file."""
        file_name = f"{asset_type.name.lower()}.json"
        file_path = os.path.join(self.data_dir, file_name)
        try:
            with open(file_path, "w") as f:
                json.dump(assets, f, indent=2)
            logger.info(f"Saved {len(assets)} {asset_type.value} to {file_path}")
        except Exception as e:
            logger.error(f"Error saving assets to {file_path}: {e}")

    def _save_instrument_types_mapping(self):
        """Saves the discovered ticker -> instrument_type mapping to a JSON file."""
        try:
            with open(self.instrument_type_mapping_file, "w") as f:
                json.dump(self.successful_instrument_types, f, indent=2)
            logger.info(
                f"Saved instrument type mapping to {self.instrument_type_mapping_file}"
            )
        except Exception as e:
            logger.error(f"Error saving instrument type mapping: {e}")

    def _categorize_bond(self, bond_details: dict) -> FixedIncomeAssetType:
        """
        Categorizes a bond based on its description, ticker, or actual_instrument_type.
        Prioritizes information from search_instrument.
        """
        description = bond_details.get("description", "").upper()
        ticker = bond_details.get("ticker", "").upper()
        actual_type = bond_details.get("actual_instrument_type", "").upper()

        # High priority based on actual instrument type found and specific ticker patterns
        if actual_type == "LETRAS":
            # Letras are generally fixed income, we can categorize them more specifically by pattern if needed
            if (
                "CER" in description
                or "AJUSTABLE POR CER" in description
                or ticker.startswith("TX")
                or ticker.startswith("PR")
                or ticker.startswith("TZX")
            ):
                return FixedIncomeAssetType.CER_LINKED
            if "DOLAR LINKED" in description or "DL" in ticker:
                return FixedIncomeAssetType.DOLLAR_LINKED
            # Default Letras to Fixed Rate if no other specific features are detected
            return FixedIncomeAssetType.FIXED_RATE

        # Categorize BONOS by ticker patterns or description
        if ticker.startswith("TT"):  # TAMAR duales
            return FixedIncomeAssetType.DUAL_BONDS
        if "DL" in ticker:  # Generic Dollar Linked pattern
            return FixedIncomeAssetType.DOLLAR_LINKED
        if (
            ticker.startswith("TX")
            or ticker.startswith("PR")
            or ticker.startswith("TZX")
        ):  # Common CER patterns
            return FixedIncomeAssetType.CER_LINKED

        # Then use description if available and helps refine for BONOS
        if "DUAL" in description and (
            "DOLAR LINKED" in description or "CER" in description
        ):
            return FixedIncomeAssetType.DUAL_BONDS
        if "CER" in description or "AJUSTABLE POR CER" in description:
            return FixedIncomeAssetType.CER_LINKED
        if "DOLAR LINKED" in description:
            return FixedIncomeAssetType.DOLLAR_LINKED

        # Fallback to Fixed Rate if no specific pattern or description matches
        logger.debug(
            f"Categorizing {ticker} as FIXED_RATE (Description: '{description}', Actual Type: '{actual_type}')"
        )
        return FixedIncomeAssetType.FIXED_RATE

    def fetch_and_store_fixed_income_assets(self):
        """
        Loads tickers from local files, fetches their details from PPI,
        categorizes them, and stores them in local JSON files.
        """
        logger.info(
            "Starting to fetch and categorize fixed income assets using local ticker lists..."
        )

        all_tickers = []
        all_tickers.extend(self._load_tickers_from_file("fixed_rate_tickers.txt"))
        all_tickers.extend(self._load_tickers_from_file("dual_tamar_tickers.txt"))
        all_tickers.extend(self._load_tickers_from_file("cer_tickers.txt"))
        all_tickers.extend(self._load_tickers_from_file("dollar_linked_tickers.txt"))

        categorized_assets = {asset_type: [] for asset_type in FixedIncomeAssetType}

        for ticker in all_tickers:
            # Determine the instrument type to try first from our mapping
            preferred_type = self.successful_instrument_types.get(
                ticker, self.default_instrument_type
            )

            bond_details = self.ppi_service.get_instrument_details(
                ticker, preferred_type
            )
            if bond_details:
                # Store the successful instrument type for this ticker for future runs
                actual_type = bond_details.get("actual_instrument_type")
                if (
                    actual_type
                    and self.successful_instrument_types.get(ticker) != actual_type
                ):
                    self.successful_instrument_types[ticker] = actual_type
                    logger.info(f"Updated {ticker}'s instrument type to {actual_type}")
                elif actual_type:  # Already known type
                    logger.debug(f"{ticker} confirmed as {actual_type}")

                # Ensure 'ticker' key exists for categorization
                bond_details["ticker"] = bond_details.get("ticker", ticker)

                category = self._categorize_bond(bond_details)
                categorized_assets[category].append(bond_details)
            else:
                logger.warning(
                    f"Could not retrieve any details for bond: {ticker}. Skipping."
                )

        # Save all categorized assets to their respective files
        for asset_type, assets in categorized_assets.items():
            self._save_assets_to_file(asset_type, assets)

        # Always save the updated instrument types mapping at the end
        self._save_instrument_types_mapping()

        logger.info("Finished fetching and categorizing fixed income assets.")
