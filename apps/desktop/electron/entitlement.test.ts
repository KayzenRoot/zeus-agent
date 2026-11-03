import assert from 'node:assert/strict'
import { generateKeyPairSync, type KeyObject, sign } from 'node:crypto'
import { mkdtempSync, readFileSync, rmSync, statSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { test } from 'vitest'

import {
  activateWithCode,
  activationUrl,
  deviceIdPath,
  entitlementPath,
  localDeviceId,
  readEntitlementStatus,
  verifyEntitlementToken
} from './entitlement'

function keys(): { privateKey: KeyObject; publicKeyPem: string } {
  const pair = generateKeyPairSync('ed25519')
  const publicKeyPem = pair.publicKey.export({ type: 'spki', format: 'pem' }).toString()

  return { privateKey: pair.privateKey, publicKeyPem }
}

function token(
  privateKey: KeyObject,
  claims: Record<string, unknown>,
  header: Record<string, unknown> = { alg: 'EdDSA', typ: 'JWT' }
): string {
  const encodedHeader = Buffer.from(JSON.stringify(header)).toString('base64url')
  const encodedPayload = Buffer.from(JSON.stringify(claims)).toString('base64url')
  const signature = sign(null, Buffer.from(`${encodedHeader}.${encodedPayload}`), privateKey)

  return `${encodedHeader}.${encodedPayload}.${signature.toString('base64url')}`
}

function claims(deviceId: string, overrides: Record<string, unknown> = {}): Record<string, unknown> {
  const now = Math.floor(Date.now() / 1000)

  return {
    iss: 'zeus-cloud',
    sub: 'user_123',
    plan: 'annual',
    features: ['agents:10'],
    seats: 10,
    device_id: deviceId,
    iat: now,
    exp: now + 3600,
    ...overrides
  }
}

test('verifies a device-bound token and rejects another device', () => {
  const { privateKey, publicKeyPem } = keys()
  const signed = token(privateKey, claims('device-abcdefgh'))

  const active = verifyEntitlementToken(signed, 'device-abcdefgh', undefined, publicKeyPem)
  assert.equal(active.active, true)
  assert.equal(active.plan, 'annual')
  assert.equal(active.seats, 10)

  const wrong = verifyEntitlementToken(signed, 'device-other-12', undefined, publicKeyPem)
  assert.equal(wrong.active, false)
  assert.equal(wrong.reason, 'device_mismatch')
})

test('rejects expired, tampered and wrong-issuer tokens', () => {
  const { privateKey, publicKeyPem } = keys()
  const now = Math.floor(Date.now() / 1000)

  const expired = verifyEntitlementToken(
    token(privateKey, claims('device-abcdefgh', { exp: now - 1 })),
    'device-abcdefgh',
    undefined,
    publicKeyPem
  )
  assert.equal(expired.reason, 'expired')

  const wrongIssuer = verifyEntitlementToken(
    token(privateKey, claims('device-abcdefgh', { iss: 'someone-else' })),
    'device-abcdefgh',
    undefined,
    publicKeyPem
  )
  assert.equal(wrongIssuer.reason, 'invalid')

  const signed = token(privateKey, claims('device-abcdefgh'))
  const tampered = `${signed.slice(0, -2)}aa`
  assert.equal(
    verifyEntitlementToken(tampered, 'device-abcdefgh', undefined, publicKeyPem).reason,
    'invalid'
  )
})

test('activation stores the token under HERMES_HOME and status reloads it', async () => {
  const home = mkdtempSync(join(tmpdir(), 'zeus-entitlement-'))
  const { privateKey, publicKeyPem } = keys()
  const deviceId = localDeviceId(home)
  const signed = token(privateKey, claims(deviceId))

  try {
    const fetchImpl = (async () =>
      ({
        ok: true,
        status: 200,
        json: async () => ({ token: signed })
      }) as Response) as typeof fetch

    const activated = await activateWithCode(home, 'code-abcdefghijklmnop', {
      cloudUrl: 'http://127.0.0.1:9121',
      fetchImpl,
      publicKeyPem
    })
    assert.equal(activated.active, true)

    const reloaded = readEntitlementStatus(home, publicKeyPem)
    assert.equal(reloaded.active, true)
    assert.equal(reloaded.plan, 'annual')

    const saved = JSON.parse(readFileSync(entitlementPath(home), 'utf8')) as { device_id: string }
    assert.equal(saved.device_id, deviceId)
    assert.equal(readFileSync(deviceIdPath(home), 'utf8'), deviceId)

    if (process.platform !== 'win32') {
      assert.equal(statSync(entitlementPath(home)).mode & 0o777, 0o600)
    }

    const url = activationUrl(home, 'http://127.0.0.1:9120')
    assert.match(url, new RegExp(deviceId))
  } finally {
    rmSync(home, { recursive: true, force: true })
  }
})

test('activation surfaces the cloud refusal without writing a token', async () => {
  const home = mkdtempSync(join(tmpdir(), 'zeus-entitlement-'))
  const { publicKeyPem } = keys()

  try {
    const fetchImpl = (async () =>
      ({
        ok: false,
        status: 403,
        json: async () => ({ detail: 'no active subscription' })
      }) as Response) as typeof fetch

    await assert.rejects(
      activateWithCode(home, 'code-abcdefghijklmnop', {
        cloudUrl: 'http://127.0.0.1:9121',
        fetchImpl,
        publicKeyPem
      }),
      /no active subscription/
    )
    assert.equal(readEntitlementStatus(home, publicKeyPem).active, false)
  } finally {
    rmSync(home, { recursive: true, force: true })
  }
})
