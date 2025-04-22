# tests/test_client.py
import os
import pathlib
import pytest
import respx
import uuid
import logging
import json # <--- Importar json
from httpx import Response

# No necesitas dotenv si usas mocks y una API key falsa
# from dotenv import load_dotenv
# load_dotenv()

from pisco_mistral_ocr import (
    PiscoMistralOcrClient,
    ApiError,
    FileError, # Sigue siendo necesario importarlo para otros tests
    NetworkError,
    PiscoMistralOcrError,
    ConfigurationError # Importar por si acaso
)
from pisco_mistral_ocr.models import (
    OcrResult,
    OcrPage,
    ChatCompletionResult,
    FileDeleteResponse,
    ChatMessage, # Importar para verificar payload de ask
    ChatCompletionChoice, # Importar para verificar payload de ask
)

# --- Configuración Constantes para Mocks ---
FAKE_API_KEY = "fake-test-key-no-secret"
MISTRAL_BASE_URL = PiscoMistralOcrClient.DEFAULT_BASE_URL
TEST_FILE_ID = f"file_id_{uuid.uuid4()}"

# --- Mock Responses ---
MOCK_OCR_RESPONSE_PAYLOAD = {
    "id": "ocr_res_123",
    "object": "ocr.ocr_result",
    "model": PiscoMistralOcrClient.DEFAULT_OCR_MODEL,
    "pages": [{"index": 0, "markdown": "# Mock Title\nMock content."}],
    "usage_info": {"pages_processed": 1, "doc_size_bytes": 1234}
}
MOCK_UPLOAD_RESPONSE_PAYLOAD = {
    "id": TEST_FILE_ID,
    "object": "file",
    "bytes": 1234,
    "created_at": 1700000000,
    "filename": "dummy_test_file.pdf", # Actualizado a nombre de archivo dummy
    "purpose": "ocr"
}
MOCK_SIGNED_URL_PAYLOAD = {"url": f"https://signed.url/for/{TEST_FILE_ID}"}
MOCK_ASK_RESPONSE_PAYLOAD = {
    "id": "chatcmpl_123",
    "object": "chat.completion",
    "created": 1700000000,
    "model": PiscoMistralOcrClient.DEFAULT_CHAT_MODEL,
    "choices": [{"index": 0, "message": {"role": "assistant", "content": "The title is Mock Title."}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}
}
MOCK_DELETE_SUCCESS_PAYLOAD = {
    "id": TEST_FILE_ID,
    "object": "file.deleted",
    "deleted": True
}
MOCK_API_ERROR_PAYLOAD = {"message": "Invalid resource ID"}

# --- Fixtures ---
TEST_DIR = pathlib.Path(__file__).parent
DUMMY_PDF_CONTENT = b"%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 100 100]>>endobj\nxref\n0 4\n0000000000 65535 f\n0000000010 00000 n\n0000000059 00000 n\n0000000118 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxref\n178\n%%EOF"
TEST_PDF_PATH = TEST_DIR / "dummy_test_file.pdf"

@pytest.fixture(scope="module", autouse=True)
def create_dummy_file():
    TEST_PDF_PATH.write_bytes(DUMMY_PDF_CONTENT)
    yield
    if TEST_PDF_PATH.exists():
        TEST_PDF_PATH.unlink()

@pytest.fixture
def client():
    return PiscoMistralOcrClient(api_key=FAKE_API_KEY)

# --- Tests ---

@pytest.mark.asyncio
@respx.mock
async def test_ocr_url_success(client: PiscoMistralOcrClient):
    """Probar OCR éxito con URL."""
    test_url = "https://example.com/document.pdf"
    ocr_route = respx.post(f"{MISTRAL_BASE_URL}/ocr").mock(return_value=Response(200, json=MOCK_OCR_RESPONSE_PAYLOAD))

    result = await client.ocr(test_url)

    assert ocr_route.called
    # CORRECCIÓN: Parsear payload y verificar diccionario
    request_payload_dict = json.loads(ocr_route.calls[0].request.content.decode())
    assert request_payload_dict.get("model") == PiscoMistralOcrClient.DEFAULT_OCR_MODEL
    assert "document" in request_payload_dict
    assert request_payload_dict["document"].get("type") == "document_url"
    assert request_payload_dict["document"].get("document_url") == test_url
    assert request_payload_dict.get("include_image_base64") is False # Verificar default

    assert isinstance(result, OcrResult)
    assert len(result.pages) == 1
    assert result.pages[0].markdown == "# Mock Title\nMock content."
    assert result.model == MOCK_OCR_RESPONSE_PAYLOAD["model"]
    assert result.usage_info.pages_processed == 1

@pytest.mark.asyncio
@respx.mock
async def test_ocr_file_success_no_delete(client: PiscoMistralOcrClient):
    """Probar OCR éxito con archivo local SIN eliminación."""
    upload_route = respx.post(f"{MISTRAL_BASE_URL}/files").mock(return_value=Response(200, json=MOCK_UPLOAD_RESPONSE_PAYLOAD))
    signed_url_route = respx.get(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}/url").mock(return_value=Response(200, json=MOCK_SIGNED_URL_PAYLOAD))
    ocr_route = respx.post(f"{MISTRAL_BASE_URL}/ocr").mock(return_value=Response(200, json=MOCK_OCR_RESPONSE_PAYLOAD))
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(200, json=MOCK_DELETE_SUCCESS_PAYLOAD))

    result = await client.ocr(str(TEST_PDF_PATH))

    assert upload_route.called
    assert signed_url_route.called
    assert ocr_route.called
    assert not delete_route.called

    # CORRECCIÓN: Parsear payload y verificar diccionario
    ocr_request_payload_dict = json.loads(ocr_route.calls[0].request.content.decode())
    assert "document" in ocr_request_payload_dict
    assert ocr_request_payload_dict["document"].get("type") == "document_url"
    assert ocr_request_payload_dict["document"].get("document_url") == MOCK_SIGNED_URL_PAYLOAD["url"]

    assert isinstance(result, OcrResult)
    assert result.pages[0].markdown == "# Mock Title\nMock content."

