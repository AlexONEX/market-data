import csv
import logging
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import requests
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class PuenteNetFetcher:
    BASE_URL = "https://www.puentenet.com/"
    CASHFLOW_ENDPOINT = "herramientas/flujo-de-fondos/calcular"
    CASHFLOW_CSV = Path("src/data/cashflows.csv")

    def __init__(self):
        self._cashflow_cache: dict[str, list[dict[str, Any]]] = {}
        self._load_cashflows_from_csv()

    def _load_cashflows_from_csv(self):
        """Loads cash flows from the CSV file into the internal cache."""
        if not self.CASHFLOW_CSV.exists():
            return

        with self.CASHFLOW_CSV.open(newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                ticker = row["Ticker"]
                payment_date = datetime.strptime(row["PaymentDate"], "%Y-%m-%d").replace(tzinfo=UTC).date()
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
        logger.info(
            "Loaded %d tickers with cash flows from %s", len(self._cashflow_cache), self.CASHFLOW_CSV
        )

    def _save_cashflows_to_csv(self, ticker: str, cashflows: list[dict[str, Any]]):
        file_exists = self.CASHFLOW_CSV.exists()
        is_empty = not file_exists or self.CASHFLOW_CSV.stat().st_size == 0

        with self.CASHFLOW_CSV.open(mode="a", newline="") as file:
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
        logger.info("Cash flows for %s saved to %s", ticker, self.CASHFLOW_CSV)

    def get_cashflows(
        self, ticker: str, nominal_value: int = 100
    ) -> list[dict[str, Any]]:
        if ticker in self._cashflow_cache:
            logger.info("Cash flows for %s found in cache/CSV.", ticker)
            return self._cashflow_cache[ticker]

        logger.info(
            "Cash flows for %s not found in cache/CSV. Attempting to fetch from PuenteNet...", ticker
        )

        raw_data = self._fetch_from_puentenet(ticker, nominal_value)
        if raw_data:
            parsed_cashflows = self._parse_cashflows(raw_data)
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
            logger.info("Cash flow data for %s obtained from PuenteNet.", ticker)
            return response.json()
        except RequestException as e:
            logger.exception("Error fetching cash flows for %s from PuenteNet: %s", ticker, e)
            return None
        except ValueError:
            logger.exception(
                "Error decoding PuenteNet JSON for %s. Response: %s", ticker, response.text if response else "No response" # Q000
            )
            return None

    def _parse_cashflows(self, raw_data: Any) -> list[dict[str, Any]]:
        if not raw_data or not isinstance(raw_data, dict):
            logger.warning("Invalid or empty raw cash flow data.")
            return []

        errors = raw_data.get("errores")
        if errors and isinstance(errors, list) and len(errors) > 0:
            for error in errors:
                logger.warning("PuenteNet reported an error: %s", error)
            return []

        target_cashflows = None

        cashflows_by_currency = raw_data.get("mapFlujosDTO", {})
        if cashflows_by_currency and isinstance(cashflows_by_currency, dict):
            for currency_key in ["USD", "ARS", "PESOS"]:
                target_cashflows = cashflows_by_currency.get(currency_key)
                if target_cashflows:
                    break
            if not target_cashflows and cashflows_by_currency:
                first_currency_key = next(iter(cashflows_by_currency.keys()))
                target_cashflows = cashflows_by_currency.get(first_currency_key)

        if not target_cashflows or not isinstance(target_cashflows, list):
            logger.warning(
                "PuenteNet response structure does not contain expected cash flows. Response: %s", raw_data
            )
            return []

        parsed = []
        for cf in target_cashflows:
            try:
                payment_date_timestamp = cf.get("fechaPago")
                if payment_date_timestamp is None:
                    logger.warning("Cash flow without payment date: %s", cf)
                    continue

                payment_date = datetime.fromtimestamp(
                    payment_date_timestamp / 1000, tz=UTC
                ).date()
                amortization_amount = Decimal(str(cf.get("importeAmortizacion", "0")))
                interest_amount = Decimal(str(cf.get("importeRenta", "0")))
                total_amount = Decimal(str(cf.get("importe", "0")))

                if total_amount > 0:
                    parsed.append(
                        {
                            "date": payment_date,
                            "amortization": amortization_amount,
                            "interest": interest_amount,
                            "total_payment": total_amount,
                        }
                    )
            except (ValueError, TypeError) as e:
                logger.warning("Error parsing a cash flow: %s. Error: %s", cf, e)
                continue

        parsed.sort(key=lambda x: x["date"])
        return parsed
