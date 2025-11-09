import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import (
    FormatStrFormatter,
)

logger = logging.getLogger(__name__)

# Constant for magic value 2
MIN_DATA_POINTS_FOR_CURVE = 2


@dataclass
class PlotConfig:
    """Configuration for time series plots."""

    plot_title: str
    output_filename: str
    y_label: str = "Valor"
    output_dir: str = "plots"


def plot_time_series(
    data_list: list,
    date_col: str,
    value_col: str,
    config: PlotConfig,
):
    if not data_list:
        logger.warning(
            "No data to plot for '%s'. Skipping plot generation.", config.plot_title
        )
        return

    df = pd.DataFrame(data_list)

    try:
        df[date_col] = pd.to_datetime(df[date_col])
        df[value_col] = pd.to_numeric(df[value_col])
    except KeyError:
        logger.exception(
            "Required columns '%s' or '%s' not found in data",
            date_col,
            value_col,
        )
        return
    except ValueError:
        logger.exception("Error converting data to numeric/date format")
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
    plt.title(config.plot_title, fontsize=16, pad=15)
    plt.xlabel("Fecha", fontsize=12)
    plt.ylabel(config.y_label, fontsize=12)
    plt.grid(visible=True, linestyle="--", alpha=0.6)
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

    output_path_dir = Path(config.output_dir)
    output_path_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_path_dir / config.output_filename

    plt.savefig(plot_path, bbox_inches="tight")
    plt.close()
    logger.info("Plot saved to %s", plot_path)


def _extract_bond_data(bond_data_list, current_date):
    """Extract days to maturity, TEM values, and labels from bond data."""
    days_to_maturity = []
    tem_values = []
    labels = []

    for bond in bond_data_list:
        maturity_date_str = bond.get("maturity_date")
        tem = bond.get("calculated_rates", {}).get("TEM")
        ticker = bond.get("ticker")

        if maturity_date_str and maturity_date_str != "N/A" and tem is not None:
            try:
                maturity_date = datetime.strptime(
                    maturity_date_str, "%Y-%m-%d"
                ).replace(tzinfo=UTC)
                delta = maturity_date - current_date

                if delta.days > 0:
                    days_to_maturity.append(delta.days)
                    tem_values.append(float(tem * Decimal(100)))
                    labels.append(ticker)
                else:
                    logger.warning(
                        "Skipping %s: Maturity date is in the past or today (%s).",
                        ticker,
                        maturity_date_str,
                    )
            except ValueError:
                logger.warning(
                    "Could not parse maturity date for %s: %s. Skipping.",
                    ticker,
                    maturity_date_str,
                )
        else:
            logger.warning(
                "Skipping %s: Missing maturity date (%s) or TEM (%s).",
                ticker,
                maturity_date_str,
                tem,
            )

    return days_to_maturity, tem_values, labels


def _plot_scatter_and_curve(x_data, y_data):
    """Plot scatter points and polynomial curve."""
    plt.scatter(
        x_data,
        y_data,
        color="skyblue",
        edgecolor="darkblue",
        s=80,
        zorder=5,
    )

    if len(x_data) > MIN_DATA_POINTS_FOR_CURVE:
        z = np.polyfit(x_data, y_data, 2)
        p = np.poly1d(z)
        x_smooth = np.linspace(x_data.min(), x_data.max(), 300)
        y_smooth = p(x_smooth)
        plt.plot(
            x_smooth,
            y_smooth,
            color="blue",
            linestyle="-",
            linewidth=2,
            alpha=0.8,
            zorder=3,
        )


def _add_plot_labels_and_formatting(
    x_data, sorted_data: tuple, *, plot_title, current_date
):
    """
    Add labels, formatting, and styling to the plot.

    Args:
        x_data: Array of x-axis data
        sorted_data: Tuple of (days_sorted, tem_sorted, labels_sorted)
        plot_title: Title for the plot
        current_date: Current date for the title

    """
    days_sorted, tem_sorted, labels_sorted = sorted_data

    for i, txt in enumerate(labels_sorted):
        plt.annotate(
            txt,
            (days_sorted[i], tem_sorted[i]),
            textcoords="offset points",
            xytext=(0, 12),
            ha="center",
            fontsize=9,
            color="dimgray",
        )

    plt.title(
        f"{plot_title} - TEM vs. Días a Vencimiento ({current_date.strftime('%Y-%m-%d')})",
        fontsize=18,
        pad=20,
    )
    plt.xlabel("Días a Vencimiento", fontsize=14, labelpad=15)
    plt.ylabel("TEM (Tasa Efectiva Mensual) [%]", fontsize=14, labelpad=15)
    plt.grid(visible=True, linestyle="--", alpha=0.5, zorder=0)
    plt.tick_params(axis="both", which="major", labelsize=12)
    plt.gca().yaxis.set_major_formatter(FormatStrFormatter("%.2f%%"))
    plt.xlim(0, x_data.max() * 1.1)


def plot_tem_vs_days_to_maturity(
    bond_data_list: list,
    plot_title: str,
    output_filename: str,
    output_dir: str = "plots",
):
    """Plot TEM vs days to maturity for a list of bonds."""
    current_date = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    days_to_maturity, tem_values, labels = _extract_bond_data(
        bond_data_list, current_date
    )

    if len(days_to_maturity) < MIN_DATA_POINTS_FOR_CURVE:
        logger.info(
            "Not enough valid data points (found %d) to plot for '%s'. Skipping.",
            len(days_to_maturity),
            plot_title,
        )
        return

    sorted_data = sorted(zip(days_to_maturity, tem_values, labels, strict=True))
    days_sorted, tem_sorted, labels_sorted = zip(*sorted_data, strict=True)

    x_data = np.array(days_sorted)
    y_data = np.array(tem_sorted)

    plt.figure(figsize=(16, 9))
    _plot_scatter_and_curve(x_data, y_data)
    _add_plot_labels_and_formatting(
        x_data,
        (days_sorted, tem_sorted, labels_sorted),
        plot_title=plot_title,
        current_date=current_date,
    )

    plt.tight_layout(pad=3.0)
    plt.figtext(
        0.5,
        0.01,
        "Fuente: Elaboración propia en base a datos de BCRA y BYMA",
        ha="center",
        fontsize=10,
        color="dimgray",
    )

    output_path_dir = Path(output_dir)
    output_path_dir.mkdir(parents=True, exist_ok=True)
    plot_path = output_path_dir / output_filename

    plt.savefig(plot_path, bbox_inches="tight", dpi=150)
    plt.close()
    logger.info("Smooth curve plot saved to %s", plot_path)
