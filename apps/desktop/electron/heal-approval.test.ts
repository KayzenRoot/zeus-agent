import assert from 'node:assert/strict'
import { mkdirSync, mkdtempSync, rmSync, writeFileSync } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'

import { afterEach, test, vi } from 'vitest'

const { ptySpawn } = vi.hoisted(() => ({ ptySpawn: vi.fn() }))

vi.mock('node-pty', () => ({ default: { spawn: ptySpawn } }))

import {
  handleHealProposal,
  type HealBackend,
  type HealProposal,
  parsePendingProposals,
  proposalDialogCopy,
  readPendingProposals,
  runHealCommand
} from './heal-approval'

const homes: string[] = []

function proposal(overrides: Partial<HealProposal> = {}): HealProposal {
  return {
    id: '0123456789abcdef',
    action: 'restart-gateway',
    reason: 'The local gateway is not running.',
    rollback: 'Run `zeus gateway restart` again.',
    expires_at: 2_000,
    status: 'pending',
    findings: [{ code: 'gateway-not-running', severity: 'medium', summary: 'Gateway offline' }],
    ...overrides
  }
}

function homeWith(payloads: Record<string, unknown>): string {
  const home = mkdtempSync(join(tmpdir(), 'zeus-heal-'))
  homes.push(home)
  const directory = join(home, 'heal-proposals')
  mkdirSync(directory)

  for (const [file, payload] of Object.entries(payloads)) {
    writeFileSync(join(directory, file), JSON.stringify(payload), 'utf8')
  }

  return home
}

afterEach(() => {
  ptySpawn.mockReset()

  for (const home of homes.splice(0)) {
    rmSync(home, { force: true, recursive: true })
  }
})

test('reads only valid, pending, unexpired proposals', () => {
  const valid = proposal()

  const home = homeWith({
    [`${valid.id}.json`]: valid,
    'fedcba9876543210.json': proposal({ id: 'fedcba9876543210', expires_at: 1_000 }),
    'aaaaaaaaaaaaaaaa.json': proposal({ id: 'aaaaaaaaaaaaaaaa', status: 'rejected' }),
    'wrong-name.json': proposal({ id: 'bbbbbbbbbbbbbbbb' })
  })

  const pending = readPendingProposals(home, 1_500)

  assert.deepEqual(
    pending.map(item => item.id),
    [valid.id]
  )
})

test('rejects tampered JSON and wrong filenames', () => {
  const proposals = parsePendingProposals(
    [
      { file: '0123456789abcdef.json', raw: '{not-json' },
      { file: 'other.json', raw: JSON.stringify(proposal()) },
      { file: '0123456789abcdef.json', raw: `\uFEFF${JSON.stringify(proposal())}` }
    ],
    1_500
  )

  assert.equal(proposals.length, 1)
  assert.equal(proposals[0].id, '0123456789abcdef')
})

test('dialog copy carries the reason, signals and rollback', () => {
  const copy = proposalDialogCopy(proposal())

  assert.match(copy.message, /restart-gateway/)
  assert.match(copy.detail, /gateway is not running/)
  assert.match(copy.detail, /Gateway offline/)
  assert.match(copy.detail, /Rollback:/)
  assert.match(copy.detail, /Fechar ou cancelar rejeita/)
})

test('approving in the app runs the same TTY approval path', async () => {
  const calls: Array<{ args: string[]; stdin?: string[] }> = []

  const result = await handleHealProposal(proposal(), {
    home: '/tmp/does-not-matter',
    getWindow: () => ({ isDestroyed: () => false, isVisible: () => true }) as never,
    resolveBackend: async () => ({
      command: '/opt/zeus/bin/zeus',
      args: ['--profile', 'default'],
      env: {},
      root: '/opt/zeus'
    }),
    showDialog: async () => ({ response: 0 }),
    runCommand: async (_backend, args, stdin) => {
      calls.push({ args, stdin })

      return { code: 0, output: 'executed' }
    }
  })

  assert.equal(result, 'approved')
  assert.deepEqual(calls, [
    {
      args: ['--profile', 'default', 'heal', 'approve', '0123456789abcdef'],
      stdin: ['APPROVE']
    }
  ])
})

test('closing or rejecting the dialog never approves', async () => {
  const calls: string[][] = []

  const result = await handleHealProposal(proposal(), {
    home: '/tmp/does-not-matter',
    getWindow: () => ({ isDestroyed: () => false, isVisible: () => true }) as never,
    resolveBackend: async () => ({ command: '/opt/zeus/bin/zeus', args: [], env: {} }),
    showDialog: async () => ({ response: 1 }),
    runCommand: async (_backend, args) => {
      calls.push(args)

      return { code: 0, output: 'rejected' }
    }
  })

  assert.equal(result, 'rejected')
  assert.deepEqual(calls, [['heal', 'reject', '0123456789abcdef']])
})

test('a hidden window or missing backend leaves the proposal untouched', async () => {
  const skipped = await handleHealProposal(proposal(), {
    home: '/tmp/does-not-matter',
    getWindow: () => null,
    resolveBackend: async () => ({ command: '/opt/zeus/bin/zeus', args: [], env: {} }),
    runCommand: async () => ({ code: 0, output: '' })
  })

  assert.equal(skipped, 'skipped')

  const failed = await handleHealProposal(proposal(), {
    home: '/tmp/does-not-matter',
    getWindow: () => ({ isDestroyed: () => false, isVisible: () => true }) as never,
    resolveBackend: async () => null,
    showDialog: async () => ({ response: 0 }),
    runCommand: async () => ({ code: 0, output: '' })
  })

  assert.equal(failed, 'failed')
})

test('the PTY runner writes APPROVE only after the CLI prompt appears', async () => {
  const handlers: Record<string, (value: unknown) => void> = {}
  const write = vi.fn()
  const kill = vi.fn()
  ptySpawn.mockReturnValue({
    kill,
    onData: (handler: (value: string) => void) => {
      handlers.data = handler as (value: unknown) => void
    },
    onExit: (handler: (value: { exitCode: number }) => void) => {
      handlers.exit = handler as (value: unknown) => void
    },
    write
  })
  const backend: HealBackend = { command: '/opt/zeus/bin/zeus', args: [], env: {}, root: '/opt/zeus' }

  const pending = runHealCommand(backend, ['heal', 'approve', '0123456789abcdef'], ['APPROVE'])
  handlers.data('Type APPROVE to continue: ')
  assert.deepEqual(write.mock.calls, [['APPROVE\r']])
  handlers.exit({ exitCode: 0 })

  const result = await pending
  assert.equal(result.code, 0)
  assert.equal(kill.mock.calls.length, 0)
})
