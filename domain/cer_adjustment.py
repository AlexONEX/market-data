"""
CER (Coefficient of Stabilization Reference) adjustment calculations for Argentine bonds.
CER bonds are inflation-indexed bonds where the final payoff is adjusted by inflation.
"""

import logging
from decimal import Decimal
from typing import Dict, Optional
from datetime import date

logger = logging.getLogger(__name__)


class CERCalculator:
    """Handles CER (inflation) adjustments for Argentine bonds."""
    
    def __init__(self):
        # These are approximate values - in production you'd fetch from BCRA API
        self.current_cer_index = Decimal("1350.0")  # Approximate current CER
        self.monthly_inflation_estimate = Decimal("0.04")  # 4% monthly estimate
    
    def estimate_cer_at_maturity(self, days_to_maturity: int) -> Decimal:
        """
        Estimate CER index at bond maturity based on inflation expectations.
        
        Args:
            days_to_maturity: Days until bond matures
            
        Returns:
            Estimated CER index at maturity
        """
        months_to_maturity = Decimal(str(days_to_maturity)) / Decimal("30")
        future_cer = self.current_cer_index * ((Decimal("1") + self.monthly_inflation_estimate) ** months_to_maturity)
        return future_cer
    
    def calculate_inflation_adjusted_payoff(
        self, 
        nominal_payoff: Decimal, 
        days_to_maturity: int,
        base_cer_index: Optional[Decimal] = None
    ) -> Decimal:
        """
        Calculate inflation-adjusted payoff for CER bonds.
        
        Args:
            nominal_payoff: Face value payoff from CSV
            days_to_maturity: Days until maturity
            base_cer_index: CER index when bond was issued (if known)
            
        Returns:
            Inflation-adjusted payoff
        """
        if base_cer_index is None:
            # Estimate base CER - assume bond was issued 1-2 years ago
            estimated_issue_months = 18  # Rough estimate
            base_cer_index = self.current_cer_index / ((Decimal("1") + self.monthly_inflation_estimate) ** Decimal(str(estimated_issue_months)))
        
        future_cer = self.estimate_cer_at_maturity(days_to_maturity)
        cer_adjustment_ratio = future_cer / base_cer_index
        
        adjusted_payoff = nominal_payoff * cer_adjustment_ratio
        
        logger.debug(f"CER adjustment: {nominal_payoff} × {cer_adjustment_ratio:.3f} = {adjusted_payoff:.2f}")
        
        return adjusted_payoff
    
    def reverse_calculate_market_expectations(
        self,
        current_price: Decimal,
        market_tir: Decimal,
        days_to_maturity: int,
        nominal_payoff: Decimal
    ) -> Dict[str, Decimal]:
        """
        Reverse calculate what the market expects for inflation/payoff based on market TIR.
        
        Args:
            current_price: Current bond price
            market_tir: Market TIR (from PPI/ALYC)
            days_to_maturity: Days to maturity
            nominal_payoff: Nominal payoff from CSV
            
        Returns:
            Dictionary with market expectations
        """
        exponent = Decimal("365") / Decimal(str(days_to_maturity))
        implied_payoff = current_price * ((Decimal("1") + market_tir) ** exponent)
        
        inflation_adjustment = implied_payoff / nominal_payoff
        
        # Calculate implied monthly inflation rate
        months_to_maturity = Decimal(str(days_to_maturity)) / Decimal("30")
        if months_to_maturity > 0:
            implied_monthly_inflation = (inflation_adjustment ** (Decimal("1") / months_to_maturity)) - Decimal("1")
        else:
            implied_monthly_inflation = Decimal("0")
        
        return {
            "implied_payoff": implied_payoff,
            "inflation_adjustment": inflation_adjustment,
            "implied_monthly_inflation": implied_monthly_inflation,
            "implied_annual_inflation": implied_monthly_inflation * Decimal("12")
        }


def create_enhanced_irr_calculator():
    """Create IRR calculator that handles CER adjustments correctly."""
    
    def calculate_irr_with_cer_adjustment(
        ticker: str,
        current_price: Decimal,
        nominal_payoff: Decimal,
        days_to_maturity: int,
        bond_type: str,
        market_tir: Optional[Decimal] = None
    ) -> Dict:
        """
        Calculate IRR for CER bonds correctly.
        
        For CER bonds in Argentina:
        - The nominal_payoff is the face value adjusted by CER since issuance
        - Current market price already incorporates inflation expectations
        - TIR calculation should use current_price vs nominal_payoff directly
        - This gives the REAL return above inflation that the market expects
        """
        from domain.financial_math import FinancialCalculator
        
        calculator = FinancialCalculator()
        cer_calc = CERCalculator()
        
        # For CER bonds, the correct calculation uses nominal payoff directly
        # This represents the real return above inflation
        cer_real_rates = calculator.calculate_irr_from_price_and_payoff(
            current_price, nominal_payoff, days_to_maturity
        )
        
        result = {
            "ticker": ticker,
            "bond_type": bond_type,
            "current_price": current_price,
            "nominal_payoff": nominal_payoff,
            "days_to_maturity": days_to_maturity,
            "cer_real_rates": cer_real_rates,  # This is the correct TIR for CER bonds
            "market_expectations": None
        }
        
        # For CER bonds, the main rate is the real rate
        if bond_type == "cer_linked":
            try:
                logger.info(f"CER bond {ticker}: Real TIR = {cer_real_rates.get('TIR', 'N/A'):.2%} "
                           f"(price: {current_price}, payoff: {nominal_payoff}, days: {days_to_maturity})")
                
                # If we have market TIR, compare with our calculation
                if market_tir:
                    market_expectations = cer_calc.reverse_calculate_market_expectations(
                        current_price, market_tir, days_to_maturity, nominal_payoff
                    )
                    result["market_expectations"] = market_expectations
                    
                    logger.info(f"Market TIR vs calculated TIR for {ticker}: "
                               f"Market={market_tir:.2%}, Calculated={cer_real_rates.get('TIR', 0):.2%}")
                    
            except Exception as e:
                logger.error(f"Error processing CER bond {ticker}: {e}")
        else:
            # For non-CER bonds, calculate normally
            result["nominal_rates"] = cer_real_rates
        
        return result
    
    return calculate_irr_with_cer_adjustment