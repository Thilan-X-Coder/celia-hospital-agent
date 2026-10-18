import logoUrl from '../assets/logo.svg'

type LogoProps = {
  size?: number
  className?: string
}

/** The one place the Celia logo is referenced - swap src/assets/logo.svg to change it everywhere. */
export default function Logo({ size = 32, className = '' }: LogoProps) {
  return (
    <img
      src={logoUrl}
      alt="Celia logo"
      width={size}
      height={size}
      className={className}
    />
  )
}
