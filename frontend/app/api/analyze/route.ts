import { NextResponse } from 'next/server'

export async function POST(request: Request) {
  const formData = await request.formData()
  const image = formData.get('image')

  if (!image || typeof image === 'string') {
    return NextResponse.json({ error: 'Missing image' }, { status: 400 })
  }

  const backendUrl = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process?.env?.BACKEND_URL || 'http://127.0.0.1:8000/analyze'
  const upload = new FormData()
  upload.append('image', image as Blob, 'capture.jpg')

  const response = await fetch(backendUrl, {
    method: 'POST',
    body: upload,
  })

  const data = await response.json()
  return NextResponse.json(data, { status: response.status })
}
