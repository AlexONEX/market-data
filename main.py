import logging
import json
import sys
import datetime
from application.bond_analyzer import BondAnalyzer
from application.asset_lister import AssetLister
from domain.financial_math import IRRCalculator, BondDataLoader
from services.ppi_service import PPIService
import requests
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


def get_mep_rate_from_data912():
    """Fetch only MEP rate from data912.com API."""
    try:
        logging.info("Fetching MEP rate from data912...")
        response = requests.get('https://data912.com/live/mep', timeout=10)
        if response.status_code == 200:
            mep_data = response.json()
            if mep_data and len(mep_data) > 0:
                close_prices = [item.get('close', 0) for item in mep_data if item.get('close')]
                if close_prices:
                    close_prices.sort()
                    n = len(close_prices)
                    median = close_prices[n//2] if n % 2 == 1 else (close_prices[n//2-1] + close_prices[n//2]) / 2
                    mep_rate = Decimal(str(median))
                    logging.info(f"MEP rate: ${median:.2f}")
                    return mep_rate
                else:
                    logging.warning("No MEP close prices found in response")
            else:
                logging.warning("Empty MEP data response")
        else:
            logging.warning(f"MEP API returned status {response.status_code}")
    except Exception as e:
        logging.warning(f"Error fetching MEP rate: {e}")

    # Default fallback
    logging.info("Using default MEP rate: $1370")
    return Decimal("1370")


def run_bond_analysis_and_plotting():
    """
    Enhanced bond analysis with IRR calculations and carry trade analysis.
    Fetches live data from data912 API and PPI, calculates TIR for all bonds,
    and generates comprehensive analysis reports.
    """
    if not settings.PPI_PUBLIC_KEY or not settings.PPI_PRIVATE_KEY:
        logging.error(
            "PPI keys (PUBLIC_KEY or PRIVATE_KEY) are not set in .env. Please check .env and config/settings.py"
        )
        return

    print("\n" + "="*100)
    print("COMPREHENSIVE BOND ANALYSIS WITH IRR AND CARRY TRADE")
    print("="*100)

    # --- Step 1: Initialize components ---
    logging.info("Initializing analysis components...")
    bond_loader = BondDataLoader()
    irr_calculator = IRRCalculator(bond_loader)
    # bond_analyzer = BondAnalyzer()  # Temporarily disabled due to PPI connection issues
    
    # --- Step 2: Fetch MEP rate from data912 ---
    mep_rate = get_mep_rate_from_data912()
    
    # --- Step 3: Get all bonds from CSV files ---
    all_bonds = bond_loader.get_all_bonds()
    logging.info(f"Loaded {len(all_bonds)} bonds from CSV files")
    
    # --- Step 4: Analyze bonds with live prices ---
    analysis_results = {
        'fixed_rate': [],
        'cer_linked': [],
        'lecaps': [],
        'dollar_linked': [],
        'dual_bonds': []
    }
    
    irr_results = {}
    carry_trade_results = []
    missing_tickers = []  # Track tickers not found in any API
    
    usd_scenarios = [1200, 1300, 1400, 1500, 1600, 1700]
    
    logging.info("Analyzing bonds with live market data...")
    
    for ticker, bond_info in all_bonds.items():
        try:
            # Get price and TIR from bonistas.com + ecovalores.com (unified approach)
            from services.bonistas_service import BonistasService
            from services.ecovalores_service import EcovaloresService

            bonistas_service = BonistasService()
            ecovalores_service = EcovaloresService()

            bond_data = None
            source = "none"
            price = None

            # Try bonistas.com first (for all types including LECAPs, CER, etc.)
            bond_data = bonistas_service.get_bond_tir(ticker)
            if bond_data and bond_data.get('tir'):
                source = "bonistas.com"
                price = bond_data.get('price')  # Try to get price from bonistas too

                # If no price from bonistas, try ecovalores for price only
                if not price:
                    eco_data = ecovalores_service.get_bond_data(ticker)
                    if eco_data and eco_data.get('price'):
                        price = eco_data['price']
                        source = "bonistas.com(TIR)+ecovalores.com(price)"

            # If bonistas failed completely, try ecovalores
            if not bond_data or not bond_data.get('tir'):
                logging.info(f"Bonistas failed for {ticker}, trying ecovalores.com")
                bond_data = ecovalores_service.get_bond_data(ticker)
                if bond_data and bond_data.get('tir'):
                    source = "ecovalores.com"
                    price = bond_data.get('price')

            # Final fallback: use data912 price + calculated TIR for LECAPs
            if (not bond_data or not bond_data.get('tir') or not price) and bond_info['bond_type'] == 'lecaps':
                logging.info(f"Trying data912 fallback for LECAP {ticker}")

                # Get data912 market data for fallback
                try:
                    import requests
                    # Get bond prices from data912
                    response = requests.get('https://data912.com/live/arg_bonds', timeout=10)
                    data912_bonds = response.json() if response.status_code == 200 else []

                    # Get notes prices from data912
                    response = requests.get('https://data912.com/live/arg_notes', timeout=10)
                    data912_notes = response.json() if response.status_code == 200 else []

                    # Find ticker in data912 data
                    data912_bond = next((b for b in data912_bonds if b.get('symbol') == ticker), None)
                    data912_note = next((n for n in data912_notes if n.get('symbol') == ticker), None)
                except Exception as e:
                    logging.warning(f"Error fetching data912 for {ticker}: {e}")
                    data912_bond = data912_note = None

                if data912_bond and data912_bond.get('price'):
                    price = Decimal(str(data912_bond['price']))
                    source = "data912_bonds"
                elif data912_note and data912_note.get('price'):
                    price = Decimal(str(data912_note['price']))
                    source = "data912_notes"

                # If we have price, calculate TIR
                if price and bond_info['days_to_maturity'] > 0:
                    final_payoff = bond_info['final_payoff']

                    # Calculate TIR using financial math
                    try:
                        tir_calc = irr_calculator.calculate_irr_for_bond_with_info(ticker, price, bond_info)
                        if tir_calc and tir_calc['rates']['TIR']:
                            bond_data = {
                                'ticker': ticker,
                                'tir': tir_calc['rates']['TIR'],
                                'price': price,
                                'source': f'{source}_calculated_tir'
                            }
                            source = f"{source}(calculated_TIR)"
                            logging.info(f"Calculated TIR for {ticker}: {tir_calc['rates']['TIR']:.1%}")
                    except Exception as e:
                        logging.warning(f"Could not calculate TIR for {ticker}: {e}")

            # Final validation
            if not bond_data or not bond_data.get('tir') or not price:
                missing_reason = []
                if not bond_data or not bond_data.get('tir'):
                    missing_reason.append("no TIR")
                if not price:
                    missing_reason.append("no price")
                missing_tickers.append(f"{ticker} - {' and '.join(missing_reason)} from bonistas/ecovalores/data912")
                continue

            if bond_info['days_to_maturity'] <= 0:
                continue

            # Create result with real TIR
            tir = bond_data['tir']
            tea = tir  # For bonds, TIR ≈ TEA
            tem = (Decimal("1") + tir) ** (Decimal("1") / Decimal("12")) - Decimal("1")

            irr_result = {
                'ticker': ticker,
                'bond_type': bond_info['bond_type'],
                'maturity_date': bond_info['maturity_date'],
                'days_to_maturity': bond_info['days_to_maturity'],
                'final_payoff': bond_info['final_payoff'],
                'current_price': price,
                'rates': {
                    'TIR': tir,
                    'TEA': tea,
                    'TEM': tem,
                    'TNA': tem * Decimal("12")
                },
                'real_tir_source': source
            }
            
            # Store IRR results
            irr_results[ticker] = {
                **irr_result,
                'price_source': source
            }
            
            # Calculate carry trade scenarios
            if mep_rate:
                final_payoff = bond_info['final_payoff']

                carry_scenarios = {}
                for usd_rate in usd_scenarios:
                    # Correct carry trade calculation:
                    # 1. Buy bond: pay 'price' ARS
                    # 2. Convert to USD today: get (price / mep_rate) USD
                    # 3. At maturity: receive 'final_payoff' ARS
                    # 4. Convert to USD at future rate: get (final_payoff / future_usd_rate) USD
                    # Return = (USD_received / USD_invested) - 1

                    usd_invested = price / mep_rate
                    usd_received = final_payoff / Decimal(str(usd_rate))
                    carry_return = (usd_received / usd_invested) - Decimal("1")
                    carry_scenarios[f"usd_{usd_rate}"] = carry_return

                # Worst case scenario: USD appreciates with inflation
                days_ratio = Decimal(str(bond_info['days_to_maturity'])) / Decimal("30")
                worst_case_usd = Decimal("1400") * (Decimal("1.01") ** days_ratio)
                usd_invested_worst = price / mep_rate
                usd_received_worst = final_payoff / worst_case_usd
                carry_worst = (usd_received_worst / usd_invested_worst) - Decimal("1")

                # MEP breakeven: future USD rate where carry return = 0
                # 0 = (final_payoff / breakeven_rate) / (price / mep_rate) - 1
                # breakeven_rate = final_payoff * mep_rate / price
                mep_breakeven = final_payoff * mep_rate / price
                
                carry_trade_results.append({
                    'ticker': ticker,
                    'bond_type': bond_info['bond_type'],
                    'irr': irr_result['rates']['TIR'],
                    'days': bond_info['days_to_maturity'],
                    'price': price,
                    'price_source': source,
                    'carry_scenarios': carry_scenarios,
                    'carry_worst': carry_worst,
                    'mep_breakeven': mep_breakeven
                })
            
            # Categorize by bond type
            bond_type = bond_info['bond_type']
            if bond_type in analysis_results:
                analysis_results[bond_type].append(irr_result)
            
        except Exception as e:
            logging.error(f"Error analyzing {ticker}: {e}")
    
    # --- Step 5: Display Results ---
    print(f"\nANALYSIS SUMMARY:")
    print(f"MEP Rate: ${mep_rate:.2f}")
    print(f"Total bonds analyzed: {len(irr_results)}")
    print(f"Data sources: bonistas.com, ecovalores.com, data912.com fallback")
    
    # Display IRR results by bond type
    for bond_type, bonds in analysis_results.items():
        if bonds:
            print(f"\n{bond_type.replace('_', ' ').upper()} BONDS IRR ANALYSIS:")
            print("-" * 70)
            
            # Sort by IRR descending
            sorted_bonds = sorted(bonds, key=lambda x: x['rates']['TIR'] or Decimal('0'), reverse=True)
            
            print(f"{'Ticker':<8} {'IRR':<8} {'TEA':<8} {'TEM':<8} {'Days':<6} {'Price':<8} {'Source':<12}")
            print("-" * 70)
            
            for bond in sorted_bonds[:10]:  # Top 10 per category
                ticker = bond['ticker']
                irr = bond['rates']['TIR']
                tea = bond['rates']['TEA']
                tem = bond['rates']['TEM']
                days = bond['days_to_maturity']
                price = bond['current_price']
                source = irr_results[ticker]['price_source']
                
                print(f"{ticker:<8} {irr:>6.1%}{'':>1} {tea:>6.1%}{'':>1} {tem:>6.1%}{'':>1} "
                      f"{days:<6} ${price:>6.2f} {source:<12}")
    
    # Display carry trade analysis
    if carry_trade_results and mep_rate:
        carry_trade_results.sort(key=lambda x: x['carry_scenarios'].get('usd_1300', Decimal('-1')), reverse=True)
        
        print(f"\nCARRY TRADE OPPORTUNITIES (MEP ${mep_rate:.2f}):")
        print("-" * 100)
        print(f"{'Ticker':<8} {'Type':<12} {'IRR':<8} {'Days':<5} ", end="")
        for scenario in usd_scenarios:
            print(f"${scenario:<6}", end=" ")
        print(f"{'Worst':<8} {'Breakeven':<10} {'Source':<8}")
        print("-" * 110)
        
        for result in carry_trade_results[:15]:  # Top 15
            ticker = result['ticker']
            bond_type = result['bond_type'].replace('_', ' ').title()[:11]
            irr = result['irr']
            days = result['days']
            source = result['price_source'][:7]
            
            print(f"{ticker:<8} {bond_type:<12} {irr:>6.1%}{'':>1} {days:<5} ", end="")
            
            for scenario in usd_scenarios:
                carry_return = result['carry_scenarios'].get(f'usd_{scenario}', Decimal('0'))
                print(f"{carry_return:>6.1%}{'':>1} ", end="")
            
            carry_worst = result['carry_worst']
            mep_breakeven = result['mep_breakeven']
            
            print(f"{carry_worst:>6.1%}{'':>1} ${mep_breakeven:>8.0f} {source:<8}")
    
    # Summary statistics
    if irr_results:
        valid_irrs = [bond['rates']['TIR'] for bond in irr_results.values() if bond['rates']['TIR']]
        if valid_irrs:
            avg_irr = sum(valid_irrs) / len(valid_irrs)
            max_irr = max(valid_irrs)
            min_irr = min(valid_irrs)
            
            print(f"\nSTATISTICS:")
            print(f"Average IRR: {avg_irr:.2%}")
            print(f"Maximum IRR: {max_irr:.2%}")
            print(f"Minimum IRR: {min_irr:.2%}")
    
    # Save results to file
    try:
        import os
        import json
        from datetime import datetime
        
        os.makedirs("data", exist_ok=True)
        
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'mep_rate': float(mep_rate) if mep_rate else None,
            'total_bonds': len(irr_results),
            'irr_results': {k: {
                'ticker': v['ticker'],
                'irr': float(v['rates']['TIR']) if v['rates']['TIR'] else None,
                'tea': float(v['rates']['TEA']) if v['rates']['TEA'] else None,
                'tem': float(v['rates']['TEM']) if v['rates']['TEM'] else None,
                'days_to_maturity': v['days_to_maturity'],
                'bond_type': v['bond_type'],
                'price': float(v['current_price']),
                'price_source': v['price_source']
            } for k, v in irr_results.items()},
            'carry_trade_summary': [
                {
                    'ticker': r['ticker'],
                    'irr': float(r['irr']),
                    'best_carry_1300': float(r['carry_scenarios']['usd_1300']),
                    'mep_breakeven': float(r['mep_breakeven'])
                } for r in carry_trade_results[:10]
            ] if carry_trade_results else []
        }
        
        with open('data/daily_analysis_results.json', 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logging.info("Analysis results saved to data/daily_analysis_results.json")
        
    except Exception as e:
        logging.error(f"Error saving results: {e}")
    
    # Save missing tickers for cleanup
    if missing_tickers:
        try:
            with open('data/missing_tickers_cleanup.txt', 'w') as f:
                from datetime import datetime as dt
                f.write(f"Missing Tickers Report - {dt.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("="*80 + "\n")
                f.write(f"Total missing: {len(missing_tickers)}\n\n")
                f.write("Tickers to consider removing from CSV files:\n")
                f.write("-"*50 + "\n")
                for ticker in missing_tickers:
                    f.write(f"{ticker}\n")
                f.write("\n" + "="*80 + "\n")
                f.write("Review these tickers and remove from CSV files if they are permanently delisted.\n")
            
            print(f"\n📋 Missing Tickers Report:")
            print(f"   {len(missing_tickers)} tickers not found in APIs")
            print(f"   Report saved to: data/missing_tickers_cleanup.txt")
            
            logging.info(f"Missing tickers report saved: {len(missing_tickers)} tickers")
            
        except Exception as e:
            logging.error(f"Error saving missing tickers report: {e}")
    
    # Generate IRR curve plots using matplotlib
    print(f"\n📊 GENERATING IRR CURVE PLOTS:")
    print("="*80)
    
    try:
        # Try to import plotting libraries
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.ticker import FormatStrFormatter
        
        plots_generated = 0
        import datetime as dt
        date_suffix = dt.datetime.now().strftime("%Y%m%d")
        
        # Plot configurations for each bond type with currency indication
        curve_configs = [
            ("fixed_rate", "Curva TIR - Bonos de Tasa Fija (USD)", f"fixed_rate_irr_curve_{date_suffix}.png"),
            ("cer_linked", "Curva TIR - Bonos CER (ARS + inflación)", f"cer_irr_curve_{date_suffix}.png"),
            ("lecaps", "Curva TIR - LECAPs (ARS)", f"lecaps_irr_curve_{date_suffix}.png"),
            ("dollar_linked", "Curva TIR - Bonos Dollar Linked (USD)", f"dollar_linked_irr_curve_{date_suffix}.png"),
            ("dual_bonds", "Curva TIR - Bonos Duales", f"dual_bonds_irr_curve_{date_suffix}.png"),
        ]
        
        for bond_type, plot_title, filename in curve_configs:
            bonds = analysis_results.get(bond_type, [])
            
            if not bonds or len(bonds) < 2:
                print(f"⚠️  {bond_type.replace('_', ' ').title()}: Insufficient data ({len(bonds)} bonds) - skipping plot")
                continue
            
            # Extract data for plotting
            days_to_maturity = []
            irr_values = []
            labels = []
            
            for bond in bonds:
                days = bond.get('days_to_maturity')
                irr = bond.get('rates', {}).get('TIR')
                ticker = bond.get('ticker')
                
                if days is not None and irr is not None and days > 0:
                    days_to_maturity.append(days)
                    irr_values.append(float(irr * Decimal("100")))  # Convert to percentage
                    labels.append(ticker)
            
            if len(days_to_maturity) < 2:
                continue
            
            # Sort data by days to maturity
            sorted_data = sorted(zip(days_to_maturity, irr_values, labels))
            days_sorted, irr_sorted, labels_sorted = zip(*sorted_data)
            
            x_data = np.array(days_sorted)
            y_data = np.array(irr_sorted)
            
            # Create the plot
            plt.figure(figsize=(16, 9))
            
            # Scatter plot of actual data points
            plt.scatter(
                x_data,
                y_data,
                color="skyblue",
                edgecolor="darkblue",
                s=80,
                zorder=5,
                alpha=0.8
            )
            
            # Fit and draw smooth curve if we have enough points
            if len(x_data) > 2:
                try:
                    # Polynomial fit (degree 2)
                    z = np.polyfit(x_data, y_data, min(2, len(x_data) - 1))
                    p = np.poly1d(z)
                    
                    # Generate smooth curve
                    x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
                    y_smooth = p(x_smooth)
                    
                    # Draw the curve
                    plt.plot(
                        x_smooth,
                        y_smooth,
                        color="blue",
                        linestyle="-",
                        linewidth=2,
                        alpha=0.8,
                        zorder=3
                    )
                except Exception as e:
                    logging.warning(f"Could not fit curve for {plot_title}: {e}")
            
            # Annotate points with ticker labels
            for i, label in enumerate(labels_sorted):
                plt.annotate(
                    label,
                    (days_sorted[i], irr_sorted[i]),
                    textcoords="offset points",
                    xytext=(0, 12),
                    ha="center",
                    fontsize=9,
                    color="dimgray",
                    weight="bold"
                )
            
            # Currency-specific Y-axis labels
            currency_labels = {
                "fixed_rate": "TIR [%] - Rendimiento en USD",
                "cer_linked": "TIR [%] - Rendimiento en ARS + Inflación",
                "lecaps": "TIR [%] - Rendimiento en ARS",
                "dollar_linked": "TIR [%] - Rendimiento en USD",
                "dual_bonds": "TIR [%] - Rendimiento Dual"
            }

            # Styling
            plt.title(
                f"{plot_title} - TIR vs. Días a Vencimiento ({date_suffix})",
                fontsize=18,
                pad=20,
                weight="bold"
            )
            plt.xlabel("Días a Vencimiento", fontsize=14, labelpad=15)
            plt.ylabel(currency_labels.get(bond_type, "TIR [%]"), fontsize=14, labelpad=15)
            plt.grid(True, linestyle="--", alpha=0.5, zorder=0)
            plt.tick_params(axis="both", which="major", labelsize=12)
            
            # Check if we need logarithmic scale (high TIR variation)
            y_ratio = y_data.max() / y_data.min() if y_data.min() > 0 else 1
            use_log_scale = y_ratio > 3.0  # Use log scale if max/min ratio > 3

            if use_log_scale:
                plt.yscale('log')
                # Custom formatter for log scale percentages
                from matplotlib.ticker import FuncFormatter
                def percent_formatter(x, pos):
                    return f"{x:.1f}%"
                plt.gca().yaxis.set_major_formatter(FuncFormatter(percent_formatter))

                # Log scale limits
                y_min = max(1, y_data.min() * 0.8)  # Don't go below 1%
                y_max = y_data.max() * 1.2
                plt.ylim(y_min, y_max)

                # Add note about log scale
                plt.text(0.02, 0.98, "Escala logarítmica", transform=plt.gca().transAxes,
                        fontsize=10, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
            else:
                # Linear scale
                plt.gca().yaxis.set_major_formatter(FormatStrFormatter("%.1f%%"))

                # Set limits with some padding
                y_padding = (y_data.max() - y_data.min()) * 0.1
                plt.ylim(max(0, y_data.min() - y_padding), y_data.max() + y_padding)

            # X-axis limits (always linear)
            x_padding = (x_data.max() - x_data.min()) * 0.1
            plt.xlim(max(0, x_data.min() - x_padding), x_data.max() + x_padding)
            
            plt.tight_layout(pad=3.0)
            
            # Currency-specific footers
            currency_footers = {
                "fixed_rate": "Bonos USD: TIR en dólares estadounidenses | Fuente: bonistas.com, ecovalores.com",
                "cer_linked": "Bonos CER: TIR en pesos + ajuste inflacionario | Fuente: bonistas.com, ecovalores.com",
                "lecaps": "LECAPs: TIR en pesos argentinos | Fuente: bonistas.com, ecovalores.com",
                "dollar_linked": "Dollar Linked: TIR en dólares | Fuente: bonistas.com, ecovalores.com",
                "dual_bonds": "Bonos Duales: TIR variable | Fuente: bonistas.com, ecovalores.com"
            }

            # Add footer
            plt.figtext(
                0.5,
                0.01,
                currency_footers.get(bond_type, "Fuente: bonistas.com, ecovalores.com"),
                ha="center",
                fontsize=10,
                color="dimgray",
            )
            
            # Save the plot
            import os
            os.makedirs("plots", exist_ok=True)
            plot_path = os.path.join("plots", filename)
            
            plt.savefig(plot_path, bbox_inches="tight", dpi=150)
            plt.close()
            
            print(f"✅ {plot_title} saved: {plot_path}")
            plots_generated += 1
        
        if plots_generated > 0:
            print(f"\n📊 Generated {plots_generated} IRR curve plots in 'plots/' directory")
        else:
            print(f"⚠️  No plots could be generated - insufficient data")
    
    except ImportError:
        print("❌ matplotlib not available - cannot generate PNG plots")
        print("   Install with: pip install matplotlib numpy")
        logging.error("matplotlib not available for plot generation")
    except Exception as e:
        logging.error(f"Error generating IRR curve plots: {e}")
        print(f"❌ Error generating curve plots: {e}")
    
    print("\n" + "="*100)
    print("COMPREHENSIVE ANALYSIS COMPLETE")
    print("="*100)


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



    print("CARRY TRADE ANALYSIS")
    print("="*100)
    
    if not settings.PPI_PUBLIC_KEY or not settings.PPI_PRIVATE_KEY:
        logging.error("PPI keys are not set. Cannot fetch market prices for carry trade analysis.")
        print("Error: PPI API keys not configured. Please check .env file.")
        return
    
    try:
        # Initialize components
        bond_loader = BondDataLoader()
        irr_calculator = IRRCalculator(bond_loader)
        ppi_service = PPIService()
        
        # Get MEP rate
        print("Fetching MEP rate...")
        try:
            response = requests.get('https://data912.com/live/mep', timeout=10)
            if response.status_code == 200:
                mep_data = response.json()
                if mep_data and len(mep_data) > 0:
                    close_prices = [item.get('close', 0) for item in mep_data if item.get('close')]
                    if close_prices:
                        close_prices.sort()
                        n = len(close_prices)
                        mep_rate = close_prices[n//2] if n % 2 == 1 else (close_prices[n//2-1] + close_prices[n//2]) / 2
                        mep_rate = Decimal(str(mep_rate))
                    else:
                        mep_rate = Decimal("1200")
                else:
                    mep_rate = Decimal("1200")
            else:
                mep_rate = Decimal("1200")
        except Exception as e:
            logging.warning(f"Error fetching MEP rate: {e}")
            mep_rate = Decimal("1200")
        
        print(f"MEP Rate: ${mep_rate:.2f}")
        
        # Get all bonds and prices
        all_bonds = bond_loader.get_all_bonds()
        tickers = list(all_bonds.keys())
        
        print(f"Analyzing {len(tickers)} bonds...")
        
        # Get market prices
        prices = {}
        for ticker in tickers:
            try:
                price_data = ppi_service.get_price(ticker, "BONOS")
                if price_data and price_data.get("price") is not None:
                    prices[ticker] = Decimal(str(price_data["price"]))
            except Exception as e:
                logging.warning(f"Could not fetch price for {ticker}: {e}")
        
        if not prices:
            print("No market prices available. Carry trade analysis cannot be performed.")
            return
        
        print(f"Found prices for {len(prices)} bonds.")
        
        # Calculate carry trade returns
        usd_scenarios = [1200, 1300, 1400, 1500, 1600, 1700]
        results = []
        
        for ticker in tickers:
            bond_info = all_bonds[ticker]
            current_price = prices.get(ticker)
            
            if not current_price or bond_info['days_to_maturity'] <= 0:
                continue
            
            # Calculate IRR
            irr_result = irr_calculator.calculate_irr_for_bond(ticker, current_price)
            if not irr_result or not irr_result['rates']['TIR']:
                continue
            
            # Calculate carry trade scenarios
            final_payoff = bond_info['final_payoff']
            bond_return_ratio = final_payoff / current_price
            
            carry_scenarios = {}
            for usd_rate in usd_scenarios:
                carry_return = bond_return_ratio * mep_rate / Decimal(str(usd_rate)) - Decimal("1")
                carry_scenarios[f"usd_{usd_rate}"] = carry_return
            
            # Worst case scenario
            days_ratio = Decimal(str(bond_info['days_to_maturity'])) / Decimal("30")
            worst_case_usd = Decimal("1400") * (Decimal("1.01") ** days_ratio)
            carry_worst = bond_return_ratio * mep_rate / worst_case_usd - Decimal("1")
            
            # MEP breakeven
            mep_breakeven = mep_rate * bond_return_ratio
            
            results.append({
                'ticker': ticker,
                'bond_type': bond_info['bond_type'],
                'irr': irr_result['rates']['TIR'],
                'days': bond_info['days_to_maturity'],
                'price': current_price,
                'carry_scenarios': carry_scenarios,
                'carry_worst': carry_worst,
                'mep_breakeven': mep_breakeven
            })
        
        if not results:
            print("No valid carry trade calculations could be performed.")
            return
        
        # Sort by best carry return (1300 USD scenario)
        results.sort(key=lambda x: x['carry_scenarios'].get('usd_1300', Decimal('-1')), reverse=True)
        
        # Display results
        print(f"\nCARRY TRADE OPPORTUNITIES:")
        print(f"{'Ticker':<8} {'Type':<12} {'IRR':<8} {'Days':<5} ", end="")
        for scenario in usd_scenarios:
            print(f"${scenario:<6}", end=" ")
        print(f"{'Worst':<8} {'Breakeven':<10}")
        print("-" * 100)
        
        for bond in results[:15]:
            ticker = bond['ticker']
            bond_type = bond['bond_type'].replace('_', ' ').title()[:11]
            irr = bond['irr']
            days = bond['days']
            
            print(f"{ticker:<8} {bond_type:<12} {irr:>6.1%}{'':>1} {days:<5} ", end="")
            
            for scenario in usd_scenarios:
                carry_return = bond['carry_scenarios'].get(f'usd_{scenario}', Decimal('0'))
                print(f"{carry_return:>6.1%}{'':>1} ", end="")
            
            carry_worst = bond['carry_worst']
            mep_breakeven = bond['mep_breakeven']
            
            print(f"{carry_worst:>6.1%}{'':>1} ${mep_breakeven:>8.0f}")
        
        print(f"\nNote: Returns assume buying bonds in ARS and selling USD at different rates.")
        print(f"Breakeven: MEP rate needed to break even on the trade.")
        print(f"Worst: Return if USD reaches $1400 with 1% monthly inflation.")
        
    except Exception as e:
        logging.error(f"Error during carry trade analysis: {e}")
        print(f"Error: {e}")
    
    print("\n" + "="*100)


def main_menu():
    """Displays the main application menu."""
    while True:
        print("\n--- Main Menu ---")
        print("1. Run Comprehensive Bond Analysis (Live Data + IRR + Carry Trade)")
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
