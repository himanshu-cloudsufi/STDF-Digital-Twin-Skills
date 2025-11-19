"""Custom exceptions for energy forecasting"""


class DataNotFoundError(Exception):
    """Raised when required dataset not found"""
    pass


class DataValidationError(Exception):
    """Raised when data fails validation checks"""
    pass


class ConfigurationError(Exception):
    """Raised when configuration is invalid"""
    pass


class EnergyBalanceError(Exception):
    """Raised when energy balance check fails"""
    pass
