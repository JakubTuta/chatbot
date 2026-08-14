import { describe, expect, it } from 'vitest'
import { cleanEmptyHtmlTags, splitMessageRaw } from '~/utils/splitMessage'

describe('splitMessageRaw', () => {
  it('returns a single text part for plain prose', () => {
    const result = splitMessageRaw('Hello, how can I help?')

    expect(result.thoughts).toBe('')
    expect(result.parts).toEqual([{ title: 'text', content: 'Hello, how can I help?' }])
  })

  it('extracts <think> content separately from the visible parts', () => {
    const result = splitMessageRaw('<think>reasoning about it</think>Here is the answer.')

    expect(result.thoughts).toBe('reasoning about it')
    expect(result.parts).toEqual([{ title: 'text', content: 'Here is the answer.' }])
  })

  it('splits text around a fenced code block and captures the language', () => {
    const message = 'Try this:\n```python\nprint("hi")\n```\nThat should work.'
    const result = splitMessageRaw(message)

    expect(result.parts).toEqual([
      { title: 'text', content: 'Try this:' },
      { title: 'code', content: 'print("hi")', language: 'python' },
      { title: 'text', content: 'That should work.' },
    ])
  })

  it('treats an unterminated code fence as still-open (mid-stream)', () => {
    // While a response is streaming, the closing ``` hasn't arrived yet —
    // must still render the code so far instead of waiting for it.
    const message = 'Here:\n```js\nconst x = 1'
    const result = splitMessageRaw(message)

    expect(result.parts).toEqual([
      { title: 'text', content: 'Here:' },
      { title: 'code', content: 'const x = 1', language: 'js' },
    ])
  })

  it('drops empty text parts entirely rather than pushing blank content', () => {
    const result = splitMessageRaw('```\ncode only\n```')

    expect(result.parts).toEqual([{ title: 'code', content: 'code only', language: '' }])
  })

  it('is a no-op when there is no <think> tag', () => {
    const result = splitMessageRaw('no thinking here')

    expect(result.thoughts).toBe('')
    expect(result.parts).toEqual([{ title: 'text', content: 'no thinking here' }])
  })
})

describe('cleanEmptyHtmlTags', () => {
  it('removes empty tags', () => {
    expect(cleanEmptyHtmlTags('<p></p>hello<span></span>')).toBe('hello')
  })

  it('removes nested empty tags left behind by removing an inner one', () => {
    expect(cleanEmptyHtmlTags('<div><p></p></div>text')).toBe('text')
  })

  it('leaves tags with content untouched', () => {
    expect(cleanEmptyHtmlTags('<p>hello</p>')).toBe('<p>hello</p>')
  })
})
