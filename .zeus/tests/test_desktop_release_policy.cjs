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
