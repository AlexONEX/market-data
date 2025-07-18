import logging
from datetime import datetime, date
import os
import json
from services.ppi_service import PPIService
from decimal import Decimal, ROUND_HALF_UP, getcontext

# Configurar el contexto Decimal de forma global para alta precisión
getcontext().prec = 50
getcontext().rounding = ROUND_HALF_UP

logger = logging.getLogger(__name__)


class BondAnalyzer:
    def __init__(self):
        """Inicializa el analizador de bonos."""
        self.ppi_service = PPIService()
        self.instrument_type_mapping = self._load_instrument_type_mapping()
        self.today = date.today()

    def _load_instrument_type_mapping(self):
        """Carga el mapeo de tipos de instrumentos desde un archivo JSON."""
        try:
            with open("data/instrument_types_mapping.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(
                "instrument_types_mapping.json no encontrado. Se inicia con un mapeo vacío."
            )
            return {}
        except json.JSONDecodeError:
            logger.error(
                "Error al decodificar instrument_types_mapping.json. Se inicia con un mapeo vacío."
            )
            return {}

    def _save_instrument_type_mapping(self):
        """Guarda el mapeo actual de tipos de instrumentos en un archivo JSON."""
        os.makedirs("data", exist_ok=True)
        with open("data/instrument_types_mapping.json", "w") as f:
            json.dump(self.instrument_type_mapping, f, indent=4)
        logger.info(
            "Mapeo de tipos de instrumento guardado en data/instrument_types_mapping.json"
        )

    def _parse_date(self, date_str: str | None) -> datetime | None:
        """Convierte una cadena de fecha en un objeto datetime, manejando múltiples formatos."""
        if not date_str:
            return None
        try:
            # Intenta formato ISO (YYYY-MM-DDTHH:MM:SSZ o YYYY-MM-DDTHH:MM:SS)
            return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        except ValueError:
            try:
                # Intenta formato YYYY-MM-DD
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                try:
                    # Intenta formato DD/MM/YYYY
                    return datetime.strptime(date_str, "%d/%m/%Y")
                except ValueError:
                    logger.error(
                        f"No se pudo parsear la fecha en ningún formato conocido: {date_str}"
                    )
                    return None

    def _calculate_rates_from_api_tir(self, api_tir_as_tea: Decimal | None) -> dict:
        """
        Calcula TEM, TNA y TEA a partir de la TIR de la API, asumiendo que es una TEA.
        """
        if api_tir_as_tea is None or api_tir_as_tea < Decimal("-1"):
            logger.warning(
                f"TIR de API inválida para el cálculo de tasas: {api_tir_as_tea}"
            )
            return {"TNA": None, "TEA": None, "TEM": None}

        # La TIR de la API es nuestra TEA (Tasa Efectiva Anual)
        tea = api_tir_as_tea

        # Calcular TEM desde TEA: TEM = (1 + TEA)^(1/12) - 1
        exponent_monthly = Decimal("1") / Decimal("12")
        tem = (Decimal("1") + tea) ** exponent_monthly - Decimal("1")

        # Calcular TNA desde TEM: TNA = TEM * 12 (definición común)
        tna = tem * Decimal("12")

        return {"TNA": tna, "TEA": tea, "TEM": tem}

    def analyze_bond(
        self,
        ticker: str,
        price_input: Decimal,
        quantity_value: Decimal,
        amount_of_money_value: Decimal,
        quantity_type_str: str,
        focus_on_quantity: bool,
    ) -> dict | None:
        """
        Analiza un bono obteniendo datos de la API de PPI y calculando sus tasas de rendimiento.
        """
        logger.info(f"Analizando bono: {ticker} usando el endpoint Bonds/Estimate.")
        logger.info(
            f"Input para {ticker}: Precio={price_input}, Tipo Cant.={quantity_type_str}, Cant.={quantity_value}, Monto={amount_of_money_value}"
        )

        api_quantity = quantity_value if focus_on_quantity else Decimal("0")
        api_amount_of_money = (
            amount_of_money_value if not focus_on_quantity else Decimal("0")
        )

        estimation_data = self.ppi_service.get_bond_estimation_details(
            ticker=ticker,
            quantity_type=quantity_type_str,
            quantity=api_quantity,
            amount_of_money=api_amount_of_money,
            price=price_input,
        )

        if not estimation_data:
            logger.error(
                f"No se pudieron obtener los detalles de estimación para {ticker}."
            )
            return None

        # --- PUNTO CLAVE: Usamos la TIR de la API como la fuente de verdad ---
        ppi_tir = (
            Decimal(str(estimation_data["tir"]))
            if estimation_data.get("tir") is not None
            else None
        )

        expiration_date_str = estimation_data.get("expirationDate")
        maturity_date = self._parse_date(expiration_date_str)

        if not maturity_date:
            logger.error(
                f"No se pudo determinar la fecha de vencimiento para {ticker}. No se pueden calcular las tasas."
            )
            return None

        days_to_maturity = (maturity_date.date() - self.today).days

        market_data_current = self.ppi_service.get_price(
            ticker, self.instrument_type_mapping.get(ticker, "BONOS")
        )
        current_market_price = (
            Decimal(str(market_data_current.get("price")))
            if market_data_current and market_data_current.get("price") is not None
            else None
        )

        # --- CAMBIO IMPORTANTE: Llamamos a la nueva función de cálculo correcta ---
        logger.info(
            f"Calculando tasas para {ticker} basado en la TIR de la API (como TEA): {ppi_tir}"
        )
        calculated_rates = self._calculate_rates_from_api_tir(ppi_tir)

        logger.info(
            f"Tasas calculadas correctamente -> TEM: {calculated_rates.get('TEM', 'N/A')}, TNA: {calculated_rates.get('TNA', 'N/A')}, TEA: {calculated_rates.get('TEA', 'N/A')}"
        )

        # El resto de la información es para visualización y contexto
        conversion_factor = Decimal("100")
        amount_to_receive_display = (
            Decimal(str(estimation_data.get("amountToReceive", 0))) * conversion_factor
        )

        return {
            "ticker": ticker,
            "description": estimation_data.get("title", "N/A"),
            "current_market_price": current_market_price,
            "price_used_for_calc": price_input,
            "calculated_rates": calculated_rates,  # <-- Tasas correctas
            "maturity_date": maturity_date.strftime("%Y-%m-%d")
            if maturity_date
            else "N/A",
            "days_to_maturity": days_to_maturity,
            "ppi_original_tir": ppi_tir,
            "amount_to_receive_api": amount_to_receive_display,  # Mantenemos esto como dato informativo
            "currency": estimation_data.get("currency"),
            "isin": estimation_data.get("isin"),
            # Puedes añadir otros campos de 'estimation_data' que necesites aquí
        }
