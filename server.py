import socket
import json
import PyPDF2
import threading
import sys
import io
from time import sleep
import google.generativeai as genai

class FlashcardServer:
    def __init__(self, host='localhost', start_port=5000):
        self.host = host
        self.port = start_port
        self.server_socket = None
        self.initialize_socket()
        
        # Initialize Gemini API (replace with your API key)
        genai.configure(api_key='AIzaSyDXaC8CCMFTpX-nxlm-cf6556Hn6eQrXI4')
        # Configure the model
        self.model = genai.GenerativeModel('gemini-pro')

    def initialize_socket(self):
        """Initialize the server socket with port finding capability"""
        max_attempts = 10
        current_port = self.port

        for attempt in range(max_attempts):
            try:
                self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.server_socket.bind((self.host, current_port))
                self.port = current_port
                self.server_socket.listen(5)
                print(f"Server successfully bound to port {self.port}")
                return
            except OSError:
                print(f"Port {current_port} is in use, trying next port...")
                if self.server_socket:
                    self.server_socket.close()
                current_port += 1

        raise Exception(f"Could not find an available port after {max_attempts} attempts")

    def cleanup(self):
        """Cleanup server resources"""
        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None
            print("Server socket closed")

    def extract_text_from_pdf(self, pdf_bytes):
        try:
            pdf_file = io.BytesIO(pdf_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_file)
            text = " ".join([page.extract_text() for page in pdf_reader.pages])
            return text
        except Exception as e:
            raise Exception(f"Error reading PDF file: {str(e)}")

    def divide_text(self, text, section_size=1000):
        sections = []
        start = 0
        end = section_size
        while start < len(text):
            section = text[start:end]
            sections.append(section)
            start = end
            end += section_size
        return sections

    def generate_flashcards_with_ai(self, text):
        try:
            divided_sections = self.divide_text(text)
            generated_flashcards = []

            for section in divided_sections[:1]:  # Limiting to first section for demo
                prompt = f"""Create flashcards from the following text. 
                Return them in JSON format as an array of objects with 'question' and 'answer' fields.
                For example:
                [
                    {{"question": "What is...", "answer": "It is..."}},
                    {{"question": "How does...", "answer": "It does..."}}
                ]
                
                Text to process: {section}"""

                # Generate response using Gemini
                response = self.model.generate_content(prompt)
                
                try:
                    # Try to parse the response directly
                    content = response.text
                    # Find the JSON part in the response
                    start_idx = content.find('[')
                    end_idx = content.rfind(']') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        cards = json.loads(json_str)
                        generated_flashcards.extend(cards)
                    else:
                        print("Could not find JSON format in response")
                        
                except json.JSONDecodeError as e:
                    print(f"Error parsing JSON: {e}")
                    print(f"Response content: {content}")
                except Exception as e:
                    print(f"Error processing response: {e}")

            return generated_flashcards

        except Exception as e:
            raise Exception(f"Error generating flashcards: {str(e)}")

    def handle_client(self, client_socket, addr):
        print(f"Connected to client: {addr}")
        
        try:
            # Receive file type
            file_type = client_socket.recv(10).decode().strip()
            
            if file_type != 'pdf':
                raise ValueError("Unsupported file type. Only PDF files are supported.")
            
            # Receive file size
            file_size = int(client_socket.recv(10).decode().strip())
            
            # Receive file content
            file_content = b""
            while len(file_content) < file_size:
                chunk = client_socket.recv(min(4096, file_size - len(file_content)))
                if not chunk:
                    break
                file_content += chunk

            # Extract text from PDF
            text = self.extract_text_from_pdf(file_content)

            # Generate flashcards using AI
            flashcards = self.generate_flashcards_with_ai(text)
            
            # Send flashcards back to client
            response = json.dumps(flashcards).encode()
            client_socket.send(str(len(response)).zfill(10).encode())
            client_socket.send(response)

        except Exception as e:
            error_msg = json.dumps({"error": str(e)}).encode()
            client_socket.send(str(len(error_msg)).zfill(10).encode())
            client_socket.send(error_msg)
        
        finally:
            client_socket.close()

    def start(self):
        print(f"Server listening on {self.host}:{self.port}")
        try:
            while True:
                client_socket, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket, addr))
                client_thread.start()
        except KeyboardInterrupt:
            print("\nShutting down server...")
        finally:
            self.cleanup()

if __name__ == "__main__":
    try:
        start_port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
        server = FlashcardServer(start_port=start_port)
        server.start()
    except Exception as e:
        print(f"Server error: {str(e)}")
        sys.exit(1)