import logging

from src.gateway.bcra_connector import BCRAAPIConnector
from src.utils.plotter import plot_time_series

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BCRAService:
    """
    Service for interacting with the BCRA API, fetching variable data
    and time series, and delegating plotting to a utility module.
    """

    def __init__(self):
        self.connector = BCRAAPIConnector()
        # Define variable descriptions for BCRA data
        self.variable_descriptions = {
            1: "Reservas Internacionales del BCRA (en millones de dólares - cifras provisorias sujetas a cambio de valuación)",
            4: "Tipo de Cambio Minorista ($ por USD) Comunicación B 9791 - Promedio vendedor",
            5: "Tipo de Cambio Mayorista ($ por USD) Comunicación A 3500 - Referencia",
            6: "Tasa de Política Monetaria (en % n.a.)",
            7: "BADLAR en pesos de bancos privados (en % n.a.)",
            8: "TM20 en pesos de bancos privados (en % n.a.)",
            9: "Tasas de interés de las operaciones de pase activas para el BCRA, a 1 día de plazo (en % n.a.)",
            10: "Tasas de interés de las operaciones de pase pasivas para el BCRA, a 1 día de plazo (en % n.a.)",
            11: "Tasas de interés por préstamos entre entidades financiera privadas (BAIBAR) (en % n.a.)",
            12: "Tasas de interés por depósitos a 30 días de plazo en entidades financieras (en % n.a.)",
            13: "Tasa de interés de préstamos por adelantos en cuenta corriente",
            14: "Tasa de interés de préstamos personales",
            15: "Base monetaria - Total (en millones de pesos)",
            16: "Circulación monetaria (en millones de pesos)",
            17: "Billetes y monedas en poder del público (en millones de pesos)",
            18: "Efectivo en entidades financieras (en millones de pesos)",
            19: "Depósitos de los bancos en cta. cte. en pesos en el BCRA (en millones de pesos)",
            21: "Depósitos en efectivo en las entidades financieras - Total (en millones de pesos)",
            22: "En cuentas corrientes (neto de utilización FUCO) (en millones de pesos)",
            23: "En Caja de ahorros (en millones de pesos)",
            24: "A plazo (incluye inversiones y excluye CEDROS) (en millones de pesos)",
            25: "M2 privado, promedio móvil de 30 días, variación interanual (en %)",
            26: "Préstamos de las entidades financieras al sector privado (en millones de pesos)",
            27: "Inflación mensual (variación en %)",
            28: "Inflación interanual (variación en % i.a.)",
            29: "Inflación esperada - REM próximos 12 meses - MEDIANA (variación en % i.a)",
            30: "CER (Base 2.2.2002=1)",
            31: "Unidad de Valor Adquisitivo (UVA) (en pesos -con dos decimales-, base 31.3.2016=14.05)",
            32: "Unidad de Vivienda (UVI) (en pesos -con dos decimales-, base 31.3.2016=14.05)",
            34: "Tasa de Política Monetaria (en % e.a.)",
            35: "BADLAR en pesos de bancos privados (en % e.a.)",
            40: "Índice para Contratos de Locación (ICL-Ley 27.551, con dos decimales, base 30.6.20=1)",
            41: "Tasas de interés de las operaciones de pase pasivas para el BCRA, a 1 día de plazo (en % e.a.)",
            42: "Pases pasivos para el BCRA - Saldos (en millones de pesos)",
            43: "Tasa de interés para uso de la Justicia - Comunicado P 14290 | Base 01/04/1991 (en %)",  # RUF001
            44: "TAMAR en pesos de bancos privados (en % n.a.)",
            45: "TAMAR en pesos de bancos privados (en % e.a.)",
            46: "Total de factores de explicación de la variación de la Base Monetaria (en millones de $)",
            47: "Efecto monetario de las compras netas de divisas al sector privado y otros (en millones de $)",
            48: "Efecto monetario de las compras netas de divisas al Tesoro Nacional (en millones de $)",
            49: "Efecto monetario de los adelantos transitorios al Tesoro Nacional (en millones de $)",
            50: "Efecto monetario de las transferencia de utilidades al Tesoro Nacional (en millones de $)",
            51: "Efecto monetario del resto de operaciones con el Tesoro Nacional  (en millones de $)",
            52: "Efecto monetario de las operaciones de pases (en millones de $)",
            53: "Efecto monetario de las LELIQ y NOTALIQ (en millones de $)",
            54: "Efecto monetario de los redescuentos y adelantos (en millones de $)",
            55: "Efecto monetario de los intereses, primas y remuneración de cuentas corrientes asociados a op. de pases, LELIQ, NOTALIQ, redescuentos y adel. (en millones de $)",
            56: "Efecto monetario de las LEBAC y NOBAC (en millones de $)",
            57: "Efecto monetario del rescate de cuasimonedas (en millones de $)",
            58: "Efecto monetario de las operaciones con Letras Fiscales de Liquidez (en millones de $)",
            59: "Otras operaciones que explican la variación de la base monetaria (en millones de $)",
            60: "Variación diaria de billetes y monedas en poder del público (en millones de $)",
            61: "Variación diaria de billetes y monedas en entidades financieras (en millones de $)",
            62: "Variación diaria de cheques cancelatorios (en millones de $)",
            63: "Variación diaria de cuentas corrientes en pesos en el BCRA  (en millones de $)",
            64: "Variación diaria de la base monetaria (en millones de $)",
            65: "Variación diaria de cuasimonedas (en millones de $)",
            66: "Variación diaria de la base monetaria más variación diaria de cuasimonedas (en millones de $)",
            67: "Saldo de billetes y monedas en poder del público (en millones de $)",
            68: "Saldo de billetes y monedas en entidades financieras (en millones de $)",
            69: "Saldo de cheques cancelatorios (en millones de $)",
            70: "Saldo de cuentas corrientes en pesos en el BCRA (en millones de $)",
            71: "Saldo de base monetaria (en millones de $)",
            72: "Saldo de cuasimonedas (en millones de $)",
            73: "Saldo de base monetaria más cuasimonedas (en millones de $)",
            74: "Saldo de reservas internacionales (excluidas asignaciones DEG 2009, en millones de USD)",
            75: "Saldo de oro, divisas, colocaciones a plazo y otros activos de reserva (en millones de USD)",
            76: "Saldo de divisas-pase pasivo en dólares con el exterior concertados en 2016 (en millones de USD)",
            77: "Total de variación diaria de las reservas internacionales (en millones de USD)",
            78: "Variación diaria de reservas internacionales por compra de divisas (en millones de USD)",
            79: "Variación diaria de reservas internacionales por operaciones con organismos internacionales (en millones de USD)",
            80: "Variación diaria de reservas internacionales por otras operaciones del sector público (en millones de USD)",
            81: "Variación diaria de reservas internacionales por efectivo mínimo (en millones de USD)",
            82: "Variación diaria de reservas internacionales por otras operaciones no incluidas en otros rubros (en millones de USD)",
            83: "Saldo de Asignaciones de DEGs del año 2009 (en millones de USD)",
            84: "Tipo de cambio peso / dólar estadounidense de valuación contable",
            85: "Saldo de depósitos en pesos en cuentas corrientes de los sectores público y privado no financieros (en millones de $)",
            86: "Saldo de depósitos en pesos en cajas de ahorro de los sectores público y privado no financieros (en millones de $)",
            87: "Saldo de depósitos en pesos a plazo no ajustables por CER/UVAs de los sectores público y privado no financieros (en millones de $)",
            88: "Saldo de depósitos en pesos a plazo ajustables por CER/UVAs de los sectores público y privado no financieros (en millones de $)",
            89: "Saldo de otros depósitos en pesos de los sectores público y privado no financieros (en millones de $)",
            90: "Saldo de CEDROS con CER de los sectores público y privado no financieros (en millones de $)",
            91: "Saldo de los depósitos en pesos de los sectores público y privados no financieros más CEDROS (en millones de $)",
            92: "Saldo de BODEN de los sectores público y privado no financieros (en millones de $)",
            93: "Saldo de los depósitos en pesos del sector público y privados no financieros más CEDRO más BODEN (en millones de $)",
            94: "Saldo de depósitos en pesos cuentas corrientes del sector privado no financiero (en millones de $)",
            95: "Saldo de depósitos en pesos en cajas de ahorro del sector privado no financiero (en millones de $)",
            96: "Saldo de depósitos en pesos a plazo no ajustables por CER/UVAs del sector privado no financiero (en millones de $)",
            97: "Saldo de depósitos en pesos a plazo ajustables por CER/UVAs del sector privado no financiero (en millones de $)",
            98: "Saldo de otros depósitos en pesos del sector privado no financiero (en millones de $)",
            99: "Saldo de CEDROS con CER del sector privado no financiero (en millones de $)",
            100: "Saldo de los depósitos en pesos del sector privado no financiero más CEDROS (en millones de $)",
            101: "Saldo de BODEN del sector privado no financiero (en millones de $)",
            102: "Saldo de los depósitos en pesos del sector privado no financiero más CEDRO más BODEN (en millones de $)",
            103: "Saldo de depósitos en dólares de los sectores público y privado no financieros, expresados en pesos (en millones de $)",
            104: "Saldo de depósitos en dólares del sector privado no financiero, expresados en pesos (en millones de $)",
            105: "Saldo de depósitos en pesos y en dólares de los sectores público y privado no financieros, expresados en pesos (en millones de $)",
            106: "Saldo de depósitos en pesos y dólares del sector privado no financiero, expresados en pesos (en millones de $)",
            107: "Saldo de depósitos en dólares de los sectores público y privado no financieros, expresados en dólares (en millones de USD)",
            108: "Saldo de depósitos en dólares del sector privado no financiero, expresados en dólares (en millones de USD)",
            109: "Saldo del agregado monetario M2 (billetes y monedas en poder del público y depósitos en cuenta corriente y en caja de ahorro en pesos correspondientes al sector privado y al sector público, en millones de $)",
            110: "Saldo de préstamos otorgados al sector privado mediante adelantos en cuenta corriente en pesos (en millones de $)",
            111: "Saldo de préstamos otorgados al sector privado mediante documentos en pesos (en millones de $)",
            112: "Saldo de préstamos hipotecarios en pesos otorgados al sector privado (en millones de $)",
            113: "Saldo de préstamos prendarios en pesos otorgados al sector privado (en millones de $)",
            114: "Saldo de préstamos personales en pesos (en millones de $)",
            115: "Saldo de préstamos en pesos mediante tarjetas de crédito otorgados al sector privado (en millones de $)",
            116: "Saldo de otros préstamos en pesos otorgados al sector privado (en millones de $)",
            117: "Saldo total de préstamos al sector privado en pesos (en millones de $)",
            118: "Saldo de préstamos otorgados al sector privado mediante adelantos en cuenta corriente en dólares (en millones de USD)",
            119: "Saldo de préstamos otorgados al sector privado mediante documentos en dólares (en millones de USD)",
            120: "Saldo de préstamos hipotecarios en dólares otorgados al sector privado (en millones de USD)",
            121: "Saldo de préstamos prendarios en dólares otorgados al sector privado (en millones de USD)",
            122: "Saldo de préstamos personales en dólares (en millones de USD)",
            123: "Saldo de préstamos en dólares mediante tarjetas de crédito otorgados al sector privado(en millones de USD)",
            124: "Saldo de otros préstamos en dólares otorgados al sector privado (en millones de USD)",
            125: "Saldo total de préstamos otorgados al sector privado en dólares (en millones de USD)",
            126: "Saldo total de préstamos otorgados al sector privado en dólares, expresado en pesos (en millones de $)",
            127: "Saldo total de préstamos otorgados del sector privado en pesos y moneda extranjera, expresado en pesos (en millones de $)",
            128: "Tasa de interés de depósitos a plazo fijo en pesos, de 30-44 días , total de operaciones,TNA (en %)",
            129: "Tasa de interés de depósitos a plazo fijo en pesos, de 30-44 días, hasta $100.000, TNA (en %)",
            130: "Tasa de interés de depósitos a plazo fijo en pesos, de 30-44 días, hasta $100.000, TEA (en %)",
            131: "Tasa de interés de depósitos a plazo fijo en pesos, de 30-44 días, de más de $1.000.000, TNA (en %)",
            132: "Tasa de interés de depósitos a plazo fijo en dólares, de 30-44 días, total de operaciones, TNA (en %)",
            133: "Tasa de interés de depósitos a plazo fijo en dólares, de 30-44 días, hasta $100.000, TNA (en %)",
            134: "Tasa de interés de depósitos a plazo fijo en dólares, de 30-44 días, de mas de USD1.000.000, TNA (en %)",
            135: "TAMAR total bancos, TNA (en %)",
            136: "TAMAR de bancos privados,TNA (en %)",
            137: "TAMAR de bancos privados,TEA (en %)",
            138: "BADLAR total bancos, TNA (en %)",
            139: "BADLAR de bancos privados,TNA (en %)",
            140: "BADLAR de bancos privados,TEA (en %)",
            141: "TM20 total bancos, TNA (en %)",
            142: "TM20 de bancos privados, TNA (en %)",
            143: "TM20 de bancos privados, TEA (en %)",
            144: "Tasa de interés de préstamos personales en pesos, TNA (en %)",
            145: "Tasa de interés por adelantos en cuenta corriente en pesos, con acuerdo de 1 a 7 días y de 10 millones o más, a empresas del sector privado, TNA (en %)",
            146: "Tasa de interés por operaciones de préstamos entre entidades financieras locales privadas (BAIBAR, TNA, en %)",
            147: "Monto de operaciones de préstamos entre entidades financieras locales privados (BAIBAR, en millones de $)",
            148: "Tasa de interes por operaciones de préstamos entre entidades financieras locales, TNA (en %)",
            149: "Monto de operaciones de préstamos entre entidades financieras locales (en millones de $)",
            150: "Tasa de interes por operaciones de pases entre terceros a 1 día, TNA (en %)",
            151: "Monto de operaciones de pases entre terceros (en millones de $)",
            152: "Saldo total de pases pasivos para el BCRA (incluye pases pasivos con FCI, en millones de $)",
            153: "Saldo de pases pasivos del BCRA con fondos comunes de inversión (en millones de $)",
            154: "Saldo de pases activos para el BCRA (en millones de $)",
            155: "Saldo de LELIQ y NOTALIQ (en millones de $)",
            156: "Saldo de LEBAC y NOBAC en Pesos, LEGAR y LEMIN  (en millones de $)",
            157: "Saldo de LEBAC y NOBAC en Pesos de Entidades Financieras (en millones de $)",
            158: "Saldo de LEBAC en dólares, LEDIV y BOPREAL  (en millones de USD)",
            159: "Saldo de NOCOM (en millones de $)",
            160: "Tasas de interés de política monetaria, TNA (en %)",
            161: "Tasas de interés de política monetaria, TEA (en %)",
            162: "Tasas de interés del BCRA para pases pasivos en pesos a 1 día, TNA (en %)",
            163: "Tasas de interés del BCRA para pases pasivos en pesos a 7 días, TNA (en %)",
            164: "Tasas de interés del BCRA para pases activos en pesos a 1 días, TNA (en %)",
            165: "Tasas de interés del BCRA para pases activos en pesos a 7 días, TNA (en %)",
            166: "Tasas de interés de LEBAC en Pesos / LELIQ de 1 mes, TNA (en %)",
            167: "Tasas de interés de LEBAC en Pesos de 2 meses, TNA (en %)",
            168: "Tasas de interés de LEBAC en Pesos de 3 meses, TNA (en %)",
            169: "Tasas de interés de LEBAC en Pesos de 4 meses, TNA (en %)",
            170: "Tasas de interés de LEBAC en Pesos de 5 meses, TNA (en %)",
            171: "Tasas de interés de LEBAC en Pesos / LELIQ a 6 meses, TNA (en %)",
            172: "Tasas de interés de LEBAC en Pesos de 7 meses, TNA (en %)",
            173: "Tasas de interés de LEBAC en Pesos de 8 meses, TNA (en %)",
            174: "Tasas de interés de LEBAC en Pesos de 9 meses, TNA (en %)",
            175: "Tasas de interés de LEBAC en Pesos de 10 meses, TNA (en %)",
            176: "Tasas de interés de LEBAC en Pesos de 11 meses, TNA (en %)",
            177: "Tasas de interés de LEBAC en Pesos de 12 meses, TNA (en %)",
            178: "Tasas de interés de LEBAC en Pesos de 18 meses, TNA (en %)",
            179: "Tasas de interés de LEBAC en Pesos de 24 meses, TNA (en %)",
            180: "Tasas de interés de LEBAC en pesos ajustables por CER de 6 meses, TNA (en %)",
            181: "Tasas de interés de LEBAC en pesos ajustables por CER de 12 meses, TNA (en %)",
            182: "Tasas de interés de LEBAC en pesos ajustables por CER de 18 meses, TNA (en %)",
            183: "Tasas de interés de LEBAC en pesos ajustables por CER de 24 meses, TNA (en %)",
            184: "Tasas de interés de LEBAC en dólares, con liquidación en pesos, de 1 mes, TNA (en %)",
            185: "Tasas de interés de LEBAC en dólares, con liquidación en pesos, de 6 meses, TNA (en %)",
            186: "Tasas de interés de LEBAC en dólares, con liquidación en pesos, de 12 meses, TNA (en %)",
            187: "Tasas de interés de LEBAC en dólares, con liquidación en dólares, de 1 mes, TNA (en %)",
            188: "Tasas de interés de LEBAC en dólares, con liquidación en dólares, de 3 meses, TNA (en %)",
            189: "Tasas de interés de LEBAC en dólares, con liquidación en dólares, de 6 meses, TNA (en %)",
            190: "Tasas de interés de LEBAC en dólares, con liquidación en dólares, de 12 meses, TNA (en %)",
            191: "Margen sobre BADLAR Bancos Privados de NOBAC de 9 meses (en %)",
            192: "Margen sobre Bancos Privados de NOBAC de 12 meses (en %)",
            193: "Margen sobre BADLAR Total de NOBAC de 2 Años (en %)",
            194: "Margen sobre BADLAR Bancos Privados de NOBAC de 2 Años (en %)",
            195: "Margen sobre Tasa de Politica Monetaria de NOTALIQ en Pesos de 190 dias (en %)",
            196: "Saldo de Letras Fiscales de Liquidez en cartera de entidades financieras, en valor técnico (en millones de $)",
            197: "Saldo de M2 Transaccional del Sector Privado (expresado en millones de Pesos)",
        }

    def get_principal_variable_data(self, variable_id: int) -> dict | None:
        data = self.connector._get_series_data(variable_id)  # SLF001
        if data:
            return data[0]
        logger.warning(
            "Could not retrieve the latest value for variable ID: %s", variable_id
        )
        return None

    def get_time_series_data(self, variable_id: int) -> list | None:
        return self.connector._get_series_data(variable_id)  # SLF001

    def plot_bcra_series(self, variable_id: int, output_dir: str = "plots"):
        description = self.variable_descriptions.get(
            variable_id,
            f"Variable ID: {variable_id}",  # UP031
        )
        data_results = self.get_time_series_data(variable_id)

        if not data_results:
            logger.warning(
                "No data retrieved to plot series for %s (ID: %s).",
                description,
                variable_id,
            )
            return

        # Determine Y-axis label based on description
        y_label = "Valor"  # Default label
        if "millones de dólares" in description:
            y_label = "Millones de Dólares"
        elif "millones de pesos" in description:
            y_label = "Millones de Pesos"
        elif "(en %" in description:  # Catch all for percentages (n.a., e.a., i.a.)
            y_label = "Porcentaje (%)"
        elif "($ por USD)" in description:
            y_label = "$ por USD"
        elif "Base" in description and "en %" in description:  # Tasa de Justicia
            y_label = "Tasa (%)"

        safe_filename = f"{description.replace(' ', '_').replace('/', '_').replace(':', '').replace('%', 'pct').replace('(', '').replace(')', '').lower()}_id{variable_id}.png"
        safe_filename = "".join(
            c for c in safe_filename if c.isalnum() or c in ["_", "."]
        ).replace("__", "_")

        plot_time_series(
            data_results,
            date_col="fecha",
            value_col="valor",
            plot_title=description,
            output_filename=safe_filename,
            y_label=y_label,
            output_dir=output_dir,
        )


