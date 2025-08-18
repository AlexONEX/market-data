import logging
from decimal import Decimal, ROUND_HALF_UP, getcontext
from datetime import date, datetime
import csv
from typing import Dict, List, Optional, Union

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

getcontext().prec = 50
getcontext().rounding = ROUND_HALF_UP

logger = logging.getLogger(__name__)


class FinancialCalculator:
    @staticmethod
    def calculate_tea_from_tir(tir: float, days_to_maturity: int) -> float:
        if tir <= -1 or days_to_maturity <= 0:
            return 0.0
        tea = (1 + tir) ** (365 / days_to_maturity) - 1
        return tea

    @staticmethod
    def calculate_tem_from_tea(tea: float) -> float:
        if tea <= -1:
            return 0.0
        tem = (1 + tea) ** (1 / 12) - 1
        return tem

    @staticmethod
    def calculate_tna_from_tem(tem: float) -> float:
        return tem * 12

    @staticmethod
    def calculate_tna_from_tea(tea: float, compounding_frequency: int = 12) -> float:
        if tea <= -1 or compounding_frequency <= 0:
            return 0.0
        tna = ((1 + tea) ** (1 / compounding_frequency) - 1) * compounding_frequency
        return tna

    @staticmethod
    def calculate_irr_from_price_and_payoff(
        current_price: Union[Decimal, float], 
        final_payoff: Union[Decimal, float], 
        days_to_maturity: int,
        method: str = "compound"
    ) -> Dict[str, Optional[Decimal]]:
        """
        Calculates IRR (Internal Rate of Return) and related rates from current price and final payoff.
        
        Args:
            current_price: Current market price of the bond
            final_payoff: Final amount to be received at maturity
            days_to_maturity: Days until bond maturity
            method: "compound" for traditional IRR, "simple" for simple interest annualization
            
        Returns:
            Dictionary with TIR (IRR), TEA, TEM, TNA rates
        """
        try:
            current_price = Decimal(str(current_price))
            final_payoff = Decimal(str(final_payoff))
            
            if current_price <= 0 or final_payoff <= 0 or days_to_maturity <= 0:
                logger.warning(f"Invalid inputs: price={current_price}, payoff={final_payoff}, days={days_to_maturity}")
                return {"TIR": None, "TEA": None, "TEM": None, "TNA": None}
            
            days_decimal = Decimal(str(days_to_maturity))
            
            if method == "simple":
                # Simple interest annualization (matches PPI/ALYC better)
                simple_return = (final_payoff - current_price) / current_price
                tir = simple_return * (Decimal("365") / days_decimal)
                
                # For simple method, TEA is the same as TIR
                tea = tir
                
            else:
                # Compound IRR (traditional financial calculation)
                # For zero-coupon bonds: final_payoff = current_price * (1 + TIR)^(days/365)
                # Therefore: TIR = (final_payoff / current_price)^(365/days) - 1
                
                price_ratio = final_payoff / current_price
                exponent = Decimal("365") / days_decimal
                
                # TIR (IRR) - annualized rate
                tir = price_ratio ** exponent - Decimal("1")
                
                # TEA (Tasa Efectiva Anual) - same as TIR for annual compounding
                tea = tir
            
            # TEM (Tasa Efectiva Mensual) - always use compound conversion
            tem = (Decimal("1") + tea) ** (Decimal("1") / Decimal("12")) - Decimal("1")
            
            # TNA (Tasa Nominal Anual)
            tna = tem * Decimal("12")
            
            return {
                "TIR": tir,
                "TEA": tea, 
                "TEM": tem,
                "TNA": tna
            }
            
        except Exception as e:
            logger.error(f"Error calculating IRR: {e}")
            return {"TIR": None, "TEA": None, "TEM": None, "TNA": None}
        
    @staticmethod
    def calculate_both_irr_methods(
        current_price: Union[Decimal, float], 
        final_payoff: Union[Decimal, float], 
        days_to_maturity: int
    ) -> Dict[str, Dict]:
        """
        Calculate IRR using both compound and simple methods for comparison.
        
        Returns:
            Dictionary with 'compound' and 'simple' calculation results
        """
        calc = FinancialCalculator()
        
        return {
            "compound": calc.calculate_irr_from_price_and_payoff(
                current_price, final_payoff, days_to_maturity, "compound"
            ),
            "simple": calc.calculate_irr_from_price_and_payoff(
                current_price, final_payoff, days_to_maturity, "simple"
            )
        }


