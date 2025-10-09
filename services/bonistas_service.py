"""
Service to fetch real TIR data from bonistas.com
"""
import requests
import logging
from decimal import Decimal
from typing import Optional, Dict
import re

logger = logging.getLogger(__name__)

class BonistasService:
    """Service to fetch bond data including real TIR from bonistas.com"""

    def __init__(self):
        self.base_url = "https://bonistas.com/bono-cotizacion-rendimiento-precio-hoy"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })

    def get_bond_tir(self, ticker: str) -> Optional[Dict]:
        """
        Get real TIR for a bond from bonistas.com

        Returns:
            Dict with ticker, tir, price, and other metrics if found, None otherwise
        """
        try:
            url = f"{self.base_url}/{ticker}"
            response = self.session.get(url, timeout=10)

            if response.status_code != 200:
                logger.warning(f"Failed to fetch {ticker} from bonistas.com: {response.status_code}")
                return None

            content = response.text

            # Check if the page actually contains bond data (not just empty/error page)
            if not content or ticker.upper() not in content.upper():
                logger.warning(f"No data found for {ticker} on bonistas.com - ticker may not exist")
                return None

            # Extract TIR from the page
            tir = self._extract_tir(content, ticker)
            if tir is None:
                return None

            # Extract other metrics
            price = self._extract_price(content, ticker)
            valor_tecnico = self._extract_valor_tecnico(content, ticker)

            return {
                'ticker': ticker,
                'tir': tir,
                'price': price,
                'valor_tecnico': valor_tecnico,
                'source': 'bonistas.com'
            }

        except Exception as e:
            logger.error(f"Error fetching TIR for {ticker}: {e}")
            return None

    def _extract_tir(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract TIR from bonistas.com page content"""
        try:
            # More specific patterns for bonistas.com HTML structure
            patterns = [
                # Direct percentage patterns (like "19.53%")
                r'TIR[^0-9]*([0-9.,]+)%',
                r'Rendimiento[^0-9]*([0-9.,]+)%',
                r'Tasa[^0-9]*([0-9.,]+)%',

                # JSON-like patterns
                r'"TIR":\s*"?([0-9.,]+)%?"?',
                r'"tir":\s*"?([0-9.,]+)%?"?',
                r'"rendimiento":\s*"?([0-9.,]+)%?"?',

                # HTML table or div patterns
                r'<[^>]*TIR[^>]*>.*?([0-9.,]+)%',
                r'TIR.*?>\s*([0-9.,]+)%',

                # Decimal patterns (0.1953 format)
                r'"TIR":\s*([0-9.]+)(?!\d)',
                r'"tir":\s*([0-9.]+)(?!\d)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE | re.DOTALL)
                if match:
                    tir_str = match.group(1).replace(',', '').strip()

                    # Validate the TIR string
                    if not tir_str or not re.match(r'^[0-9]+\.?[0-9]*$', tir_str):
                        continue

                    try:
                        tir_value = float(tir_str)

                        # If TIR is between 0 and 1, it's in decimal form (e.g., 0.1953)
                        # If TIR is > 1, it's in percentage form (e.g., 19.53)
                        if 0 <= tir_value <= 1:
                            return Decimal(str(tir_value))  # Already in decimal form
                        elif 1 < tir_value <= 100:
                            return Decimal(str(tir_value / 100))  # Convert percentage to decimal
                        else:
                            # Invalid TIR value
                            logger.warning(f"Invalid TIR value for {ticker}: {tir_value}")
                            continue

                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid TIR format for {ticker}: '{tir_str}' - {e}")
                        continue

            logger.warning(f"Could not extract TIR for {ticker}")
            return None

        except Exception as e:
            logger.error(f"Error extracting TIR for {ticker}: {e}")
            return None

    def _extract_price(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract current price from bonistas.com page content"""
        try:
            # More specific patterns for bonistas.com price extraction
            patterns = [
                # JSON-LD structured data (most reliable)
                r'"price":\s*"([0-9.]+)"',
                r'"price":\s*([0-9.]+)',

                # Specific bonistas price section
                r'Precio\s*\n\s*([0-9.]+)',
                r'Precio[^0-9]*\s*([0-9.]+)',

                # Direct numeric patterns (5+ digits for bonds)
                r'\b([0-9]{5,}\.?[0-9]{0,2})\b',

                # Currency patterns
                r'ARS\s*([0-9.]+)',
                r'\$\s*([0-9.]+)',

                # HTML content patterns
                r'>([0-9]{5,}\.?[0-9]{0,2})<',
                r'precio[^0-9]*([0-9.]+)',
                r'cotizacion[^0-9]*([0-9.]+)',
            ]

            for pattern in patterns:
                matches = re.finditer(pattern, content, re.IGNORECASE | re.DOTALL)
                for match in matches:
                    price_str = match.group(1).replace(',', '').strip()

                    # Validate the price string
                    if not price_str or not re.match(r'^[0-9]+\.?[0-9]*$', price_str):
                        continue

                    try:
                        price_value = Decimal(price_str)
                        # Basic validation (positive value)
                        if price_value > 0:
                            return price_value
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid price format for {ticker}: '{price_str}' - {e}")
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting price for {ticker}: {e}")
            return None

    def _extract_valor_tecnico(self, content: str, ticker: str) -> Optional[Decimal]:
        """Extract valor tecnico from bonistas.com page content"""
        try:
            # Look for valor tecnico patterns
            patterns = [
                r'"valor_tecnico":\s*([0-9.,]+)',
                r'"Valor Técnico":\s*([0-9.,]+)',
                r'Valor\s+[Tt]écnico["\s]*:?\s*([0-9.,]+)',
            ]

            for pattern in patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    valor_str = match.group(1).replace(',', '').strip()

                    # Validate the valor tecnico string before converting to Decimal
                    if not valor_str or not re.match(r'^[0-9]+\.?[0-9]*$', valor_str):
                        continue

                    try:
                        return Decimal(valor_str)
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Invalid valor tecnico format for {ticker}: '{valor_str}' - {e}")
                        continue

            return None

        except Exception as e:
            logger.error(f"Error extracting valor tecnico for {ticker}: {e}")
            return None