import { describe, expect, it } from 'vitest'
import { extractTemplateVariables, renderTemplate } from '~/utils/promptTemplate'

describe('extractTemplateVariables', () => {
  it('returns an empty array for content with no placeholders', () => {
    expect(extractTemplateVariables('Just plain text.')).toEqual([])
  })

  it('extracts a single variable', () => {
    expect(extractTemplateVariables('Summarize {{topic}} for me.')).toEqual(['topic'])
  })

  it('extracts multiple variables in first-appearance order', () => {
    expect(extractTemplateVariables('Bug: {{summary}}\nSteps: {{steps}}\nExpected: {{expected}}'))
      .toEqual(['summary', 'steps', 'expected'])
  })

  it('deduplicates a variable used more than once', () => {
    expect(extractTemplateVariables('{{name}}, hello {{name}}!')).toEqual(['name'])
  })

  it('tolerates extra whitespace inside the braces', () => {
    expect(extractTemplateVariables('{{  topic  }}')).toEqual(['topic'])
  })

  it('ignores malformed placeholders', () => {
    expect(extractTemplateVariables('{{}} {not a var} {{1invalid}}')).toEqual([])
  })
})

describe('renderTemplate', () => {
  it('substitutes every provided variable', () => {
    expect(renderTemplate('Bug: {{summary}}\nSteps: {{steps}}', { summary: 'Crash on save', steps: 'Click save' }))
      .toBe('Bug: Crash on save\nSteps: Click save')
  })

  it('leaves a placeholder untouched when no value was provided for it', () => {
    expect(renderTemplate('{{a}} and {{b}}', { a: 'x' })).toBe('x and {{b}}')
  })

  it('substitutes an intentionally blank value as empty text', () => {
    expect(renderTemplate('before{{gap}}after', { gap: '' })).toBe('beforeafter')
  })

  it('is a no-op on content with no placeholders', () => {
    expect(renderTemplate('Nothing to fill in.', {})).toBe('Nothing to fill in.')
  })
})
