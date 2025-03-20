import sys
import os
import json
from collections import Counter

from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QFileDialog, QComboBox, QTextEdit, QListWidget, QSpacerItem, QSizePolicy, QDialog
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap, QImage

import PyPDF2
from gtts import gTTS
import pygame
import spacy  # For NLP character extraction

# Initialize pygame mixer for audio playback
pygame.init()
pygame.mixer.init()

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

# Functions to load and save last-read progress
def load_last_read_data():
    if os.path.exists("last_read.json"):
        try:
            with open("last_read.json", "r") as f:
                return json.load(f)
        except Exception as e:
            print("Error reading last_read.json:", e)
            return {}
    return {}

def save_last_read_data(data):
    with open("last_read.json", "w") as f:
        json.dump(data, f)

class PDFViewerWindow(QWidget):
    def __init__(self, pages, last_page=None, parent=None):
        super().__init__(parent)
        self.pages = pages
        self.current_font_size = 14  # Default font size
        self.setWindowTitle("PDF Contents")
        self.setMinimumSize(800, 600)
        self.initUI()
        self.apply_styles()
        if last_page is not None and 1 <= last_page <= len(self.pages):
            self.list_widget.setCurrentRow(last_page - 1)
    
    def initUI(self):
        main_layout = QHBoxLayout()
        self.list_widget = QListWidget()
        for i in range(len(self.pages)):
            self.list_widget.addItem(f"Page {i+1}")
        self.list_widget.currentRowChanged.connect(self.display_page_content)
        main_layout.addWidget(self.list_widget, 1)
        
        right_layout = QVBoxLayout()
        controls_layout = QHBoxLayout()
        font_label = QLabel("Font Size:")
        controls_layout.addWidget(font_label)
        self.decrease_button = QPushButton("-")
        self.decrease_button.clicked.connect(self.decrease_font)
        controls_layout.addWidget(self.decrease_button)
        self.increase_button = QPushButton("+")
        self.increase_button.clicked.connect(self.increase_font)
        controls_layout.addWidget(self.increase_button)
        controls_layout.addSpacerItem(QSpacerItem(20, 10, QSizePolicy.Expanding, QSizePolicy.Minimum))
        right_layout.addLayout(controls_layout)
        
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        right_layout.addWidget(self.text_edit, 1)
        
        main_layout.addLayout(right_layout, 3)
        self.setLayout(main_layout)
        if self.pages:
            self.list_widget.setCurrentRow(0)
    
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QListWidget {
                background-color: #34495e;
                border: none;
            }
            QTextEdit {
                background-color: #34495e;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                padding: 10px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                border-radius: 10px;
                padding: 5px 10px;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
        """)
        self.update_font()
    
    def update_font(self):
        font = QFont()
        font.setPointSize(self.current_font_size)
        self.text_edit.document().setDefaultFont(font)
        current_row = self.list_widget.currentRow()
        if current_row >= 0:
            self.text_edit.setText(self.pages[current_row])
    
    def increase_font(self):
        self.current_font_size += 2
        self.update_font()
    
    def decrease_font(self):
        if self.current_font_size > 6:
            self.current_font_size -= 2
            self.update_font()
    
    def display_page_content(self, row):
        if 0 <= row < len(self.pages):
            self.text_edit.setText(self.pages[row])

class PDFReaderApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("PDF Audio Reader")
        self.setMinimumSize(600, 500)
        self.viewer = None
        self.is_paused = False
        self.initUI()
        self.apply_styles()
        # Diffusion pipeline initialization omitted for brevity

    def initUI(self):
        layout = QVBoxLayout()
        self.label = QLabel("Select a PDF File:")
        layout.addWidget(self.label)
        self.select_button = QPushButton("Select PDF")
        self.select_button.clicked.connect(self.load_pdf)
        layout.addWidget(self.select_button)
        self.page_label = QLabel("Start from Page:")
        layout.addWidget(self.page_label)
        self.page_dropdown = QComboBox()
        self.page_dropdown.setEnabled(False)
        layout.addWidget(self.page_dropdown)
        self.text_area = QTextEdit()
        self.text_area.setReadOnly(True)
        layout.addWidget(self.text_area, 1)

        controls_layout = QHBoxLayout()
        self.read_button = QPushButton("Read Aloud")
        self.read_button.setEnabled(False)
        self.read_button.clicked.connect(self.read_pdf)
        controls_layout.addWidget(self.read_button)

        self.pause_button = QPushButton("Pause")
        self.pause_button.setEnabled(False)
        self.pause_button.clicked.connect(self.pause_audio)
        controls_layout.addWidget(self.pause_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_reading)
        controls_layout.addWidget(self.stop_button)
        layout.addLayout(controls_layout)
        
        rewind_layout = QHBoxLayout()
        self.rewind_5_button = QPushButton("Rewind 5s")
        self.rewind_5_button.clicked.connect(lambda: self.rewind_audio(5))
        rewind_layout.addWidget(self.rewind_5_button)
        self.rewind_10_button = QPushButton("Rewind 10s")
        self.rewind_10_button.clicked.connect(lambda: self.rewind_audio(10))
        rewind_layout.addWidget(self.rewind_10_button)
        self.rewind_30_button = QPushButton("Rewind 30s")
        self.rewind_30_button.clicked.connect(lambda: self.rewind_audio(30))
        rewind_layout.addWidget(self.rewind_30_button)
        layout.addLayout(rewind_layout)
        
        self.extract_button = QPushButton("Extract Characters")
        self.extract_button.setEnabled(False)
        self.extract_button.clicked.connect(self.extract_characters)
        layout.addWidget(self.extract_button)
        
        self.setLayout(layout)

    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #2c3e50;
                color: #ecf0f1;
                font-family: 'Segoe UI', sans-serif;
                font-size: 14px;
            }
            QPushButton {
                background-color: #3498db;
                border: none;
                border-radius: 10px;
                padding: 10px;
                color: white;
            }
            QPushButton:pressed {
                background-color: #2980b9;
            }
            QComboBox {
                border-radius: 5px;
                padding: 5px;
                background-color: #34495e;
                color: #ecf0f1;
            }
            QTextEdit {
                background-color: #34495e;
                border: 1px solid #7f8c8d;
                border-radius: 5px;
                padding: 5px;
            }
            QLabel {
                font-weight: bold;
            }
        """)

    def load_pdf(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Open PDF File", "", "PDF Files (*.pdf)")
        if file_path:
            self.file_path = file_path
            pages = []
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)
                self.total_pages = len(reader.pages)
                for page in reader.pages:
                    text = page.extract_text()
                    pages.append(text if text else "[No text found on this page]")
                self.page_dropdown.clear()
                self.page_dropdown.addItems([str(i) for i in range(1, self.total_pages + 1)])
                self.page_dropdown.setEnabled(True)
                self.read_button.setEnabled(True)
                self.extract_button.setEnabled(True)
            last_read_data = load_last_read_data()
            last_page = last_read_data.get(self.file_path, 1)
            if 1 <= last_page <= self.total_pages:
                self.page_dropdown.setCurrentIndex(last_page - 1)
            self.viewer = PDFViewerWindow(pages, last_page=last_page)
            self.viewer.show()

    def read_pdf(self):
        start_page = int(self.page_dropdown.currentText()) - 1  # zero-indexed
        extracted_text = ""
        with open(self.file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages[start_page:]:
                text = page.extract_text()
                if text:
                    extracted_text += text + "\n"
        if extracted_text:
            self.text_area.setText(extracted_text)
            tts = gTTS(text=extracted_text, lang='en')
            audio_file = "temp_audio.mp3"
            tts.save(audio_file)
            pygame.mixer.music.load(audio_file)
            pygame.mixer.music.play()
            self.stop_button.setEnabled(True)
            self.pause_button.setEnabled(True)
            self.is_paused = False
            self.pause_button.setText("Pause")

    def pause_audio(self):
        if pygame.mixer.music.get_busy():
            if not self.is_paused:
                pygame.mixer.music.pause()
                self.is_paused = True
                self.pause_button.setText("Resume")
            else:
                pygame.mixer.music.unpause()
                self.is_paused = False
                self.pause_button.setText("Pause")

    def rewind_audio(self, seconds):
        pos_ms = pygame.mixer.music.get_pos()
        if pos_ms < 0:
            pos_ms = 0
        new_time = max(0, (pos_ms / 1000.0) - seconds)
        pygame.mixer.music.stop()
        if os.path.exists("temp_audio.mp3"):
            pygame.mixer.music.load("temp_audio.mp3")
            pygame.mixer.music.play(start=new_time)

    def stop_reading(self):
        pygame.mixer.music.stop()
        self.stop_button.setEnabled(False)
        self.pause_button.setEnabled(False)
        last_read_data = load_last_read_data()
        current_page = int(self.page_dropdown.currentText())
        last_read_data[self.file_path] = current_page
        save_last_read_data(last_read_data)
        if os.path.exists("temp_audio.mp3"):
            os.remove("temp_audio.mp3")
    
    def extract_characters(self):
        """
        Extracts PERSON entities from the entire PDF text and writes
        the most frequent names to 'characters.txt'.
        """
        full_text = ""
        with open(self.file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text + "\n"
        
        if not full_text:
            print("No text found in PDF.")
            return
        
        doc = nlp(full_text)
        # Filter for PERSON entities
        persons = [ent.text.strip() for ent in doc.ents if ent.label_ == "PERSON"]
        if not persons:
            print("No PERSON entities found.")
            return
        
        # Count frequency of each name (case-insensitive)
        counts = Counter(name.lower() for name in persons)
        # Sort by frequency (most common first) and then format names (capitalized)
        main_characters = [name.capitalize() for name, count in counts.most_common()]
        
        # Write the names to a text file
        with open("characters.txt", "w") as f:
            for name in main_characters:
                f.write(name + "\n")
        
        print("Extracted character names saved to characters.txt.")
        # Optionally, update the text area to show confirmation
        self.text_area.append("\nExtracted character names saved to characters.txt.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = PDFReaderApp()
    window.show()
    sys.exit(app.exec_())
