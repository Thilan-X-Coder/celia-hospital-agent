import { useState } from 'react'

type ImageWithFallbackProps = {
  src: string
  alt: string
  className?: string
}

/** Shows the real image, or a soft palette placeholder if it fails to load (e.g. not added yet). */
export default function ImageWithFallback({ src, alt, className = '' }: ImageWithFallbackProps) {
  const [failed, setFailed] = useState(false)

  if (failed) {
    return (
      <div
        className={`flex items-center justify-center bg-gradient-to-br from-cream to-primary/10 ${className}`}
      >
        <span className="sr-only">{alt}</span>
        <svg
          viewBox="0 0 24 24"
          width="40"
          height="40"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.5"
          className="text-primary/40"
          aria-hidden="true"
        >
          <rect x="3" y="4" width="18" height="16" rx="2" />
          <circle cx="8.5" cy="9.5" r="1.5" />
          <path d="M3 16l5-5 4 4 3-3 6 6" />
        </svg>
      </div>
    )
  }

  return (
    <img
      src={src}
      alt={alt}
      className={className}
      onError={() => setFailed(true)}
    />
  )
}
