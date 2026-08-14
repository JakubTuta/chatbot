export interface MessagePart {
  title: 'text' | 'code'
  content: string
  language?: string
}

export interface SplitMessageResult {
  thoughts: string
  parts: MessagePart[]
}

export function cleanEmptyHtmlTags(text: string): string {
  const emptyTagRegex = /<([a-z0-9]+)(\s[^>]*)?>(\s*)<\/\1>/gi

  let previousText = ''
  let currentText = text

  while (previousText !== currentText) {
    previousText = currentText
    currentText = currentText.replace(emptyTagRegex, '')
  }

  return currentText
}

export function splitMessageRaw(message: string): SplitMessageResult {
  let thoughts = ''
  let remainingMessage = message

  const thinkTagStart = remainingMessage.indexOf('<think>')
  const thinkTagEnd = remainingMessage.indexOf('</think>')

  if (thinkTagStart !== -1 && thinkTagEnd !== -1) {
    thoughts = remainingMessage.substring(thinkTagStart + 7, thinkTagEnd).trim()
    remainingMessage = remainingMessage.substring(0, thinkTagStart) + remainingMessage.substring(thinkTagEnd + 8)
  }

  const parts: MessagePart[] = []
  while (remainingMessage.length > 0) {
    const codeBlockStart = remainingMessage.indexOf('```')

    if (codeBlockStart === -1) {
      if (remainingMessage) {
        const cleanedText = cleanEmptyHtmlTags(remainingMessage).trim()
        if (cleanedText)
          parts.push({ title: 'text', content: cleanedText })
      }
      break
    }

    if (codeBlockStart > 0) {
      const textContent = remainingMessage.substring(0, codeBlockStart)
      const cleanedText = cleanEmptyHtmlTags(textContent).trim()
      if (cleanedText)
        parts.push({ title: 'text', content: cleanedText })
    }

    const codeBlockEnd = remainingMessage.indexOf('```', codeBlockStart + 3)

    if (codeBlockEnd !== -1) {
      const fullCodeBlock = remainingMessage.substring(codeBlockStart, codeBlockEnd + 3)
      const programmingLanguage = fullCodeBlock.match(/```(.*)\n/)?.[1] || ''
      const code = fullCodeBlock.replace(/```(.*)\n|```$/g, '')

      parts.push({ title: 'code', content: code.trim(), language: programmingLanguage.trim() })
      remainingMessage = remainingMessage.substring(codeBlockEnd + 3)
    }
    else {
      const code = remainingMessage.substring(codeBlockStart + 3)
      const programmingLanguage = code.match(/^(.*)\n/)?.[1] || ''
      const codeContent = programmingLanguage
        ? code.substring(programmingLanguage.length + 1)
        : code

      parts.push({
        title: 'code',
        content: codeContent.trim(),
        language: programmingLanguage.trim(),
      })
      break
    }
  }

  return { thoughts, parts }
}
