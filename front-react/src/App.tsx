import React, { useState, useRef } from 'react';
import './App.css';

interface FileData {
  name: string;
  content: string;
  totalPages: number;
  path?: string;
}

function App() {
  const [file, setFile] = useState<FileData | null>(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [isReading, setIsReading] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [audioFiles, setAudioFiles] = useState<string[]>([]);
  const [currentAudio, setCurrentAudio] = useState<number>(0);
  const [snackbar, setSnackbar] = useState<{open: boolean, message: string, severity: 'success'|'error'|'info'}>({open: false, message: '', severity: 'info'});
  const [dialog, setDialog] = useState<{open: boolean, title: string, content: string}>({open: false, title: '', content: ''});

  const audioRef = useRef<HTMLAudioElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Upload file to backend
  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const uploadedFile = event.target.files?.[0];
    if (!uploadedFile) return;
    setIsLoading(true);
    try {
      const formData = new FormData();
      formData.append('file', uploadedFile);
      const res = await fetch('http://localhost:8000/api/upload', {
        method: 'POST',
        body: formData,
      });
      if (!res.ok) throw new Error('Upload failed');
      const content = await uploadedFile.text();
      const pages = content.split('\n\n').filter(page => page.trim());
      setFile({
        name: uploadedFile.name,
        content: content,
        totalPages: pages.length || 1,
        path: uploadedFile.name,
      });
      setCurrentPage(1);
      setSnackbar({open: true, message: 'File uploaded successfully!', severity: 'success'});
      // Fetch audio files list
      fetchAudioFiles();
    } catch (error) {
      setSnackbar({open: true, message: 'Error uploading file', severity: 'error'});
    } finally {
      setIsLoading(false);
    }
  };

  // Fetch audio files from backend
  const fetchAudioFiles = async () => {
    const res = await fetch('http://localhost:8000/api/audio-files');
    const data = await res.json();
    setAudioFiles(data.files || []);
    setCurrentAudio(0);
  };

  // Play audio file
  const playAudio = (index: number) => {
    if (audioFiles.length === 0) return;
    setCurrentAudio(index);
    setIsReading(true);
    setIsPaused(false);
    setTimeout(() => {
      audioRef.current?.play();
    }, 100);
  };

  // Read aloud (start from first audio)
  const handleReadAloud = async () => {
    if (!file) return;
    setIsReading(true);
    setIsPaused(false);
    // Send full path to backend
    await fetch('http://localhost:8000/api/read-aloud', {
      method: 'POST',
      body: new URLSearchParams({ file_path: `uploads/${file.name}` }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    setSnackbar({open: true, message: 'Generating audio...', severity: 'info'});
    fetchAudioFiles();
    playAudio(0);
  };

  // Pause/Resume
  const handlePauseResume = () => {
    if (isPaused) {
      audioRef.current?.play();
      setIsPaused(false);
    } else {
      audioRef.current?.pause();
      setIsPaused(true);
    }
  };

  // Stop
  const handleStop = () => {
    audioRef.current?.pause();
    audioRef.current!.currentTime = 0;
    setIsReading(false);
    setIsPaused(false);
  };

  // Rewind 10s
  const handleRewind = () => {
    if (audioRef.current) {
      audioRef.current.currentTime = Math.max(0, audioRef.current.currentTime - 10);
    }
  };

  // Extract characters
  const handleExtractCharacters = async () => {
    if (!file) return;
    const res = await fetch('http://localhost:8000/api/extract-characters', {
      method: 'POST',
      body: new URLSearchParams({ file_path: `uploads/${file.name}` }),
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const data = await res.json().catch(() => null);
    setDialog({open: true, title: 'Extracted Characters', content: data?.characters?.join(', ') || 'Characters extracted!'});
  };

  // When audio ends, play next
  const handleAudioEnded = () => {
    if (currentAudio < audioFiles.length - 1) {
      playAudio(currentAudio + 1);
    } else {
      setIsReading(false);
      setIsPaused(false);
    }
  };

  const handlePageChange = (page: number) => {
    if (page >= 1 && page <= (file?.totalPages || 1)) {
      setCurrentPage(page);
    }
  };

  // Show snackbar for 2.5s then auto-close
  React.useEffect(() => {
    if (snackbar.open) {
      const timer = setTimeout(() => setSnackbar(s => ({...s, open: false})), 2500);
      return () => clearTimeout(timer);
    }
  }, [snackbar.open]);

  return (
    <div className="app-root">
      {/* --- Animated Background Layers --- */}
      <div className="background-animated-layers">
        <div className="bg-pulse-orb bg-pulse-orb1"></div>
        <div className="bg-pulse-orb bg-pulse-orb2"></div>
        <div className="bg-pulse-orb bg-pulse-orb3"></div>
        <div className="bg-pulse-orb bg-pulse-orb4"></div>
        <div className="bg-pulse-orb bg-pulse-orb5"></div>
      </div>
      <div className="bg-animated-lines">
        <div className="animated-line line1"></div>
        <div className="animated-line line2"></div>
        <div className="animated-line line3"></div>
        <div className="animated-line line4"></div>
      </div>
      <div className="bg-animated-stars">
        <div className="animated-star star1"></div>
        <div className="animated-star star2"></div>
        <div className="animated-star star3"></div>
        <div className="animated-star star4"></div>
        <div className="animated-star star5"></div>
        <div className="animated-star star6"></div>
        <div className="animated-star star7"></div>
        <div className="animated-star star8"></div>
        <div className="animated-star star9"></div>
        <div className="animated-star star10"></div>
        <div className="animated-star star11"></div>
        <div className="animated-star star12"></div>
        <div className="animated-star star13"></div>
        <div className="animated-star star14"></div>
        <div className="animated-star star15"></div>
      </div>
      <header className="app-header">
        <div className="logo">📚</div>
        <h1>AI Story Reader</h1>
      </header>
      <main className="app-main">
        {!file ? (
          <div className="upload-card">
            <div className="upload-icon">📄</div>
            <h2>Upload Your Story</h2>
            <p>Choose a PDF or text file to get started</p>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt"
              onChange={handleFileUpload}
              style={{ display: 'none' }}
              id="file-upload"
              tabIndex={-1}
            />
            <label htmlFor="file-upload" style={{ width: '100%' }}>
              <button
                className="primary-btn"
                type="button"
                disabled={isLoading}
                tabIndex={0}
                onClick={() => fileInputRef.current?.click()}
              >
                {isLoading ? <span className="loader"></span> : <><span className="icon">⬆️</span> Select File</>}
              </button>
            </label>
          </div>
        ) : (
          <div className="reader-card">
            <div className="reader-header">
              <span className="filename">{file.name}</span>
              <button className="secondary-btn" onClick={() => setFile(null)}>
                <span className="icon">➕</span> New File
              </button>
            </div>
            <div className="reader-controls">
              <button onClick={() => handlePageChange(currentPage - 1)} disabled={currentPage <= 1} className="icon-btn" title="Previous Page">◀️</button>
              <span className="page-indicator">Page {currentPage} of {file.totalPages}</span>
              <button onClick={() => handlePageChange(currentPage + 1)} disabled={currentPage >= file.totalPages} className="icon-btn" title="Next Page">▶️</button>
            </div>
            <div className="story-content-box">
              <div className="story-content-scroll">
                {file.content.split('\n\n')[currentPage - 1] || 'No content available'}
              </div>
            </div>
            <div className="action-row">
              <button className="primary-btn" onClick={isReading ? handlePauseResume : handleReadAloud}>
                {isReading ? (isPaused ? '▶️ Resume' : '⏸️ Pause') : '🔊 Read Aloud'}
              </button>
              {isReading && (
                <button className="secondary-btn" onClick={handleStop}>⏹️ Stop</button>
              )}
              <button className="secondary-btn" onClick={handleRewind}>⏪ Rewind 10s</button>
              <button className="secondary-btn" onClick={handleExtractCharacters}>👤 Extract Characters</button>
            </div>
            <div className="pagination-row">
              {[...Array(file.totalPages)].map((_, idx) => (
                <button
                  key={idx}
                  className={`page-btn${currentPage === idx + 1 ? ' active' : ''}`}
                  onClick={() => handlePageChange(idx + 1)}
                >
                  {idx + 1}
                </button>
              ))}
            </div>
            {audioFiles.length > 0 && (
              <audio
                ref={audioRef}
                src={`http://localhost:8000/api/audio/${audioFiles[currentAudio]}`}
                onEnded={handleAudioEnded}
                autoPlay={isReading && !isPaused}
                controls
                className="audio-player"
              />
            )}
          </div>
        )}
        {snackbar.open && (
          <div className={`snackbar snackbar-${snackbar.severity}`}>{snackbar.message}</div>
        )}
        {dialog.open && (
          <div className="dialog-overlay" onClick={() => setDialog({...dialog, open: false})}>
            <div className="dialog" onClick={e => e.stopPropagation()}>
              <h3>{dialog.title}</h3>
              <div>{dialog.content}</div>
              <button className="primary-btn" onClick={() => setDialog({...dialog, open: false})}>Close</button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
