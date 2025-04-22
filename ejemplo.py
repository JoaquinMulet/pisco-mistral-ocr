#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Ejemplo de uso de la librería PiscoMistralOcr.

Este script demuestra cómo:
1. Realizar OCR en un archivo PDF local y eliminarlo automáticamente del servidor después.
2. Realizar una pregunta sobre un archivo PDF local y eliminarlo automáticamente después.
3. Realizar OCR en un PDF desde una URL especificada.
4. Realizar una pregunta sobre un PDF desde la URL especificada.

Requiere:
- Un archivo .env en el mismo directorio (o un directorio superior)
  que contenga la línea: MISTRAL_API_KEY=TU_CLAVE_SECRETA
- Que el archivo 'test.pdf' exista en 'pisco-mistral-ocr/tests/test.pdf' relativo
  a la ubicación desde donde se ejecuta el script.
- La librería 'python-dotenv' instalada (`pip install python-dotenv`).
"""
import asyncio
import os
import logging
import pathlib
from dotenv import load_dotenv # <--- IMPORTAR load_dotenv
from pisco_mistral_ocr import PiscoMistralOcrClient, PiscoMistralOcrError

# --- Cargar variables de entorno desde .env ---
# load_dotenv() buscará un archivo .env en el directorio actual o superiores
# y cargará las variables definidas en él en el entorno de ejecución.
load_dotenv() # <--- LLAMAR A load_dotenv() TEMPRANO

# --- Configuración del Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("PiscoMistralOcrExample")

# --- Definir Rutas y URLs Específicas ---
try:
    BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
    LOCAL_PDF_PATH = BASE_DIR / "pisco-mistral-ocr" / "tests" / "test.pdf"
except NameError:
     LOCAL_PDF_PATH = pathlib.Path("pisco-mistral-ocr") / "tests" / "test.pdf"

EXAMPLE_URL = "https://www.buds.com.ua/images/Lorem_ipsum.pdf"

async def main():
    """Función principal que demuestra el uso de PiscoMistralOcrClient."""

    # --- Verificar que el archivo local existe ---
    if not LOCAL_PDF_PATH.exists():
        logger.error(
            "El archivo PDF local especificado no se encontró en: %s",
            LOCAL_PDF_PATH.resolve()
        )
        logger.error("Asegúrate de que la ruta es correcta y el archivo existe.")
        return

    logger.info("=== Ejemplo de uso de PiscoMistralOcr con archivos específicos ===")
    logger.info("Usando archivo local: %s", LOCAL_PDF_PATH.resolve())
    logger.info("Usando URL: %s", EXAMPLE_URL)
    logger.info("Nota: La API key se leerá desde el archivo .env o la variable de entorno MISTRAL_API_KEY.")

    # --- Verificar API Key ANTES de inicializar el cliente ---
    # (Aunque el cliente también lo verifica, es bueno hacerlo antes)
    api_key_check = os.getenv("MISTRAL_API_KEY")
    if not api_key_check:
         logger.critical("MISTRAL_API_KEY no encontrada en el entorno o archivo .env. Saliendo.")
         return

    # Inicializar el cliente (ahora os.getenv leerá la clave cargada por load_dotenv)
    try:
        async with PiscoMistralOcrClient() as client:
            # El resto del bloque try/except/finally permanece igual...
            try:
                # === 1. OCR desde Archivo Local Específico (con Auto-Eliminación) ===
                logger.info("\n--- 1. OCR desde Archivo Local (con Auto-Eliminación) ---")
                ocr_result_file = await client.ocr(
                    str(LOCAL_PDF_PATH),
                    delete_after_processing=True
                )
                logger.info("OCR de archivo local completado.")
                if ocr_result_file.pages:
                    print("\nContenido Markdown OCR (Archivo Local, Página 0, Primeros 500 chars):")
                    print("-" * 30)
                    print(ocr_result_file.pages[0].markdown[:500] + "...")
                    print("-" * 30)
                else:
                    logger.warning("El resultado del OCR del archivo local no contiene páginas.")
                logger.info("El archivo subido para OCR local debería haber sido eliminado del servidor Mistral.")

                # === 2. Preguntar sobre Archivo Local Específico (con Auto-Eliminación) ===
                logger.info("\n--- 2. Preguntar sobre Archivo Local (con Auto-Eliminación) ---")
                question_local = "¿Qué texto está presente en este documento?"
                logger.info("Pregunta: %s", question_local)
                ask_result_file = await client.ask(
                    str(LOCAL_PDF_PATH),
                    question_local,
                    delete_after_processing=True
                )
                logger.info("Pregunta sobre archivo local completada.")
                if ask_result_file.choices:
                    answer_local = ask_result_file.choices[0].message.content
                    print("\nRespuesta (Archivo Local):")
                    print("-" * 30)
                    print(answer_local)
                    print("-" * 30)
                else:
                    logger.warning("La respuesta de 'ask' sobre archivo local no contiene choices.")
                logger.info("El archivo subido para Ask local debería haber sido eliminado del servidor Mistral.")

                # === 3. OCR desde URL Específica ===
                logger.info("\n--- 3. OCR desde URL Específica ---")
                logger.info("Procesando URL: %s", EXAMPLE_URL)
                ocr_result_url = await client.ocr(EXAMPLE_URL)
                logger.info("OCR de URL completado.")
                if ocr_result_url.pages:
                    print("\nContenido Markdown OCR (URL, Página 0, Primeros 500 caracteres):")
                    print("-" * 30)
                    print(ocr_result_url.pages[0].markdown[:500] + "...")
                    print("-" * 30)
                else:
                    logger.warning("El resultado del OCR de URL no contiene páginas.")

                # === 4. Preguntar sobre URL Específica ===
                logger.info("\n--- 4. Preguntar sobre URL Específica ---")
                question_url = "¿De qué trata este documento?"
                logger.info("Procesando URL: %s", EXAMPLE_URL)
                logger.info("Pregunta: %s", question_url)
                ask_result_url = await client.ask(EXAMPLE_URL, question_url)
                logger.info("Pregunta sobre URL completada.")
                if ask_result_url.choices:
                    answer_url = ask_result_url.choices[0].message.content
                    print("\nRespuesta (URL):")
                    print("-" * 30)
                    print(answer_url)
                    print("-" * 30)
                else:
                    logger.warning("La respuesta de 'ask' sobre URL no contiene choices.")

            except PiscoMistralOcrError as e:
                logger.error("Ocurrió un error durante la operación con la API: %s", e, exc_info=True)
                if hasattr(e, 'status_code'):
                    logger.error("Código de estado HTTP: %s", e.status_code)
                if hasattr(e, 'error_details'):
                    logger.error("Detalles del error API: %s", e.error_details)
            except FileNotFoundError:
                 logger.error("Error interno: El archivo %s no se encontró justo antes de usarlo.", LOCAL_PDF_PATH)
            except Exception as e:
                logger.critical("Ocurrió un error inesperado no controlado: %s", e, exc_info=True)

    except ImportError:
        logger.error("No se pudo importar PiscoMistralOcrClient. ¿Instalaste la librería?")
    except Exception as e: # Captura errores de inicialización del cliente si la key no se cargó
        logger.critical("Error al inicializar PiscoMistralOcrClient: %s", e, exc_info=True)

    # No hay 'finally' para borrar el archivo local, ya que usamos uno existente.

if __name__ == "__main__":
    # load_dotenv() ya se llamó arriba, ahora verificamos si funcionó
    if not os.getenv("MISTRAL_API_KEY"):
        logger.critical("MISTRAL_API_KEY no encontrada. Asegúrate de que existe un archivo .env válido o que la variable está configurada en el entorno.")
    else:
        if not LOCAL_PDF_PATH.exists():
             logger.error("El archivo PDF local especificado no se encontró en: %s", LOCAL_PDF_PATH.resolve())
        else:
             asyncio.run(main())