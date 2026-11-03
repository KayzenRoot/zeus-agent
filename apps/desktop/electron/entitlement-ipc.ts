/**
 * entitlement-ipc.ts
 *
 * IPC registration for the Zeus subscription. Kept out of main.ts so the
 * facade does not grow for every entitlement handler.
 */

import { ipcMain } from 'electron'

import { activateWithCode, activationUrl, readEntitlementStatus } from './entitlement'

interface Options {
  hermesHome: string
  openExternal: (url: string) => Promise<{ ok?: boolean }>
}

export function registerEntitlementIpc({ hermesHome, openExternal }: Options): void {
  ipcMain.handle('zeus:entitlement:status', () => readEntitlementStatus(hermesHome))

  ipcMain.handle('zeus:entitlement:activate', async (_event, code: unknown) => {
    if (typeof code !== 'string' || code.length < 16) {
      throw new Error('Invalid activation code')
    }

    return activateWithCode(hermesHome, code)
  })

  ipcMain.handle('zeus:entitlement:open', async () => {
    const result = await openExternal(activationUrl(hermesHome))

    if (result.ok === false) {
      throw new Error('Could not open the activation page')
    }
  })
}
