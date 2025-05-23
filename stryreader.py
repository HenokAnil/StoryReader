import os
import re
import shutil
from collections import Counter
from typing import List, Dict

# For PDF reading
import PyPDF2
# For TTS
import pyttsx3


def read_file_content(filepath: str) -> Dict:
    """
    Reads a PDF or TXT file and returns its content split into pages.
    """
    pages = []
    if filepath.lower().endswith('.pdf'):
        with open(filepath, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text = page.extract_text()
                pages.append(text if text else "[No text found on this page]")
    elif filepath.lower().endswith('.txt'):
        with open(filepath, "r", encoding="utf-8") as file:
            content = file.read()
            pages = content.split("\n\n")
    else:
        raise ValueError("Unsupported file type")
    return {"pages": pages, "total_pages": len(pages)}


def generate_audio(filepath: str, temp_audio_dir: str) -> List[str]:
    """
    Generate audio files for each page and return list of audio file paths.
    """
    # Clean temp_audio_dir
    if os.path.exists(temp_audio_dir):
        shutil.rmtree(temp_audio_dir)
    os.makedirs(temp_audio_dir, exist_ok=True)

    file_data = read_file_content(filepath)
    pages = file_data["pages"]
    audio_files = []
    for idx, text in enumerate(pages):
        audio_file = os.path.join(temp_audio_dir, f"temp_audio_page_{idx+1}.mp3")
        try:
            engine = pyttsx3.init()
            engine.save_to_file(text, audio_file)
            engine.runAndWait()
            print(f"Generated audio: {audio_file}")
            if os.path.exists(audio_file):
                audio_files.append(audio_file)
            else:
                print(f"Failed to create: {audio_file}")
        except Exception as e:
            print(f"Error generating audio for page {idx+1}: {e}")
    print(f"All generated audio files: {audio_files}")
    return audio_files


def extract_characters(filepath: str) -> List[str]:
    """
    Extracts capitalized words (simple heuristic for names) from the file.
    """
    file_data = read_file_content(filepath)
    full_text = "\n".join(file_data["pages"])
    words = re.findall(r'\b[A-Z][a-z]*\b', full_text)
    counts = Counter(words)
    main_characters = [name for name, count in counts.most_common()]
    # Optionally write to file
    with open("characters.txt", "w") as f:
        for name in main_characters:
            f.write(name + "\n")
    return main_characters
