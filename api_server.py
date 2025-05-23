from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import shutil
import os
from stryreader import read_file_content, generate_audio, extract_characters

app = FastAPI()

# Allow CORS for local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
TEMP_AUDIO_DIR = "temp_audio"

os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(TEMP_AUDIO_DIR, exist_ok=True)

@app.post("/api/upload")
def upload_file(file: UploadFile = File(...)):
    file_path = os.path.abspath(os.path.join(UPLOAD_DIR, file.filename))
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    # Read file content and return page info
    try:
        file_data = read_file_content(file_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"filename": file.filename, "total_pages": file_data["total_pages"]}

@app.get("/api/audio-files")
def list_audio_files():
    files = [f for f in os.listdir(TEMP_AUDIO_DIR) if f.endswith(".mp3")]
    return {"files": files}

@app.get("/api/audio/{filename}")
def get_audio_file(filename: str):
    file_path = os.path.join(TEMP_AUDIO_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="audio/mpeg")
    return JSONResponse(status_code=404, content={"error": "File not found"})

@app.post("/api/extract-characters")
def extract_characters_api(file_path: str = Form(...)):
    try:
        characters = extract_characters(file_path)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"characters": characters}

@app.post("/api/read-aloud")
def read_aloud(file_path: str = Form(...)):
    print(f"/api/read-aloud called with file_path: {file_path}")
    try:
        audio_files = generate_audio(file_path, TEMP_AUDIO_DIR)
        print(f"Audio files generated: {audio_files}")
    except Exception as e:
        print(f"Error in generate_audio: {e}")
        return JSONResponse(status_code=500, content={"error": str(e)})
    return {"audio_files": audio_files}

# Add more endpoints for pause, stop, rewind, etc. as needed
