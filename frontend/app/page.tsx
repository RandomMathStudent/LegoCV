"use client"

import { useCallback, useRef, useState } from 'react'
import Webcam from '@/components/Webcam'
import DetectionResults from '@/components/DetectionResults'
import { analyzeImage } from '@/lib/api'

export default function Page() {
  const [isCapturing, setIsCapturing] = useState(false)
  const [status, setStatus] = useState('Ready to capture your photo')
  const [result, setResult] = useState<any>(null)
  const webcamRef = useRef<any>(null)

  const capture = useCallback(async () => {
    if (!webcamRef.current) return

    const imageSrc = webcamRef.current.getScreenshot()
    if (!imageSrc) {
      setStatus('Unable to capture a frame from the camera')
      return
    }

    setIsCapturing(true)
    setStatus('Capturing and sending your photo...')

    try {
      const blob = await fetch(imageSrc).then((res) => res.blob())
      const file = new File([blob], 'capture.jpg', { type: 'image/jpeg' })
      const data = await analyzeImage(file)
      setResult(data)
      setStatus('Analysis complete')
    } catch (error) {
      console.error(error)
      setStatus('Analysis failed. Please try again.')
    } finally {
      setIsCapturing(false)
    }
  }, [])

  return (
    <main className="studio-page">
      <div className="studio-shell">
        <header className="studio-heading">
          <p className="eyebrow">LEGO® lookalike lab</p>
          <h1>Build your minifigure match</h1>
          <p>Capture a photo to identify visible features and find compatible LEGO parts.</p>
        </header>

        <div className="capture-grid">
          <div className="webcam-frame">
            <Webcam webcamRef={webcamRef} />
          </div>

          <aside className="capture-controls">
            <button
              onClick={capture}
              disabled={isCapturing}
              className="capture-button"
            >
              {isCapturing ? 'Analyzing...' : 'Capture & Analyze'}
            </button>

            <div className="status-card">
              <strong>Status</strong>
              <p>{status}</p>
            </div>
            <p className="capture-note">For the clearest match, face the camera in even lighting and keep hair visible.</p>
          </aside>
        </div>

        {result && <DetectionResults result={result} />}
      </div>
    </main>
  )
}
