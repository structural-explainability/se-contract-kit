"""Shared exception types."""


class ContractKitError(Exception):
    """Base exception for se-contract-kit errors."""


class ContractKitFileError(ContractKitError):
    """Raised when a required file cannot be found, read, or written."""


class ContractKitConfigError(ContractKitError):
    """Raised when a declaration or configuration file is invalid."""


class ContractKitPathError(ContractKitError):
    """Raised when a path cannot be resolved safely."""


class ContractKitJsonError(ContractKitError):
    """Raised when JSON serialization or parsing fails."""
