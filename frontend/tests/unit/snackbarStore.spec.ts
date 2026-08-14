import { createPinia, defineStore, setActivePinia } from 'pinia'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { ref } from 'vue'

// stores/snackbarStore.ts is written for Nuxt's auto-import environment
// (`defineStore`/`ref` resolved globally by the Nuxt/Pinia build pipeline
// rather than imported). Stubbing them as globals here satisfies the same
// free-variable lookups without needing a full Nuxt test runtime.
vi.stubGlobal('defineStore', defineStore)
vi.stubGlobal('ref', ref)

const { useSnackbarStore } = await import('~/stores/snackbarStore')

beforeEach(() => {
  setActivePinia(createPinia())
})

describe('snackbarStore', () => {
  it('shows an enqueued item immediately', () => {
    const store = useSnackbarStore()

    store.showSnackbarSuccess('Saved')

    expect(store.toasts).toHaveLength(1)
    expect(store.toasts[0]).toMatchObject({ text: 'Saved', color: 'success' })
  })

  it('skips an exact duplicate of a toast already showing', () => {
    const store = useSnackbarStore()

    store.showSnackbarError('Docker is not running')
    store.showSnackbarError('Docker is not running')

    expect(store.toasts).toHaveLength(1)
  })

  it('stacks multiple different toasts at once, newest last', () => {
    const store = useSnackbarStore()

    store.showSnackbarInfo('first')
    store.showSnackbarInfo('second')

    expect(store.toasts.map(t => t.text)).toEqual(['first', 'second'])
  })

  it('drops the oldest toast once past the 3-visible cap', () => {
    const store = useSnackbarStore()

    store.showSnackbarInfo('q1')
    store.showSnackbarInfo('q2')
    store.showSnackbarInfo('q3')
    store.showSnackbarInfo('q4') // q1 drops, q2/q3/q4 remain

    expect(store.toasts.map(t => t.text)).toEqual(['q2', 'q3', 'q4'])
  })

  it('auto-dismisses a toast after 5s', () => {
    vi.useFakeTimers()
    const store = useSnackbarStore()

    store.showSnackbarSuccess('Saved')
    expect(store.toasts).toHaveLength(1)

    vi.advanceTimersByTime(5000)
    expect(store.toasts).toHaveLength(0)

    vi.useRealTimers()
  })

  it('dismisses a specific toast by id without affecting others', () => {
    const store = useSnackbarStore()

    store.showSnackbarInfo('keep')
    store.showSnackbarInfo('remove')

    const toRemove = store.toasts.find(t => t.text === 'remove')!
    store.dismiss(toRemove.id)

    expect(store.toasts.map(t => t.text)).toEqual(['keep'])
  })
})
