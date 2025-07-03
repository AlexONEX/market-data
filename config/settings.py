import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    PPI_PUBLIC_KEY = os.getenv("PPI_PUBLIC_KEY")
    PPI_PRIVATE_KEY = os.getenv("PPI_PRIVATE_KEY")


settings = Settings()

if __name__ == "__main__":
    print(f"PPI Public Key: {settings.PPI_PUBLIC_KEY}")
    print(f"PPI Private Key: {'*' * len(settings.PPI_PRIVATE_KEY) if settings.PPI_PRIVATE_KEY else 'Not set'}")
