const VARIABLE_PATTERN = /\{\{\s*([a-z_]\w*)\s*\}\}/gi

export function extractTemplateVariables(content: string): string[] {
  const seen = new Set<string>()
  const variables: string[] = []

  for (const match of content.matchAll(VARIABLE_PATTERN)) {
    const name = match[1]
    if (!seen.has(name)) {
      seen.add(name)
      variables.push(name)
    }
  }

  return variables
}

export function renderTemplate(content: string, values: Record<string, string>): string {
  return content.replace(VARIABLE_PATTERN, (match, name) => values[name] ?? match)
}
