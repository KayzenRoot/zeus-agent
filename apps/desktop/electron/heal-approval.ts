/**
 * heal-approval.ts
 *
 * Native desktop approval for `zeus heal` proposals. The agent may only write a proposal; this
 * watcher turns a pending proposal into a modal owned by the main window, and only an explicit
 * "Aprovar" click runs the CLI through its existing TTY + APPROVE gate. Closing the dialog is a
 * rejection, so there is no implicit approval path.
 */

import fs from 'node:fs'
import path from 'node:path'

import type { BrowserWindow, MessageBoxOptions } from 'electron'
import nodePty from 'node-pty'

const PROPOSAL_ID = /^[0-9a-f]{16}$/
const APPROVAL_PROMPT = 'Type APPROVE to continue:'
const RUN_TIMEOUT_MS = 30_000
const DEFAULT_INTERVAL_MS = 2_000

export interface HealProposal {
  id: string
  action: string
  reason: string
  rollback?: string
  expires_at: number
  status: string
  findings?: Array<{ code?: string; severity?: string; summary?: string }>
}

export interface HealBackend {
  command: string | null
  args: string[]
  env: NodeJS.ProcessEnv
  root?: string
  shell?: boolean
}

export interface HealRunResult {
  code: number
  output: string
}

export interface HealApprovalDeps {
  home: string
  getWindow: () => BrowserWindow | null
  resolveBackend: () => Promise<HealBackend | null>
  now?: () => number
  log?: (line: string) => void
  showDialog?: (window: BrowserWindow, options: MessageBoxOptions) => Promise<{ response: number }>
  runCommand?: (backend: HealBackend, args: string[], stdin?: string[]) => Promise<HealRunResult>
}

export function parsePendingProposals(
  payloads: Array<{ file: string; raw: string }>,
  now: number
): HealProposal[] {
  const proposals: HealProposal[] = []

  for (const { file, raw } of payloads) {
    let parsed: unknown

    try {
      parsed = JSON.parse(raw.replace(/^\uFEFF/, ''))
    } catch {
      continue
    }

    if (!parsed || typeof parsed !== 'object') {
      continue
    }

    const candidate = parsed as Record<string, unknown>
    const id = typeof candidate.id === 'string' ? candidate.id : ''

    if (!PROPOSAL_ID.test(id) || path.basename(file) !== `${id}.json`) {
      continue
    }

    if (
      candidate.status !== 'pending' ||
      typeof candidate.action !== 'string' ||
      typeof candidate.reason !== 'string' ||
      typeof candidate.expires_at !== 'number' ||
      candidate.expires_at <= now
    ) {
      continue
    }

    proposals.push(candidate as unknown as HealProposal)
  }

  return proposals.sort((a, b) => a.expires_at - b.expires_at)
}

export function readPendingProposals(home: string, now: number): HealProposal[] {
  const directory = path.join(home, 'heal-proposals')

  let names: string[]

  try {
    names = fs.readdirSync(directory)
  } catch {
    return []
  }

  const payloads = names
    .filter(name => name.endsWith('.json'))
    .flatMap(file => {
      try {
        return [{ file, raw: fs.readFileSync(path.join(directory, file), 'utf8') }]
      } catch {
        return []
      }
    })

  return parsePendingProposals(payloads, now)
}

export function proposalDialogCopy(proposal: HealProposal): { message: string; detail: string } {
  const signals = (proposal.findings ?? [])
    .map(finding => finding.summary || finding.code)
    .filter((value): value is string => Boolean(value))
    .slice(0, 3)

  const rollback =
    proposal.rollback?.trim() || 'Nenhum rollback automático disponível para esta ação.'

  const expires = new Date(proposal.expires_at * 1000).toLocaleTimeString('pt-BR', {
    hour: '2-digit',
    minute: '2-digit'
  })

  return {
    message: `Zeus propõe: ${proposal.action}`,
    detail: [
      `Motivo: ${proposal.reason}`,
      ...(signals.length ? [`Sinais: ${signals.join(' · ')}`] : []),
      `Rollback: ${rollback}`,
      `Proposta ${proposal.id.slice(0, 8)} · expira às ${expires}`,
      'Fechar ou cancelar rejeita a proposta; nada será executado.'
    ].join('\n')
  }
}

