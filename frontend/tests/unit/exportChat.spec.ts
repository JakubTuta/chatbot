import { describe, expect, it } from 'vitest'
import { buildJsonExport, buildMarkdownExport } from '~/utils/exportChat'

describe('buildMarkdownExport', () => {
  it('renders the title as a heading and each message under a role label', () => {
    const md = buildMarkdownExport('My chat', [
      { role: 'user', content: 'Hi there', image: '' },
      { role: 'assistant', content: 'Hello!', image: '' },
    ])

    expect(md).toContain('# My chat')
    expect(md).toContain('**User:**')
    expect(md).toContain('Hi there')
    expect(md).toContain('**Assistant:**')
    expect(md).toContain('Hello!')
  })

  it('notes an attached image without embedding the raw data URI', () => {
    const md = buildMarkdownExport('My chat', [
      { role: 'user', content: 'Look at this', image: 'data:image/png;base64,abc123' },
    ])

    expect(md).toContain('*[Image attached]*')
    expect(md).not.toContain('data:image/png;base64,abc123')
  })

  it('handles an empty conversation without throwing', () => {
    expect(buildMarkdownExport('Empty chat', [])).toContain('# Empty chat')
  })
})

describe('buildJsonExport', () => {
  it('produces valid JSON carrying the title, model, and full messages including images', () => {
    const json = buildJsonExport('My chat', 'llama3.1', [
      { role: 'user', content: 'Look at this', image: 'data:image/png;base64,abc123' },
    ])

    const parsed = JSON.parse(json)

    expect(parsed.title).toBe('My chat')
    expect(parsed.model).toBe('llama3.1')
    expect(parsed.messages).toEqual([
      { role: 'user', content: 'Look at this', image: 'data:image/png;base64,abc123' },
    ])
    expect(typeof parsed.exported_at).toBe('string')
  })
})
