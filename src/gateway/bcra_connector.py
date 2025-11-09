import requests
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class BCRAAPIConnector:
    BASE_URL = "https://api.bcra.gob.ar/estadisticas/v3.0/monetarias"
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BCRAAPIConnector, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """Inicializa el conector. En este caso, no hay autenticación compleja."""
        logging.info("Inicializando BCRAAPIConnector.")
        # No se requiere autenticación ni manejo de tokens para esta API pública.

    def _get_series_data(self, variable_id: int):
        url = f"{self.BASE_URL}/{variable_id}"
        try:
            response = requests.get(url, verify=False)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])
        except requests.exceptions.RequestException:
            logging.error("Error when connecting to BCRA API")
            return None
        except ValueError as e:
            logging.error(f"Error when parsing api response for ID {variable_id}: {e}")
            return None
