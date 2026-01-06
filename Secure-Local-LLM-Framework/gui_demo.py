import sys
import os
import PyPDF2
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, 
    QTextEdit, QLineEdit, QPushButton, QLabel, QFileDialog, QMessageBox
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal

# Import your Core Framework
try:
    from ai_manager import AIManager
    from voice_manager import VoiceManager
except ImportError:
    print("CRITICAL: Libraries missing. Run 'pip install -r requirements.txt'")
    sys.exit(1)

# --- WORKER THREAD FOR AI (Prevents GUI Freezing) ---
class AIWorker(QThread):
    finished = pyqtSignal(str)
    
    def __init__(self, ai_manager, history):
        super().__init__()
        self.ai = ai_manager
        self.history = history

    def run(self):
        # This triggers the heavy engine_loader.py logic
        response = self.ai.get_response(self.history)
        self.finished.emit(response)

# --- WORKER THREAD FOR AUDIO (Prevents GUI Freezing) ---
class AudioWorker(QThread):
    def __init__(self, voice_manager):
        super().__init__()
        self.vm = voice_manager

    def run(self):
        # This runs the RAM-only recording loop
        self.vm.start_recording()

class OpsGuardReferenceGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpsGuard Core Framework - Reference Implementation")
        self.resize(600, 500)
        
        # 1. Initialize Managers
        self.model_path = "tinyllama.gguf"
        if not os.path.exists(self.model_path):
            QMessageBox.critical(self, "Error", f"Model '{self.model_path}' not found.\nPlease download it to this folder.")
            sys.exit(1)
            
        self.ai_manager = AIManager(self.model_path)
        self.voice_manager = VoiceManager()
        
        # State
        self.history = [{"role": "system", "content": "You are a secure, local AI assistant."}]
        self.pdf_context = ""
        self.is_recording = False
        self.audio_thread = None

        # 2. Build UI Layout
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # Header
        lbl_info = QLabel("<b>Secure Local Inference Demo</b><br>Powered by Nuitka-hardened Engine & Ephemeral RAM Buffers")
        lbl_info.setStyleSheet("color: #555; font-size: 12px;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

        # Chat Area
        self.chat_display = QTextEdit()
        self.chat_display.setReadOnly(True)
        self.chat_display.setPlaceholderText("Conversation history will appear here...")
        layout.addWidget(self.chat_display)

        # PDF Status Area
        self.lbl_status = QLabel("System Ready. (No context loaded)")
        self.lbl_status.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.lbl_status)

        # Input Controls
        input_layout = QHBoxLayout()
        
        self.btn_pdf = QPushButton("📄 Attach PDF")
        self.btn_pdf.clicked.connect(self.attach_pdf)
        
        self.btn_mic = QPushButton("🎤 Record")
        self.btn_mic.clicked.connect(self.toggle_recording)
        
        self.inp_text = QLineEdit()
        self.inp_text.setPlaceholderText("Type a message...")
        self.inp_text.returnPressed.connect(self.send_message)
        
        self.btn_send = QPushButton("Send")
        self.btn_send.clicked.connect(self.send_message)

        input_layout.addWidget(self.btn_pdf)
        input_layout.addWidget(self.btn_mic)
        input_layout.addWidget(self.inp_text)
        input_layout.addWidget(self.btn_send)
        
        layout.addLayout(input_layout)
        self.setLayout(layout)

    def attach_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select PDF", "", "PDF Files (*.pdf)")
        if file_path:
            try:
                # Simulating the SpeechBubble.py logic
                text = ""
                with open(file_path, 'rb') as f:
                    reader = PyPDF2.PdfReader(f)
                    limit = min(5, len(reader.pages)) # Limit for demo
                    for i in range(limit):
                        text += reader.pages[i].extract_text() + "\n"
                
                self.pdf_context = text
                filename = os.path.basename(file_path)
                self.lbl_status.setText(f"✅ Loaded: {filename} ({len(text)} chars) into RAM.")
                self.lbl_status.setStyleSheet("color: green; font-weight: bold;")
                
            except Exception as e:
                QMessageBox.warning(self, "Error", str(e))

    def toggle_recording(self):
        if not self.is_recording:
            # Start Recording
            self.is_recording = True
            self.btn_mic.setText("⏹ Stop")
            self.btn_mic.setStyleSheet("background-color: #ffcccc; color: red;")
            self.lbl_status.setText("🔴 Recording to Volatile RAM Buffer...")
            
            self.audio_thread = AudioWorker(self.voice_manager)
            self.audio_thread.start()
        else:
            # Stop Recording
            self.is_recording = False
            self.voice_manager.stop_recording()
            self.audio_thread.wait() # Wait for thread to finish
            
            self.btn_mic.setText("⏳ Processing...")
            self.btn_mic.setEnabled(False)
            
            # Transcribe (This uses the RAM buffer)
            success, text = self.voice_manager.save_and_transcribe()
            
            self.btn_mic.setText("🎤 Record")
            self.btn_mic.setStyleSheet("")
            self.btn_mic.setEnabled(True)
            self.lbl_status.setText("System Ready.")

            if success:
                self.inp_text.setText(self.inp_text.text() + " " + text)
            else:
                QMessageBox.warning(self, "Voice Error", text)

    def send_message(self):
        user_text = self.inp_text.text().strip()
        if not user_text: return

        self.chat_display.append(f"<b>You:</b> {user_text}")
        self.inp_text.clear()
        self.lbl_status.setText("🧠 AI is thinking...")

        # Construct RAG Prompt
        full_prompt = user_text
        if self.pdf_context:
             full_prompt = f"Context:\n{self.pdf_context}\n\nUser: {user_text}"

        # Update History (Ephemeral: We don't save the PDF text to history, just the prompt)
        current_turn = self.history + [{"role": "user", "content": full_prompt}]

        # Start AI Thread
        self.ai_worker = AIWorker(self.ai_manager, current_turn)
        self.ai_worker.finished.connect(self.handle_response)
        self.ai_worker.start()

    def handle_response(self, response):
        self.chat_display.append(f"<b>OpsGuard:</b> {response}")
        self.chat_display.append("<hr>")
        self.history.append({"role": "user", "content": self.inp_text.text()}) # Save clean history
        self.history.append({"role": "assistant", "content": response})
        self.lbl_status.setText("System Ready.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = OpsGuardReferenceGUI()
    window.show()
    sys.exit(app.exec())
