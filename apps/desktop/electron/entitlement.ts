/**
 * entitlement.ts
 *
 * Zeus subscription activation for the desktop main process. The JWT is signed
 * by the cloud service with Ed25519; this module verifies it locally (device
 * bound, 7-day expiry) and stores it under HERMES_HOME with 0600 semantics.
 * The Python runtime reads the same file, so both sides agree on the gate.
 */

import { createPublicKey, randomUUID, verify } from 'node:crypto'
import { existsSync, readFileSync } from 'node:fs'
import { join } from 'node:path'

import { writeSecretFileAtomic } from './hardening'

export const ENTITLEMENT_PUBLIC_KEY = `-----BEGIN PUBLIC KEY-----
MCowBQYDK2VwAyEAfnOaaYWOq76IAhosov89hflCjYD340F1ydVLCtX5vQg=
-----END PUBLIC KEY-----`

export interface EntitlementStatus {
  active: boolean
  reason: string
  plan: string | null
  features: string[]
  seats: number | null
  expires_at: number | null
  device_id: string | null
}

interface EntitlementClaims {
  iss?: string
  sub?: string
  plan?: string
  features?: string[]
  seats?: number
  device_id?: string
  iat?: number
  exp?: number
}

export function entitlementPath(hermesHome: string): string {
  return join(hermesHome, 'zeus-entitlement.json')
}

export function deviceIdPath(hermesHome: string): string {
  return join(hermesHome, 'zeus-device-id')
}

export function localDeviceId(hermesHome: string): string {
  const path = deviceIdPath(hermesHome)

  if (existsSync(path)) {
    const existing = readFileSync(path, 'utf8').trim()

    if (existing.length >= 8 && existing.length <= 128) {
      return existing
    }
  }

  const value = randomUUID().replace(/-/g, '')
  writeSecretFileAtomic(path, value)

  return value
}

function inactive(reason: string, deviceId: string | null = null): EntitlementStatus {
  return {
    active: false,
    reason,
    plan: null,
    features: [],
    seats: null,
    expires_at: null,
    device_id: deviceId
  }
}

export function verifyEntitlementToken(
  token: string,
  deviceId: string,
  nowSeconds = Math.floor(Date.now() / 1000),
  publicKeyPem = ENTITLEMENT_PUBLIC_KEY
): EntitlementStatus {
  const parts = token.split('.')

  if (parts.length !== 3) {
    return inactive('invalid', deviceId)
  }

  try {
    const header = JSON.parse(Buffer.from(parts[0], 'base64url').toString('utf8')) as { alg?: string }

    if (header.alg !== 'EdDSA') {
      return inactive('invalid', deviceId)
    }

    const signatureOk = verify(
      null,
      Buffer.from(`${parts[0]}.${parts[1]}`),
      createPublicKey(publicKeyPem),
      Buffer.from(parts[2], 'base64url')
    )

    if (!signatureOk) {
      return inactive('invalid', deviceId)
    }

    const claims = JSON.parse(Buffer.from(parts[1], 'base64url').toString('utf8')) as EntitlementClaims

    if (claims.iss !== 'zeus-cloud' || !claims.sub) {
      return inactive('invalid', deviceId)
    }

    if (!claims.exp || claims.exp <= nowSeconds) {
      return inactive('expired', deviceId)
    }

    if (claims.device_id !== deviceId) {
      return inactive('device_mismatch', deviceId)
    }

    return {
      active: true,
      reason: 'active',
      plan: claims.plan || null,
      features: Array.isArray(claims.features) ? claims.features.map(String) : [],
      seats: typeof claims.seats === 'number' ? claims.seats : null,
      expires_at: claims.exp,
      device_id: deviceId
    }
  } catch {
    return inactive('invalid', deviceId)
  }
}

export function readEntitlementStatus(
  hermesHome: string,
  publicKeyPem = ENTITLEMENT_PUBLIC_KEY
): EntitlementStatus {
  const deviceId = localDeviceId(hermesHome)
  const path = entitlementPath(hermesHome)

  if (!existsSync(path)) {
    return inactive('missing', deviceId)
  }

  try {
    const saved = JSON.parse(readFileSync(path, 'utf8')) as { token?: string }
    const token = typeof saved.token === 'string' ? saved.token : ''

    return token ? verifyEntitlementToken(token, deviceId, undefined, publicKeyPem) : inactive('invalid', deviceId)
  } catch {
    return inactive('invalid', deviceId)
  }
}

export function activationUrl(
  hermesHome: string,
  siteUrl = process.env.ZEUS_SITE_URL || 'http://127.0.0.1:9120'
): string {
  return `${siteUrl.replace(/\/+$/, '')}/?device_id=${encodeURIComponent(localDeviceId(hermesHome))}`
}

export async function activateWithCode(
  hermesHome: string,
  code: string,
  options: {
    cloudUrl?: string
    fetchImpl?: typeof fetch
    publicKeyPem?: string
  } = {}
): Promise<EntitlementStatus> {
  const deviceId = localDeviceId(hermesHome)
  const cloudUrl = (options.cloudUrl || process.env.ZEUS_CLOUD_URL || 'http://127.0.0.1:9121').replace(/\/+$/, '')
  const fetchImpl = options.fetchImpl || fetch
  const response = await fetchImpl(`${cloudUrl}/api/device/exchange`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, device_id: deviceId })
  })

  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string }

    throw new Error(body.detail || `Activation failed (${response.status})`)
  }

  const body = (await response.json()) as { token?: string }
  const token = typeof body.token === 'string' ? body.token : ''
  const status = verifyEntitlementToken(token, deviceId, undefined, options.publicKeyPem)

  if (!status.active) {
    throw new Error(`Zeus Cloud returned an unusable token (${status.reason})`)
  }

  writeSecretFileAtomic(
    entitlementPath(hermesHome),
    JSON.stringify({ token, device_id: deviceId, saved_at: Math.floor(Date.now() / 1000) })
  )

  return status
}
