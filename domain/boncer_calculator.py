"""
BONCER Calculator - Calcula TIR correctamente para bonos CER + cupón.
BONCER = Bonos del Tesoro ajustados por CER con cupón real fijo.
"""

import logging
from decimal import Decimal
from datetime import date, datetime
from typing import List, Dict, Optional, Tuple
from dateutil.relativedelta import relativedelta
import csv

logger = logging.getLogger(__name__)


class BONCERCalculator:
    """Calculadora específica para bonos BONCER (CER + cupón real)."""
    
    def __init__(self, current_cer: Optional[Decimal] = None):
        """
        Args:
            current_cer: CER actual. Si es None, usa valor estimado.
        """
        # CER aproximado actual (agosto 2025)
        self.current_cer = current_cer or Decimal("1350.0")
        
    def load_boncer_data(self, csv_path: str = "data/boncer_bonds.csv") -> Dict[str, Dict]:
        """Carga datos de bonos BONCER desde CSV."""
        boncer_bonds = {}
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    ticker = row['Ticker'].strip()
                    boncer_bonds[ticker] = {
                        'ticker': ticker,
                        'nombre': row['Nombre'],
                        'vencimiento': datetime.strptime(row['Vencimiento'], '%Y-%m-%d').date(),
                        'valor_nominal': Decimal(row['Valor_Nominal']),
                        'tasa_real_anual': Decimal(row['Tasa_Real_Anual']),
                        'frecuencia_cupon': int(row['Frecuencia_Cupon']),
                        'cer_emision': Decimal(row['CER_Emision']),
                        'fecha_emision': datetime.strptime(row['Fecha_Emision'], '%Y-%m-%d').date(),
                        'tipo': row['Tipo']
                    }
        except FileNotFoundError:
            logger.error(f"No se encontró el archivo {csv_path}")
        except Exception as e:
            logger.error(f"Error cargando datos BONCER: {e}")
            
        return boncer_bonds
    
    def calculate_cer_adjustment_ratio(self, cer_emision: Decimal) -> Decimal:
        """Calcula el factor de ajuste CER actual vs emisión."""
        return self.current_cer / cer_emision
    
    def estimate_future_cer(self, target_date: date, monthly_inflation: Decimal = Decimal("0.04")) -> Decimal:
        """Estima CER futuro basado en inflación mensual esperada."""
        today = date.today()
        if target_date <= today:
            return self.current_cer
            
        months_diff = (target_date.year - today.year) * 12 + (target_date.month - today.month)
        future_cer = self.current_cer * ((Decimal("1") + monthly_inflation) ** Decimal(str(months_diff)))
        
        return future_cer
    
    def generate_coupon_schedule(self, bond_data: Dict) -> List[Dict]:
        """Genera cronograma de cupones para un BONCER."""
        schedule = []
        
        fecha_emision = bond_data['fecha_emision'] 
        vencimiento = bond_data['vencimiento']
        frecuencia = bond_data['frecuencia_cupon']  # cupones por año
        tasa_real = bond_data['tasa_real_anual']
        
        # Calcular fechas de cupón
        months_between_coupons = 12 // frecuencia
        current_date = fecha_emision + relativedelta(months=months_between_coupons)
        
        coupon_number = 1
        while current_date <= vencimiento:
            # Estimar CER en fecha de cupón
            estimated_cer = self.estimate_future_cer(current_date)
            cer_ratio = estimated_cer / bond_data['cer_emision']
            
            # Valor nominal ajustado en fecha de cupón
            valor_ajustado = bond_data['valor_nominal'] * cer_ratio
            
            # Cupón = (tasa_real / frecuencia) * valor_nominal_ajustado
            cupon_amount = (tasa_real / Decimal(str(frecuencia))) * valor_ajustado
            
            # Principal solo en el último pago
            principal = valor_ajustado if current_date == vencimiento else Decimal("0")
            
            schedule.append({
                'numero': coupon_number,
                'fecha': current_date,
                'days_from_today': (current_date - date.today()).days,
                'cer_estimado': estimated_cer,
                'cer_ratio': cer_ratio,
                'valor_nominal_ajustado': valor_ajustado,
                'cupon': cupon_amount,
                'principal': principal,
                'flujo_total': cupon_amount + principal
            })
            
            current_date += relativedelta(months=months_between_coupons)
            coupon_number += 1
            
        return schedule
    
    def calculate_boncer_tir(self, ticker: str, current_price: Decimal) -> Optional[Dict]:
        """
        Calcula TIR real para un bono BONCER.
        
        La TIR se calcula como el rendimiento real por encima de inflación,
        usando el valor nominal original como base.
        """
        boncer_data = self.load_boncer_data()
        
        if ticker not in boncer_data:
            logger.error(f"No se encontraron datos para {ticker}")
            return None
            
        bond_data = boncer_data[ticker]
        
        # Generar cronograma de flujos
        coupon_schedule = self.generate_coupon_schedule(bond_data)
        
        if not coupon_schedule:
            logger.error(f"No se pudo generar cronograma para {ticker}")
            return None
        
        # Calcular TIR usando flujos reales (deflactados)
        # Los flujos están en pesos ajustados por CER, pero la TIR es real
        valor_nominal_original = bond_data['valor_nominal']
        
        # Para BONCER, el precio cotiza como porcentaje del valor nominal ajustado
        cer_ratio_actual = self.calculate_cer_adjustment_ratio(bond_data['cer_emision'])
        valor_nominal_ajustado_actual = valor_nominal_original * cer_ratio_actual
        
        # El precio actual es sobre valor ajustado, convertir a base original
        precio_base_original = current_price / cer_ratio_actual
        
        # Calcular TIR usando Newton-Raphson para encontrar la tasa que iguala NPV = 0
        tir_real = self._calculate_irr_newton_raphson(
            precio_base_original, 
            coupon_schedule, 
            bond_data['cer_emision']
        )
        
        return {
            'ticker': ticker,
            'bond_data': bond_data,
            'current_price': current_price,
            'cer_ratio_actual': cer_ratio_actual,
            'valor_nominal_ajustado_actual': valor_nominal_ajustado_actual,
            'precio_base_original': precio_base_original,
            'coupon_schedule': coupon_schedule,
            'tir_real': tir_real,
            'tir_real_percent': tir_real * 100 if tir_real else None
        }
    
    def _calculate_irr_newton_raphson(
        self, 
        present_value: Decimal, 
        cash_flows: List[Dict], 
        cer_emision: Decimal,
        max_iterations: int = 100,
        tolerance: Decimal = Decimal("0.0001")
    ) -> Optional[Decimal]:
        """
        Calcula TIR usando método Newton-Raphson.
        Los flujos están en valores ajustados por CER, se deflactan para obtener TIR real.
        """
        
        # Estimación inicial
        tir = Decimal("0.05")  # 5% inicial
        
        for iteration in range(max_iterations):
            npv = -present_value  # Inversión inicial (negativa)
            npv_derivative = Decimal("0")
            
            for cf in cash_flows:
                days = Decimal(str(cf['days_from_today']))
                if days <= 0:
                    continue
                    
                # El flujo está en pesos ajustados por CER futura
                # Para TIR real, deflactamos por la proporción de CER
                cer_ratio = cf['cer_ratio']
                flujo_real = cf['flujo_total'] / cer_ratio
                
                years = days / Decimal("365")
                discount_factor = (Decimal("1") + tir) ** years
                
                # NPV
                npv += flujo_real / discount_factor
                
                # Derivada para Newton-Raphson
                npv_derivative -= flujo_real * years / (discount_factor * (Decimal("1") + tir))
            
            if abs(npv) < tolerance:
                logger.info(f"TIR convergió en {iteration} iteraciones: {tir:.4f}")
                return tir
                
            if abs(npv_derivative) < tolerance:
                logger.warning("Derivada muy pequeña, no se puede continuar")
                break
                
            # Actualización Newton-Raphson
            tir_new = tir - npv / npv_derivative
            
            if abs(tir_new - tir) < tolerance:
                logger.info(f"TIR convergió por cambio mínimo en {iteration} iteraciones: {tir_new:.4f}")
                return tir_new
                
            tir = tir_new
            
            # Evitar valores negativos extremos
            if tir < Decimal("-0.9"):
                tir = Decimal("-0.5")
        
        logger.warning(f"TIR no convergió después de {max_iterations} iteraciones")
        return None


def test_boncer_calculation():
    """Función de prueba para validar cálculos BONCER."""
    
    calc = BONCERCalculator()
    
    # Prueba con TX26
    print("=== PRUEBA TX26 ===")
    result = calc.calculate_boncer_tir("TX26", Decimal("1346.51"))  # Precio que da ~22.58% TIR
    
    if result:
        print(f"Ticker: {result['ticker']}")
        print(f"TIR Real: {result['tir_real_percent']:.2f}%")
        print(f"CER Ratio: {result['cer_ratio_actual']:.4f}")
        print(f"Valor nominal ajustado: {result['valor_nominal_ajustado_actual']:.2f}")
        print("\nCronograma de cupones:")
        for i, cf in enumerate(result['coupon_schedule'][:3]):  # Primeros 3 cupones
            print(f"  {cf['fecha']}: Cupón {cf['cupon']:.2f}, Principal {cf['principal']:.2f}")


if __name__ == "__main__":
    test_boncer_calculation()