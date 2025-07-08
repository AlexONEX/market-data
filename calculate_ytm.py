from datetime import datetime


def calcular_valor_final(
    precio_corte, tirea_anual, fecha_liquidacion_str, fecha_vencimiento_str
):
    try:
        fecha_liquidacion = datetime.strptime(fecha_liquidacion_str, "%Y-%m-%d").date()
        fecha_vencimiento = datetime.strptime(fecha_vencimiento_str, "%Y-%m-%d").date()

        dias_totales = (fecha_vencimiento - fecha_liquidacion).days
        if dias_totales < 0:
            return (
                None,
                "La fecha de liquidación no puede ser posterior a la de vencimiento.",
            )

        tiempo_en_anios = dias_totales / 365.0

        valor_final = precio_corte * (1 + tirea_anual) ** tiempo_en_anios
        return valor_final, None

    except ValueError:
        return None, "El formato de una de las fechas es incorrecto."


def convertir_tirea_a_tem(tirea_anual):
    """
    Convierte una Tasa Efectiva Anual (TIREA) a su Tasa Efectiva Mensual (TEM) equivalente.
    """
    tem = (1 + tirea_anual) ** (1 / 12) - 1
    return tem


def main():
    """
    Función principal para solicitar datos al usuario y mostrar los resultados.
    """
    print("--- Calculadora de Valor Final y TEM de LECAPs ---")
    print("Ingrese los datos obtenidos de la licitación primaria:")

    try:
        precio_corte = float(input("➡️ Precio de Corte (ej: 1506.00): "))
        tirea_porcentaje = float(input("➡️ TIREA en porcentaje (ej: 36.93): "))
        fecha_liquidacion_str = input("➡️ Fecha de Liquidación (formato YYYY-MM-DD): ")
        fecha_vencimiento_str = input("➡️ Fecha de Vencimiento (formato YYYY-MM-DD): ")

        tirea_decimal = tirea_porcentaje / 100.0

        valor_final_calculado, error = calcular_valor_final(
            precio_corte, tirea_decimal, fecha_liquidacion_str, fecha_vencimiento_str
        )

        if error:
            print(f"\n❌ Error: {error}")
            return

        tem_calculada = convertir_tirea_a_tem(tirea_decimal)

        print("\n" + "=" * 30)
        print("       Resultados del Cálculo")
        print("=" * 30)
        print(f"📈 Valor Final a Vencimiento: ${valor_final_calculado:,.2f}")
        print("   (Este es el monto que pagará el bono en su fecha de vencimiento)")
        print("\n" + "-" * 30 + "\n")
        print(f"📅 Tasa Efectiva Mensual (TEM): {tem_calculada:.4%}")
        print("   (Esta es la tasa de rendimiento mensual equivalente a la TIREA)")
        print("=" * 30)

    except ValueError:
        print("\n❌ Error: El valor del precio o la TIREA debe ser un número válido.")
    except Exception as e:
        print(f"\n❌ Ocurrió un error inesperado: {e}")


if __name__ == "__main__":
    main()
