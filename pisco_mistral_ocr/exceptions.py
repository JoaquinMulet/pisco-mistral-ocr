# pisco_mistral_ocr/exceptions.py
from typing import Dict, Any

class PiscoMistralOcrError(Exception):
    """Clase base de excepción para errores de PiscoMistralOcr."""
    pass

class ConfigurationError(PiscoMistralOcrError):
    """Error relacionado con la configuración de la librería (ej., falta de API key)."""
    pass

class ApiError(PiscoMistralOcrError):
    """Representa un error devuelto por la API de Mistral."""
    def __init__(self, status_code: int, error_details: Dict[str, Any]):
        self.status_code = status_code
        self.error_details = error_details
        message = error_details.get('message', 'Error de API desconocido')
        super().__init__(f"Error de API Mistral {status_code}: {message}")

class NetworkError(PiscoMistralOcrError):
    """Error relacionado con la conectividad de red durante las llamadas a la API."""
    pass

class FileError(PiscoMistralOcrError):
    """Error relacionado con el manejo de archivos locales (ej., archivo no encontrado)."""
    pass
