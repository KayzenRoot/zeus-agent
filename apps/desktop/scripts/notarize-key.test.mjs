import assert from 'node:assert/strict'
import fs from 'node:fs'
import os from 'node:os'
import path from 'node:path'

import { test } from 'vitest'

import { resolveApiKeyPath } from './notarize.mjs'

const INLINE_KEY = '-----BEGIN PRIVATE KEY-----\nTEST\n-----END PRIVATE KEY-----'

test('inline .p8 key lands in a private mkdtemp dir, not a predictable tmpfile', () => {
  const { keyPath, cleanup } = resolveApiKeyPath(INLINE_KEY)
  try {
    const tempDir = path.dirname(keyPath)
    assert.ok(path.basename(tempDir).startsWith('hermes-notary-'))
    assert.notEqual(tempDir, os.tmpdir())
    assert.ok(fs.existsSync(keyPath), 'key file must exist')
    assert.equal(fs.readFileSync(keyPath, 'utf8'), INLINE_KEY)
    if (process.platform !== 'win32') {
      const mode = fs.statSync(tempDir).mode & 0o777
      assert.equal(mode, 0o700, 'temp dir must be private on POSIX')
    }
  } finally {
    cleanup()
  }
  const tempDir = path.dirname(keyPath)
  assert.equal(fs.existsSync(tempDir), false, 'cleanup must remove the whole temp dir')
})

test('cleanup is a no-op for empty input and file-path input creates no temp dir', () => {
  const empty = resolveApiKeyPath('')
  assert.equal(empty.keyPath, '')
  empty.cleanup()

  const filePath = path.join(os.tmpdir(), `notary-test-${process.pid}.p8`)
  fs.writeFileSync(filePath, INLINE_KEY, 'utf8')
  try {
    const fromFile = resolveApiKeyPath(filePath)
    assert.equal(fromFile.keyPath, filePath)
    // A provided path is used as-is: no temp dir is created for it.
    assert.notEqual(path.dirname(fromFile.keyPath), path.join(os.tmpdir(), 'hermes-notary-key.p8'))
  } finally {
    fs.rmSync(filePath, { force: true })
  }
})

test('invalid inline key is rejected before any temp dir is created', () => {
  assert.throws(() => resolveApiKeyPath('not a key'), /APPLE_API_KEY/)
  assert.equal(
    fs.readdirSync(os.tmpdir()).some((e) => e.startsWith('hermes-notary-')),
    false,
  )
})
