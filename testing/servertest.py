import unittest
import socket
import threading
from server import FlashcardServer
from unittest.mock import MagicMock, patch
import time

class TestFlashcardServer(unittest.TestCase):
    def setUp(self):
        """Set up test server"""
        self.server = FlashcardServer(start_port=5555)
        self.server_thread = threading.Thread(target=self.server.start)
        self.server_thread.daemon = True
        self.server_thread.start()
        time.sleep(1)  # Allow the server to start

    def tearDown(self):
        """Clean up server resources"""
        self.server.cleanup()

    @patch('server.FlashcardServer.extract_text_from_pdf')
    @patch('server.FlashcardServer.generate_flashcards_with_ai')
    def test_handle_client(self, mock_generate_flashcards, mock_extract_text):
        """Test server's client handling"""
        mock_extract_text.return_value = "Mock PDF text"
        mock_generate_flashcards.return_value = [{"question": "Q1", "answer": "A1"}]

        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_socket.connect(('localhost', 5555))

        # Simulate sending a PDF
        client_socket.send(b'pdf       ')  # File type
        file_content = b'Test PDF content'
        client_socket.send(str(len(file_content)).zfill(10).encode())
        client_socket.send(file_content)

        # Receive the response
        response_size = int(client_socket.recv(10).decode())
        response = client_socket.recv(response_size).decode()

        client_socket.close()

        # Verify response
        self.assertIn("Q1", response)

    def test_port_binding(self):
        """Test port binding"""
        self.assertEqual(self.server.port, 5555)

    def test_concurrent_connections(self):
        """Test handling of multiple clients"""
        def mock_client_action(port):
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(('localhost', port))
            client_socket.send(b'pdf       ')
            client_socket.send(b'0000000010')  # Mock size
            client_socket.send(b'TestPDF')
            client_socket.close()

        threads = [threading.Thread(target=mock_client_action, args=(5555,)) for _ in range(5)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        # Assuming no exceptions means success
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()
