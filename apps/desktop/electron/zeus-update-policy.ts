/**
 * ZEUS-001 release gate for the local desktop updater.
 *
 * The Hermes updater is not a trusted Zeus distribution channel. Neither
 * inherited environment variables nor an existing install stamp may enable
 * check, download, handoff or OS update from the in-app UI until the publisher,
 * feed, signature verification and rollback plan have been independently
 * audited. The gate is intentionally unconditional, including in development.
 *
 * This does not intercept OS-managed updates of packages installed previously:
 * such packages must never be distributed before their native feeds are vetted.
 */
import type { UpdaterApplyResultWire, UpdaterStatusWire } from './updater'

export const ZEUS_NATIVE_UPDATES_APPROVED = false

export const ZEUS_UPDATE_BLOCKED_MESSAGE =
  'Zeus updates are unavailable until a signed Zeus release channel is approved. ' +
  'Review updates in KayzenRoot/zeus-agent; do not use the Hermes updater.'

export function zeusUpdatesBlockedStatus(): UpdaterStatusWire {
  return {
    supported: false,
    mechanism: 'external',
    reason: 'zeus-release-unapproved',
    updateAvailable: false,
    message: ZEUS_UPDATE_BLOCKED_MESSAGE,
    fetchedAt: Date.now()
  }
}

export function zeusUpdatesBlockedApply(): UpdaterApplyResultWire {
  return {
    ok: false,
    mechanism: 'external',
    error: 'zeus-release-unapproved',
    message: ZEUS_UPDATE_BLOCKED_MESSAGE
  }
}
