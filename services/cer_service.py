"""
CER (Coefficient of Stabilization Reference) service for fetching inflation data from BCRA.
CER is the official inflation index used by Argentine CER-linked bonds.
"""

import logging
import requests
from decimal import Decimal
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Tuple
import json

logger = logging.getLogger(__name__)


class CERService:
    """Service to fetch CER data from BCRA API and calculate inflation adjustments."""
    
    def __init__(self):
        self.base_url = "https://api.bcra.gob.ar/estadisticas/v2.0"
        self.cer_series_id = "7927"  # CER series ID in BCRA API
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Market-Data-Analyzer/1.0'
        })
        self._cer_cache = {}
    
    def get_latest_cer(self) -> Optional[Decimal]:
        """Get the most recent CER value."""
        try:
            url = f"{self.base_url}/datos/{self.cer_series_id}"
            params = {"limite": 1}  # Get only the latest value
            
            response = self.session.get(url, params=params, timeout=15, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) > 0:
                    latest = data["results"][0]
                    cer_value = Decimal(str(latest["valor"]))
                    logger.info(f"Latest CER: {cer_value} (date: {latest['fecha']})")
                    return cer_value
            
            logger.warning(f"Could not fetch latest CER. Status: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching latest CER: {e}")
            return None
    
    def get_cer_at_date(self, target_date: date) -> Optional[Decimal]:
        """Get CER value at a specific date."""
        try:
            # Format date for BCRA API
            date_str = target_date.strftime("%Y-%m-%d")
            
            # Check cache first
            if date_str in self._cer_cache:
                return self._cer_cache[date_str]
            
            # Calculate date range (get a few days around target)
            start_date = target_date - timedelta(days=5)
            end_date = target_date + timedelta(days=5)
            
            url = f"{self.base_url}/datos/{self.cer_series_id}"
            params = {
                "desde": start_date.strftime("%Y-%m-%d"),
                "hasta": end_date.strftime("%Y-%m-%d")
            }
            
            response = self.session.get(url, params=params, timeout=15, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    # Find exact date or closest
                    for item in data["results"]:
                        item_date = datetime.strptime(item["fecha"], "%Y-%m-%d").date()
                        if item_date == target_date:
                            cer_value = Decimal(str(item["valor"]))
                            self._cer_cache[date_str] = cer_value
                            return cer_value
                    
                    # If exact date not found, use closest available
                    if data["results"]:
                        closest = data["results"][0]
                        cer_value = Decimal(str(closest["valor"]))
                        self._cer_cache[date_str] = cer_value
                        logger.info(f"Using closest CER for {date_str}: {cer_value}")
                        return cer_value
            
            logger.warning(f"Could not fetch CER for {date_str}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching CER for {target_date}: {e}")
            return None
    
    def estimate_cer_at_maturity(self, maturity_date: date, monthly_inflation_rate: Optional[Decimal] = None) -> Optional[Decimal]:
        """
        Estimate CER value at bond maturity based on current CER and inflation expectations.
        
        Args:
            maturity_date: Bond maturity date
            monthly_inflation_rate: Expected monthly inflation (if None, uses historical average)
        """
        try:
            current_cer = self.get_latest_cer()
            if not current_cer:
                return None
            
            today = date.today()
            if maturity_date <= today:
                return current_cer
            
            # Calculate months to maturity
            months_diff = (maturity_date.year - today.year) * 12 + (maturity_date.month - today.month)
            
            # Use provided inflation rate or estimate
            if monthly_inflation_rate is None:
                # Use recent historical inflation or reasonable estimate
                monthly_inflation_rate = self._estimate_monthly_inflation()
            
            # Project CER forward
            estimated_cer = current_cer * ((Decimal("1") + monthly_inflation_rate) ** Decimal(str(months_diff)))
            
            logger.info(f"Estimated CER at {maturity_date}: {estimated_cer:.2f} "
                       f"(current: {current_cer:.2f}, months: {months_diff}, "
                       f"monthly inflation: {monthly_inflation_rate:.2%})")
            
            return estimated_cer
            
        except Exception as e:
            logger.error(f"Error estimating CER at maturity: {e}")
            return None
    
    def _estimate_monthly_inflation(self) -> Decimal:
        """Estimate monthly inflation rate from recent CER data."""
        try:
            # Get CER data for last 6 months to calculate average inflation
            end_date = date.today()
            start_date = end_date - timedelta(days=180)
            
            url = f"{self.base_url}/datos/{self.cer_series_id}"
            params = {
                "desde": start_date.strftime("%Y-%m-%d"),
                "hasta": end_date.strftime("%Y-%m-%d")
            }
            
            response = self.session.get(url, params=params, timeout=15, verify=False)
            if response.status_code == 200:
                data = response.json()
                if data.get("results") and len(data["results"]) >= 2:
                    results = data["results"]
                    
                    # Calculate monthly inflation from first to last
                    first_cer = Decimal(str(results[0]["valor"]))
                    last_cer = Decimal(str(results[-1]["valor"]))
                    
                    first_date = datetime.strptime(results[0]["fecha"], "%Y-%m-%d").date()
                    last_date = datetime.strptime(results[-1]["fecha"], "%Y-%m-%d").date()
                    
                    months = ((last_date.year - first_date.year) * 12 + 
                             (last_date.month - first_date.month))
                    
                    if months > 0:
                        total_inflation = (last_cer / first_cer) - Decimal("1")
                        monthly_inflation = (Decimal("1") + total_inflation) ** (Decimal("1") / Decimal(str(months))) - Decimal("1")
                        
                        logger.info(f"Estimated monthly inflation from recent data: {monthly_inflation:.2%}")
                        return monthly_inflation
            
            # Fallback to reasonable estimate
            logger.warning("Could not calculate historical inflation, using 3% monthly estimate")
            return Decimal("0.03")
            
        except Exception as e:
            logger.warning(f"Error estimating inflation: {e}, using 3% monthly")
            return Decimal("0.03")
    
    def calculate_cer_adjusted_payoff(
        self, 
        nominal_payoff: Decimal, 
        issue_date: Optional[date] = None,
        maturity_date: Optional[date] = None
    ) -> Tuple[Optional[Decimal], Dict[str, Optional[Decimal]]]:
        """
        Calculate CER-adjusted payoff for a bond.
        
        Args:
            nominal_payoff: Face value from CSV
            issue_date: When bond was issued (if known)
            maturity_date: When bond matures
            
        Returns:
            Tuple of (adjusted_payoff, cer_data_dict)
        """
        try:
            cer_data = {
                "current_cer": self.get_latest_cer(),
                "issue_cer": None,
                "maturity_cer": None,
                "adjustment_ratio": None
            }
            
            if not cer_data["current_cer"]:
                return None, cer_data
            
            # If we have issue date, get actual CER at issue
            if issue_date:
                cer_data["issue_cer"] = self.get_cer_at_date(issue_date)
            
            # If we have maturity date, estimate CER at maturity
            if maturity_date:
                cer_data["maturity_cer"] = self.estimate_cer_at_maturity(maturity_date)
            
            # Calculate adjustment
            if cer_data["issue_cer"] and cer_data["maturity_cer"]:
                # Use actual issue CER and estimated maturity CER
                cer_data["adjustment_ratio"] = cer_data["maturity_cer"] / cer_data["issue_cer"]
                adjusted_payoff = nominal_payoff * cer_data["adjustment_ratio"]
                
                logger.info(f"CER adjustment: {nominal_payoff} × {cer_data['adjustment_ratio']:.4f} = {adjusted_payoff:.2f}")
                
            elif cer_data["maturity_cer"]:
                # Estimate issue CER based on typical bond life (assume 2-3 years)
                estimated_issue_months = 24  # Assume bond was issued ~2 years ago
                estimated_issue_cer = cer_data["current_cer"] / ((Decimal("1.03") ** Decimal(str(estimated_issue_months))))
                
                cer_data["issue_cer"] = estimated_issue_cer
                cer_data["adjustment_ratio"] = cer_data["maturity_cer"] / estimated_issue_cer
                adjusted_payoff = nominal_payoff * cer_data["adjustment_ratio"]
                
                logger.info(f"CER adjustment (estimated issue): {nominal_payoff} × {cer_data['adjustment_ratio']:.4f} = {adjusted_payoff:.2f}")
                
            else:
                # No adjustment possible
                adjusted_payoff = nominal_payoff
                logger.warning("Could not calculate CER adjustment, using nominal payoff")
            
            return adjusted_payoff, cer_data
            
        except Exception as e:
            logger.error(f"Error calculating CER-adjusted payoff: {e}")
            return None, {}
    
    def get_cer_summary(self) -> Dict:
        """Get summary of current CER situation."""
        try:
            current_cer = self.get_latest_cer()
            monthly_inflation = self._estimate_monthly_inflation()
            
            return {
                "current_cer": current_cer,
                "estimated_monthly_inflation": monthly_inflation,
                "estimated_annual_inflation": monthly_inflation * Decimal("12") if monthly_inflation else None,
                "last_updated": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error getting CER summary: {e}")
            return {}