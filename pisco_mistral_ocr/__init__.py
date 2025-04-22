# pisco_mistral_ocr/__init__.py
# (El código anterior está bien, nos aseguramos de que los modelos y excepciones necesarios estén)
"""
PiscoMistralOcr: Un cliente asíncrono fácil de usar para las APIs de OCR y
Comprensión de Documentos de Mistral AI.
"""
from .client import PiscoMistralOcrClient
from .exceptions import (
    PiscoMistralOcrError, ApiError, NetworkError, FileError, ConfigurationError
)
from .models import (
    OcrResult, ChatCompletionResult, OcrPage, ChatMessage, ChatCompletionChoice,
    FileUploadResponse, SignedUrlResponse, FileDeleteResponse # Asegúrate que todos los necesarios están
)

__version__ = "0.1.1" # Incrementar versión por la nueva funcionalidad

__all__ = [
    "PiscoMistralOcrClient",
    # Exceptions
    "PiscoMistralOcrError",
    "ApiError",
    "NetworkError",
    "FileError",
    "ConfigurationError",
    # Models (Exportar los principales y componentes útiles)
    "OcrResult",
    "ChatCompletionResult",
    "OcrPage",
    "ChatMessage",
    "ChatCompletionChoice",
    # Probablemente no necesites exportar los de archivos/URL/delete
]