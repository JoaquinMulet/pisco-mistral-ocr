# PiscoMistralOcr

[![PyPI version](https://badge.fury.io/py/pisco-mistral-ocr.svg)](https://badge.fury.io/py/pisco-mistral-ocr) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

PiscoMistralOcr es una biblioteca cliente Python asíncrona y fácil de usar para interactuar con las [APIs de OCR y Comprensión de Documentos de Mistral AI](https://docs.mistral.ai/capabilities/document_understanding/).

Simplifica tareas comunes como extraer texto de PDFs/imágenes (a través de URL o archivo local) y hacer preguntas sobre el contenido de documentos, manejando cargas de archivos, interacciones con la API y **eliminación opcional de archivos** de manera transparente.

## Características

* Completamente asíncrono (`async`/`await`).
* Interfaz simple: `ocr(source)` y `ask(source, question)`.
* Detección automática de URL vs. ruta de archivo local para las fuentes.
* Maneja cargas de archivos y generación de URL firmadas automáticamente.
* **Opción para eliminar automáticamente archivos del servidor Mistral después del procesamiento.**
* Respuestas tipadas usando modelos Pydantic para una mejor experiencia de desarrollo.
* Manejo robusto de errores con excepciones personalizadas.
* Construido sobre la excelente biblioteca `httpx`.
* Uso de `logging` para mejor visibilidad de operaciones.

## Instalación

```bash
pip install pisco-mistral-ocr
````

## Requisitos Previos

  * Python 3.8+
  * Una clave de API de Mistral AI. Puedes obtener una en la [plataforma Mistral AI](https://console.mistral.ai/).
  * **Configuración de la API Key:** La biblioteca busca la clave en la variable de entorno `MISTRAL_API_KEY`. Puedes:
      * Establecer la variable de entorno en tu sistema:
          * Linux/macOS: `export MISTRAL_API_KEY="TU_CLAVE_API_MISTRAL"`
          * Windows (cmd): `set MISTRAL_API_KEY=TU_CLAVE_API_MISTRAL`
          * Windows (PowerShell): `$env:MISTRAL_API_KEY="TU_CLAVE_API_MISTRAL"`
      * Crear un archivo `.env` en el directorio de tu proyecto o uno superior con el contenido `MISTRAL_API_KEY=TU_CLAVE_API_MISTRAL` e instalar `python-dotenv` (`pip install python-dotenv`) para que tu script lo cargue (ver ejemplo abajo).
      * Pasar la clave directamente al inicializar el cliente: `client = PiscoMistralOcrClient(api_key="TU_CLAVE_API_MISTRAL")`.

## Cookbook: Uso Simple

Así es como realizar tareas comunes con `PiscoMistralOcr`. Todas las llamadas a la API son asíncronas y deben ser esperadas con `await`.

```python
#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ejemplo de uso de la librería PiscoMistralOcr actualizado.
"""
import asyncio
import os
import logging
import pathlib
from dotenv import load_dotenv # Necesario si usas .env
from pisco_mistral_ocr import PiscoMistralOcrClient, PiscoMistralOcrError

# --- Cargar .env (si existe) ---
load_dotenv()

# --- Configuración del Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PiscoMistralOcrExample")

# --- Crear un archivo PDF ficticio para pruebas locales ---
PDF_CONTENT = b"%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\n3 0 obj<</Type/Page/MediaBox[0 0 612 792]/Contents 4 0 R/Parent 2 0 R>>endobj\n4 0 obj<</Length 35>>stream\nBT /F1 24 Tf 100 700 Td (Hello Pisco!) Tj ET\nendstream\nendobj\nxref\n0 5\n0000000000 65535 f \n0000000010 00000 n \n0000000059 00000 n \n0000000118 00000 n \n0000000197 00000 n \ntrailer<</Size 5/Root 1 0 R>>\nstartxref\n269\n%%EOF"
# Usar pathlib para manejar la ruta
LOCAL_PDF_PATH = pathlib.Path("hello_pisco_readme_example.pdf")

async def main():
    """Función principal que demuestra el uso de PiscoMistralOcrClient."""
    # Crear archivo de prueba
    try:
        LOCAL_PDF_PATH.write_bytes(PDF_CONTENT)
        logger.info("Archivo PDF de prueba creado: %s", LOCAL_PDF_PATH)
    except OSError as e:
        logger.error("No se pudo crear el archivo PDF de prueba: %s", e)
        return

    logger.info("=== Ejemplo de uso de PiscoMistralOcr ===")
    api_key_check = os.getenv("MISTRAL_API_KEY")
    if not api_key_check:
         logger.critical("MISTRAL_API_KEY no encontrada. Saliendo.")
         # Limpiar archivo antes de salir si se creó
         if LOCAL_PDF_PATH.exists(): LOCAL_PDF_PATH.unlink()
         return

    try:
        # Inicializar el cliente usando 'async with' para gestión automática
        async with PiscoMistralOcrClient() as client:
            try:
                # === 1. OCR desde Archivo Local (con Auto-Eliminación) ===
                logger.info("\n--- 1. OCR desde Archivo Local (con Auto-Eliminación) ---")
                ocr_result_file = await client.ocr(
                    str(LOCAL_PDF_PATH), # Convertir Path a string
                    delete_after_processing=True # <-- ¡Activado!
                )
                logger.info("OCR de archivo local completado (archivo eliminado del servidor).")
                if ocr_result_file.pages:
                    print("\nContenido Markdown OCR (Archivo Local, Página 0):")
                    print("-" * 30)
                    print(ocr_result_file.pages[0].markdown)
                    print("-" * 30)
                else:
                    logger.warning("El resultado OCR local no contiene páginas.")

                # === 2. Preguntar sobre Archivo Local (con Auto-Eliminación) ===
                logger.info("\n--- 2. Preguntar sobre Archivo Local (con Auto-Eliminación) ---")
                question_local = "¿Qué texto está presente en este documento?"
                logger.info("Pregunta: %s", question_local)
                ask_result_file = await client.ask(
                    str(LOCAL_PDF_PATH),
                    question_local,
                    delete_after_processing=True # <-- ¡Activado!
                )
                logger.info("Pregunta sobre archivo local completada (archivo eliminado del servidor).")
                if ask_result_file.choices:
                    answer_local = ask_result_file.choices[0].message.content
                    print("\nRespuesta (Archivo Local):")
                    print("-" * 30)
                    print(answer_local)
                    print("-" * 30)
                else:
                    logger.warning("La respuesta Ask local no contiene choices.")

                # === 3. OCR desde URL Específica ===
                logger.info("\n--- 3. OCR desde URL Específica ---")
                example_url = "[https://www.buds.com.ua/images/Lorem_ipsum.pdf](https://www.buds.com.ua/images/Lorem_ipsum.pdf)"
                logger.info("Procesando URL: %s", example_url)
                ocr_result_url = await client.ocr(example_url)
                # delete_after_processing no aplica a URLs
                logger.info("OCR de URL completado.")
                if ocr_result_url.pages:
                    print("\nContenido Markdown OCR (URL, Página 0, Primeros 500 chars):")
                    print("-" * 30)
                    print(ocr_result_url.pages[0].markdown[:500] + "...")
                    print("-" * 30)
                else:
                    logger.warning("El resultado OCR de URL no contiene páginas.")

                # === 4. Preguntar sobre URL Específica ===
                logger.info("\n--- 4. Preguntar sobre URL Específica ---")
                question_url = "¿De qué trata este documento?"
                logger.info("Procesando URL: %s", example_url)
                logger.info("Pregunta: %s", question_url)
                ask_result_url = await client.ask(example_url, question_url)
                # delete_after_processing no aplica a URLs
                logger.info("Pregunta sobre URL completada.")
                if ask_result_url.choices:
                    answer_url = ask_result_url.choices[0].message.content
                    print("\nRespuesta (URL):")
                    print("-" * 30)
                    print(answer_url)
                    print("-" * 30)
                else:
                    logger.warning("La respuesta Ask de URL no contiene choices.")

            except PiscoMistralOcrError as e:
                logger.error("Ocurrió un error durante la operación con la API: %s", e, exc_info=True)
                if hasattr(e, 'status_code'): logger.error("Código de estado HTTP: %s", e.status_code)
                if hasattr(e, 'error_details'): logger.error("Detalles del error API: %s", e.error_details)
            except Exception as e:
                logger.critical("Ocurrió un error inesperado no controlado: %s", e, exc_info=True)

    except Exception as e:
        logger.critical("Error al inicializar PiscoMistralOcrClient: %s", e, exc_info=True)
    finally:
        # Limpiar el archivo ficticio local SIEMPRE
        if LOCAL_PDF_PATH.exists():
            try:
                LOCAL_PDF_PATH.unlink() # Usar unlink() para Path
                logger.info("Archivo de prueba local %s eliminado.", LOCAL_PDF_PATH)
            except OSError as e:
                logger.error("No se pudo eliminar el archivo de prueba local %s: %s", LOCAL_PDF_PATH, e)

if __name__ == "__main__":
    asyncio.run(main())

```

## Eliminación Automática de Archivos (Buena Práctica)

Cuando procesas archivos locales usando los métodos `.ocr(ruta_archivo, ...)` o `.ask(ruta_archivo, ...)`, la biblioteca sube primero el archivo a los servidores de Mistral. Estos archivos permanecen en sus servidores a menos que se eliminen explícitamente.

Para **eliminar automáticamente** el archivo subido de los servidores de Mistral inmediatamente después de que la operación de OCR o Ask se complete (o falle después de la subida), utiliza el flag `delete_after_processing=True`:

```python
import asyncio
from pisco_mistral_ocr import PiscoMistralOcrClient

async def process_and_delete(file_path):
    async with PiscoMistralOcrClient() as client:
        # Procesar el archivo local y eliminarlo de Mistral después
        result = await client.ocr(file_path, delete_after_processing=True)
        print("OCR procesado. El archivo debería estar eliminado de Mistral.")
        # ... usar resultado ...

        # Similar para ask:
        answer = await client.ask(file_path, "Pregunta?", delete_after_processing=True)
        print("Ask procesado. El archivo debería estar eliminado de Mistral.")
        # ... usar respuesta ...

# asyncio.run(process_and_delete("ruta/a/tu/documento.pdf"))
```

**¿Por qué usar `delete_after_processing=True`?**

  * **Privacidad de Datos:** Evita dejar documentos potencialmente sensibles en los servidores de Mistral más tiempo del necesario.
  * **Gestión de Recursos:** Mantiene limpio tu almacenamiento de archivos en la plataforma Mistral.
  * **Costos:** Podría prevenir posibles costos futuros de almacenamiento si fueran aplicables.

Generalmente se recomienda activar este flag (`True`) al procesar archivos locales, a menos que tengas una razón específica para mantener el archivo en los servidores de Mistral.

La biblioteca también proporciona un método manual `client.delete_file(file_id)`, pero usar el flag es típicamente más simple para el flujo de trabajo estándar.

## Manejo de errores

La biblioteca utiliza excepciones personalizadas que heredan de `PiscoMistralOcrError`:

  * `ConfigurationError`: Para problemas como una clave de API faltante.
  * `FileError`: Para problemas al leer archivos locales.
  * `NetworkError`: Para problemas de red durante las llamadas a la API (tiempos de espera, errores de conexión).
  * `ApiError`: Cuando la API de Mistral devuelve un error (por ejemplo, códigos de estado 4xx, 5xx). Contiene atributos `status_code` y `error_details`.

Envuelve tus llamadas en un bloque `try...except PiscoMistralOcrError` para manejar posibles problemas de manera elegante.

## Contribuir

¡Las contribuciones son bienvenidas\! Por favor, abre un issue o envía un pull request en el [repositorio de GitHub](https://github.com/tu_usuario/pisco-mistral-ocr). \#\# Licencia

Este proyecto está licenciado bajo la Licencia MIT - consulta el archivo [LICENSE](https://www.google.com/search?q=LICENSE) para más detalles.
