# PDF Flashcard Generator

## Overview

The PDF Flashcard Generator is a client-server application designed to generate flashcards from PDF files using AI. The server processes uploaded PDFs to extract text and uses a generative AI model to create flashcards. The client provides a graphical interface for users to upload PDFs, view generated flashcards, and save them locally.

## Requirements

- **Python Version:** 3.7+
- **Libraries:**
  - `socket`
  - `json`
  - `PyPDF2`
  - `threading`
  - `sys`
  - `io`
  - `google.generativeai`
  - `tkinter`
  - `nltk` (optional, for further processing)

## Running the Server

1. Navigate to the directory containing `server.py`.
2. Run the server:

   ```bash
   python server.py [optional_start_port]
   ```

   - Replace `[optional_start_port]` with a custom starting port (default is 5000).

## Running the Client

1. Navigate to the directory containing `client.py`.
2. Run the client:

   ```bash
   python client.py
   ```

   - The client GUI will open. Configure the server port in the GUI, then upload a PDF file to generate flashcards.

## Configuration Settings

### Environment Variables
- **Google Generative AI API Key:** The server requires a valid API key to interact with the AI model. Replace the placeholder in `server.py`:

  ```python
  genai.configure(api_key='YOUR_API_KEY')
  ```

### Default Ports
- The server starts on port 5000 by default. If unavailable, it increments to the next available port.
- The client connects to port 5000 by default but can be adjusted in the GUI.

## Testing the Application

### Testing Setup
There are three testing conducted `clienttest.py` for client, `servertest.py`, and `fileoperationtest.py`
Move the three files within the `testing` folder to the same directory as `client.py` and `server.py`


### Running Unit Tests
1. Run the scripts `clienttest.py` `servertest.py` `fileoperationtest.py`
2. Verify all tests pass.

### Manual Testing
- Start the server and client applications.
- Test file upload, flashcard generation, navigation, and saving functionality in the client GUI.

## Troubleshooting

- **Error:** "Connection Refused"
  - Ensure the server is running and reachable.

- **Error:** "File Not Found"
  - Verify the file path on the client side.

- **Error:** "API Key Invalid"
  - Confirm the API key is correct and active.