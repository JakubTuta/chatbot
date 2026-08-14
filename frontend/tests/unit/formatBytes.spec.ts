import { describe, expect, it } from 'vitest'
import { formatBytes } from '~/utils/formatBytes'

describe('formatBytes', () => {
  it('formats null/undefined as Unknown', () => {
    expect(formatBytes(null)).toBe('Unknown')
    expect(formatBytes(undefined)).toBe('Unknown')
  })

  it('formats 0 bytes', () => {
    expect(formatBytes(0)).toBe('0 B')
  })

  it('formats bytes under 1 KB with no decimal', () => {
    expect(formatBytes(512)).toBe('512 B')
  })

  it('formats kilobytes', () => {
    expect(formatBytes(2048)).toBe('2.0 KB')
  })

  it('formats gigabytes', () => {
    expect(formatBytes(4_920_753_328)).toBe('4.6 GB')
  })

  it('formats terabytes', () => {
    expect(formatBytes(1_500_000_000_000)).toBe('1.4 TB')
  })
})
