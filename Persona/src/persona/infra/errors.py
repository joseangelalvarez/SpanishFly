class PersonaError(Exception):
    """Base error for Persona module."""


class ConfigError(PersonaError):
    """Configuration is invalid or missing."""


class ModelLoadError(PersonaError):
    """A model failed to load from a local path."""


class GenerationCancelled(PersonaError):
    """Generation was cancelled by the user."""
