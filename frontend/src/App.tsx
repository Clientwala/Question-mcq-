import { useState, useEffect, useCallback } from 'react'
import axios from 'axios'
import { io, Socket } from 'socket.io-client'
import { useDropzone } from 'react-dropzone'
import './App.css'

// API Configuration
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

interface JobResponse {
  job_id: string
  status: string
  progress: number
  current_step?: string
  pdf_filename?: string
}

interface ProgressData {
  progress: number
  step: string
  timestamp: string
}

interface CompleteData {
  output_filename: string
  total_questions: number
  diagrams_detected: number
}

function App() {
  const [pdfFile, setPdfFile] = useState<File | null>(null)
  const [jobId, setJobId] = useState<string | null>(null)
  const [status, setStatus] = useState<string>('idle')
  const [progress, setProgress] = useState<number>(0)
  const [currentStep, setCurrentStep] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const [socket, setSocket] = useState<Socket | null>(null)
  const [result, setResult] = useState<CompleteData | null>(null)

  // Configuration
  const [pageStart, setPageStart] = useState<string>('1')
  const [pageEnd, setPageEnd] = useState<string>('10')
  const [questionStart, setQuestionStart] = useState<string>('1')
  const [questionEnd, setQuestionEnd] = useState<string>('15')
  const [chapterName, setChapterName] = useState<string>('')
  const [unitName, setUnitName] = useState<string>('')
  const [outputFilename, setOutputFilename] = useState<string>('')

  // File drop handler
  const onDrop = useCallback((acceptedFiles: File[]) => {
    if (acceptedFiles.length > 0) {
      setPdfFile(acceptedFiles[0])
      setError(null)
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'application/pdf': ['.pdf'] },
    multiple: false,
    maxSize: 50 * 1024 * 1024, // 50MB
  })

  // Connect to WebSocket
  useEffect(() => {
    const newSocket = io(API_URL)
    setSocket(newSocket)

    newSocket.on('connect', () => {
      console.log('WebSocket connected')
    })

    newSocket.on('disconnect', () => {
      console.log('WebSocket disconnected')
    })

    return () => {
      newSocket.close()
    }
  }, [])

  // Subscribe to job updates when jobId changes
  useEffect(() => {
    if (socket && jobId) {
      // Subscribe to job updates
      socket.emit('subscribe', { job_id: jobId })

      // Listen for progress updates
      socket.on('progress', (data: ProgressData) => {
        setProgress(data.progress)
        setCurrentStep(data.step)
      })

      // Listen for completion
      socket.on('complete', (data: CompleteData) => {
        setStatus('completed')
        setProgress(100)
        setResult(data)
        setCurrentStep('Processing complete!')
      })

      // Listen for errors
      socket.on('error', (data: { message: string }) => {
        setStatus('failed')
        setError(data.message)
      })

      return () => {
        socket.emit('unsubscribe', { job_id: jobId })
        socket.off('progress')
        socket.off('complete')
        socket.off('error')
      }
    }
  }, [socket, jobId])

  // Upload PDF and start processing
  const handleSubmit = async () => {
    if (!pdfFile) {
      setError('Please select a PDF file')
      return
    }

    // Validate inputs
    const ps = parseInt(pageStart)
    const pe = parseInt(pageEnd)
    const qs = parseInt(questionStart)
    const qe = parseInt(questionEnd)

    if (isNaN(ps) || isNaN(pe) || isNaN(qs) || isNaN(qe)) {
      setError('Please enter valid numbers for page and question ranges')
      return
    }

    if (ps > pe) {
      setError('Page start must be less than or equal to page end')
      return
    }

    if (qs > qe) {
      setError('Question start must be less than or equal to question end')
      return
    }

    try {
      setStatus('uploading')
      setError(null)
      setProgress(0)
      setCurrentStep('Uploading PDF...')

      const formData = new FormData()
      formData.append('pdf_file', pdfFile)
      formData.append('page_start', pageStart)
      formData.append('page_end', pageEnd)
      formData.append('question_start', questionStart)
      formData.append('question_end', questionEnd)
      if (chapterName) {
        formData.append('chapter_name', chapterName)
      }

      const response = await axios.post<JobResponse>(`${API_URL}/api/v1/jobs/`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      })

      setJobId(response.data.job_id)
      setStatus('processing')
      setCurrentStep('PDF uploaded. Processing started...')
    } catch (err: any) {
      setStatus('failed')
      setError(err.response?.data?.detail || err.message || 'Upload failed')
    }
  }

  // Download result
  const handleDownload = async () => {
    if (!jobId) return

    try {
      const response = await axios.get(`${API_URL}/api/v1/jobs/${jobId}/download`, {
        responseType: 'blob',
      })

      const url = window.URL.createObjectURL(new Blob([response.data]))
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', result?.output_filename || 'questions.docx')
      document.body.appendChild(link)
      link.click()
      link.remove()
    } catch (err: any) {
      setError('Download failed: ' + (err.message || 'Unknown error'))
    }
  }

  // Reset form
  const handleReset = () => {
    setPdfFile(null)
    setJobId(null)
    setStatus('idle')
    setProgress(0)
    setCurrentStep('')
    setError(null)
    setResult(null)
  }

  return (
    <div className="app-container">
      <header className="app-header">
        <h1>📄 PDF Question Document Generator</h1>
        <p>Extract questions from PDF and generate formatted Word documents</p>
      </header>

      <main className="app-main">
        {status === 'idle' || status === 'uploading' ? (
          <div className="upload-section">
            {/* File Upload */}
            <div {...getRootProps()} className={`dropzone ${isDragActive ? 'active' : ''}`}>
              <input {...getInputProps()} />
              {pdfFile ? (
                <div className="file-info">
                  <p>✅ {pdfFile.name}</p>
                  <p className="file-size">
                    {(pdfFile.size / (1024 * 1024)).toFixed(2)} MB
                  </p>
                </div>
              ) : (
                <div className="dropzone-content">
                  <p>🖱️ Click to select PDF or drag & drop here</p>
                  <p className="dropzone-hint">Maximum file size: 50MB</p>
                </div>
              )}
            </div>

            {/* Configuration Form */}
            <div className="config-form">
              <h3>Configuration</h3>

              <div className="form-row">
                <div className="form-group">
                  <label>Page Range</label>
                  <div className="input-group">
                    <input
                      type="number"
                      placeholder="Start"
                      value={pageStart}
                      onChange={(e) => setPageStart(e.target.value)}
                      min="1"
                    />
                    <span>to</span>
                    <input
                      type="number"
                      placeholder="End"
                      value={pageEnd}
                      onChange={(e) => setPageEnd(e.target.value)}
                      min="1"
                    />
                  </div>
                </div>

                <div className="form-group">
                  <label>Question Range</label>
                  <div className="input-group">
                    <input
                      type="number"
                      placeholder="Start"
                      value={questionStart}
                      onChange={(e) => setQuestionStart(e.target.value)}
                      min="1"
                    />
                    <span>to</span>
                    <input
                      type="number"
                      placeholder="End"
                      value={questionEnd}
                      onChange={(e) => setQuestionEnd(e.target.value)}
                      min="1"
                    />
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Chapter Name (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g., Chapter 2"
                    value={chapterName}
                    onChange={(e) => setChapterName(e.target.value)}
                  />
                </div>

                <div className="form-group">
                  <label>Unit Name (Optional)</label>
                  <input
                    type="text"
                    placeholder="e.g., Laminar Flow"
                    value={unitName}
                    onChange={(e) => setUnitName(e.target.value)}
                  />
                </div>
              </div>

              <div className="form-group">
                <label>Output Filename (Optional)</label>
                <input
                  type="text"
                  placeholder="Leave empty for auto-generated name"
                  value={outputFilename}
                  onChange={(e) => setOutputFilename(e.target.value)}
                />
                <small style={{ color: '#718096', fontSize: '0.85rem', marginTop: '0.25rem' }}>
                  Auto-generated format: ChapterName_UnitName_Q{questionStart}-{questionEnd}.docx
                </small>
              </div>

              <button
                className="btn-primary"
                onClick={handleSubmit}
                disabled={!pdfFile || status === 'uploading'}
              >
                {status === 'uploading' ? (
                  <>
                    <span className="spinner"></span> Uploading...
                  </>
                ) : (
                  'Generate Document'
                )}
              </button>
            </div>

            {error && (
              <div className="error-message">
                <strong>Error:</strong> {error}
              </div>
            )}
          </div>
        ) : (
          <div className="processing-section">
            {/* Progress Tracker */}
            {status === 'processing' && (
              <div className="progress-card">
                <div className="loading-icon"></div>
                <h3 className="pulse">Processing...</h3>
                <div className="progress-bar-container">
                  <div className="progress-bar" style={{ width: `${progress}%` }}>
                    <span className="progress-text">{progress}%</span>
                  </div>
                </div>
                <p className="current-step">{currentStep}</p>
              </div>
            )}

            {/* Completion */}
            {status === 'completed' && result && (
              <div className="completion-card">
                <h3>✅ Processing Complete!</h3>
                <div className="result-info">
                  <p>
                    <strong>Total Questions:</strong> {result.total_questions}
                  </p>
                  <p>
                    <strong>Diagrams Detected:</strong> {result.diagrams_detected}
                  </p>
                  <p>
                    <strong>Output File:</strong> {result.output_filename}
                  </p>
                </div>
                <div className="action-buttons">
                  <button className="btn-primary" onClick={handleDownload}>
                    📥 Download Word Document
                  </button>
                  <button className="btn-secondary" onClick={handleReset}>
                    🔄 Process Another PDF
                  </button>
                </div>
              </div>
            )}

            {/* Error */}
            {status === 'failed' && (
              <div className="error-card">
                <h3>❌ Processing Failed</h3>
                <p>{error}</p>
                <button className="btn-secondary" onClick={handleReset}>
                  Try Again
                </button>
              </div>
            )}
          </div>
        )}
      </main>

      <footer className="app-footer">
        <p>Powered by FastAPI + React + Socket.IO</p>
      </footer>
    </div>
  )
}

export default App
