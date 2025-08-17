import logging
from decimal import Decimal
from typing import Dict, List
from services.irr_service import IRRService

logger = logging.getLogger(__name__)


class IRRAnalyzer:
    """Application layer for IRR analysis and reporting."""
    
    def __init__(self):
        self.irr_service = IRRService()
    
    def display_irr_summary(self) -> None:
        """Display a summary of IRR calculations for all bonds."""
        print("\n" + "="*80)
        print("INTERNAL RATE OF RETURN (IRR) ANALYSIS FOR ALL BONDS")
        print("="*80)
        
        # Get summary statistics
        stats = self.irr_service.get_bond_summary_stats()
        
        print(f"\nSUMMARY STATISTICS:")
        print(f"Total bonds in database: {stats['total_bonds']}")
        print(f"Bonds with market prices: {stats['bonds_with_prices']}")
        print(f"Bonds with valid IRR: {stats['bonds_with_valid_irr']}")
        
        if stats['avg_irr']:
            print(f"Average IRR: {stats['avg_irr']:.2%}")
            print(f"Maximum IRR: {stats['max_irr']:.2%}")
            print(f"Minimum IRR: {stats['min_irr']:.2%}")
        
        print("\n" + "-"*80)
    
    def display_top_irr_bonds(self, limit: int = 10) -> None:
        """Display top N bonds by IRR."""
        print(f"\nTOP {limit} BONDS BY IRR:")
        print("-"*80)
        
        top_bonds = self.irr_service.get_top_irr_bonds(limit)
        
        if not top_bonds:
            print("No bonds with valid IRR data found.")
            return
        
        # Table header
        print(f"{'Rank':<4} {'Ticker':<8} {'Type':<12} {'IRR (TIR)':<10} {'TEA':<10} {'TEM':<10} {'Days':<6} {'Price':<8}")
        print("-" * 80)
        
        for rank, bond in enumerate(top_bonds, 1):
            ticker = bond['ticker']
            bond_type = bond['bond_type'].replace('_', ' ').title()
            irr = bond['rates']['TIR']
            tea = bond['rates']['TEA'] 
            tem = bond['rates']['TEM']
            days = bond['days_to_maturity']
            price = bond['current_price']
            
            print(f"{rank:<4} {ticker:<8} {bond_type:<12} "
                  f"{irr:.2%}{'':>3} {tea:.2%}{'':>3} {tem:.2%}{'':>3} "
                  f"{days:<6} ${price:>6.2f}")
    
    def display_irr_by_bond_type(self) -> None:
        """Display IRR analysis grouped by bond type."""
        print(f"\nIRR ANALYSIS BY BOND TYPE:")
        print("-"*80)
        
        by_type = self.irr_service.calculate_irr_by_bond_type()
        
        for bond_type, bonds in by_type.items():
            if not bonds:
                continue
                
            print(f"\n{bond_type.replace('_', ' ').upper()} BONDS:")
            print("-" * 50)
            
            # Calculate type statistics
            valid_irrs = [b['rates']['TIR'] for b in bonds if b['rates']['TIR'] is not None]
            if valid_irrs:
                avg_irr = sum(valid_irrs) / len(valid_irrs)
                max_irr = max(valid_irrs)
                print(f"Count: {len(bonds)} | Avg IRR: {avg_irr:.2%} | Max IRR: {max_irr:.2%}")
                print()
            
            # Show top 5 bonds for this type
            for i, bond in enumerate(bonds[:5]):
                ticker = bond['ticker']
                irr = bond['rates']['TIR']
                days = bond['days_to_maturity']
                price = bond['current_price']
                
                if irr is not None:
                    print(f"  {i+1}. {ticker:<8} IRR: {irr:>7.2%}  Days: {days:>3}  Price: ${price:>6.2f}")
                else:
                    print(f"  {i+1}. {ticker:<8} IRR: {'N/A':>7}      Days: {days:>3}  Price: ${price:>6.2f}")
    
    def get_bond_comparison(self, tickers: List[str]) -> None:
        """Compare IRR for specific bonds."""
        if not tickers:
            print("No tickers provided for comparison.")
            return
            
        print(f"\nBOND COMPARISON:")
        print("-"*60)
        
        results = {}
        for ticker in tickers:
            bond_info = self.irr_service.bond_loader.get_bond_info(ticker.upper())
            if not bond_info:
                print(f"Bond {ticker} not found in database.")
                continue
                
            # Get current price
            prices = self.irr_service.get_current_market_prices([ticker.upper()])
            price = prices.get(ticker.upper())
            
            if price is None:
                print(f"No market price available for {ticker}.")
                continue
                
            # Calculate IRR
            irr_result = self.irr_service.irr_calculator.calculate_irr_for_bond(ticker.upper(), price)
            if irr_result:
                results[ticker.upper()] = irr_result
        
        if not results:
            print("No valid results for comparison.")
            return
            
        # Display comparison table
        print(f"{'Ticker':<8} {'IRR':<10} {'TEA':<10} {'TEM':<10} {'Days':<6} {'Type':<12}")
        print("-" * 60)
        
        for ticker, bond in results.items():
            irr = bond['rates']['TIR']
            tea = bond['rates']['TEA']
            tem = bond['rates']['TEM'] 
            days = bond['days_to_maturity']
            bond_type = bond['bond_type'].replace('_', ' ').title()
            
            print(f"{ticker:<8} {irr:>7.2%}{'':>2} {tea:>7.2%}{'':>2} {tem:>7.2%}{'':>2} "
                  f"{days:<6} {bond_type:<12}")
    
    def analyze_all_bonds(self) -> None:
        """Run complete IRR analysis and display all reports."""
        self.display_irr_summary()
        self.display_top_irr_bonds()
        self.display_irr_by_bond_type()
        print("\n" + "="*80)
        print("IRR ANALYSIS COMPLETE")
        print("="*80)