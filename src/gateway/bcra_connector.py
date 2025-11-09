import logging

import requests
from requests.exceptions import HTTPError, RequestException

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class BCRAAPIConnector:
    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializa el conector. En este caso, no hay autenticación compleja."""
        logger.info("Inicializando BCRAAPIConnector.")
        # No se requiere autenticación ni manejo de tokens para esta API pública.

    def get_series_data(self, variable_id: int): # Made public
        url = f"{self.BASE_URL}/{variable_id}"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except (RequestException, HTTPError) as e:
            logger.exception("Error when connecting to BCRA API: %s", e)
            return None
        except ValueError as e:
            logger.exception(
                "Error when parsing api response for ID %s: %s", variable_id, e
            )
            return None
