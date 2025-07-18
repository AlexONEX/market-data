import logging
import json
import sys
from application.bond_analyzer import BondAnalyzer
from application.asset_lister import AssetLister
from config.settings import settings
from decimal import Decimal
from utils.plotter import plot_tem_vs_days_to_maturity
from services.bcra_service import BCRAService

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
# Set specific loggers to INFO to reduce verbosity.
logging.getLogger("ppi_service").setLevel(logging.INFO)
logging.getLogger("application.bond_analyzer").setLevel(logging.INFO)
logging.getLogger("application.asset_lister").setLevel(logging.INFO)
logging.getLogger("utils.plotter").setLevel(logging.INFO)
logging.getLogger("bcra_service").setLevel(logging.INFO)


def load_bond_list_from_file(filepath):
    """Helper to load bond tickers from JSON files."""
    try:
        with open(filepath, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logging.warning(f"File not found: {filepath}")
        return []
    except json.JSONDecodeError as e:
        logging.error(f"Error decoding JSON from {filepath}: {e}")
        return []


def run_bond_analysis_and_plotting():
    """
    Executes the bond analysis, fetches data, calculates rates,
    and generates the bond curve plots.
    Designed for daily PNG generation.
    """
    if not settings.PPI_PUBLIC_KEY or not settings.PPI_PRIVATE_KEY:
        logging.error(
            "PPI keys (PUBLIC_KEY or PRIVATE_KEY) are not set in .env. Please check .env and config/settings.py"
        )
        return

    # --- Step 1: Fetch and store fixed-income asset lists ---
    logging.info("Fetching and storing fixed-income asset lists...")
    asset_lister = AssetLister()
    asset_lister.fetch_and_store_fixed_income_assets()
    print("\n" + "#" * 70 + "\n")

    logging.info("Starting bond analysis...")
    analyzer = BondAnalyzer()

    fixed_rate_bonds = load_bond_list_from_file("data/fixed_rate.json")
    cer_linked_bonds = load_bond_list_from_file("data/cer_linked.json")
    dual_bonds = load_bond_list_from_file("data/dual_bonds.json")
    dolar_linked_bonds = load_bond_list_from_file("data/dolar_linked.json")
    all_analyzed_bonds = {
        "Fixed Rate": [],
        "CER Linked": [],
        "Dual Bonds": [],
        "Dolar Linked": [],
    }

    # Helper function to process bond lists
    def process_bond_list(bond_list, category_name):
        logging.info(f"\n--- Analyzing {category_name} Bonds ---")
        for bond_data in bond_list:
            ticker = bond_data["ticker"]

            # Get current market price and use that as the input price for Estimate
            market_data = analyzer.ppi_service.get_price(
                ticker, analyzer.instrument_type_mapping.get(ticker, "BONOS")
            )
            current_price_for_estimate = market_data.get("price")

            if current_price_for_estimate is None:
                logging.warning(
                    f"No current market price for {ticker}. Using dummy price 100.0 for estimation."
                )
                current_price_for_estimate = Decimal("100.0")  # Fallback dummy price

            result = analyzer.analyze_bond(
                ticker=ticker,
                price_input=current_price_for_estimate,
                quantity_value=Decimal("1"),
                amount_of_money_value=Decimal("1"),
                quantity_type_str="PAPELES",
                focus_on_quantity=True,
            )
            if result:
                all_analyzed_bonds[category_name].append(result)
                # Display TIR from API, and our calculated TEM/TEA/TNA
                logging.info(
                    f"Analyzed {result['ticker']}: Market Price={result['current_market_price']},"
                    f" Input Price for Est.={result['price_used_for_calc']},"
                    f" API_TIR={result['calculated_rates'].get('TIR')},"
                    f" TEM={result['calculated_rates'].get('TEM')},"
                    f" Maturity={result['maturity_date']}"
                )

    process_bond_list(fixed_rate_bonds, "Fixed Rate")
    process_bond_list(cer_linked_bonds, "CER Linked")
    process_bond_list(dual_bonds, "Dual Bonds")
    process_bond_list(dolar_linked_bonds, "Dolar Linked")

    logging.info("\nBond analysis completed. Generating plots...")

    # --- Step 3: Generate Plots ---
    # Filter out bonds without valid TEM or maturity dates for plotting
    plot_tem_vs_days_to_maturity(
        [
            b
            for b in all_analyzed_bonds["Fixed Rate"]
            if b.get("calculated_rates", {}).get("TEM") is not None
            and b.get("maturity_date") != "N/A"
        ],
        "Curva de Bonos de Tasa Fija",
        "fixed_rate_curve.png",
    )
    plot_tem_vs_days_to_maturity(
        [
            b
            for b in all_analyzed_bonds["CER Linked"]
            if b.get("calculated_rates", {}).get("TEM") is not None
            and b.get("maturity_date") != "N/A"
        ],
        "Curva de Bonos CER",
        "cer_curve.png",
    )
    plot_tem_vs_days_to_maturity(
        [
            b
            for b in all_analyzed_bonds["Dual Bonds"]
            if b.get("calculated_rates", {}).get("TEM") is not None
            and b.get("maturity_date") != "N/A"
        ],
        "Curva de Bonos Duales",
        "dual_bonds_curve.png",
    )

    logging.info("Plots generated and saved in the 'plots' directory.")


def display_bcra_menu():
    """Displays a dynamic, paginated menu of all available BCRA variables."""
    bcra_service = BCRAService()

    # Get all variables and sort them by ID for consistent display
    all_vars = sorted(bcra_service.variable_descriptions.items())

    page_size = 20
    current_page = 0
    total_pages = (len(all_vars) - 1) // page_size + 1

    while True:
        print("\n--- BCRA Data Menu (Dynamic) ---")
        print(f"--- Page {current_page + 1} of {total_pages} ---")

        # Display the variables for the current page
        start_index = current_page * page_size
        end_index = start_index + page_size
        page_vars = all_vars[start_index:end_index]

        for var_id, description in page_vars:
            # Shorten long descriptions for menu display
            short_desc = (
                (description[:75] + "...") if len(description) > 75 else description
            )
            print(f"ID: {var_id:<5} - {short_desc}")

        print("\n" + "-" * 30)
        print("Enter a variable ID to plot it.")
        print("N: Next Page | P: Previous Page | B: Back to Main Menu | Q: Quit")

        choice = input("Your choice: ").strip().upper()

        if choice == "N":
            current_page = (current_page + 1) % total_pages
        elif choice == "P":
            current_page = (current_page - 1 + total_pages) % total_pages
        elif choice == "B":
            return  # Go back to the main menu
        elif choice == "Q":
            sys.exit("Exiting program.")
        elif choice.isdigit():
            actual_id = int(choice)
            if actual_id in bcra_service.variable_descriptions:
                try:
                    logging.info(f"Attempting to plot BCRA Variable ID {actual_id}...")
                    bcra_service.plot_bcra_series(actual_id)
                    logging.info(
                        f"Plot for BCRA Variable ID {actual_id} generated successfully."
                    )
                except Exception as e:
                    logging.error(f"Error plotting BCRA series for ID {actual_id}: {e}")
            else:
                print("Invalid ID. Please choose an ID from the list.")
        else:
            print(
                "Invalid input. Please enter a valid ID or navigation command (N, P, B, Q)."
            )


def main_menu():
    """Displays the main application menu."""
    while True:
        print("\n--- Main Menu ---")
        print("1. Run Daily Bond Analysis and Plotting")
        print("2. Explore BCRA Data (CLI Menu)")
        print("Q. Quit")

        choice = input("Enter your choice: ").strip().upper()

        if choice == "1":
            run_bond_analysis_and_plotting()
        elif choice == "2":
            display_bcra_menu()
        elif choice == "Q":
            sys.exit("Exiting program.")
        else:
            print("Invalid choice. Please select 1, 2, or Q.")


if __name__ == "__main__":
    main_menu()
