"use client"

import { useEffect, useState } from 'react'
import WebcamComponent from 'react-webcam'

export default function Webcam({ webcamRef }: { webcamRef?: React.Ref<any> }) {
  const [permissionError, setPermissionError] = useState<string | null>(null)
  const [isClient, setIsClient] = useState(false)

  useEffect(() => {
    setIsClient(true)
  }, [])

  if (!isClient) {
    return <div style={{ width: '100%', aspectRatio: '4 / 3', background: '#ddd', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Preparing camera…</div>
  }

  if (permissionError) {
    return (
      <div style={{ width: '100%', aspectRatio: '4 / 3', background: '#fff3f3', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24, textAlign: 'center' }}>
        <div>
          <strong>Camera access needed</strong>
          <p style={{ marginBottom: 0 }}>{permissionError}</p>
        </div>
      </div>
    )
  }

  return (
    <div style={{ width: '100%', aspectRatio: '4 / 3', background: '#000' }}>
      <WebcamComponent
        ref={webcamRef as any}
        audio={false}
        muted
        mirrored
        screenshotFormat="image/jpeg"
        videoConstraints={{ facingMode: 'user' }}
        onUserMediaError={(error: any) => {
          const name = typeof error === 'string' ? error : error?.name
          const message = name === 'NotAllowedError'
            ? 'Camera access was blocked. Please allow camera permissions for this site and refresh the page.'
            : 'Unable to start the camera. Please refresh the page and try again.'
          setPermissionError(message)
        }}
        style={{ width: '100%', height: '100%', objectFit: 'cover' }}
      />
    </div>
  )
}
