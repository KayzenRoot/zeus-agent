/**
 * backend-identity.ts
 *
 * Process-start-marker identity checks used by the orphan-reaper paths. Extracted from main.ts so
 * the facade stays inside its file-lines ratchet.
 */

import { isPidOnlyStartMarker, processStartMarker, REAP_PROBE_TIMEOUT_MS } from './backend-claim'

interface ProcessIdentity {
  pid: number
  startMarker: unknown
}

export async function processIdentityMatches(
  identity: ProcessIdentity,
  timeoutMs: number = 30_000
): Promise<boolean | undefined> {
  // Degraded PID-only identity (#93608): the start-marker probe failed while
  // the child was verifiably alive, so only PID liveness can be checked here.
  // backendIdentityMatches layers the command-line check on top before
  // anything destructive relies on the answer.
  if (isPidOnlyStartMarker(identity.startMarker)) {
    try {
      process.kill(identity.pid, 0)

      return true
    } catch (error) {
      const code = (error as NodeJS.ErrnoException | null)?.code

      return code === 'ESRCH' || code === 'ENOENT' ? false : code === 'EPERM' ? true : undefined
    }
  }

  try {
    return (await processStartMarker(identity.pid, timeoutMs)) === identity.startMarker
  } catch (error) {
    const code = (error as NodeJS.ErrnoException | null)?.code

    return code === 'ENOENT' || code === 'ESRCH' ? false : undefined
  }
}

// True when the recorded parent Electron is still running (same PID AND start
// marker); false when it is gone or its PID was reused; undefined when the
// ownership record predates parent tracking. Undefined deliberately falls back
// to the pre-parent reap behaviour so legacy orphan cleanup keeps working.
export async function backendParentMatches(entry: {
  parentPid?: number
  parentStartMarker?: string
}): Promise<boolean | undefined> {
  if (
    !Number.isInteger(entry.parentPid) ||
    typeof entry.parentStartMarker !== 'string' ||
    !entry.parentStartMarker
  ) {
    return undefined
  }

  try {
    return (
      (await processStartMarker(entry.parentPid as number, REAP_PROBE_TIMEOUT_MS)) ===
      entry.parentStartMarker
    )
  } catch (error) {
    const code = (error as NodeJS.ErrnoException | null)?.code

    return code === 'ENOENT' || code === 'ESRCH' ? false : undefined
  }
}
