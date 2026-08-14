const UNITS = ['B', 'KB', 'MB', 'GB', 'TB']

export function formatBytes(bytes: number | null | undefined): string {
  if (bytes === null || bytes === undefined || Number.isNaN(bytes))
    return 'Unknown'

  if (bytes === 0)
    return '0 B'

  const exponent = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), UNITS.length - 1)
  const value = bytes / 1024 ** exponent

  return `${value.toFixed(exponent === 0
    ? 0
    : 1)} ${UNITS[exponent]}`
}
