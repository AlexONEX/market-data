import logging
from datetime import date
from decimal import Decimal, DivisionByZero, InvalidOperation, getcontext

getcontext().prec = 50

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def calculate_tir(
    cashflows: list[tuple[date, Decimal]], price: Decimal, settlement_date: date
) -> Decimal | None:
    """
    TIR using Newton-Raphson (XIRR).
    """
    if not cashflows or price <= 0:
        logger.debug("calculate_tir: Cashflows vacíos o precio <= 0. Price: %s", price) # G004
        return None

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
        logger.debug(
            "calculate_tir: No hay flujos de caja futuros después de la fecha de liquidación."
        )
        return None

    dates = [cf[0] for cf in future_cashflows]
    amounts = [cf[1] for cf in future_cashflows]

    def npv(rate):
        if Decimal("1.0") + rate <= 0:
            return Decimal("NaN")
        total_npv = Decimal("0.0")
        for i in range(len(dates)):
            days = Decimal((dates[i] - settlement_date).days)
            exponent = days / Decimal("365.0")
            try:
                denominator = Decimal("1.0") + rate
                if denominator == 0:
                    return Decimal("NaN")
                total_npv += amounts[i] / (denominator ** exponent)
            except InvalidOperation:
                return Decimal("NaN")
        return total_npv - price

    def d_npv(rate):
        if Decimal("1.0") + rate <= 0:
            return Decimal("NaN")
        total_d_npv = Decimal("0.0")
        for i in range(len(dates)):
            days = Decimal((dates[i] - settlement_date).days)
            exponent = days / Decimal("365.0")
            try:
                denominator = Decimal("1.0") + rate
                if denominator == 0:
                    return Decimal("NaN")
                total_d_npv -= (
                    amounts[i] * exponent / (denominator ** (exponent + Decimal("1.0")))
                )
            except (InvalidOperation, DivisionByZero):
                return Decimal("NaN")
        return total_d_npv

    guess = Decimal("0.1")
    for i in range(100):
        npv_val = npv(guess)
        d_npv_val = d_npv(guess)

        logger.debug(
            "Iter %d: Guess=%.6f, NPV=%.6f, dNPV=%.6f", i, guess, npv_val, d_npv_val # G004
        )

        if npv_val.is_nan() or d_npv_val.is_nan():
            logger.debug("calculate_tir: NaN detectado en NPV o dNPV.")
            return None

        if abs(npv_val) < Decimal("1e-9"):
            logger.debug(
                "calculate_tir: Convergencia alcanzada en %d iteraciones. TIR=%.6f", i, guess # G004
            )
            return guess

        if d_npv_val == 0:
            logger.debug("calculate_tir: Derivada de NPV es cero.")
            return None

        new_guess = guess - npv_val / d_npv_val
        guess = new_guess

    logger.debug(
        "calculate_tir: No se encontró convergencia después de 100 iteraciones."
    )
    return None


def convert_tirea_to_tem(tirea_anual: Decimal) -> Decimal:
    if tirea_anual <= Decimal(-1):
        return Decimal(-1)

    exponent_monthly = Decimal(1) / Decimal(12)
    return (Decimal(1) + tirea_anual) ** exponent_monthly - Decimal(1) # RET504


def convert_tem_to_tea(tem: Decimal) -> Decimal:
    return (Decimal(1) + tem) ** Decimal(12) - Decimal(1) # RET504


def convert_tem_to_tna(tem: Decimal) -> Decimal:
    return tem * Decimal(12) # RET504
