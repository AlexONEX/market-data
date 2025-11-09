#!/usr/bin/env python3

import csv
import logging
import os
from datetime import date
from decimal import Decimal

import matplotlib.pyplot as plt
import numpy as np
import requests
from requests.exceptions import RequestException
from src.gateway.puentenet_fetcher import PuenteNetFetcher

from src.domain.financial_math import calculate_tir

# Minimal logging - only errors and critical info
logging.basicConfig(level=logging.ERROR)

URL_BONDS = "https://data912.com/live/arg_bonds"
URL_NOTES = "https://data912.com/live/arg_notes"
OUTPUT_CSV = "src/data/tirs.csv"

BOND_TICKERS = {
    "hard_dollar": [
        "AL30",
        "GD30",
        "AL29",
        "GD29",
        "AE38",
        "AL35",
        "GD35",
        "AL41",
        "GD38",
        "GD41",
        "AL46",
        "GD46",
    ],
    "lecap_boncap": [
        "M10N5",
        "M15D5",
        "M16E6",
        "M27F6",
        "S10N5",
        "S16E6",
        "S27F6",
        "S28N5",
        "S29Y6",
        "S30A6",
        "S30O6",
        "T30E6",
        "T30J6",
        "TD5D",
        "T15D5",
        "T15E7",
        "T30A6",
        "T30A7",
        "T30J6",
        "TY30P",
    ],
}


