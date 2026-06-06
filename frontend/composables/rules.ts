export const requiredRule = () => (value: string | number | null, textError = 'Required field') => Boolean(value) || textError

export function minLengthRule(min: number) {
  return (value: string) => (typeof value === 'string' && value.length >= min) || `Must be at least ${min} characters`
}