class BondDataLoader:
    """Loads bond data from CSV files and provides unified access to bond information."""
    
    def __init__(self, data_dir: str = "data"):
        self.data_dir = data_dir
        self.bond_data = {}
        self._load_all_bond_data()
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Parse date from various formats found in CSV files."""
        if not date_str or date_str.strip() == '':
            return None
            
        date_str = str(date_str).strip()
        
        # Try different date formats
        for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"]:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue
                
        logger.warning(f"Could not parse date: {date_str}")
        return None
    
    def _load_csv_bonds(self, filename: str, bond_type: str) -> Dict:
        """Load bonds from a specific CSV file."""
        filepath = f"{self.data_dir}/{filename}"
        bonds = {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    ticker = row.get('Ticker', '').strip()
                    if not ticker:
                        continue
                        
                    vencimiento_str = row.get('Vencimiento', '').strip()
                    pago_final_str = row.get('Pago_Final', '').strip()
                    
                    # Clean pago_final_str - remove any trailing commas or spaces
                    pago_final_str = pago_final_str.rstrip(',').strip()
                    
                    if not vencimiento_str or not pago_final_str:
                        continue
                    
                    maturity_date = self._parse_date(vencimiento_str)
                    if not maturity_date:
                        continue
                        
                    try:
                        final_payoff = Decimal(pago_final_str)
                    except:
                        logger.warning(f"Could not parse final payoff for {ticker}: {pago_final_str}")
                        continue
                    
                    bonds[ticker] = {
                        'ticker': ticker,
                        'maturity_date': maturity_date,
                        'final_payoff': final_payoff,
                        'bond_type': bond_type,
                        'days_to_maturity': (maturity_date - date.today()).days
                    }
                    
        except FileNotFoundError:
            logger.warning(f"Bond data file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading bond data from {filepath}: {e}")
            
        return bonds
    
    def _load_all_bond_data(self):
        """Load all bond data from CSV files."""
        # Load different types of bonds
        bond_files = [
            ("fixed_rate_tickers.csv", "fixed_rate"),
            ("cer_tickers.csv", "cer_linked"), 
            ("tamar_tickers.csv", "dual_bonds")
        ]
        
        for filename, bond_type in bond_files:
            bonds = self._load_csv_bonds(filename, bond_type)
            self.bond_data.update(bonds)
            logger.info(f"Loaded {len(bonds)} bonds from {filename}")
        
        logger.info(f"Total bonds loaded: {len(self.bond_data)}")
    
    def get_bond_info(self, ticker: str) -> Optional[Dict]:
        """Get bond information for a specific ticker."""
        return self.bond_data.get(ticker.upper())
    
    def get_all_bonds(self) -> Dict:
        """Get all loaded bond data."""
        return self.bond_data
    
    def get_bonds_by_type(self, bond_type: str) -> Dict:
        """Get bonds filtered by type."""
        return {k: v for k, v in self.bond_data.items() if v['bond_type'] == bond_type}


class IRRCalculator:
    """Provides IRR calculations for all bonds using current market data."""
    
    def __init__(self, bond_loader: Optional[BondDataLoader] = None):
        self.bond_loader = bond_loader or BondDataLoader()
        self.calculator = FinancialCalculator()
    
    def calculate_irr_for_bond(self, ticker: str, current_price: Union[Decimal, float]) -> Optional[Dict]:
        """Calculate IRR for a specific bond given its current market price."""
        bond_info = self.bond_loader.get_bond_info(ticker)
        if not bond_info:
            logger.warning(f"No bond data found for ticker: {ticker}")
            return None
            
        if bond_info['days_to_maturity'] <= 0:
            logger.warning(f"Bond {ticker} has already matured or invalid maturity date")
            return None
        
        rates = self.calculator.calculate_irr_from_price_and_payoff(
            current_price=current_price,
            final_payoff=bond_info['final_payoff'],
            days_to_maturity=bond_info['days_to_maturity']
        )
        
        return {
            **bond_info,
            'current_price': Decimal(str(current_price)),
            'rates': rates
        }
    
    def calculate_irr_for_all_bonds(self, price_data: Dict[str, Union[Decimal, float]]) -> Dict:
        """
        Calculate IRR for all bonds given a dictionary of current prices.
        
        Args:
            price_data: Dictionary mapping ticker to current price
            
        Returns:
            Dictionary with IRR calculations for each bond
        """
        results = {}
        
        for ticker, price in price_data.items():
            result = self.calculate_irr_for_bond(ticker, price)
            if result:
                results[ticker] = result
                
        return results
    
    def get_bonds_sorted_by_irr(self, price_data: Dict[str, Union[Decimal, float]]) -> List[Dict]:
        """Get bonds sorted by IRR (TIR) in descending order."""
        results = self.calculate_irr_for_all_bonds(price_data)
        
        # Filter bonds with valid TIR and sort by TIR descending
        valid_bonds = [
            bond for bond in results.values() 
            if bond['rates']['TIR'] is not None
        ]
        
        return sorted(
            valid_bonds, 
            key=lambda x: x['rates']['TIR'], 
            reverse=True
        )