def fetch_instruments_from_data912(url: str) -> list[dict]:
    """Fetch instruments from data912 API."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.json()
    except RequestException:
        return []
    except ValueError:
        return []


def get_all_data912_instruments() -> dict[str, dict]:
    """Get all instruments from data912 organized by ticker."""
    all_instruments_list = []
    all_instruments_list.extend(fetch_instruments_from_data912(URL_BONDS))
    all_instruments_list.extend(fetch_instruments_from_data912(URL_NOTES))

    instruments_by_ticker = {}
    for instrument in all_instruments_list:
        ticker = instrument.get("symbol")
        if ticker:
            instruments_by_ticker[ticker] = instrument
    return instruments_by_ticker


def _plot_single_curve(points, label, color, is_lecap):
    """Plots a single yield curve with optional smoothing and special handling for LECAP/BONCAP bonds."""
    if not points:
        return

    points.sort(key=lambda x: x["time_to_maturity"])
    times = np.array([p["time_to_maturity"] for p in points])

    if is_lecap:
        # Convert TIR to TEM
        rates = np.array(
            [float(((1 + float(p["tir"])) ** (1 / 12) - 1) * 100) for p in points]
        )
        labels = [
            f"{p['ticker']} ({((1 + float(p['tir'])) ** (1 / 12) - 1) * 100:.2f}%)"
            for p in points
        ]
    else:
        rates = np.array([float(p["tir"] * 100) for p in points])
        labels = [f"{p['ticker']} ({p['tir'] * 100:.2f}%)" for p in points]

    plt.scatter(times, rates, label=f"{label} Points", color=color)

    for i, txt in enumerate(labels):
        plt.annotate(
            txt,
            (times[i], rates[i]),
            textcoords="offset points",
            xytext=(5, 5),
            ha="left",
        )

    # Smooth curve
    if len(times) > 2:
        try:
            # Exclude S16E6 from smoothing if it's an outlier in LECAP/BONCAP
            if is_lecap:
                # Find the index of S16E6
                s16e6_index = -1
                for i, p in enumerate(points):
                    if p["ticker"] == "S16E6":
                        s16e6_index = i
                        break

                if s16e6_index != -1:
                    # Create new arrays excluding S16E6
                    times_for_fit = np.delete(times, s16e6_index)
                    rates_for_fit = np.delete(rates, s16e6_index)
                else:
                    times_for_fit = times
                    rates_for_fit = rates
            else:
                times_for_fit = times
                rates_for_fit = rates

            if (
                len(times_for_fit) > 2
            ):  # Ensure enough points for fitting after exclusion
                deg = 2 if is_lecap else min(3, len(times_for_fit) - 1)
                p = np.polyfit(times_for_fit, rates_for_fit, deg)
                f = np.poly1d(p)
                t_smooth = np.linspace(times.min(), times.max(), 300)
                rate_smooth = f(t_smooth)
                plt.plot(t_smooth, rate_smooth, label=f"{label} Curve", color=color)
            else:
                # Fallback to simple line if not enough points for fitting
                plt.plot(times, rates, linestyle="--", color=color, alpha=0.7)

        except np.linalg.LinAlgError:
            # Fallback to simple line if fitting fails
            plt.plot(times, rates, linestyle="--", color=color, alpha=0.7)


def plot_yield_curve(bond_data: list[dict], title: str, filename: str, today: date):
    """Generate and save a yield curve plot."""
    if not bond_data:
        return

    is_lecap = "LECAP/BONCAP" in title

    plt.figure(figsize=(14, 8))
    plt.title(title)
    plt.xlabel("Time to Maturity (days)" if is_lecap else "Time to Maturity (years)")
    if is_lecap:
        plt.xscale("log")
    plt.ylabel("TEM (%)" if is_lecap else "TIR (%)")
    plt.grid(True)

    if "Hard Dollar" in title:
        global_bonds = []
        argentinian_law_bonds = []
        for bond in bond_data:
            if bond.get("tir") is not None and bond.get("maturity_date") is not None:
                time_to_maturity = (
                    (bond["maturity_date"] - today).days
                    if is_lecap
                    else (bond["maturity_date"] - today).days / 365.25
                )
                if time_to_maturity > 0:
                    point = {
                        "ticker": bond["ticker"],
                        "time_to_maturity": time_to_maturity,
                        "tir": bond["tir"],
                    }
                    if bond["ticker"].startswith("GD"):
                        global_bonds.append(point)
                    else:
                        argentinian_law_bonds.append(point)

        _plot_single_curve(global_bonds, "Global Bonds", "blue", is_lecap)
        _plot_single_curve(
            argentinian_law_bonds, "Argentinian Law Bonds", "green", is_lecap
        )
        plt.legend()

    else:
        plot_points = []
        for bond in bond_data:
            if bond.get("tir") is not None and bond.get("maturity_date") is not None:
                time_to_maturity = (
                    (bond["maturity_date"] - today).days
                    if is_lecap
                    else (bond["maturity_date"] - today).days / 365.25
                )
                if time_to_maturity > 0:
                    plot_points.append(
                        {
                            "ticker": bond["ticker"],
                            "time_to_maturity": time_to_maturity,
                            "tir": bond["tir"],
                        }
                    )
        _plot_single_curve(plot_points, title, "blue", is_lecap)

    plt.tight_layout()
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    plt.savefig(filename)
    plt.close()


def _get_bond_tickers(bond_type: str, ticker_base: str) -> tuple[str, str]:
    """Determines data912 and PuenteNet tickers based on bond type."""
    if bond_type == "hard_dollar":
        return ticker_base + "D", ticker_base
    return ticker_base, ticker_base


def _get_instrument_price(instrument_data: dict) -> Decimal:
    """Determines the instrument price from available bid, ask, or close prices."""
    price_bid = Decimal(str(instrument_data.get("px_bid", "0")))
    price_ask = Decimal(str(instrument_data.get("px_ask", "0")))
    price_close = Decimal(str(instrument_data.get("c", "0")))

    price = (
        price_close if price_close > 0 else (price_ask if price_ask > 0 else price_bid)
    )
    return price


def main():
    """Main script to calculate Yields (TIRs) and generate yield curves for bond portfolios."""
    puentenet_fetcher = PuenteNetFetcher()
    all_data912_instruments = get_all_data912_instruments()

    results = []
    today = date.today()

    with open(OUTPUT_CSV, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Ticker", "Type", "Price", "TIR (%)", "Maturity Date"])

        processed_count = 0

        for bond_type, tickers in BOND_TICKERS.items():
            for ticker_base in tickers:
                ticker_data912, puentenet_ticker = _get_bond_tickers(
                    bond_type, ticker_base
                )

                instrument_data = all_data912_instruments.get(ticker_data912)

                if not instrument_data:
                    continue

                price = _get_instrument_price(instrument_data)

                if price <= 0:
                    continue

                normalized_price = price

                cashflow_dicts = puentenet_fetcher.get_cashflows(puentenet_ticker)
                cashflow = [(cf["date"], cf["total_payment"]) for cf in cashflow_dicts]

                if not cashflow:
                    continue

                tir = calculate_tir(cashflow, normalized_price, settlement_date=today)
                maturity_date = cashflow[-1][0] if cashflow else None

                if tir is not None and maturity_date is not None:
                    tir_percentage = tir * Decimal(100)
                    writer.writerow(
                        [
                            ticker_data912,
                            bond_type,
                            f"{normalized_price:.2f}",
                            f"{tir_percentage:.2f}",
                            maturity_date.isoformat(),
                        ]
                    )
                    results.append(
                        {
                            "ticker": ticker_data912,
                            "type": bond_type,
                            "price": normalized_price,
                            "tir": tir,
                            "maturity_date": maturity_date,
                        }
                    )
                    processed_count += 1

    hard_dollar_bonds = [b for b in results if b["type"] == "hard_dollar"]
    plot_yield_curve(
        hard_dollar_bonds,
        "Hard Dollar Bonds Yield Curve",
        "src/plots/yield_curve_hard_dollar.png",
        today,
    )

    lecap_boncap_bonds = [b for b in results if b["type"] == "lecap_boncap"]
    plot_yield_curve(
        lecap_boncap_bonds,
        "LECAP/BONCAP Yield Curve",
        "src/plots/yield_curve_fixed_rate_peso.png",
        today,
    )

    print(f"Processed {processed_count} instruments")
    print(f"Results saved to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
