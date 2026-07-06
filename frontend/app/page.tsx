"use client"

import { useCallback, useRef, useState } from 'react'
import Webcam from '@/components/Webcam'
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
    <main style={{ minHeight: '100vh', padding: '2rem', fontFamily: 'Arial, sans-serif', background: '#f7f7f7' }}>
      <div style={{ maxWidth: 900, margin: '0 auto', background: 'white', borderRadius: 20, padding: 24, boxShadow: '0 8px 30px rgba(0,0,0,0.08)' }}>
        <h1 style={{ marginBottom: 8 }}>LEGO Lookalike Studio</h1>
        <p style={{ marginTop: 0, color: '#666' }}>Allow camera access, capture a photo, and send it to the backend for analysis.</p>

        <div style={{ display: 'grid', gap: 20, gridTemplateColumns: '1.2fr 0.8fr' }}>
          <div style={{ border: '1px solid #e3e3e3', borderRadius: 16, overflow: 'hidden', background: '#fff' }}>
            <Webcam webcamRef={webcamRef} />
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            <button
              onClick={capture}
              disabled={isCapturing}
              style={{ padding: '0.9rem 1.2rem', border: 'none', borderRadius: 999, background: '#ffcf00', color: '#111', fontWeight: 700, cursor: isCapturing ? 'wait' : 'pointer' }}
            >
              {isCapturing ? 'Analyzing...' : 'Capture & Analyze'}
            </button>

            <div style={{ padding: 16, background: '#fafafa', borderRadius: 12, border: '1px solid #eee' }}>
              <strong>Status</strong>
              <p style={{ marginBottom: 0 }}>{status}</p>
            </div>

            {result && (
              <div style={{ padding: 16, background: '#f2fbf4', borderRadius: 12, border: '1px solid #d7f0dc' }}>
                <strong>Analysis result</strong>
                <pre style={{ marginTop: 8, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{JSON.stringify(result, null, 2)}</pre>
              </div>
            )}
          </div>
        </div>
      </div>
    </main>
  )
}
