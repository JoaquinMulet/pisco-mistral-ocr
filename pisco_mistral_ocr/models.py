# pisco_mistral_ocr/models.py
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field, ConfigDict

class BaseMistralModel(BaseModel):
    model_config = ConfigDict(extra='allow')

# --- Modelos OCR ---
class OcrPage(BaseMistralModel):
    index: int
    markdown: str
    images: Optional[List[Any]] = None
    dimensions: Optional[Dict[str, Any]] = None

class OcrUsageInfo(BaseMistralModel):
    pages_processed: int
    doc_size_bytes: Optional[int] = None

class OcrResult(BaseMistralModel):
    id: Optional[str] = None
    object: Optional[str] = "ocr.ocr_result"
    model: str
    pages: List[OcrPage]
    usage_info: Optional[OcrUsageInfo] = None

# --- Modelos Chat/Document Understanding ---
class TextContentPart(BaseMistralModel):
    type: str = "text"
    text: str

class DocumentUrlContentPart(BaseMistralModel):
    type: str = "document_url"
    document_url: str

MessageContentPart = Union[TextContentPart, DocumentUrlContentPart]

class ChatMessage(BaseMistralModel):
    role: str
    content: Union[str, List[MessageContentPart]]

class ChatCompletionChoice(BaseMistralModel):
    index: int
    message: ChatMessage
    finish_reason: Optional[str] = None

class UsageInfo(BaseMistralModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResult(BaseMistralModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: UsageInfo

# --- Modelos para el manejo de archivos ---
class FileUploadResponse(BaseMistralModel):
    id: str
    object: str = "file"
    size_bytes: int = Field(..., alias='bytes')
    created_at: int
    filename: str
    purpose: str

class SignedUrlResponse(BaseMistralModel):
    url: str

# NUEVO: Modelo para la respuesta de eliminación de archivo
class FileDeleteResponse(BaseMistralModel):
    id: str
    object: str # Probablemente algo como 'file.deleted'
    deleted: bool