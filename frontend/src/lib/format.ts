export function formatDate(iso: string): string {
  const [year, month, day] = iso.split('-').map(Number)
  const date = new Date(year, month - 1, day)
  return date.toLocaleDateString('en-GB', { weekday: 'long', day: 'numeric', month: 'long' })
}

export function formatTime12h(hhmm: string): string {
  const [hours, minutes] = hhmm.split(':').map(Number)
  const period = hours >= 12 ? 'PM' : 'AM'
  const hours12 = hours % 12 === 0 ? 12 : hours % 12
  return `${hours12}:${String(minutes).padStart(2, '0')} ${period}`
}

export function formatLkr(amount: number): string {
  return `LKR ${amount.toLocaleString('en-US')}`
}
