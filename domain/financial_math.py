import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class FinancialCalculator:
    @staticmethod
    def calculate_tea_from_tir(tir: float, days_to_maturity: int) -> float:
        if tir <= -1 or days_to_maturity <= 0:
            return 0.0
        tea = (1 + tir) ** (365 / days_to_maturity) - 1
        return tea

    @staticmethod
    def calculate_tem_from_tea(tea: float) -> float:
        if tea <= -1:
            return 0.0
        tem = (1 + tea) ** (1 / 12) - 1
        return tem

    @staticmethod
    def calculate_tna_from_tem(tem: float) -> float:
        return tem * 12

    @staticmethod
    def calculate_tna_from_tea(tea: float, compounding_frequency: int = 12) -> float:
        if tea <= -1 or compounding_frequency <= 0:
            return 0.0
        tna = ((1 + tea) ** (1 / compounding_frequency) - 1) * compounding_frequency
        return tna
