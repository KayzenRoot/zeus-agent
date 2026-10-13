'use strict'

const assert = require('node:assert/strict')
const { execFileSync } = require('node:child_process')
const path = require('node:path')
const { test } = require('node:test')

const configPath = path.resolve(__dirname, '../../apps/desktop/electron-builder.config.cjs')

// Exercise the real electron-builder configuration in a fresh process for
// each variant. A reused require cache would conceal environment regressions.
function inspectConfig(variant, env = {}) {
  const program = `
    const config = require(process.argv[1])
    process.stdout.write(JSON.stringify({
      publish: config.publish,
      macPublish: config.mac.publish,
      dmgTitle: config.dmg.title,
      synopsis: config.linux.synopsis,
      appId: config.appId
    }))
  `
  const result = execFileSync(process.execPath, ['-e', program, configPath], {
    encoding: 'utf8',
    env: {
      ...process.env,
      HERMES_DESKTOP_VARIANT: variant,
      HERMES_PAYLOAD_TAG: '',
      HERMES_BUILD_COMMIT: '',
      // Even stale or malicious inherited CI configuration must not inject a
      // publisher while the Zeus release channel is unapproved.
      GITHUB_REPOSITORY: 'NousResearch/hermes-agent',
      CLOUDFLARE_R2_PUBLIC_URL: 'https://upstream.invalid/releases',
      ...env
    },
    timeout: 15_000
  })
  return JSON.parse(result)
}

for (const variant of ['', 'light', 'bundled', 'store']) {
  test(`ZEUS-001: ${variant || 'stable'} package has no unverified native update feed`, () => {
    const config = inspectConfig(variant)
    assert.equal(config.publish, null)
    assert.equal(config.macPublish, null)
    assert.match(config.dmgTitle, /^Zeus (Agent|Light|Agent Bundled) Installer$/)
    assert.match(config.synopsis, /Zeus Agent/)
    assert.doesNotMatch(config.synopsis, /Hermes Agent/)
    assert.match(config.appId, /^com\.kayzenroot\.zeus-/)
  })
}

test('ZEUS-001: release-like environment does not enable a publisher', () => {
  const config = inspectConfig('', { HERMES_PAYLOAD_TAG: 'v1.2.3' })
  assert.equal(config.publish, null)
  assert.equal(config.macPublish, null)
})

test('ZEUS-001: Electron connection updaters are gated before any remote I/O', () => {
  const fs = require('node:fs')
  const main = fs.readFileSync(path.resolve(__dirname, '../../apps/desktop/electron/main.ts'), 'utf8')
  const managedStart = main.indexOf('async function requestManagedSshUpdate(rawId) {')
  const managedEnd = main.indexOf("ipcMain.handle('hermes:connections:update-managed'", managedStart)
  assert.ok(managedStart >= 0 && managedEnd > managedStart, 'managed SSH updater handler missing')
  const managed = main.slice(managedStart, managedEnd)
  const denySsh = managed.indexOf('if (!ZEUS_NATIVE_UPDATES_APPROVED)')
  const sshRegistry = managed.indexOf('readDesktopConnectionsRegistry()')
  assert.ok(denySsh >= 0 && sshRegistry > denySsh, 'managed SSH update must refuse before registry access')
  assert.match(managed.slice(denySsh, sshRegistry), /refusedManagedSshUpdate\([\s\S]*ZEUS_UPDATE_BLOCKED_MESSAGE/)

  const batchStart = main.indexOf("ipcMain.handle('hermes:connections:update-all'")
  const batchEnd = main.indexOf('// Convenience wrappers around the bearer-aware descriptor', batchStart)
  assert.ok(batchStart >= 0 && batchEnd > batchStart, 'connection batch updater handler missing')
  const batch = main.slice(batchStart, batchEnd)
  const denyBatch = batch.indexOf('if (!ZEUS_NATIVE_UPDATES_APPROVED)')
  const batchRegistry = batch.indexOf('readDesktopConnectionsRegistry()')
  assert.ok(denyBatch >= 0 && batchRegistry > denyBatch, 'update-all must refuse before any registered connection I/O')
  assert.match(batch.slice(denyBatch, batchRegistry), /error: 'zeus-release-unapproved'/)
  assert.match(batch.slice(denyBatch, batchRegistry), /results: \[\]/)
})
