import { describe, expect, it } from 'vitest'

import {
  ZEUS_NATIVE_UPDATES_APPROVED,
  ZEUS_UPDATE_BLOCKED_MESSAGE,
  zeusUpdatesBlockedApply,
  zeusUpdatesBlockedStatus
} from './zeus-update-policy'

describe('ZEUS-001 native update release admission', () => {
  it('fails closed until Zeus signatures, release feed and recovery are verified', () => {
    expect(ZEUS_NATIVE_UPDATES_APPROVED).toBe(false)
    const result = zeusUpdatesBlockedStatus()
    expect(result).toMatchObject({
      supported: false,
      mechanism: 'external',
      reason: 'zeus-release-unapproved',
      updateAvailable: false,
      message: ZEUS_UPDATE_BLOCKED_MESSAGE
    })
    expect(result.fetchedAt).toBeTypeOf('number')
  })

  it('refuses apply without requesting a handoff or updater process', () => {
    expect(zeusUpdatesBlockedApply()).toEqual({
      ok: false,
      mechanism: 'external',
      error: 'zeus-release-unapproved',
      message: ZEUS_UPDATE_BLOCKED_MESSAGE
    })
  })
})
