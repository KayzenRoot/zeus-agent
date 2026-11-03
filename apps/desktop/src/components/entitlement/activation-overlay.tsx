import { useStore } from '@nanostores/react'
import { useEffect, useState } from 'react'

import { BrandMark } from '@/components/brand-mark'
import {
  $entitlement,
  activateEntitlement,
  openEntitlementActivation,
  refreshEntitlement
} from '@/store/entitlement'
import { $desktopOnboarding } from '@/store/onboarding'

interface Props {
  enabled: boolean
}

/**
 * Full-screen activation gate. It only appears after first-run onboarding so
 * the provider setup is never stacked behind a subscription wall.
 */
export function EntitlementActivationOverlay({ enabled }: Props) {
  const state = useStore($entitlement)
  const onboarding = useStore($desktopOnboarding)
  const [code, setCode] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (enabled && onboarding.configured === true) {
      void refreshEntitlement()
    }
  }, [enabled, onboarding.configured])

  if (!enabled || onboarding.configured !== true || state.phase === 'active') {
    return null
  }

  const activating = state.phase === 'activating' || submitting

  const submit = async () => {
    if (!code.trim() || activating) {
      return
    }

    setSubmitting(true)

    try {
      await activateEntitlement(code.trim())
      setCode('')
    } catch {
      // The store carries the user-facing error.
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div
      className="fixed inset-0 z-(--z-onboarding) flex items-center justify-center bg-background/95 p-6 backdrop-blur-md"
      data-glass-opaque
    >
      <div className="w-full max-w-lg rounded-2xl border border-(--stroke-nous) bg-card p-8 shadow-nous">
        <div className="flex items-start gap-4">
          <BrandMark className="size-11 shrink-0" />
          <div className="min-w-0">
            <h2 className="text-xl font-semibold tracking-tight">Ative sua assinatura</h2>
            <p className="mt-2 text-sm leading-6 text-muted-foreground">
              O Zeus requer uma assinatura ativa para este dispositivo. Entre na sua conta e gere
              um código de ativação.
            </p>
          </div>
        </div>

        {state.phase === 'checking' ? (
          <p className="mt-6 text-sm text-muted-foreground">Verificando assinatura…</p>
        ) : (
          <>
            {state.error ? (
              <p className="mt-4 rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-300">
                {state.error}
              </p>
            ) : null}

            <button
              className="mt-6 w-full rounded-lg bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground transition hover:bg-primary/90 disabled:opacity-60"
              disabled={activating}
              onClick={() => void openEntitlementActivation()}
              type="button"
            >
              Ativar no navegador
            </button>

            <div className="mt-5 border-t border-(--ui-stroke-tertiary) pt-5">
              <label className="text-xs font-medium text-muted-foreground" htmlFor="zeus-activation-code">
                Ou cole o código de ativação
              </label>
              <div className="mt-2 flex gap-2">
                <input
                  autoComplete="off"
                  className="min-w-0 flex-1 rounded-lg border border-(--ui-stroke-tertiary) bg-(--ui-bg-quinary) px-3 py-2 text-sm outline-none focus:border-primary"
                  id="zeus-activation-code"
                  onChange={event => setCode(event.target.value)}
                  onKeyDown={event => {
                    if (event.key === 'Enter') {
                      void submit()
                    }
                  }}
                  placeholder="cole o código aqui"
                  value={code}
                />
                <button
                  className="rounded-lg border border-(--ui-stroke-tertiary) px-4 py-2 text-sm font-medium transition hover:bg-(--chrome-action-hover) disabled:opacity-60"
                  disabled={!code.trim() || activating}
                  onClick={() => void submit()}
                  type="button"
                >
                  {activating ? 'Ativando…' : 'Ativar'}
                </button>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
