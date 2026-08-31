import type { Readable } from 'node:stream'

/**
 * Where files live: uploaded images and rendered mp4s.
 *
 * The same seam DocStore is for films. The API never learns whether it is
 * talking to a directory or to Azure Blob Storage, so the local implementation
 * is a real development mode rather than a stub, and swapping is one class.
 *
 * Nothing is ever public. A browser reaches a file through a short-lived url
 * this mints, so revoking access is a matter of not minting another one.
 */
export interface BlobStore {
  readonly description: string
  put(key: string, body: Buffer | Readable, mime: string): Promise<void>
  /** a url the browser can fetch directly, valid for `ttl` seconds */
  url(key: string, ttl?: number): Promise<string>
  get(key: string): Promise<Readable | null>
  delete(key: string): Promise<void>
  exists(key: string): Promise<boolean>
}

/** two containers, kept apart so a lifecycle rule can expire one and not the other */
export const ASSETS = 'assets'
export const EXPORTS = 'exports'

/** keys are always workspace-scoped, so a listing can never cross a tenant */
export const assetKey = (workspace: string, name: string) => `${workspace}/${name}`
export const exportKey = (workspace: string, id: string) => `${workspace}/${id}.mp4`
