import csv
import logging
from datetime import date
from decimal import Decimal

import requests
from requests.exceptions import RequestException
import matplotlib.pyplot as plt

from src.domain.financial_math import calculate_tir
from src.gateway.puentenet_fetcher import PuenteNetFetcher

# --- Configuración ---
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

URL_BONDS = "https://data912.com/live/arg_bonds"
URL_NOTES = "https://data912.com/live/arg_notes"
OUTPUT_CSV = "src/data/tirs.csv"

# --- Listas de bonos (ejemplos, ajustar según necesidad) ---
# Estos son ejemplos. La idea es que el script los obtenga dinámicamente o se configuren.
# Para el placeholder de PuenteNetFetcher, solo AL30 y GD30 tienen datos.
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
    ],  # Agregado GD38
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
        "TY30P",  # Nuevos tickers
    ],
    # "cer": [], # Para más adelante
    # "dolar_linked": [], # Para más adelante
}


def fetch_instruments_from_data912(url: str) -> list[dict]:
    """
    Obtiene la lista de instrumentos desde una URL de data912.
    """
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Lanza un error para respuestas 4xx/5xx
        logging.info(f"Datos obtenidos exitosamente de {url}")
        return response.json()
    except RequestException as e:
        logging.error(f"Error al contactar a {url}: {e}")
        return []
    except ValueError:  # Incluye json.JSONDecodeError
        logging.error(f"Error al decodificar el JSON de {url}")
        return []


def get_all_data912_instruments() -> dict[str, dict]:
    """
    Obtiene todos los instrumentos de data912 y los organiza por ticker.
    Retorna un diccionario {ticker: instrument_data}.
    """
    all_instruments_list = []
    all_instruments_list.extend(fetch_instruments_from_data912(URL_BONDS))
    all_instruments_list.extend(fetch_instruments_from_data912(URL_NOTES))

    instruments_by_ticker = {}
    for instrument in all_instruments_list:
        ticker = instrument.get("symbol")
        if ticker:
            instruments_by_ticker[ticker] = instrument
    return instruments_by_ticker


def plot_yield_curve(bond_data: list[dict], title: str, filename: str, today: date):
    """
    Genera un gráfico de curva de rendimiento.
    bond_data: Lista de diccionarios con 'ticker', 'tir' y 'maturity_date'.
    """
    if not bond_data:
        logging.warning(f"No hay datos para graficar la curva de {title}.")
        return

    # Filtrar datos válidos para el gráfico y calcular tiempo a vencimiento
    plot_points = []
    for bond in bond_data:
        if bond.get("tir") is not None and bond.get("maturity_date") is not None:
            time_to_maturity = (
                bond["maturity_date"] - today
            ).days / 365.25  # Usar 365.25 para años bisiestos
            if time_to_maturity > 0:  # Solo bonos con vencimiento futuro
                plot_points.append(
                    {
                        "ticker": bond["ticker"],
                        "time_to_maturity": time_to_maturity,
                        "tir": bond["tir"],
                    }
                )

    if not plot_points:
        logging.warning(f"No hay puntos válidos para graficar la curva de {title}.")
        return

    plot_points.sort(
        key=lambda x: x["time_to_maturity"]
    )  # Ordenar por tiempo a vencimiento

    times = [p["time_to_maturity"] for p in plot_points]
    tirs = [p["tir"] * 100 for p in plot_points]  # Convertir a porcentaje
    labels = [f"{p['ticker']} ({p['tir'] * 100:.2f}%) " for p in plot_points]

    plt.figure(figsize=(14, 8))
    plt.plot(times, tirs, marker="o", linestyle="-")
    plt.title(title)
    plt.xlabel("Tiempo a Vencimiento (años)")
    plt.ylabel("TIR (%)")
    plt.grid(True)

    # Añadir etiquetas a los puntos
    for i, txt in enumerate(labels):
        plt.annotate(
            txt,
            (times[i], tirs[i]),
            textcoords="offset points",
            xytext=(5, 5),
            ha="left",
        )

    plt.tight_layout()
    plt.savefig(filename)
    plt.close()
    logging.info(f"Gráfico '{title}' guardado en {filename}")


