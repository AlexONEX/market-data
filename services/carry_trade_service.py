import logging
from decimal import Decimal, ROUND_HALF_UP, getcontext
from datetime import date
from typing import Dict, List, Optional, Union
from domain.financial_math import BondDataLoader, IRRCalculator
from services.ppi_service import PPIService
import requests

getcontext().prec = 50
getcontext().rounding = ROUND_HALF_UP

logger = logging.getLogger(__name__)


class CarryTradeService:
    """Service for carry trade analysis using existing bond infrastructure."""
    
    def __init__(self):
        self.bond_loader = BondDataLoader()
        self.irr_calculator = IRRCalculator(self.bond_loader)
        self.ppi_service = PPIService()
    
    def get_mep_rate(self) -> Optional[Decimal]:
        """Get current MEP (dollar blue) rate from data912.com API."""
        try:
            response = requests.get('https://data912.com/live/mep', timeout=10)
            if response.status_code == 200:
                mep_data = response.json()
                if mep_data and len(mep_data) > 0:
                    # Calculate median from close prices
                    close_prices = [item.get('close', 0) for item in mep_data if item.get('close')]
                    if close_prices:
                        close_prices.sort()
                        n = len(close_prices)
                        median = close_prices[n//2] if n % 2 == 1 else (close_prices[n//2-1] + close_prices[n//2]) / 2
                        return Decimal(str(median))
            logger.warning("Could not fetch MEP rate from API")
            return None
        except Exception as e:
            logger.error(f"Error fetching MEP rate: {e}")
            return None
    
    def calculate_carry_trade_returns(self, usd_scenarios: Optional[List[int]] = None) -> Dict:
        """
        Calculate carry trade returns for different USD scenarios.
        
        Args:
            usd_scenarios: List of USD/ARS exchange rates to analyze
            
        Returns:
            Dictionary with carry trade analysis results
        """
        if usd_scenarios is None:
            usd_scenarios = [1000, 1100, 1200, 1300, 1400]
        
        # Get all bonds
        all_bonds = self.bond_loader.get_all_bonds()
        tickers = list(all_bonds.keys())
        
        logger.info(f"Analyzing carry trade for {len(tickers)} bonds")
        
        # Get current market prices
        prices = {}
        for ticker in tickers:
            try:
                price_data = self.ppi_service.get_price(ticker, "BONOS")
                if price_data and price_data.get("price") is not None:
                    prices[ticker] = Decimal(str(price_data["price"]))
            except Exception as e:
                logger.warning(f"Could not fetch price for {ticker}: {e}")
        
        # Get MEP rate
        mep_rate = self.get_mep_rate()
        if not mep_rate:
            logger.warning("Using default MEP rate of 1200")
            mep_rate = Decimal("1200")
        
        results = {}
        
        for ticker in tickers:
            bond_info = all_bonds[ticker]
            current_price = prices.get(ticker)
            
            if not current_price or bond_info['days_to_maturity'] <= 0:
                continue
            
            # Calculate basic rates
            irr_result = self.irr_calculator.calculate_irr_for_bond(ticker, current_price)
            if not irr_result or not irr_result['rates']['TIR']:
                continue
            
            # Calculate carry trade scenarios
            final_payoff = bond_info['final_payoff']
            bond_return_ratio = final_payoff / current_price
            
            carry_scenarios = {}
            for usd_rate in usd_scenarios:
                # Calculate return if selling at different USD rates
                # Return = (payoff / entry_price) * (mep_at_entry / usd_at_exit) - 1
                carry_return = bond_return_ratio * mep_rate / Decimal(str(usd_rate)) - Decimal("1")
                carry_scenarios[f"carry_{usd_rate}"] = carry_return
            
            # Calculate "worst case" scenario with 1% monthly inflation
            days_ratio = Decimal(str(bond_info['days_to_maturity'])) / Decimal("30")
            worst_case_usd = Decimal("1400") * (Decimal("1.01") ** days_ratio)
            carry_worst = bond_return_ratio * mep_rate / worst_case_usd - Decimal("1")
            
            # MEP breakeven point
            mep_breakeven = mep_rate * bond_return_ratio
            
            results[ticker] = {
                **bond_info,
                'current_price': current_price,
                'rates': irr_result['rates'],
                'bond_return_ratio': bond_return_ratio,
                'carry_scenarios': carry_scenarios,
                'carry_worst': carry_worst,
                'mep_breakeven': mep_breakeven,
                'worst_case_usd': worst_case_usd
            }
        
        return {
            'bonds': results,
            'mep_rate': mep_rate,
            'scenarios': usd_scenarios,
            'analysis_date': date.today()
        }
    
    def display_carry_trade_analysis(self, limit: int = 15) -> None:
        """Display carry trade analysis results."""
        analysis = self.calculate_carry_trade_returns()
        
        if not analysis['bonds']:
            print("No bonds available for carry trade analysis.")
            return
        
        print("\n" + "="*100)
        print("CARRY TRADE ANALYSIS")
        print("="*100)
        print(f"MEP Rate: ${analysis['mep_rate']:.2f}")
        print(f"Analysis Date: {analysis['analysis_date']}")
        
        # Sort bonds by best carry trade return (using 1300 USD scenario)
        sorted_bonds = sorted(
            analysis['bonds'].values(),
            key=lambda x: x['carry_scenarios'].get('carry_1300', Decimal('-1')),
            reverse=True
        )
        
        # Display table header
        print(f"\n{'Ticker':<8} {'Type':<12} {'IRR':<8} {'Days':<5} ", end="")
        for scenario in analysis['scenarios']:
            print(f"${scenario:<6}", end=" ")
        print(f"{'Worst':<8} {'Breakeven':<10}")
        print("-" * 100)
        
        # Display top bonds
        for bond in sorted_bonds[:limit]:
            ticker = bond['ticker']
            bond_type = bond['bond_type'].replace('_', ' ').title()[:11]
            irr = bond['rates']['TIR']
            days = bond['days_to_maturity']
            
            print(f"{ticker:<8} {bond_type:<12} {irr:>6.1%}{'':>1} {days:<5} ", end="")
            
            for scenario in analysis['scenarios']:
                carry_return = bond['carry_scenarios'].get(f'carry_{scenario}', Decimal('0'))
                print(f"{carry_return:>6.1%}{'':>1} ", end="")
            
            carry_worst = bond['carry_worst']
            mep_breakeven = bond['mep_breakeven']
            
            print(f"{carry_worst:>6.1%}{'':>1} ${mep_breakeven:>8.0f}")
        
        print("\n" + "="*100)
        print("Note: Carry returns assume buying bonds in ARS and selling USD at different rates.")
        print("Breakeven: MEP rate needed to break even on the trade.")
        print("Worst: Return if USD reaches $1400 with 1% monthly inflation.")
        print("="*100)
    
    def get_best_carry_opportunities(self, min_irr: float = 0.3, limit: int = 5) -> List[Dict]:
        """Get best carry trade opportunities based on criteria."""
        analysis = self.calculate_carry_trade_returns()
        
        # Filter bonds meeting criteria
        opportunities = []
        for bond in analysis['bonds'].values():
            irr = bond['rates']['TIR']
            if irr and float(irr) >= min_irr:
                # Use conservative scenario (1300 USD)
                carry_1300 = bond['carry_scenarios'].get('carry_1300', Decimal('0'))
                if carry_1300 > 0:
                    opportunities.append({
                        'ticker': bond['ticker'],
                        'irr': irr,
                        'carry_return': carry_1300,
                        'days': bond['days_to_maturity'],
                        'bond_type': bond['bond_type']
                    })
        
        # Sort by carry return
        opportunities.sort(key=lambda x: x['carry_return'], reverse=True)
        
        return opportunities[:limit]