import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinter.scrolledtext import ScrolledText
import json
import socket
import os
import nltk

class FlashcardClient:
    def __init__(self, host='localhost', port=5000):
        self.host = host
        self.port = port

    def test_connection(self):
        """Test if the server is available on the specified port"""
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as test_socket:
                test_socket.connect((self.host, self.port))
                return True
        except:
            return False

    def send_file(self, file_path):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
            try:
                client_socket.connect((self.host, self.port))
                
                #Determines the file type
                file_type = file_path.split('.')[-1].lower()
                if file_type != 'pdf':
                    raise ValueError("Unsupported file type. Only PDF files are supported.")

                #Sends the the file type
                client_socket.send(file_type.ljust(10).encode())
                
                #Read & Send file content
                with open(file_path, 'rb') as file:
                    file_content = file.read()
                    client_socket.send(str(len(file_content)).zfill(10).encode())
                    client_socket.send(file_content)

                #Receive response size
                response_size = int(client_socket.recv(10).decode())
                
                #Receives the flashcards
                response = b""
                while len(response) < response_size:
                    chunk = client_socket.recv(min(4096, response_size - len(response)))
                    if not chunk:
                        break
                    response += chunk

                return json.loads(response.decode())

            except ConnectionRefusedError:
                return {"error": "Could not connect to server. Please check if the server is running."}
            except Exception as e:
                return {"error": str(e)}

class FlashcardGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Flashcard Generator")
        self.root.geometry("800x600")
        
        #grid weights
        self.root.grid_rowconfigure(1, weight=1)
        self.root.grid_columnconfigure(0, weight=1)
        
        #create and pack widgets
        self.create_server_config_frame()
        self.create_upload_frame()
        self.create_flashcard_viewer()
        self.create_status_bar()
        
        #flashcards state
        self.current_card_index = 0
        self.flashcards = []
        self.showing_question = True
        
        #client for server communication
        self.client = FlashcardClient()

    def create_server_config_frame(self):
        config_frame = ttk.Frame(self.root, padding="10")
        config_frame.grid(row=0, column=0, sticky="ew")

        ttk.Label(config_frame, text="Server Configuration", font=('Arial', 12, 'bold')).pack()

        #port configuration
        port_frame = ttk.Frame(config_frame)
        port_frame.pack(pady=5)
        ttk.Label(port_frame, text="Port:").pack(side=tk.LEFT, padx=5)
        self.port_var = tk.StringVar(value="5000")
        port_entry = ttk.Entry(port_frame, textvariable=self.port_var, width=10)
        port_entry.pack(side=tk.LEFT, padx=5)

        #test connection button
        test_btn = ttk.Button(config_frame, text="Test Connection", command=self.test_server_connection)
        test_btn.pack(pady=5)

    def create_upload_frame(self):
        upload_frame = ttk.Frame(self.root, padding="10")
        upload_frame.grid(row=1, column=0, sticky="ew")

        #upload button
        upload_btn = ttk.Button(upload_frame, text="Upload PDF File", command=self.upload_file)
        upload_btn.pack(pady=5)

    def create_flashcard_viewer(self):
        viewer_frame = ttk.Frame(self.root, padding="10")
        viewer_frame.grid(row=2, column=0, sticky="nsew")

        #displays the card
        self.card_text = ScrolledText(viewer_frame, wrap=tk.WORD, height=10, font=('Arial', 12))
        self.card_text.pack(fill=tk.BOTH, expand=True, pady=5)

        #navigation button
        nav_frame = ttk.Frame(viewer_frame)
        nav_frame.pack(fill=tk.X, pady=5)

        self.prev_btn = ttk.Button(nav_frame, text="Previous", command=self.previous_card)
        self.prev_btn.pack(side=tk.LEFT, padx=5)

        self.flip_btn = ttk.Button(nav_frame, text="Flip", command=self.flip_card)
        self.flip_btn.pack(side=tk.LEFT, padx=5)

        self.next_btn = ttk.Button(nav_frame, text="Next", command=self.next_card)
        self.next_btn.pack(side=tk.LEFT, padx=5)

        #save button
        self.save_btn = ttk.Button(viewer_frame, text="Save Flashcards", command=self.save_flashcards)
        self.save_btn.pack(pady=5)

    def create_status_bar(self):
        self.status_var = tk.StringVar(value="Not connected")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.grid(row=3, column=0, sticky="ew")

    def upload_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("PDF files", "*.pdf")]
        )
        if file_path:
            try:
                self.status_var.set("Uploading file and generating flashcards...")
                self.root.update()
                
                response = self.client.send_file(file_path)
                
                if "error" in response:
                    messagebox.showerror("Error", response["error"])
                    self.status_var.set("Error generating flashcards")
                else:
                    self.flashcards = response
                    self.current_card_index = 0
                    self.showing_question = True
                    self.update_card_display()
                    self.status_var.set(f"Generated {len(self.flashcards)} flashcards")
            except Exception as e:
                messagebox.showerror("Error", str(e))
                self.status_var.set("Error processing file")

    def save_flashcards(self):
        if not self.flashcards:
            messagebox.showwarning("Warning", "No flashcards to save!")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile="flashcards.txt"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    for card in self.flashcards:
                        f.write(f"Q: {card['question']}\nA: {card['answer']}\n\n")
                messagebox.showinfo("Success", "Flashcards saved successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Error saving flashcards: {str(e)}")

    def update_card_display(self):
        if not self.flashcards:
            self.card_text.delete(1.0, tk.END)
            self.card_text.insert(tk.END, "No flashcards available")
            return

        card = self.flashcards[self.current_card_index]
        self.card_text.delete(1.0, tk.END)
        
        if self.showing_question:
            self.card_text.insert(tk.END, f"Question ({self.current_card_index + 1}/{len(self.flashcards)}):\n\n")
            self.card_text.insert(tk.END, card["question"])
        else:
            self.card_text.insert(tk.END, f"Answer ({self.current_card_index + 1}/{len(self.flashcards)}):\n\n")
            self.card_text.insert(tk.END, card["answer"])
            self.prev_btn["state"] = "normal" if self.current_card_index > 0 else "disabled"
            self.next_btn["state"] = "normal" if self.current_card_index < len(self.flashcards) - 1 else "disabled"

    def flip_card(self):
        if self.flashcards:
            self.showing_question = not self.showing_question
            self.update_card_display()

    def next_card(self):
        if self.current_card_index < len(self.flashcards) - 1:
            self.current_card_index += 1
            self.showing_question = True
            self.update_card_display()

    def previous_card(self):
        if self.current_card_index > 0:
            self.current_card_index -= 1
            self.showing_question = True
            self.update_card_display()

    def test_server_connection(self):
        try:
            port = int(self.port_var.get())
            self.client = FlashcardClient(port=port)
            if self.client.test_connection():
                messagebox.showinfo("Success", "Successfully connected to server!")
                self.status_var.set("Connected to server")
            else:
                messagebox.showerror("Error", "Could not connect to server")
                self.status_var.set("Not connected")
        except ValueError:
            messagebox.showerror("Error", "Invalid port number")

def main():
    root = tk.Tk()
    app = FlashcardGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()