export async function handleHealProposal(
  proposal: HealProposal,
  deps: HealApprovalDeps
): Promise<'approved' | 'rejected' | 'skipped' | 'failed'> {
  const log = deps.log ?? (() => undefined)
  const window = deps.getWindow()

  if (!window || window.isDestroyed() || !window.isVisible()) {
    return 'skipped'
  }

  const copy = proposalDialogCopy(proposal)

  const showDialog =
    deps.showDialog ??
    ((target, options) =>
      import('electron').then(({ dialog }) => dialog.showMessageBox(target, options)))

  const { response } = await showDialog(window, {
    type: 'warning',
    buttons: ['Aprovar', 'Rejeitar'],
    defaultId: 1,
    cancelId: 1,
    noLink: true,
    title: 'Zeus — correção proposta',
    message: copy.message,
    detail: copy.detail
  })

  const approved = response === 0
  const backend = await deps.resolveBackend()

  if (!backend?.command) {
    log(`[heal] ${approved ? 'approval' : 'rejection'} could not run: no local Zeus backend`)

    return 'failed'
  }

  const runCommand = deps.runCommand ?? runHealCommand
  const args = [...backend.args, 'heal', approved ? 'approve' : 'reject', proposal.id]

  try {
    const result = await runCommand(backend, args, approved ? ['APPROVE'] : undefined)
    log(
      `[heal] ${approved ? 'approve' : 'reject'} ${proposal.id} (${proposal.action}) exited ${result.code}`
    )

    if (approved && result.code !== 0) {
      log(`[heal] approval output: ${result.output.slice(-500)}`)

      return 'failed'
    }

    return approved ? 'approved' : 'rejected'
  } catch (error) {
    log(`[heal] ${approved ? 'approve' : 'reject'} ${proposal.id} failed: ${String(error)}`)

    return 'failed'
  }
}

export function startHealApprovalWatcher(
  deps: HealApprovalDeps & { intervalMs?: number }
): () => void {
  const now = deps.now ?? (() => Math.floor(Date.now() / 1000))
  const log = deps.log ?? (() => undefined)
  const shown = new Set<string>()
  let stopped = false
  let running = false

  const tick = async () => {
    if (stopped || running) {
      return
    }

    const proposal = readPendingProposals(deps.home, now()).find(item => !shown.has(item.id))

    if (!proposal) {
      return
    }

    running = true
    shown.add(proposal.id)

    try {
      const result = await handleHealProposal(proposal, deps)

      if (result === 'skipped') {
        shown.delete(proposal.id)
      }
    } finally {
      running = false
    }
  }

  const timer = setInterval(() => void tick(), deps.intervalMs ?? DEFAULT_INTERVAL_MS)
  timer.unref?.()
  void tick()

  return () => {
    stopped = true
    clearInterval(timer)
  }
}

function windowsQuote(value: string): string {
  return `"${value.replace(/"/g, '""')}"`
}

export function runHealCommand(
  backend: HealBackend,
  args: string[],
  stdin?: string[]
): Promise<HealRunResult> {
  if (!backend.command) {
    return Promise.reject(new Error('no backend command'))
  }

  const command = backend.command.replace(/^"|"$/g, '')
  const batch = process.platform === 'win32' && /\.(cmd|bat)$/i.test(command)
  const spawnCommand = batch ? process.env.ComSpec || 'cmd.exe' : command

  const spawnArgs = batch
    ? ['/d', '/s', '/c', `${windowsQuote(command)} ${args.map(windowsQuote).join(' ')}`]
    : args

  return new Promise((resolve, reject) => {
    let output = ''
    let sent = false
    const expectPrompt = Boolean(stdin?.length)

    const env = Object.fromEntries(
      Object.entries({ ...process.env, ...backend.env }).filter(
        (entry): entry is [string, string] => typeof entry[1] === 'string'
      )
    )

    const child = nodePty.spawn(spawnCommand, spawnArgs, {
      name: 'xterm-color',
      cols: 120,
      rows: 30,
      cwd: backend.root || process.cwd(),
      env
    })

    const timer = setTimeout(() => {
      output += '\n[heal] timed out waiting for the approval prompt'
      child.kill()

      if (expectPrompt && !sent) {
        reject(new Error('approval prompt did not appear'))
      } else {
        resolve({ code: -1, output })
      }
    }, RUN_TIMEOUT_MS)

    child.onData(data => {
      output += data

      if (expectPrompt && !sent && output.includes(APPROVAL_PROMPT)) {
        sent = true
        child.write(`${stdin?.[0] ?? ''}\r`)
      }
    })
    child.onExit(({ exitCode }) => {
      clearTimeout(timer)
      resolve({ code: exitCode, output })
    })
  })
}
