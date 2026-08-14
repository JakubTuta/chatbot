export interface ExportableMessage {
  role: 'user' | 'assistant'
  content: string
  image: string
}

function sanitizeFilename(title: string): string {
  return title.trim().replace(/[\\/:*?"<>|]+/g, '_').slice(0, 80) || 'chat'
}

export function buildMarkdownExport(title: string, messages: ExportableMessage[]): string {
  const lines: string[] = [`# ${title}`, '']

  for (const message of messages) {
    const heading = message.role === 'user'
      ? 'User'
      : 'Assistant'

    lines.push(`**${heading}:**`, '')
    lines.push(message.content)

    if (message.image)
      lines.push('', '*[Image attached]*')

    lines.push('', '---', '')
  }

  return lines.join('\n').trim()
}

export function buildJsonExport(title: string, model: string, messages: ExportableMessage[]): string {
  return JSON.stringify(
    {
      title,
      model,
      exported_at: new Date().toISOString(),
      messages,
    },
    null,
    2,
  )
}

export function downloadTextFile(title: string, extension: string, content: string, mimeType: string): void {
  const blob = new Blob([content], { type: mimeType })
  const url = URL.createObjectURL(blob)

  const link = document.createElement('a')
  link.href = url
  link.download = `${sanitizeFilename(title)}.${extension}`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)

  URL.revokeObjectURL(url)
}
