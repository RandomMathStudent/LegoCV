export async function analyzeImage(file: File) {
  const form = new FormData()
  form.append('image', file)
  const res = await fetch('/api/analyze', { method: 'POST', body: form })
  return res.json()
}
