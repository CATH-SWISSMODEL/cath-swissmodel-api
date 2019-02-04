"""
Defines errors that can occur within this library
"""

class ApiClientError(Exception):
    pass

class ConfigError(Exception):
    pass

class ArgError(Exception):
    pass

class AuthenticationError(ApiClientError):
    pass
