import { describe, expect, it } from 'vitest'
import { formatStats } from '~/utils/formatStats'

describe('formatStats', () => {
  it('returns an empty string when there are no stats', () => {
    expect(formatStats(undefined)).toBe('')
  })

  it('returns an empty string for an empty stats object', () => {
    expect(formatStats({})).toBe('')
  })

  it('formats tokens/sec and token count without context usage when num_ctx is unset', () => {
    expect(formatStats({ tokens_per_second: 25.4, completion_tokens: 30 })).toBe('25.4 tok/s · 30 tokens')
  })

  it('includes context usage percentage when context_limit is set', () => {
    expect(
      formatStats({ tokens_per_second: 25.4, completion_tokens: 30, context_used: 40, context_limit: 4096 }),
    ).toBe('25.4 tok/s · 30 tokens · 1% of context')
  })

  it('omits context usage when context_limit is 0 (falsy, nothing meaningful to divide by)', () => {
    expect(formatStats({ completion_tokens: 30, context_used: 40, context_limit: 0 })).toBe('30 tokens')
  })

  it('only shows the fields that are actually present', () => {
    expect(formatStats({ completion_tokens: 12 })).toBe('12 tokens')
    expect(formatStats({ tokens_per_second: 9.99 })).toBe('10.0 tok/s')
  })
})
