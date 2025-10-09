"""
Service to fetch bond data from ecovalores.com
"""
import requests
import logging
from decimal import Decimal
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)

class EcovaloresService:
    """Service to fetch bond data from ecovalores.com"""

    def __init__(self):
        self.base_url = "https://bonos.ecovalores.com.ar/eco/ticker.php"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_bond_data(self, ticker: str) -> Optional[Dict]:
        """
        Get bond data from ecovalores.com

        Returns:
            Dict with ticker, tir, price, paridad, valor_tecnico, and other metrics if found, None otherwise
        """
        try:
            url = f"{self.base_url}?t={ticker}"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch {ticker} from ecovalores.com: {response.status_code}")
                return None

            content = response.text

            # Extract all metrics
            tir = self._extract_tir(content, ticker)
            price = self._extract_price(content, ticker)
            paridad = self._extract_paridad(content, ticker)
            valor_tecnico = self._extract_valor_tecnico(content, ticker)
            duration = self._extract_duration(content, ticker)

            if not tir and not price:
                logger.warning(f"No TIR or price data found for {ticker} on ecovalores.com")
                return None

            return {
                'ticker': ticker,
                'tir': tir,
                'price': price,
                'paridad': paridad,
                'valor_tecnico': valor_tecnico,
                'duration': duration,
                'source': 'ecovalores.com'
            }

        except Exception as e:
            logger.error(f"Error fetching data for {ticker} from ecovalores.com: {e}")
            return None

    def _extract_tir(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract TIR from ecovalores.com page content"""
        try:
            # Ecovalores patterns for TIR
            patterns = [
                # Direct TIR patterns (e.g., "TIR: 18,98%")
                r'TIR[^0-9]*([0-9,]+)%',
                r'Rendimiento[^0-9]*([0-9,]+)%',
                r'Yield[^0-9]*([0-9,]+)%',

                # HTML table patterns
                r'TIR.*?([0-9,]+)%',
                r'>TIR<.*?>([0-9,]+)%',

                # JSON-like patterns
                r'"TIR":\s*"([0-9,]+)%"',
                r'"tir":\s*"([0-9,]+)%"',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    tir_str = match.group(1).replace(',', '.').strip()

                    # Validate the TIR string
                    if not tir_str or not re.match(r'^[0-9]+\.?[0-9]*$', tir_str):
                        continue

                    try:
                        tir_value = float(tir_str)
                        # Convert percentage to decimal (18.98% -> 0.1898)
                        if tir_value > 1:
                            return Decimal(str(tir_value / 100))
                        else:
                            return Decimal(str(tir_value))

                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid TIR format for {ticker}: '{tir_str}' - {e}")
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting TIR for {ticker}: {e}")
            return None

    def _extract_price(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract current price from ecovalores.com page content"""
        try:
            # Ecovalores price patterns
            patterns = [
                # Main price display (like "74.990,00")
                r'([0-9]{2,}\.?[0-9]*,?[0-9]{2})(?=\s*<|$)',

                # Price section patterns
                r'Precio[^0-9]*([0-9.]+,?[0-9]*)',
                r'Cotización[^0-9]*([0-9.]+,?[0-9]*)',

                # Large number patterns (for bond prices)
                r'([0-9]{3,}\.?[0-9]*,?[0-9]{0,2})(?!\d)',
            ]

            price_candidates = []

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE)
                for match in matches:
                    price_str = match.group(1).replace('.', '').replace(',', '.').strip()

                    # Validate the price string
                    if not price_str or not re.match(r'^[0-9]+\.?[0-9]*$', price_str):
                        continue

                    try:
                        price_value = Decimal(price_str)
                        # Bond prices validation: reasonable range 1-1,000,000 ARS
                        if 1 <= price_value <= 1000000:
                            price_candidates.append(price_value)
                    except (ValueError, TypeError):
                        continue

            # Return the largest reasonable price (likely the main bond price)
            if price_candidates:
                return max(price_candidates)

            return None

        except Exception as e:
            logger.error(f"Error extracting price for {ticker}: {e}")
            return None

    def _extract_paridad(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract paridad from ecovalores.com page content"""
        try:
            patterns = [
                r'Paridad[^0-9]*([0-9,]+)%',
                r'Parity[^0-9]*([0-9,]+)%',
                r'>Paridad<.*?>([0-9,]+)%',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    paridad_str = match.group(1).replace(',', '.').strip()

                    if not paridad_str or not re.match(r'^[0-9]+\.?[0-9]*$', paridad_str):
                        continue

                    try:
                        paridad_value = float(paridad_str)
                        return Decimal(str(paridad_value / 100))  # Convert percentage to decimal
                    except (ValueError, TypeError):
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting paridad for {ticker}: {e}")
            return None

    def _extract_valor_tecnico(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract valor tecnico from ecovalores.com page content"""
        try:
            patterns = [
                r'Valor\s+Técnico[^0-9]*([0-9,]+)',
                r'Technical\s+Value[^0-9]*([0-9,]+)',
                r'>Valor Técnico<.*?>([0-9,]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    valor_str = match.group(1).replace(',', '.').strip()

                    if not valor_str or not re.match(r'^[0-9]+\.?[0-9]*$', valor_str):
                        continue

                    try:
                        return Decimal(valor_str)
                    except (ValueError, TypeError):
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting valor tecnico for {ticker}: {e}")
            return None

    def _extract_duration(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract duration from ecovalores.com page content"""
        try:
            patterns = [
                r'Duration[^0-9]*([0-9,]+)',
                r'Duración[^0-9]*([0-9,]+)',
                r'>Duration<.*?>([0-9,]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    duration_str = match.group(1).replace(',', '.').strip()

                    if not duration_str or not re.match(r'^[0-9]+\.?[0-9]*$', duration_str):
                        continue

                    try:
                        return Decimal(duration_str)
                    except (ValueError, TypeError):
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting duration for {ticker}: {e}")
            return None