def main():
    """
    Script principal para calcular y guardar las TIRs y generar gráficos.
    """
    logging.info("Iniciando el proceso de cálculo de TIRs...")

    puentenet_fetcher = PuenteNetFetcher()
    all_data912_instruments = get_all_data912_instruments()

    results = []  # Para almacenar los resultados y luego graficar
    today = date.today()

    # Preparar archivo CSV
    with open(OUTPUT_CSV, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Ticker", "Tipo", "Precio", "TIR (%)", "Fecha Vencimiento"])

        processed_count = 0

        for bond_type, tickers in BOND_TICKERS.items():
            for ticker_base in tickers:
                # Para bonos hard_dollar, usar el ticker con 'D'
                if bond_type == "hard_dollar":
                    ticker_data912 = ticker_base + "D"
                    puentenet_ticker = ticker_base
                else:
                    # Para LECAPs/BONCAPs, el ticker es el mismo para data912 y PuenteNet
                    ticker_data912 = ticker_base
                    puentenet_ticker = ticker_base

                instrument_data = all_data912_instruments.get(ticker_data912)

                if not instrument_data:
                    logging.warning(
                        f"Instrumento {ticker_data912} no encontrado en data912. Saltando."
                    )
                    continue

                price_bid = Decimal(str(instrument_data.get("px_bid", "0")))
                price_ask = Decimal(str(instrument_data.get("px_ask", "0")))
                price_close = Decimal(str(instrument_data.get("c", "0")))

                # Seleccionar el precio a usar (prioridad: close, ask, bid)
                price = (
                    price_close
                    if price_close > 0
                    else (price_ask if price_ask > 0 else price_bid)
                )

                if price <= 0:
                    logging.warning(
                        f"Ignorando {ticker_data912} por precio no válido ({price})."
                    )
                    continue

                # Asumimos que el precio de los tickers 'D' ya está en USD por 100 nominal.
                # Para LECAPs/BONCAPs, asumimos que el precio ya está en ARS por 100 nominal.
                normalized_price = price

                logging.info(
                    f"Procesando {ticker_data912} ({bond_type}) con precio ${normalized_price:.2f}..."
                )

                # 1. Obtener flujo de fondos (desde caché/CSV o PuenteNet)
                cashflow_dicts = puentenet_fetcher.get_cashflows(puentenet_ticker)

                # Convertir a formato (date, Decimal) para calculate_tir
                cashflow = [(cf["date"], cf["total_payment"]) for cf in cashflow_dicts]

                if not cashflow:
                    logging.warning(
                        f"No se encontró flujo de fondos para {puentenet_ticker}. Saltando."
                    )
                    continue

                # 2. Calcular TIR
                tir = calculate_tir(cashflow, normalized_price, settlement_date=today)

                # 3. Obtener fecha de vencimiento (placeholder, se necesita de PuenteNet o data912)
                # Por ahora, tomamos la fecha del último flujo de caja como vencimiento aproximado
                maturity_date = cashflow[-1][0] if cashflow else None

                # 4. Guardar resultado
                if tir is not None and maturity_date is not None:
                    tir_percentage = tir * Decimal("100")
                    writer.writerow(
                        [
                            ticker_data912,
                            bond_type,
                            f"{normalized_price:.2f}",
                            f"{tir_percentage:.2f}",
                            maturity_date.isoformat(),
                        ]
                    )
                    logging.info(
                        f"  -> TIR calculada para {ticker_data912}: {tir_percentage:.2f}%"
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
                else:
                    logging.warning(
                        f"No se pudo calcular la TIR o obtener vencimiento para {ticker_data912}."
                    )

    logging.info("Proceso completado.")
    logging.info(
        f"Se calcularon y guardaron las TIRs para {processed_count} instrumentos en '{OUTPUT_CSV}'."
    )

    # --- Generar gráficos ---
    hard_dollar_bonds = [b for b in results if b["type"] == "hard_dollar"]
    plot_yield_curve(
        hard_dollar_bonds,
        "Curva de Rendimiento Bonos Hard Dollar",
        "src/plots/yield_curve_hard_dollar.png",
        today,
    )

    # Para la curva de tasa fija en pesos, necesitaríamos identificar esos bonos.
    # Con los placeholders actuales, no tenemos esa distinción clara.
    # Asumiendo que 'lecap_boncap' son de tasa fija en pesos para el ejemplo.
    fixed_rate_peso_bonds = [b for b in results if b["type"] == "lecap_boncap"]
    plot_yield_curve(
        fixed_rate_peso_bonds,
        "Curva de Rendimiento Tasa Fija Pesos (LECAP/BONCAP)",
        "src/plots/yield_curve_fixed_rate_peso.png",
        today,
    )


if __name__ == "__main__":
    main()
