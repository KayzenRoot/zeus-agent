/**
 * ZEUS-001 bootstrap admission is independent of auto-update admission.
 *
 * A first-run or repair installer cannot safely use the inherited Hermes
 * download or Windows updater handoff. Leave this source-controlled,
 * fail-closed until Zeus-owned provenance, signatures, rollback, install
 * isolation and native test evidence are independently approved.
 * Never read an environment variable to authorize these operations.
 */
export const ZEUS_DESKTOP_BOOTSTRAP_APPROVED = false
export const ZEUS_DESKTOP_BOOTSTRAP_DENIAL = 'zeus-release-unapproved'

export function isZeusDesktopBootstrapApproved(): boolean {
  return ZEUS_DESKTOP_BOOTSTRAP_APPROVED
}
