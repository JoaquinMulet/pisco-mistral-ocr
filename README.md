# PiscoMistralOcr

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
PiscoMistralOcr is a user-friendly, asynchronous Python client library for interacting with the [Mistral AI OCR and Document Understanding APIs](https://docs.mistral.ai/capabilities/document_understanding/).

It simplifies common tasks like extracting text from PDFs/images (via URL or local file) and asking questions about document content, transparently handling file uploads, API interactions, and **optional automatic file deletion**.

## Features

* Fully asynchronous (`async`/`await`).
* Simple interface: `ocr(source)` and `ask(source, question)`.
* Automatic detection of URL vs. local file path for sources.
* Handles file uploads and signed URL generation automatically.
* **Option to automatically delete files from Mistral servers after processing.**
* Typed responses using Pydantic models for an improved developer experience.
* Robust error handling with custom exceptions.
* Built on the excellent `httpx` library.

## Installation

**Note:** This library is not currently published on PyPI. You must install it directly from the GitHub repository.

Use `pip` to install the latest version from the main branch:

```bash
pip install git+[https://github.com/JoaquinMulet/pisco-mistral-ocr.git](https://github.com/JoaquinMulet/pisco-mistral-ocr.git)
```

(Ensure you have `git` installed on your system.)

## Prerequisites

  * Python 3.8+
  * A Mistral AI API Key (see "Detailed API Key Setup" below).
  * `git` installed on your system (for GitHub installation).

-----

## Cookbook: Ultra-Simple Usage

These examples showcase the core library usage with minimal code. They assume your `MISTRAL_API_KEY` is configured and that file paths/URLs are valid.

**Important:** All code using `await` must be run inside an `async` function using `asyncio.run()`.

```python
import asyncio
from pisco_mistral_ocr import PiscoMistralOcrClient

# --- 1. OCR a local file (with auto-delete) ---
async def ocr_local_file():
    file_path = "path/to/your/document.pdf"
    async with PiscoMistralOcrClient() as client:
        ocr_result = await client.ocr(file_path, delete_after_processing=True)
        extracted_text = ocr_result.pages[0].markdown


# --- 2. Ask a question about a local file (with auto-delete) ---
async def ask_local_file():
    file_path = "path/to/your/image.png" 
    question = "What is this about?"
    async with PiscoMistralOcrClient() as client:
        ask_result = await client.ask(
            file_path,
            question,
            delete_after_processing=True
        )
        answer = ask_result.choices[0].message.content

# --- 3. OCR from a URL ---
async def ocr_url():
    doc_url = "[https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf](https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf)"
    async with PiscoMistralOcrClient() as client:
        ocr_result = await client.ocr(doc_url)
        extracted_text_url = ocr_result.pages[0].markdown

# --- 4. Ask a question about a URL ---
async def ask_url():
    doc_url = "[https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf](https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf)"
    question = "What is the summary?"
    async with PiscoMistralOcrClient() as client:
        ask_result = await client.ask(doc_url, question)
        answer_url = ask_result.choices[0].message.content

# --- How to run (basic example) ---
async def main():
    await ocr_local_file()
    await ask_local_file()
    await ocr_url()
    await ask_url()

if __name__ == "__main__":
    # --- REQUIRED SETUP BEFORE RUNNING! ---
    # 1. Set your MISTRAL_API_KEY environment variable or use .env.
    # 2. Modify the file paths/URLs inside the example functions above.
    # ---------------------------------------
    try:
        asyncio.run(main())
    except ImportError:
         print("Error: Install the library first: pip install git+[https://github.com/JoaquinMulet/pisco-mistral-ocr.git](https://github.com/JoaquinMulet/pisco-mistral-ocr.git)")
    except Exception as e:
         print(f"\nError during execution: {e}")
         print("Verify your API key, file paths/URLs, and internet connection.")


# NOTE ON PRODUCTION CODE:
# These examples are extremely minimal for clarity. Real-world applications MUST:
# 1. Check if results were actually returned (e.g., verify that `result.pages`
#    or `result.choices` are not empty) before accessing their elements.
# 2. Implement robust error handling using try/except blocks (see "Error Handling").
```

-----

## Automatic File Deletion (Best Practice)

When processing **local files** (`.pdf`, `.png`, etc.) with `ocr()` or `ask()`, the library uploads them to Mistral AI servers. To **automatically delete** these files from their servers immediately after processing, simply add `delete_after_processing=True` to the call:

```python
# Example inside an async function:
async with PiscoMistralOcrClient() as client:
    # OCR and delete
    await client.ocr("path/to/local/file.pdf", delete_after_processing=True)
    print("File processed with OCR and deleted from Mistral server.")

    # Ask and delete
    await client.ask("path/to/local/image.png", "Question?", delete_after_processing=True)
    print("File processed with Ask and deleted from Mistral server.")

```

**Why use `delete_after_processing=True`?**

  * **Data Privacy:** Avoid leaving potentially sensitive documents on external servers longer than necessary.
  * **Resource Management:** Keep your file storage on the Mistral platform tidy.
  * **Potential Costs:** May prevent future storage costs if applicable.

It is generally **recommended to use `delete_after_processing=True` when processing local files**, unless you have a specific reason to keep the file on Mistral's servers. This option does *not* apply when providing a URL, as the library does not upload the file in that case.

-----

## Detailed API Key Setup (Prerequisite)

The library requires your Mistral AI API key to function. It looks for the key in the `MISTRAL_API_KEY` environment variable. You have several options for setting it up:

1.  **Environment Variable (Recommended):**

      * Linux/macOS (terminal):
        ```bash
        export MISTRAL_API_KEY="YOUR_MISTRAL_API_KEY"
        ```
      * Windows (cmd):
        ```cmd
        set MISTRAL_API_KEY=YOUR_MISTRAL_API_KEY
        ```
      * Windows (PowerShell):
        ```powershell
        $env:MISTRAL_API_KEY="YOUR_MISTRAL_API_KEY"
        ```
      * *Note: These commands set it only for the current terminal session. To make it permanent, consult your OS documentation on setting environment variables.*

2.  **`.env` File:**

      * Create a file named `.env` in your project's root directory.
      * Add the line: `MISTRAL_API_KEY=YOUR_MISTRAL_API_KEY`
      * Install the `python-dotenv` library: `pip install python-dotenv`
      * Load the file at the beginning of your Python script:
        ```python
        from dotenv import load_dotenv
        load_dotenv()
        ```

3.  **Directly in Code (Less Secure):**

      * You can pass the key when initializing the client. **Avoid this if you share your code.**
        ```python
        client = PiscoMistralOcrClient(api_key="YOUR_MISTRAL_API_KEY")
        # async with client: ...
        ```

Obtain your API key from the [Mistral AI platform](https://console.mistral.ai/).

-----

## Error Handling

The library uses custom exceptions inheriting from `PiscoMistralOcrError`:

  * `ConfigurationError`: For issues like a missing API key.
  * `FileError`: For problems reading local files (e.g., not found).
  * `NetworkError`: For network issues during API calls (timeouts, connection errors).
  * `ApiError`: When the Mistral API returns an error (e.g., 4xx, 5xx status codes). Contains `status_code` and `error_details` attributes.

For robust code, wrap API calls in `try...except` blocks:

```python
import asyncio
from pisco_mistral_ocr import PiscoMistralOcrClient, PiscoMistralOcrError

async def ocr_with_error_handling(file_path):
    try:
        async with PiscoMistralOcrClient() as client:
            result = await client.ocr(file_path, delete_after_processing=True)
            if result.pages:
                print("OCR successful:", result.pages[0].markdown[:100] + "...")
            else:
                print("OCR completed but returned no pages.")
    except FileNotFoundError:
        print(f"Error: File not found at {file_path}")
    except PiscoMistralOcrError as e:
        # Handle specific library errors
        print(f"Library Error: {e}")
        if hasattr(e, 'status_code'): print(f"HTTP Status Code: {e.status_code}")
        if hasattr(e, 'error_details'): print(f"API Error Details: {e.error_details}")
    except Exception as e:
        # Handle any other unexpected errors
        print(f"An unexpected error occurred: {e}")

# Example of how to call it:
# asyncio.run(ocr_with_error_handling("path/to/nonexistent/file.pdf"))
# asyncio.run(ocr_with_error_handling("path/to/your/real/file.pdf")) # Test with a valid path
```

## Contributing

Contributions are welcome\! Please open an issue or submit a pull request on the [GitHub repository](https://www.google.com/search?q=https://github.com/JoaquinMulet/pisco-mistral-ocr).

## License

This project is licensed under the MIT License - see the [LICENSE](https://www.google.com/search?q=LICENSE) file for details.
