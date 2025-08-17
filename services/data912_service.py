import logging
import requests
from decimal import Decimal
from typing import Dict, List, Optional
import json

logger = logging.getLogger(__name__)


class Data912Service:
    """Service to fetch data from data912.com API for bonds and MEP rates."""
    
    def __init__(self):
        self.base_url = "https://data912.com/live"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Market-Data-Analyzer/1.0'
        })
    
    def get_mep_rate(self) -> Optional[Decimal]:
        """Get current MEP (dollar blue) rate."""
        try:
            response = self.session.get(f"{self.base_url}/mep", timeout=10)
            if response.status_code == 200:
                mep_data = response.json()
                if mep_data and len(mep_data) > 0:
                    # Calculate median from close prices
                    close_prices = [item.get('close', 0) for item in mep_data if item.get('close')]
                    if close_prices:
                        close_prices.sort()
                        n = len(close_prices)
                        median = close_prices[n//2] if n % 2 == 1 else (close_prices[n//2-1] + close_prices[n//2]) / 2
                        logger.info(f"MEP rate fetched: ${median:.2f}")
                        return Decimal(str(median))
            logger.warning("Could not fetch MEP rate from data912 API")
            return None
        except Exception as e:
            logger.error(f"Error fetching MEP rate: {e}")
            return None
    
    def get_bond_prices(self) -> Dict[str, Dict]:
        """Get bond prices from data912 API."""
        bond_prices = {}
        
        # Fetch bonds data
        try:
            response = self.session.get(f"{self.base_url}/arg_bonds", timeout=15)
            if response.status_code == 200:
                bonds_data = response.json()
                if bonds_data:
                    for bond in bonds_data:
                        symbol = bond.get('symbol')
                        if symbol:
                            bond_prices[symbol] = {
                                'price': bond.get('c'),  # Close price
                                'bid': bond.get('px_bid'),
                                'ask': bond.get('px_ask'),
                                'volume': bond.get('v'),
                                'source': 'data912_bonds'
                            }
                    logger.info(f"Fetched {len(bond_prices)} bond prices from data912")
        except Exception as e:
            logger.error(f"Error fetching bond prices: {e}")
        
        # Fetch notes data
        try:
            response = self.session.get(f"{self.base_url}/arg_notes", timeout=15)
            if response.status_code == 200:
                notes_data = response.json()
                if notes_data:
                    for note in notes_data:
                        symbol = note.get('symbol')
                        if symbol:
                            bond_prices[symbol] = {
                                'price': note.get('c'),  # Close price
                                'bid': note.get('px_bid'),
                                'ask': note.get('px_ask'),
                                'volume': note.get('v'),
                                'source': 'data912_notes'
                            }
                    logger.info(f"Fetched {len([n for n in notes_data if n.get('symbol')])} note prices from data912")
        except Exception as e:
            logger.error(f"Error fetching note prices: {e}")
        
        return bond_prices
    
    def get_comprehensive_market_data(self) -> Dict:
        """Get comprehensive market data including MEP rate and bond prices."""
        logger.info("Fetching comprehensive market data from data912...")
        
        data = {
            'mep_rate': self.get_mep_rate(),
            'bond_prices': self.get_bond_prices(),
            'timestamp': None
        }
        
        # Add timestamp if available
        try:
            import datetime
            data['timestamp'] = datetime.datetime.now().isoformat()
        except:
            pass
        
        logger.info(f"Market data summary: MEP=${data['mep_rate']}, {len(data['bond_prices'])} bond prices")
        return data
    
    def save_market_data(self, filename: str = "market_data.json") -> None:
        """Save market data to JSON file for caching."""
        try:
            data = self.get_comprehensive_market_data()
            import os
            os.makedirs("data", exist_ok=True)
            filepath = f"data/{filename}"
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Market data saved to {filepath}")
        except Exception as e:
            logger.error(f"Error saving market data: {e}")
    
    def load_market_data(self, filename: str = "market_data.json") -> Optional[Dict]:
        """Load cached market data from JSON file."""
        try:
            filepath = f"data/{filename}"
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Convert MEP rate back to Decimal if it exists
            if data.get('mep_rate'):
                data['mep_rate'] = Decimal(str(data['mep_rate']))
            
            logger.info(f"Market data loaded from {filepath}")
            return data
        except FileNotFoundError:
            logger.info(f"No cached market data found at data/{filename}")
            return None
        except Exception as e:
            logger.error(f"Error loading market data: {e}")
            return None