@pytest.mark.asyncio
@respx.mock
async def test_ocr_file_success_with_delete(client: PiscoMistralOcrClient):
    """Probar OCR éxito con archivo local CON eliminación."""
    upload_route = respx.post(f"{MISTRAL_BASE_URL}/files").mock(return_value=Response(200, json=MOCK_UPLOAD_RESPONSE_PAYLOAD))
    signed_url_route = respx.get(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}/url").mock(return_value=Response(200, json=MOCK_SIGNED_URL_PAYLOAD))
    ocr_route = respx.post(f"{MISTRAL_BASE_URL}/ocr").mock(return_value=Response(200, json=MOCK_OCR_RESPONSE_PAYLOAD))
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(200, json=MOCK_DELETE_SUCCESS_PAYLOAD))

    result = await client.ocr(str(TEST_PDF_PATH), delete_after_processing=True)

    assert upload_route.called
    assert signed_url_route.called
    assert ocr_route.called
    assert delete_route.called # Verificar que SÍ se llamó a delete

    assert isinstance(result, OcrResult)
    assert result.pages[0].markdown == "# Mock Title\nMock content."

@pytest.mark.asyncio
@respx.mock
async def test_ocr_file_delete_uses_204_no_content(client: PiscoMistralOcrClient):
    """Probar que el borrado maneja correctamente un 204 No Content."""
    upload_route = respx.post(f"{MISTRAL_BASE_URL}/files").mock(return_value=Response(200, json=MOCK_UPLOAD_RESPONSE_PAYLOAD))
    signed_url_route = respx.get(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}/url").mock(return_value=Response(200, json=MOCK_SIGNED_URL_PAYLOAD))
    ocr_route = respx.post(f"{MISTRAL_BASE_URL}/ocr").mock(return_value=Response(200, json=MOCK_OCR_RESPONSE_PAYLOAD))
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(204))

    result = await client.ocr(str(TEST_PDF_PATH), delete_after_processing=True)

    assert upload_route.called
    assert signed_url_route.called
    assert ocr_route.called
    assert delete_route.called
    assert isinstance(result, OcrResult)

@pytest.mark.asyncio
@respx.mock
async def test_ocr_file_delete_fails_gracefully(client: PiscoMistralOcrClient, caplog):
    """Probar que un fallo en delete no interrumpe y se loguea."""
    upload_route = respx.post(f"{MISTRAL_BASE_URL}/files").mock(return_value=Response(200, json=MOCK_UPLOAD_RESPONSE_PAYLOAD))
    signed_url_route = respx.get(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}/url").mock(return_value=Response(200, json=MOCK_SIGNED_URL_PAYLOAD))
    ocr_route = respx.post(f"{MISTRAL_BASE_URL}/ocr").mock(return_value=Response(200, json=MOCK_OCR_RESPONSE_PAYLOAD))
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(500, json={"message": "Internal Server Error"}))

    with caplog.at_level(logging.WARNING):
        result = await client.ocr(str(TEST_PDF_PATH), delete_after_processing=True)

    assert upload_route.called
    assert signed_url_route.called
    assert ocr_route.called
    assert delete_route.called
    assert isinstance(result, OcrResult)
    assert result.pages[0].markdown == "# Mock Title\nMock content."

    assert f"Failed to delete file {TEST_FILE_ID} after OCR processing" in caplog.text
    assert "ApiError" in caplog.text

