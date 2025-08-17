import os
import logging
from datetime import datetime
from decimal import Decimal

logger = logging.getLogger(__name__)


def plot_irr_vs_days_to_maturity(
    bond_data_list: list, 
    plot_title: str, 
    output_filename: str,
    output_dir: str = "plots"
):
    """
    Generates an IRR vs Days to Maturity plot from bond analysis results.
    
    Args:
        bond_data_list (list): List of bond analysis results with 'ticker', 'days_to_maturity', 
                               and 'rates' containing 'TIR' (IRR)
        plot_title (str): Title for the plot
        output_filename (str): Filename to save the plot (e.g., 'fixed_rate_irr_curve.png')
        output_dir (str): Directory where the plot will be saved
    """
    if not bond_data_list:
        logger.warning(f"No bond data to plot for '{plot_title}'. Skipping plot generation.")
        return

    try:
        import matplotlib.pyplot as plt
        import numpy as np
        from matplotlib.ticker import FormatStrFormatter
    except ImportError:
        logger.error("matplotlib not available. Cannot generate PNG plots.")
        return
    
    # Extract data for plotting
    days_to_maturity = []
    irr_values = []
    labels = []
    
    for bond in bond_data_list:
        days = bond.get('days_to_maturity')
        irr = bond.get('rates', {}).get('TIR')
        ticker = bond.get('ticker')
        
        if days is not None and irr is not None and days > 0:
            days_to_maturity.append(days)
            irr_values.append(float(irr * Decimal("100")))  # Convert to percentage
            labels.append(ticker)
    
    if len(days_to_maturity) < 2:
        logger.info(f"Not enough valid data points (found {len(days_to_maturity)}) to plot for '{plot_title}'. Skipping.")
        return
    
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
            logger.warning(f"Could not fit curve for {plot_title}: {e}")
    
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
    
    # Styling
    current_date = datetime.now()
    plt.title(
        f"{plot_title} - IRR vs. Días a Vencimiento ({current_date.strftime('%Y-%m-%d')})",
        fontsize=18,
        pad=20,
        weight="bold"
    )
    plt.xlabel("Días a Vencimiento", fontsize=14, labelpad=15)
    plt.ylabel("TIR (Tasa Interna de Retorno) [%]", fontsize=14, labelpad=15)
    plt.grid(True, linestyle="--", alpha=0.5, zorder=0)
    plt.tick_params(axis="both", which="major", labelsize=12)
    
    # Format y-axis as percentage
    plt.gca().yaxis.set_major_formatter(FormatStrFormatter("%.1f%%"))
    
    # Set limits with some padding
    x_padding = (x_data.max() - x_data.min()) * 0.1
    y_padding = (y_data.max() - y_data.min()) * 0.1
    
    plt.xlim(max(0, x_data.min() - x_padding), x_data.max() + x_padding)
    plt.ylim(max(0, y_data.min() - y_padding), y_data.max() + y_padding)
    
    plt.tight_layout(pad=3.0)
    
    # Add footer
    plt.figtext(
        0.5,
        0.01,
        "Fuente: Elaboración propia en base a datos de data912.com y PPI",
        ha="center",
        fontsize=10,
        color="dimgray",
    )
    
    # Save the plot
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, output_filename)
    
    plt.savefig(plot_path, bbox_inches="tight", dpi=150)
    plt.close()
    
    logger.info(f"IRR curve plot saved to {plot_path}")
    print(f"📊 IRR curve plot saved: {plot_path}")


def plot_all_irr_curves(analysis_results: dict, date_suffix: str = None):
    """
    Plot IRR curves for all bond types.
    
    Args:
        analysis_results (dict): Dictionary with bond types as keys and bond lists as values
        date_suffix (str): Optional date suffix for filenames
    """
    if date_suffix is None:
        date_suffix = datetime.now().strftime("%Y%m%d")
    
    curve_configs = [
        ("fixed_rate", "Curva IRR - Bonos de Tasa Fija", f"fixed_rate_irr_curve_{date_suffix}.png"),
        ("cer_linked", "Curva IRR - Bonos CER", f"cer_irr_curve_{date_suffix}.png"),
        ("dual_bonds", "Curva IRR - Bonos Duales", f"dual_bonds_irr_curve_{date_suffix}.png"),
    ]
    
    plots_generated = 0
    
    for bond_type, title, filename in curve_configs:
        bonds = analysis_results.get(bond_type, [])
        if bonds:
            try:
                plot_irr_vs_days_to_maturity(bonds, title, filename)
                plots_generated += 1
            except Exception as e:
                logger.error(f"Error generating plot for {bond_type}: {e}")
                print(f"❌ Error generating {bond_type} plot: {e}")
        else:
            logger.info(f"No bonds found for {bond_type} - skipping plot")
            print(f"⚠️  No {bond_type.replace('_', ' ')} bonds found - skipping plot")
    
    if plots_generated > 0:
        print(f"\n✅ Generated {plots_generated} IRR curve plots in 'plots/' directory")
    else:
        print(f"\n❌ No plots could be generated (missing matplotlib or insufficient data)")
    
    return plots_generated