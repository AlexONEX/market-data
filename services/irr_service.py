import logging
from decimal import Decimal
from typing import Dict, List, Optional, Union
from domain.financial_math import IRRCalculator, BondDataLoader
from services.ppi_service import PPIService

logger = logging.getLogger(__name__)


class IRRService:
    """Service for calculating IRR for all bonds using live market data."""
    
    def __init__(self):
        self.bond_loader = BondDataLoader()
        self.irr_calculator = IRRCalculator(self.bond_loader)
        self.ppi_service = PPIService()
    
    def get_current_market_prices(self, tickers: List[str]) -> Dict[str, Optional[Decimal]]:
        """Fetch current market prices for a list of tickers."""
        prices = {}
        
        for ticker in tickers:
            try:
                # Try to get price from PPI service
                price_data = self.ppi_service.get_price(ticker, "BONOS")
                if price_data and price_data.get("price") is not None:
                    prices[ticker] = Decimal(str(price_data["price"]))
                else:
                    logger.warning(f"No price data available for {ticker}")
                    prices[ticker] = None
            except Exception as e:
                logger.error(f"Error fetching price for {ticker}: {e}")
                prices[ticker] = None
                
        return prices
    
    def calculate_irr_for_all_loaded_bonds(self) -> Dict[str, Dict]:
        """Calculate IRR for all bonds loaded from CSV files."""
        all_bonds = self.bond_loader.get_all_bonds()
        tickers = list(all_bonds.keys())
        
        logger.info(f"Calculating IRR for {len(tickers)} bonds")
        
        # Get current market prices
        market_prices = self.get_current_market_prices(tickers)
        
        # Calculate IRR only for bonds with available prices
        valid_prices = {k: v for k, v in market_prices.items() if v is not None}
        
        if not valid_prices:
            logger.warning("No valid market prices found for any bonds")
            return {}
        
        logger.info(f"Found prices for {len(valid_prices)} out of {len(tickers)} bonds")
        
        # Calculate IRR for bonds with valid prices
        irr_results = self.irr_calculator.calculate_irr_for_all_bonds(dict(valid_prices))
        
        return irr_results
    
    def get_top_irr_bonds(self, limit: int = 10) -> List[Dict]:
        """Get top N bonds sorted by IRR (highest first)."""
        all_bonds = self.bond_loader.get_all_bonds()
        tickers = list(all_bonds.keys())
        
        market_prices = self.get_current_market_prices(tickers)
        valid_prices = {k: v for k, v in market_prices.items() if v is not None}
        
        if not valid_prices:
            return []
        
        sorted_bonds = self.irr_calculator.get_bonds_sorted_by_irr(dict(valid_prices))
        
        return sorted_bonds[:limit]
    
    def calculate_irr_by_bond_type(self) -> Dict[str, List[Dict]]:
        """Calculate IRR grouped by bond type."""
        all_results = self.calculate_irr_for_all_loaded_bonds()
        
        # Group by bond type
        by_type = {}
        for ticker, bond_data in all_results.items():
            bond_type = bond_data['bond_type']
            if bond_type not in by_type:
                by_type[bond_type] = []
            by_type[bond_type].append(bond_data)
        
        # Sort each type by IRR
        for bond_type in by_type:
            by_type[bond_type] = sorted(
                by_type[bond_type],
                key=lambda x: x['rates']['TIR'] or Decimal('0'),
                reverse=True
            )
        
        return by_type
    
    def get_bond_summary_stats(self) -> Dict:
        """Get summary statistics for all bonds."""
        all_results = self.calculate_irr_for_all_loaded_bonds()
        
        if not all_results:
            return {
                "total_bonds": 0,
                "bonds_with_prices": 0,
                "avg_irr": None,
                "max_irr": None,
                "min_irr": None
            }
        
        valid_irrs = [
            bond_data['rates']['TIR'] 
            for bond_data in all_results.values() 
            if bond_data['rates']['TIR'] is not None
        ]
        
        if not valid_irrs:
            avg_irr = max_irr = min_irr = None
        else:
            avg_irr = sum(valid_irrs) / len(valid_irrs)
            max_irr = max(valid_irrs)
            min_irr = min(valid_irrs)
        
        return {
            "total_bonds": len(self.bond_loader.get_all_bonds()),
            "bonds_with_prices": len(all_results),
            "bonds_with_valid_irr": len(valid_irrs),
            "avg_irr": avg_irr,
            "max_irr": max_irr,
            "min_irr": min_irr
        }