@pytest.mark.asyncio
@respx.mock
async def test_ask_url_success(client: PiscoMistralOcrClient):
    """Probar Ask éxito con URL."""
    test_url = "https://example.com/ask_me.pdf"
    question = "¿Cuál es el título?"
    ask_route = respx.post(f"{MISTRAL_BASE_URL}/chat/completions").mock(return_value=Response(200, json=MOCK_ASK_RESPONSE_PAYLOAD))

    result = await client.ask(test_url, question)

    assert ask_route.called
    # CORRECCIÓN: Parsear payload y verificar diccionario
    request_payload_dict = json.loads(ask_route.calls[0].request.content.decode())
    assert request_payload_dict.get("model") == PiscoMistralOcrClient.DEFAULT_CHAT_MODEL
    assert "messages" in request_payload_dict
    assert isinstance(request_payload_dict["messages"], list) and len(request_payload_dict["messages"]) == 1
    assert request_payload_dict["messages"][0].get("role") == "user"
    content_list = request_payload_dict["messages"][0].get("content")
    assert isinstance(content_list, list)
    # Verificar ambas partes del contenido
    assert {"type": "text", "text": question} in content_list
    assert {"type": "document_url", "document_url": test_url} in content_list

    assert isinstance(result, ChatCompletionResult)
    assert result.choices[0].message.content == "The title is Mock Title."
    assert result.model == MOCK_ASK_RESPONSE_PAYLOAD["model"]

@pytest.mark.asyncio
@respx.mock
async def test_ask_file_success_with_delete(client: PiscoMistralOcrClient):
    """Probar Ask éxito con archivo local CON eliminación."""
    question = "¿Contenido?"
    upload_route = respx.post(f"{MISTRAL_BASE_URL}/files").mock(return_value=Response(200, json=MOCK_UPLOAD_RESPONSE_PAYLOAD))
    signed_url_route = respx.get(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}/url").mock(return_value=Response(200, json=MOCK_SIGNED_URL_PAYLOAD))
    ask_route = respx.post(f"{MISTRAL_BASE_URL}/chat/completions").mock(return_value=Response(200, json=MOCK_ASK_RESPONSE_PAYLOAD))
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(200, json=MOCK_DELETE_SUCCESS_PAYLOAD))

    result = await client.ask(str(TEST_PDF_PATH), question, delete_after_processing=True)

    assert upload_route.called
    assert signed_url_route.called
    assert ask_route.called
    assert delete_route.called

    assert isinstance(result, ChatCompletionResult)
    assert result.choices[0].message.content == "The title is Mock Title."

@pytest.mark.asyncio
@respx.mock
async def test_delete_file_success(client: PiscoMistralOcrClient):
    """Probar el método delete_file directamente con éxito."""
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(200, json=MOCK_DELETE_SUCCESS_PAYLOAD))

    deleted = await client.delete_file(TEST_FILE_ID)

    assert delete_route.called
    assert deleted is True

@pytest.mark.asyncio
@respx.mock
async def test_delete_file_not_found(client: PiscoMistralOcrClient):
    """Probar fallo de delete_file si el archivo no existe en Mistral."""
    delete_route = respx.delete(f"{MISTRAL_BASE_URL}/files/{TEST_FILE_ID}").mock(return_value=Response(404, json=MOCK_API_ERROR_PAYLOAD))

    with pytest.raises(ApiError) as exc_info:
        await client.delete_file(TEST_FILE_ID)

    assert delete_route.called
    assert exc_info.value.status_code == 404
    assert MOCK_API_ERROR_PAYLOAD["message"] in str(exc_info.value)

@pytest.mark.asyncio
@respx.mock
async def test_api_error_ocr(client: PiscoMistralOcrClient):
    """Probar que se maneja correctamente un error de API en OCR."""
    test_url = "https://example.com/document.pdf"
    error_payload = {"message": "Processing failed"}
    ocr_route = respx.post(f"{MISTRAL_BASE_URL}/ocr").mock(return_value=Response(500, json=error_payload))

    with pytest.raises(ApiError) as exc_info:
        await client.ocr(test_url)

    assert ocr_route.called
    assert exc_info.value.status_code == 500
    assert error_payload["message"] in str(exc_info.value)

@pytest.mark.asyncio
async def test_file_not_found_error(client: PiscoMistralOcrClient):
    """Probar que se lanza ValueError si el archivo local no existe.""" # Actualizado docstring
    non_existent_file = f"/no/existe/aqui_{uuid.uuid4()}.pdf"
    assert not os.path.exists(non_existent_file)

    # CORRECCIÓN: Esperar ValueError en lugar de FileError
    with pytest.raises(ValueError) as exc_info:
        await client.ocr(non_existent_file)

    # CORRECCIÓN: Verificar el mensaje específico de ValueError
    assert f"Source '{non_existent_file}' is not recognized" in str(exc_info.value)
    print(f"\nError capturado correctamente: {exc_info.value}") # Añadir print para confirmación

@pytest.mark.asyncio
async def test_invalid_source_error(client: PiscoMistralOcrClient):
    """Probar que se lanza ValueError si el source no es URL ni archivo."""
    invalid_source = "esto no es ni url ni archivo existente"
    assert not os.path.exists(invalid_source)
    assert not invalid_source.startswith(("http://", "https://"))

    with pytest.raises(ValueError) as exc_info:
        await client.ocr(invalid_source)

    assert f"Source '{invalid_source}' is not recognized" in str(exc_info.value)