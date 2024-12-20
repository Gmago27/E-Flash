# test_file_operations.py
import unittest
import os
import fpdf
from server import FlashcardServer
from client import FlashcardClient

class TestFileOperations(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.test_pdf_path = "test.pdf"
        self.create_test_pdf()
        self.server = FlashcardServer(start_port=5557)
        self.client = FlashcardClient(port=5557)

    def tearDown(self):
        """Clean up test files"""
        if os.path.exists(self.test_pdf_path):
            os.remove(self.test_pdf_path)
        self.server.cleanup()

    def create_test_pdf(self):
        """Create a test PDF file"""
        pdf = fpdf.FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Test content for flashcards", ln=1, align="C")
        pdf.output(self.test_pdf_path)

    def test_pdf_extraction(self):
        """Test PDF text extraction"""
        with open(self.test_pdf_path, 'rb') as file:
            content = file.read()
        extracted_text = self.server.extract_text_from_pdf(content)
        self.assertIsInstance(extracted_text, str)
        self.assertGreater(len(extracted_text), 0)

    def test_text_division(self):
        """Test text division into chunks"""
        test_text = "A" * 2000
        chunks = self.server.divide_text(test_text, section_size=1000)
        self.assertEqual(len(chunks), 2)
        self.assertEqual(len(chunks[0]), 1000)

    def test_large_file_handling(self):
        """Test handling of large PDF files"""
        # Create a larger PDF
        pdf = fpdf.FPDF()
        for _ in range(10):  # 10 pages
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt="Test content " * 100, ln=1, align="C")
        pdf.output("large_test.pdf")

        try:
            with open("large_test.pdf", 'rb') as file:
                content = file.read()
            extracted_text = self.server.extract_text_from_pdf(content)
            self.assertIsInstance(extracted_text, str)
            self.assertGreater(len(extracted_text), 1000)
        finally:
            if os.path.exists("large_test.pdf"):
                os.remove("large_test.pdf")

if __name__ == '__main__':
    unittest.main()