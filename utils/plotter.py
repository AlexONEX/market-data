import matplotlib.pyplot as plt
import pandas as pd
import os
import logging
import numpy as np
from datetime import datetime
from decimal import Decimal
from matplotlib.ticker import (
    FormatStrFormatter,
)

logger = logging.getLogger(__name__)


def plot_time_series(
    data_list: list,
    date_col: str,
    value_col: str,
    plot_title: str,
    output_filename: str,
    y_label: str = "Valor",
    output_dir: str = "plots",
):
    """
    Generates a time series plot from a list of dictionaries.

    Args:
        data_list (list): List of dictionaries containing the data.
        date_col (str): Name of the column containing dates.
        value_col (str): Name of the column containing values to plot.
        plot_title (str): Title of the plot.
        output_filename (str): Filename to save the plot image (e.g., 'tna_plot.png').
        y_label (str): Label for the Y-axis.
        output_dir (str): Directory where the plot will be saved.
    """
    if not data_list:
        logger.warning(f"No data to plot for '{plot_title}'. Skipping plot generation.")
        return

    df = pd.DataFrame(data_list)

    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df[value_col] = pd.to_numeric(df[value_col])
    except KeyError as e:
        logger.error(
            f"Required columns '{date_col}' or '{value_col}' not found in data: {e}"
        )
        return
    except ValueError as e:
        logger.error(f"Error converting data to numeric/date format: {e}")
        return

    df = df.sort_values(by=date_col)

    plt.figure(figsize=(14, 7))
    plt.plot(
        df[date_col],
        df[value_col],
        marker="o",
        linestyle="-",
        color="skyblue",
        markersize=4,
    )
    plt.title(plot_title, fontsize=16, pad=15)
    plt.xlabel("Fecha", fontsize=12)
    plt.ylabel(y_label, fontsize=12)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.xticks(rotation=45)

    plt.tight_layout(pad=3.0)

    plt.figtext(
        0.5,
        0.01,
        "Fuente: Elaboración propia en base a datos de BCRA y BYMA",
        ha="center",
        fontsize=10,
        color="dimgray",
    )

    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, output_filename)

    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    logger.info(f"Plot saved to {plot_path}")


def plot_tem_vs_days_to_maturity(
    bond_data_list: list, plot_title: str, output_filename: str
):
    """
    Generates a scatter plot of TEM vs. Days to Maturity, fitting a smooth
    polynomial curve to the data points.

    Args:
        bond_data_list (list): A list of dictionaries, where each dict is a bond analysis result
                               from BondAnalyzer, containing 'ticker', 'maturity_date',
                               'calculated_rates' (with 'TEM').
        plot_title (str): The title for the plot.
        output_filename (str): The filename to save the plot image (e.g., 'cer_curve.png').
    """
    days_to_maturity = []
    tem_values = []
    labels = []
    current_date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

    for bond in bond_data_list:
        maturity_date_str = bond.get("maturity_date")
        tem = bond.get("calculated_rates", {}).get("TEM")
        ticker = bond.get("ticker")

        if maturity_date_str and maturity_date_str != "N/A" and tem is not None:
            try:
                maturity_date = datetime.strptime(maturity_date_str, "%Y-%m-%d")
                delta = maturity_date - current_date

                if delta.days > 0:
                    days_to_maturity.append(delta.days)
                    tem_values.append(float(tem * Decimal("100")))
                    labels.append(ticker)
                else:
                    logger.warning(
                        f"Skipping {ticker}: Maturity date is in the past or today ({maturity_date_str})."
                    )
            except ValueError:
                logger.warning(
                    f"Could not parse maturity date for {ticker}: {maturity_date_str}. Skipping."
                )
        else:
            logger.warning(
                f"Skipping {ticker}: Missing maturity date ({maturity_date_str}) or TEM ({tem})."
            )

    if len(days_to_maturity) < 2:  # Necesitamos al menos 2 puntos para una curva
        logger.info(
            f"Not enough valid data points (found {len(days_to_maturity)}) to plot for '{plot_title}'. Skipping."
        )
        return

    # No es necesario ordenar aquí si solo vamos a ajustar una curva,
    # pero es bueno para las etiquetas.
    sorted_data = sorted(zip(days_to_maturity, tem_values, labels))
    days_to_maturity_sorted, tem_values_sorted, labels_sorted = zip(*sorted_data)

    x_data = np.array(days_to_maturity_sorted)
    y_data = np.array(tem_values_sorted)

    plt.figure(figsize=(16, 9))  # Ajustado para un aspect ratio más panorámico

    # --- 2. DIBUJAR LOS PUNTOS ORIGINALES COMO SCATTER PLOT ---
    plt.scatter(
        x_data,
        y_data,
        color="skyblue",
        edgecolor="darkblue",
        s=80,  # Tamaño de los marcadores
        zorder=5,  # Poner los puntos por encima de la curva y la grilla
    )

    # --- 3. CALCULAR Y DIBUJAR LA CURVA SUAVIZADA ---
    # Solo intentar ajustar la curva si hay suficientes puntos para el grado del polinomio
    if len(x_data) > 2:
        # Ajuste polinómico de grado 2 (una parábola)
        z = np.polyfit(x_data, y_data, 2)
        p = np.poly1d(z)

        # Generar puntos X suaves para una curva continua
        x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
        y_smooth = p(x_smooth)

        # Dibujar la línea de la curva
        plt.plot(
            x_smooth,
            y_smooth,
            color="blue",
            linestyle="-",
            linewidth=2,
            alpha=0.8,
            zorder=3,  # Poner la línea por debajo de los puntos
        )

    # --- Anotar las etiquetas de los tickers ---
    for i, txt in enumerate(labels_sorted):
        plt.annotate(
            txt,
            (days_to_maturity_sorted[i], tem_values_sorted[i]),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=9,
            color="dimgray",
        )

    # --- Estilo y etiquetas del gráfico ---
    plt.title(
        f"{plot_title} - TEM vs. Días a Vencimiento ({current_date.strftime('%Y-%m-%d')})",
        fontsize=18,
        pad=20,
    )
    plt.xlabel("Días a Vencimiento", fontsize=14, labelpad=15)
    plt.ylabel("TEM (Tasa Efectiva Mensual) [%]", fontsize=14, labelpad=15)
    plt.grid(True, linestyle="--", alpha=0.5, zorder=0)
    plt.tick_params(axis="both", which="major", labelsize=12)
    plt.gca().yaxis.set_major_formatter(FormatStrFormatter("%.2f%%"))

    # Ajustar límites para dar más espacio
    plt.xlim(0, x_data.max() * 1.1)

    plt.tight_layout(pad=3.0)

    plt.figtext(
        0.5,
        0.01,
        "Fuente: Elaboración propia en base a datos de BCRA y BYMA",
        ha="center",
        fontsize=10,
        color="dimgray",
    )

    output_dir = "plots"
    os.makedirs(output_dir, exist_ok=True)
    plot_path = os.path.join(output_dir, output_filename)

    plt.savefig(plot_path, bbox_inches="tight", dpi=150)
    plt.close()
    logger.info(f"Smooth curve plot saved to {plot_path}")
