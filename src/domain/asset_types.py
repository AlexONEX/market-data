from enum import Enum


class FixedIncomeAssetType(Enum):
    """Defines categories for fixed-income assets."""

    FIXED_RATE = "Fixed Rate Bonds"
    CER_LINKED = "CER Linked Bonds"
    DOLLAR_LINKED = "Dollar Linked Bonds"
    DUAL_BONDS = "Dual Bonds"
    OTHER_BONDS = "Other Bonds"

    @staticmethod
    def from_string(s: str):
        for member in FixedIncomeAssetType:
            if member.value.lower() == s.lower():
                return member
        raise ValueError(f"'{s}' is not a valid FixedIncomeAssetType")
