import unittest
import os
import socket
import json
from unittest.mock import Mock, patch
from client import FlashcardClient

class TestFlashcardClient(unittest.TestCase):
    def setUp(self):
        self.client = FlashcardClient(host='localhost', port=5000)
        self.test_pdf_path = "test_document.pdf"
        
        # Create a dummy PDF file for testing
        with open(self.test_pdf_path, 'wb') as f:
            f.write(b"%PDF-1.4\ntest content")
    
    def tearDown(self):
        # Clean up test file
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)

    def test_test_connection_success(self):
        with patch('socket.socket') as mock_socket:
            # Configure mock to simulate successful connection
            mock_socket.return_value.__enter__.return_value.connect.return_value = None
            
            # Test the connection
            result = self.client.test_connection()
            
            # Verify the result
            self.assertTrue(result)
            mock_socket.return_value.__enter__.return_value.connect.assert_called_with(('localhost', 5000))

    def test_test_connection_failure(self):
        with patch('socket.socket') as mock_socket:
            # Configure mock to simulate connection failure
            mock_socket.return_value.__enter__.return_value.connect.side_effect = ConnectionRefusedError
            
            # Test the connection
            result = self.client.test_connection()
            
            # Verify the result
            self.assertFalse(result)

    def test_send_file_success(self):
        with patch('socket.socket') as mock_socket:
            # Configure mock socket for successful file sending
            mock_socket_instance = Mock()
            mock_socket.return_value.__enter__.return_value = mock_socket_instance
            
            # Mock successful response from server
            expected_response = [{"question": "Test Q?", "answer": "Test A"}]
            mock_socket_instance.recv.side_effect = [
                "10".zfill(10).encode(),  # Response size
                json.dumps(expected_response).encode()  # Response content
            ]
            
            # Send test file
            response = self.client.send_file(self.test_pdf_path)
            
            # Verify the response
            self.assertEqual(response, expected_response)
            
            # Verify correct data was sent
            calls = mock_socket_instance.send.call_args_list
            self.assertEqual(len(calls), 3)  # Should send file type, size, and content
            
            # Verify file type was sent
            self.assertEqual(calls[0][0][0], b'pdf       ')  # File type padded to 10 chars

    def test_send_file_invalid_type(self):
        # Create a test file with invalid extension
        invalid_file = "test.txt"
        with open(invalid_file, 'w') as f:
            f.write("test content")
        
        try:
            # Test sending invalid file type
            response = self.client.send_file(invalid_file)
            
            # Verify error response
            self.assertIn("error", response)
            self.assertIn("Unsupported file type", response["error"])
        
        finally:
            # Clean up test file
            if os.path.exists(invalid_file):
                os.remove(invalid_file)

    def test_send_file_connection_error(self):
        with patch('socket.socket') as mock_socket:
            # Configure mock to simulate connection error
            mock_socket.return_value.__enter__.return_value.connect.side_effect = ConnectionRefusedError
            
            # Test sending file
            response = self.client.send_file(self.test_pdf_path)
            
            # Verify error response
            self.assertIn("error", response)
            self.assertIn("Could not connect to server", response["error"])

if __name__ == '__main__':
    unittest.main()