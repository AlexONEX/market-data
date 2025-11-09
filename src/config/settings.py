import logging
import os

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

load_dotenv()


class Settings:
    PPI_PUBLIC_KEY = os.getenv("PPI_PUBLIC_KEY")
    PPI_PRIVATE_KEY = os.getenv("PPI_PRIVATE_KEY")


settings = Settings()

if __name__ == "__main__":
    logger.info("PPI Public Key: %s", settings.PPI_PUBLIC_KEY) # T201
    logger.info( # T201
        "PPI Private Key: %s",
        "*" * len(settings.PPI_PRIVATE_KEY) if settings.PPI_PRIVATE_KEY else "Not set",
    )
