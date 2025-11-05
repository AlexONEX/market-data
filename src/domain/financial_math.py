"""
Módulo para cálculos financieros y matemáticos.
"""
from datetime import date
from decimal import Decimal, getcontext, InvalidOperation, DivisionByZero
import logging

# Configuración de alta precisión para cálculos decimales
getcontext().prec = 50

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO) # Revert to INFO level

def calculate_tir(
    cashflows: list[tuple[date, Decimal]], price: Decimal, settlement_date: date
) -> Decimal | None:
    """
    Calcula la Tasa Interna de Retorno (TIR) para una serie de flujos de caja y un precio dado,
    utilizando el método de Newton-Raphson para flujos no periódicos (XIRR).

    Args:
        cashflows: Lista de tuplas (fecha, monto) para cada flujo de caja futuro.
        price: El precio de compra del bono (inversión inicial).
        settlement_date: La fecha de liquidación de la compra.

    Returns:
        La TIR como un valor Decimal, o None si no se puede calcular.
    """
    if not cashflows or price <= 0:
        logger.debug(f"calculate_tir: Cashflows vacíos o precio <= 0. Price: {price}")
        return None

    # Filtrar flujos de caja que ya pasaron
    future_cashflows = []
    for cf_date, cf_amount in cashflows:
        if cf_date > settlement_date:
            future_cashflows.append((cf_date, cf_amount))
        else:
            # Si el flujo de caja es en o antes de la fecha de liquidación, se considera parte del precio inicial
            # Esto es una simplificación, en un cálculo XIRR estricto, los flujos pasados no se incluyen.
            # Para bonos, asumimos que el precio ya descuenta estos flujos.
            pass

    if not future_cashflows:
        logger.debug("calculate_tir: No hay flujos de caja futuros después de la fecha de liquidación.")
        return None

    # Estructurar los datos para el cálculo
    dates = [cf[0] for cf in future_cashflows]
    amounts = [cf[1] for cf in future_cashflows]

    # Función NPV(rate)
    def npv(rate):
        if Decimal("1.0") + rate <= 0: 
            return Decimal('NaN')
        total_npv = Decimal("0.0")
        for i in range(len(dates)):
            days = Decimal((dates[i] - settlement_date).days)
            exponent = days / Decimal("365.0")
            try:
                total_npv += amounts[i] / ((Decimal("1.0") + rate) ** exponent)
            except InvalidOperation:
                return Decimal('NaN') 
        return total_npv - price

    # Derivada de la función NPV con respecto a la tasa
    def d_npv(rate):
        if Decimal("1.0") + rate <= 0: 
            return Decimal('NaN')
        total_d_npv = Decimal("0.0")
        for i in range(len(dates)):
            days = Decimal((dates[i] - settlement_date).days)
            exponent = days / Decimal("365.0")
            try:
                denominator = (Decimal("1.0") + rate)
                if denominator == 0:
                    return Decimal('NaN')
                total_d_npv -= (
                    amounts[i]
                    * exponent
                    / (denominator ** (exponent + Decimal("1.0")))
                )
            except (InvalidOperation, DivisionByZero):
                return Decimal('NaN') 
        return total_d_npv

    # Implementación del método de Newton-Raphson
    guess = Decimal("0.1")  # Estimación inicial del 10%
    for i in range(100):  # Límite de iteraciones para evitar bucles infinitos
        npv_val = npv(guess)
        d_npv_val = d_npv(guess)

        logger.debug(f"Iter {i}: Guess={guess:.6f}, NPV={npv_val:.6f}, dNPV={d_npv_val:.6f}")

        if npv_val.is_nan() or d_npv_val.is_nan():
            logger.debug("calculate_tir: NaN detectado en NPV o dNPV.")
            return None 

        if abs(npv_val) < Decimal("1e-9"):  # Convergencia
            logger.debug(f"calculate_tir: Convergencia alcanzada en {i} iteraciones. TIR={guess:.6f}")
            return guess

        if d_npv_val == 0:  # No se puede continuar
            logger.debug("calculate_tir: Derivada de NPV es cero.")
            return None

        new_guess = guess - npv_val / d_npv_val
        guess = new_guess

    logger.debug("calculate_tir: No se encontró convergencia después de 100 iteraciones.")
    return None 


def convert_tirea_to_tem(tirea_anual: Decimal) -> Decimal:
    """
    Convierte una Tasa Efectiva Anual (TIREA) a su Tasa Efectiva Mensual (TEM) equivalente.
    """
    if tirea_anual <= Decimal("-1"):
        return Decimal("-1")  # No se puede calcular la raíz de un número negativo

    exponent_monthly = Decimal("1") / Decimal("12")
    tem = (Decimal("1") + tirea_anual) ** exponent_monthly - Decimal("1")
    return tem


def convert_tem_to_tea(tem: Decimal) -> Decimal:
    """
    Convierte una Tasa Efectiva Mensual (TEM) a su Tasa Efectiva Anual (TEA) equivalente.
    """
    tea = (Decimal("1") + tem) ** Decimal("12") - Decimal("1")
    return tea


def convert_tem_to_tna(tem: Decimal) -> Decimal:
    """
    Convierte una Tasa Efectiva Mensual (TEM) a su Tasa Nominal Anual (TNA) simple.
    """
    tna = tem * Decimal("12")
    return tna