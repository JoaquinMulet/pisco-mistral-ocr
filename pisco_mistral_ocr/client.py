# pisco_mistral_ocr/client.py
import httpx
import os
import mimetypes
import logging # Importar logging
from typing import Optional, Type, Dict, Any, Union, Tuple # Añadir Tuple
from types import TracebackType

from .exceptions import (
    PiscoMistralOcrError, ApiError, ConfigurationError, NetworkError, FileError
)
from .models import (
    OcrResult, ChatCompletionResult, FileUploadResponse, SignedUrlResponse,
    FileDeleteResponse, # Importar nuevo modelo
    BaseMistralModel
)

# Configurar un logger básico para la librería
logger = logging.getLogger(__name__)

# Re-export exceptions
PiscoMistralOcrError = PiscoMistralOcrError
ApiError = ApiError
ConfigurationError = ConfigurationError
NetworkError = NetworkError
FileError = FileError


class PiscoMistralOcrClient:
    DEFAULT_BASE_URL = "https://api.mistral.ai/v1"
    DEFAULT_OCR_MODEL = "mistral-ocr-latest"
    DEFAULT_CHAT_MODEL = "mistral-small-latest"

    def __init__( # ... (sin cambios en __init__) ...
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        default_ocr_model: str = DEFAULT_OCR_MODEL,
        default_chat_model: str = DEFAULT_CHAT_MODEL,
        timeout: float = 60.0,
    ):
        self.api_key = api_key or os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ConfigurationError(
                "Mistral API key not provided. Set the MISTRAL_API_KEY "
                "environment variable or pass the api_key argument."
            )
        self.base_url = base_url
        self.default_ocr_model = default_ocr_model
        self.default_chat_model = default_chat_model

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Accept": "application/json",
            },
            timeout=timeout
        )

    async def __aenter__(self): # ... (sin cambios) ...
        return self

    async def __aexit__( # ... (sin cambios) ...
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType]
    ) -> None:
        await self.aclose()

    async def aclose(self): # ... (sin cambios) ...
        await self._client.aclose()

    async def _request( # ... (sin cambios en la lógica principal, solo añadir logging) ...
        self,
        method: str,
        endpoint: str,
        response_model: Optional[Type[BaseMistralModel]] = None, # Hacer opcional para DELETE
        **kwargs
    ) -> Union[BaseMistralModel, Dict[str, Any], None]: # Puede devolver None para DELETE
        if 'json' in kwargs and 'headers' not in kwargs:
             kwargs['headers'] = {'Content-Type': 'application/json'}
        elif 'json' in kwargs and 'Content-Type' not in kwargs.get('headers', {}):
             if 'headers' not in kwargs: kwargs['headers'] = {}
             kwargs['headers']['Content-Type'] = 'application/json'

        try:
            logger.debug("Sending API request: %s %s", method, endpoint)
            response = await self._client.request(method, endpoint, **kwargs)
            logger.debug("Received API response: Status %d", response.status_code)
            response.raise_for_status()

            # Handle successful deletion (e.g., 200 OK with body or 204 No Content)
            if method.upper() == "DELETE":
                if response.status_code == 204:
                    logger.debug("File deleted successfully (204 No Content).")
                    return None # O un objeto FileDeleteResponse(deleted=True) si prefieres
                # Si hay cuerpo, intenta parsearlo
                if not response.content: # Check if body is empty even on 200
                    logger.debug("File deleted successfully (200 OK, empty body).")
                    return None # O un objeto FileDeleteResponse(deleted=True)

            # If response_model is None (e.g. for DELETE with no expected body), return None
            if response_model is None:
                 return None # Or the raw response if preferred for some reason

            try:
                response_data = response.json()
                logger.debug("Parsing response into %s", response_model.__name__)
                return response_model.model_validate(response_data)
            except Exception as e:
                logger.warning(
                    "Failed to parse response into %s: %s. Response: %s",
                    response_model.__name__, e, response.text, exc_info=True
                )
                return response.json() # Return raw dict as fallback

        except httpx.HTTPStatusError as e:
            error_details = {}
            try:
                error_details = e.response.json()
            except Exception:
                error_details = {"message": e.response.text or "No error details available"}
            logger.error("API Error %d: %s", e.response.status_code, error_details, exc_info=True)
            raise ApiError(e.response.status_code, error_details) from e
        except httpx.RequestError as e:
            logger.error("Network request to %s failed: %s", e.request.url, e, exc_info=True)
            raise NetworkError(f"Network request to {e.request.url} failed: {e}") from e
        except Exception as e:
            logger.exception("An unexpected error occurred during API request.") # Log full traceback
            raise PiscoMistralOcrError(f"An unexpected error occurred: {e}") from e

    # MODIFICADO: Devuelve Tuple[str, str] (signed_url, file_id)
    async def _handle_file_upload(self, file_path: str) -> Tuple[str, str]:
        """Uploads file, returns (signed_url, file_id)."""
        filename = os.path.basename(file_path)
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or 'application/octet-stream'
        file_id: Optional[str] = None # Para el finally

        try:
            logger.info("Uploading file: %s", file_path)
            with open(file_path, "rb") as f:
                files = {'file': (filename, f, mime_type)}
                data = {'purpose': 'ocr'}
                upload_resp = await self._request(
                    "POST", "/files", response_model=FileUploadResponse,
                    files=files, data=data, headers={}
                )
                if not isinstance(upload_resp, FileUploadResponse):
                     raise PiscoMistralOcrError(f"Failed to parse file upload response: {upload_resp}")
                file_id = upload_resp.id
                logger.info("File uploaded successfully. File ID: %s", file_id)

            logger.info("Getting signed URL for file ID: %s", file_id)
            signed_url_resp = await self._request(
                "GET", f"/files/{file_id}/url", response_model=SignedUrlResponse
            )
            if not isinstance(signed_url_resp, SignedUrlResponse):
                raise PiscoMistralOcrError(f"Failed to parse signed URL response: {signed_url_resp}")
            logger.info("Obtained signed URL successfully.")
            return signed_url_resp.url, file_id # Devolver ambos

        except FileNotFoundError:
            logger.error("Local file not found for upload: %s", file_path)
            raise FileError(f"Local file not found: {file_path}") from None
        except OSError as e:
            logger.error("Could not read file for upload %s: %s", file_path, e)
            raise FileError(f"Could not read file {file_path}: {e}") from e
        # ApiError, NetworkError son manejados y logueados por _request

    # NUEVO: Método para eliminar archivo
    async def delete_file(self, file_id: str) -> bool:
        """
        Deletes a file previously uploaded to Mistral.

        Args:
            file_id: The ID of the file to delete.

        Returns:
            True if deletion was successful, False otherwise (though usually raises error on failure).

        Raises:
            ApiError: If the Mistral API returns an error during deletion.
            NetworkError: If a network issue occurs.
        """
        logger.info("Requesting deletion for file ID: %s", file_id)
        try:
            # Esperamos FileDeleteResponse o None si la API devuelve 204 o 200 vacío
            result = await self._request(
                "DELETE",
                f"/files/{file_id}",
                response_model=FileDeleteResponse # Usa el modelo, aunque puede ser None
            )
            # Consideramos éxito si no hubo excepción y la respuesta es None (204)
            # o si es FileDeleteResponse con deleted=True
            deleted = result is None or (isinstance(result, FileDeleteResponse) and result.deleted)
            if deleted:
                 logger.info("File %s deleted successfully.", file_id)
                 return True
            else:
                 # Esto podría pasar si la API devuelve 200 OK pero un JSON inesperado
                 logger.warning("File deletion request for %s completed but response indicates not deleted or parsing failed: %s", file_id, result)
                 return False
        except (ApiError, NetworkError) as e:
            logger.error("Failed to delete file %s: %s", file_id, e)
            raise e # Re-lanzar para que el llamador sepa que falló
        except Exception as e:
            logger.exception("Unexpected error during file deletion for %s.", file_id)
            raise PiscoMistralOcrError(f"Unexpected error deleting file {file_id}: {e}") from e

    
    async def ocr(
        self,
        source: str,
        model: Optional[str] = None,
        include_image_base64: bool = True,
        delete_after_processing: bool = True, # Nuevo parámetro
    ) -> OcrResult:
        """ Performs OCR... (docstring sin cambios excepto añadir el nuevo parámetro) """
        model = model or self.default_ocr_model
        doc_type: str
        doc_value: str
        file_id_to_delete: Optional[str] = None # Para guardar el ID si subimos archivo

        try:
            is_likely_url = source.startswith(("http://", "https://"))
            is_file = not is_likely_url and os.path.exists(source)

            if is_file:
                logger.info("Processing local file for OCR: %s", source)
                # Obtener URL firmada Y file_id
                doc_value, file_id_to_delete = await self._handle_file_upload(source)
                doc_type = "document_url"
            elif is_likely_url:
                logger.info("Processing URL for OCR: %s", source)
                doc_value = source
                if any(source.lower().endswith(ext) for ext in ['.png', '.jpg', '.jpeg', '.webp', '.gif']):
                     doc_type = "image_url"
                else:
                     doc_type = "document_url"
            else:
                raise ValueError(
                    f"Source '{source}' is not recognized as a valid URL "
                    "or an existing local file path."
                )

            document_payload = {"type": doc_type}
            if doc_type == "image_url":
                document_payload["image_url"] = doc_value
            else:
                document_payload["document_url"] = doc_value

            payload = {
                "model": model,
                "document": document_payload,
                "include_image_base64": include_image_base64,
            }

            logger.info("Sending OCR request for source: %s", source)
            result = await self._request("POST", "/ocr", response_model=OcrResult, json=payload)
            if not isinstance(result, OcrResult):
                 raise PiscoMistralOcrError(f"OCR request did not return a valid OcrResult: {result}")
            logger.info("OCR request successful for source: %s", source)
            return result # Devolver el resultado ANTES del finally

        finally:
            # Intentar borrar SOLO si se subió un archivo Y se pidió borrarlo
            if file_id_to_delete and delete_after_processing:
                logger.info("Attempting post-OCR deletion for file ID: %s", file_id_to_delete)
                try:
                    await self.delete_file(file_id_to_delete)
                except Exception as e:
                    # Loguear el error de borrado pero NO relanzarlo para no ocultar el resultado/error original
                    logger.warning(
                        "Failed to delete file %s after OCR processing: %s",
                        file_id_to_delete, e, exc_info=True # Añadir traceback al log
                    )


    # MODIFICADO: Añadir delete_after_processing y bloque finally
    async def ask(
        self,
        source: str,
        question: str,
        model: Optional[str] = None,
        doc_image_limit: int = 8,
        doc_page_limit: int = 64,
        delete_after_processing: bool = False, # Nuevo parámetro
    ) -> ChatCompletionResult:
        """ Asks a question... (docstring sin cambios excepto añadir el nuevo parámetro) """
        model = model or self.default_chat_model
        doc_url: str
        file_id_to_delete: Optional[str] = None # Para guardar el ID

        try:
            is_likely_url = source.startswith(("http://", "https://"))
            is_file = not is_likely_url and os.path.exists(source)

            if is_file:
                 logger.info("Processing local file for Ask: %s", source)
                 # Obtener URL firmada Y file_id
                 doc_url, file_id_to_delete = await self._handle_file_upload(source)
            elif is_likely_url:
                 logger.info("Processing URL for Ask: %s", source)
                 doc_url = source
            else:
                 raise ValueError(
                    f"Source '{source}' is not recognized as a valid URL "
                    "or an existing local file path."
                 )

            message_content = [
                {"type": "text", "text": question},
                {"type": "document_url", "document_url": doc_url}
            ]
            payload = {
                "model": model,
                "messages": [{"role": "user", "content": message_content}],
                "document_image_limit": doc_image_limit,
                "document_page_limit": doc_page_limit,
            }

            logger.info("Sending Ask request for source: %s", source)
            result = await self._request("POST", "/chat/completions", response_model=ChatCompletionResult, json=payload)
            if not isinstance(result, ChatCompletionResult):
                 raise PiscoMistralOcrError(f"Ask request did not return a valid ChatCompletionResult: {result}")
            logger.info("Ask request successful for source: %s", source)
            return result # Devolver el resultado ANTES del finally

        finally:
             # Intentar borrar SOLO si se subió un archivo Y se pidió borrarlo
            if file_id_to_delete and delete_after_processing:
                logger.info("Attempting post-Ask deletion for file ID: %s", file_id_to_delete)
                try:
                    await self.delete_file(file_id_to_delete)
                except Exception as e:
                    logger.warning(
                        "Failed to delete file %s after Ask processing: %s",
                        file_id_to_delete, e, exc_info=True
                    )
