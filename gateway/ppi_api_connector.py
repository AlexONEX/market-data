import logging
import os
from datetime import datetime, timedelta

from ppi_client.ppi import PPI

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class PPIAPIConnector:
    """
    Manages the connection and authentication to the PPI API.
    Acts as a singleton to ensure a single authenticated client instance.
    """

    _instance = None
    _ppi_client: PPI | None = None  # Explicitly type hint as possibly None initially
    _public_key: str | None = None
    _private_key: str | None = None
    _token_expires_at: datetime | None = None

    def __new__(cls):
        """Implements the Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(PPIAPIConnector, cls).__new__(cls)
            # Call _initialize on the new instance only if the class-level client is not set
            # This ensures initialization (including key loading and first auth) happens only once
            if PPIAPIConnector._ppi_client is None:
                cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        """
        Initializes the PPI client and performs the initial authentication.
        This method is guaranteed to run only once for the singleton.
        """
        PPIAPIConnector._public_key = os.getenv("PPI_PUBLIC_KEY")
        PPIAPIConnector._private_key = os.getenv("PPI_PRIVATE_KEY")

        if PPIAPIConnector._public_key is None:
            raise ValueError("Environment variable PPI_PUBLIC_KEY not set.")
        if PPIAPIConnector._private_key is None:
            raise ValueError("Environment variable PPI_PRIVATE_KEY not set.")

        # Instantiate the PPI client
        PPIAPIConnector._ppi_client = PPI(sandbox=False)

        # Perform initial authentication
        self._authenticate()

    def _authenticate(self):
        """Performs authentication to establish a session with the PPI API."""
        logging.info(
            "PPIAPIConnector: Autenticando con la API de PPI usando Public/Private Keys..."
        )
        try:
            # Ensure _ppi_client is not None before calling its method
            if PPIAPIConnector._ppi_client is None:
                # This should ideally not happen if _initialize runs correctly
                raise RuntimeError(
                    "PPI client is not initialized before authentication attempt."
                )

            # Assert to help the type checker understand that these are definitely strings here
            assert PPIAPIConnector._public_key is not None
            assert PPIAPIConnector._private_key is not None

            PPIAPIConnector._ppi_client.account.login_api(
                PPIAPIConnector._public_key, PPIAPIConnector._private_key
            )

            # Assuming a successful login establishes a session handled internally by ppi_client.
            # We set a dummy expiry time for internal tracking or to trigger a re-auth if needed.
            PPIAPIConnector._token_expires_at = datetime.now() + timedelta(
                minutes=60
            )  # Assume 60 min session
            logging.info("PPIAPIConnector: Autenticación exitosa. Sesión establecida.")
        except Exception as e:
            logging.error(
                f"PPIAPIConnector: Error durante la autenticación con Public/Private Keys: {e}"
            )
            # Re-raise as ConnectionError to indicate a critical setup failure
            raise ConnectionError("No se pudo autenticar con la API de PPI.") from e

    def get_client(self) -> PPI:
        """
        Returns the authenticated PPI client instance.
        If the session is near expiry (based on our internal tracker), it attempts re-authentication.
        Raises RuntimeError if the client was somehow not initialized (which shouldn't happen).
        """
        # Ensure _ppi_client is initialized. If it's None here, it means _initialize failed or wasn't called.
        if PPIAPIConnector._ppi_client is None:
            logging.error(
                "PPIAPIConnector: get_client called but PPI client is None. Initialization failed?"
            )
            raise RuntimeError("PPI client not initialized.")

        # Check if our tracked token expiry is near. If so, attempt to re-authenticate.
        # This is a proactive step; the ppi_client library might also have its own internal refresh.
        if PPIAPIConnector._token_expires_at and datetime.now() >= (
            PPIAPIConnector._token_expires_at - timedelta(minutes=5)
        ):
            logging.info(
                "PPIAPIConnector: Session might be expiring soon. Attempting re-authentication."
            )
            self._authenticate()  # Re-authenticate, which updates PPIAPIConnector._token_expires_at

        # At this point, _ppi_client is guaranteed to be a PPI instance or an error would have been raised.
        return PPIAPIConnector._ppi_client