if __name__ == "__main__":
    bcra_service = BCRAService()

    logger.info("--- Fetching and plotting Interest Rates ---")
    tasas_interes_ids = [6, 34, 44, 45, 7, 35, 8, 9, 11, 12, 13, 14, 43]
    for var_id in tasas_interes_ids:
        bcra_service.plot_bcra_series(var_id)

    logger.info("--- Fetching and plotting Monetary Base and Deposits Variables ---")
    base_monetaria_vars_ids = [15, 16, 17, 18, 19, 21, 22, 23, 24, 25]
    for var_id in base_monetaria_vars_ids:
        bcra_service.plot_bcra_series(var_id)

    logger.info("--- Fetching and plotting International Reserves ---")
    bcra_service.plot_bcra_series(1)

    logger.info("--- Example of fetching a principal (latest) value ---")
    # Tasa de Política Monetaria (en % n.a.)
    tpm_id = 6
    latest_tpm = bcra_service.get_principal_variable_data(tpm_id)
    if latest_tpm:
        logger.info(
            "Latest %s: %s (Fecha: %s)",
            bcra_service.variable_descriptions.get(tpm_id),
            latest_tpm.get("valor"),
            latest_tpm.get("fecha"),
        )

    # Tipo de Cambio Minorista ($ por USD)
    tc_minorista_id = 4
    latest_tc_minorista = bcra_service.get_principal_variable_data(tc_minorista_id)
    if latest_tc_minorista:
        logger.info(
            "Latest %s: %s (Fecha: %s)",
            bcra_service.variable_descriptions.get(tc_minorista_id),
            latest_tc_minorista.get("valor"),
            latest_tc_minorista.get("fecha"),
        )
