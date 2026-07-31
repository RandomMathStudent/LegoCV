type RecordValue = Record<string, unknown>

type DetectionResult = {
  detected_face?: { status?: string; face_confidence?: number }
  features?: {
    geometry?: RecordValue
    semantics?: RecordValue
    engineered?: { dense_dim?: number; sparse_dim?: number; face_shape?: string }
  }
  embedding_length?: number
  matches?: Array<{ part_id?: string; category?: string; score?: number; name?: string }>
  ranking?: { hair?: Array<{ part_id?: string; category?: string; score?: number; metadata?: RecordValue }> }
}

function asRecord(value: unknown): RecordValue {
  return value && typeof value === 'object' && !Array.isArray(value) ? value as RecordValue : {}
}

function label(value: unknown) {
  if (value === null || value === undefined || value === '' || value === 'unknown') return 'Not detected'
  if (typeof value === 'boolean') return value ? 'Yes' : 'No'
  return String(value).replace(/_/g, ' ')
}

function title(value: unknown) {
  const text = label(value)
  return text === 'Not detected' ? text : text.replace(/\b\w/g, (letter) => letter.toUpperCase())
}

function confidence(value?: number) {
  if (typeof value !== 'number' || !Number.isFinite(value)) return null
  return `${Math.round(value * 100)}%`
}

function Attribute({ name, value }: { name: string; value: unknown }) {
  return <div className="attribute"><span>{name}</span><strong>{title(value)}</strong></div>
}

function PartList({ parts }: { parts: Array<{ part_id?: string; category?: string; score?: number; metadata?: RecordValue }> }) {
  if (!parts.length) return <p className="empty-state">No part recommendations yet.</p>

  return (
    <ol className="part-list">
      {parts.slice(0, 5).map((part, index) => (
        <li key={`${part.part_id ?? 'part'}-${index}`} className="part-item">
          <span className="rank-number">{index + 1}</span>
          <div>
            <strong>{part.metadata?.name ? String(part.metadata.name) : part.part_id ?? 'LEGO part'}</strong>
            <span>{title(part.category ?? part.metadata?.category ?? 'Hair part')}</span>
          </div>
          {typeof part.score === 'number' && <b>{Math.round(part.score * 100)}%</b>}
        </li>
      ))}
    </ol>
  )
}

export default function DetectionResults({ result }: { result: DetectionResult }) {
  const semantics = asRecord(result.features?.semantics)
  const hair = asRecord(semantics.hair)
  const glasses = asRecord(semantics.glasses)
  const facialHair = asRecord(semantics.facial_hair)
  const geometry = asRecord(result.features?.geometry)
  const face = result.detected_face ?? {}
  const score = confidence(face.face_confidence)
  const recommendedHair = result.ranking?.hair?.length
    ? result.ranking.hair
    : (result.matches ?? []).map((match) => ({ ...match, metadata: { name: match.name } }))

  return (
    <section className="results-panel" aria-live="polite">
      <div className="results-header">
        <div>
          <p className="eyebrow">Detection result</p>
          <h2>{face.status === 'aligned_face' ? 'Face detected' : 'Analysis complete'}</h2>
          <p>{face.status ? title(face.status) : 'Your image has been processed.'}</p>
        </div>
        <div className="confidence-badge">
          <span>Confidence</span>
          <strong>{score ?? '—'}</strong>
        </div>
      </div>

      <div className="results-grid">
        <article className="result-card appearance-card">
          <div className="card-heading"><span className="card-icon">◉</span><div><h3>Detected appearance</h3><p>Visible details used for matching</p></div></div>
          <div className="attribute-grid">
            <Attribute name="Hair colour" value={hair.colour} />
            <Attribute name="Hair style" value={hair.style} />
            <Attribute name="Hair length" value={hair.length} />
            <Attribute name="Glasses" value={glasses.present} />
            <Attribute name="Facial hair" value={facialHair.beard} />
            <Attribute name="Expression" value={semantics.expression} />
            <Attribute name="Skin tone" value={semantics.skin_tone} />
            <Attribute name="Face shape" value={result.features?.engineered?.face_shape} />
          </div>
        </article>

        <article className="result-card recommendations-card">
          <div className="card-heading"><span className="card-icon">★</span><div><h3>Suggested hair pieces</h3><p>Best matching LEGO part options</p></div></div>
          <PartList parts={recommendedHair} />
        </article>
      </div>

      <details className="technical-details">
        <summary>View analysis details</summary>
        <div className="technical-grid">
          <Attribute name="Face width" value={geometry.face_width} />
          <Attribute name="Face height" value={geometry.face_height} />
          <Attribute name="Smile score" value={geometry.smile} />
          <Attribute name="Embedding size" value={result.embedding_length} />
          <Attribute name="Dense features" value={result.features?.engineered?.dense_dim} />
          <Attribute name="Sparse features" value={result.features?.engineered?.sparse_dim} />
        </div>
      </details>
    </section>
  )
}