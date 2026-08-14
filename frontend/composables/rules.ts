export const requiredRule = () => (value: string | number | null, textError = 'Required field') => Boolean(value) || textError
