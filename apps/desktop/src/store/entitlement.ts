import { atom } from 'nanostores'

import type { ZeusEntitlementStatus } from '@/global'

export type EntitlementPhase = 'checking' | 'activating' | 'active' | 'required' | 'error'

export interface EntitlementState {
  phase: EntitlementPhase
  status: ZeusEntitlementStatus | null
  error: string | null
}

export const $entitlement = atom<EntitlementState>({
  phase: 'checking',
  status: null,
  error: null
})

function message(error: unknown): string {
  return error instanceof Error ? error.message : String(error)
}

export async function refreshEntitlement(): Promise<void> {
  const bridge = window.hermesDesktop

  if (!bridge?.entitlementStatus) {
    $entitlement.set({ phase: 'active', status: null, error: null })

    return
  }

  try {
    const status = await bridge.entitlementStatus()
    $entitlement.set({ phase: status.active ? 'active' : 'required', status, error: null })
  } catch (error) {
    $entitlement.set({ phase: 'error', status: null, error: message(error) })
  }
}

export async function activateEntitlement(code: string): Promise<void> {
  const bridge = window.hermesDesktop

  if (!bridge?.entitlementActivate) {
    throw new Error('Activation is unavailable in this build')
  }

  $entitlement.set({ ...$entitlement.get(), phase: 'activating', error: null })

  try {
    const status = await bridge.entitlementActivate(code)
    $entitlement.set({ phase: status.active ? 'active' : 'required', status, error: null })
  } catch (error) {
    $entitlement.set({ phase: 'required', status: $entitlement.get().status, error: message(error) })
    throw error
  }
}

export async function openEntitlementActivation(): Promise<void> {
  await window.hermesDesktop?.openEntitlementActivation?.()
}
