import logging
import csv
import os
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PuenteNetFetcher:
    """
    Obtiene flujos de fondos de PuenteNet y los persiste/carga desde un CSV.
    """

    BASE_URL = "https://www.puentenet.com/"
    CASHFLOW_ENDPOINT = "herramientas/flujo-de-fondos/calcular"
    CASHFLOW_CSV = "src/data/cashflows.csv"

    def __init__(self):
        self._cashflow_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._load_cashflows_from_csv()

    def _load_cashflows_from_csv(self):
        """
        Carga los flujos de fondos desde el archivo CSV al caché interno.
        """
        if not os.path.exists(self.CASHFLOW_CSV):
            return

        with open(self.CASHFLOW_CSV, mode="r", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                ticker = row["Ticker"]
                payment_date = datetime.strptime(row["PaymentDate"], "%Y-%m-%d").date()
                total_payment = Decimal(row["TotalPayment"])
                amortization = Decimal(row["Amortization"])
                interest = Decimal(row["Interest"])

                if ticker not in self._cashflow_cache:
                    self._cashflow_cache[ticker] = []
                self._cashflow_cache[ticker].append(
                    {
                        "date": payment_date,
                        "total_payment": total_payment,
                        "amortization": amortization,
                        "interest": interest,
                    }
                )
        logging.info(
            f"Cargados {len(self._cashflow_cache)} tickers con flujos de fondos desde {self.CASHFLOW_CSV}"
        )

    def _save_cashflows_to_csv(self, ticker: str, cashflows: List[Dict[str, Any]]):
        """
        Guarda los flujos de fondos de un ticker al archivo CSV.
        """
        file_exists = os.path.exists(self.CASHFLOW_CSV)
        is_empty = not file_exists or os.stat(self.CASHFLOW_CSV).st_size == 0

        with open(self.CASHFLOW_CSV, mode="a", newline="") as file:
            writer = csv.writer(file)
            if is_empty:
                writer.writerow(
                    [
                        "Ticker",
                        "PaymentDate",
                        "TotalPayment",
                        "Amortization",
                        "Interest",
                    ]
                )

            for cf in cashflows:
                writer.writerow(
                    [
                        ticker,
                        cf["date"].isoformat(),
                        str(cf["total_payment"]),
                        str(cf["amortization"]),
                        str(cf["interest"]),
                    ]
                )
        logging.info(f"Flujos de fondos para {ticker} guardados en {self.CASHFLOW_CSV}")

    def get_cashflows(
        self, ticker: str, nominal_value: int = 100
    ) -> List[Dict[str, Any]]:
        if ticker in self._cashflow_cache:
            logging.info(f"Flujos de fondos para {ticker} encontrados en caché/CSV.")
            return self._cashflow_cache[ticker]

        raw_data = self._fetch_from_puentenet(ticker, nominal_value)
        if raw_data:
            parsed_cashflows = self.parse_cashflows(raw_data)
            if parsed_cashflows:
                self._cashflow_cache[ticker] = parsed_cashflows
                self._save_cashflows_to_csv(ticker, parsed_cashflows)
                return parsed_cashflows
        return []

    def _fetch_from_puentenet(self, ticker: str, nominal_value: int = 100) -> Any:
        url = f"{self.BASE_URL}{self.CASHFLOW_ENDPOINT}"
        payload = {f"BONO_{ticker}": str(nominal_value)}
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36",
            "Referer": self.BASE_URL + self.CASHFLOW_ENDPOINT.split("/calcular")[0],
        }

        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            response.raise_for_status()
            logging.info(
                f"Datos de flujo de fondos obtenidos para {ticker} de PuenteNet."
            )
            return response.json()
        except RequestException as e:
            logging.error(
                f"Error al obtener flujos de fondos para {ticker} de PuenteNet: {e}"
            )
            return None
        except ValueError:
            logging.error(
                f"Error al decodificar el JSON de PuenteNet para {ticker}. Respuesta: {response.text if response else 'No response'}"
            )
            return None

    def parse_cashflows(self, raw_data: Any) -> List[Dict[str, Any]]:
        if not raw_data or not isinstance(raw_data, dict):
            logging.warning("Datos crudos de flujo de fondos inválidos o vacíos.")
            return []

        errores = raw_data.get("errores")
        if errores and isinstance(errores, list) and len(errores) > 0:
            for error in errores:
                logging.warning(f"PuenteNet reportó un error: {error}")
            return []

        target_cashflows = None

        cashflows_by_currency = raw_data.get("mapFlujosDTO", {})
        if cashflows_by_currency and isinstance(cashflows_by_currency, dict):
            for currency_key in ["USD", "ARS", "PESOS"]:
                target_cashflows = cashflows_by_currency.get(currency_key)
                if target_cashflows:
                    break
            if not target_cashflows and cashflows_by_currency:
                first_currency_key = list(cashflows_by_currency.keys())[0]
                target_cashflows = cashflows_by_currency.get(first_currency_key)

        if not target_cashflows:
            target_cashflows = raw_data.get("flujosMapDTO", [])

        if not target_cashflows or not isinstance(target_cashflows, list):
            logging.warning(
                f"La estructura de la respuesta de PuenteNet no contiene flujos esperados. Respuesta: {raw_data}"
            )
            return []

        parsed = []
        for cf in target_cashflows:
            try:
                timestamp_ms = cf.get("fechaPago")
                if timestamp_ms is None:
                    logging.warning(f"Flujo de fondos sin fechaPago: {cf}")
                    continue

                payment_date = datetime.fromtimestamp(timestamp_ms / 1000).date()
                amortization = Decimal(str(cf.get("importeAmortizacion", "0")))
                interest = Decimal(str(cf.get("importeRenta", "0")))
                total_payment = Decimal(str(cf.get("importe", "0")))

                if total_payment > 0:
                    parsed.append(
                        {
                            "date": payment_date,
                            "amortization": amortization,
                            "interest": interest,
                            "total_payment": total_payment,
                        }
                    )
            except (ValueError, TypeError) as e:
                logging.warning(
                    f"Error al parsear un flujo de fondos: {cf}. Error: {e}"
                )
                continue

        parsed.sort(key=lambda x: x["date"])
        return parsed
