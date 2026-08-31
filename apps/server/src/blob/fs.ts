import { createReadStream } from 'node:fs'
import { mkdir, rm, stat, writeFile } from 'node:fs/promises'
import { dirname, join, resolve, sep } from 'node:path'
import { Readable } from 'node:stream'
import { pipeline } from 'node:stream/promises'
import { createWriteStream } from 'node:fs'
import type { BlobStore } from './types.js'

/**
 * Files on disk, for development without an Azure account.
 *
 * `url()` returns a path back through our own API rather than a filesystem
 * path, so the browser fetches it exactly the way it will fetch a SAS url in
 * production and the client code has no branch in it.
 */
export class FsBlobStore implements BlobStore {
  private readonly root: string

  constructor(base: string, private readonly container: string, private readonly mount = '/api/blob') {
    this.root = resolve(base, container)
  }

  get description(): string {
    return this.root
  }

  /** a key is untrusted input; never let one climb out of its container */
  private path(key: string): string {
    const p = resolve(this.root, key)
    if (p !== this.root && !p.startsWith(this.root + sep)) throw new Error('key escapes the store')
    return p
  }

  async put(key: string, body: Buffer | Readable, _mime: string): Promise<void> {
    const p = this.path(key)
    await mkdir(dirname(p), { recursive: true })
    if (Buffer.isBuffer(body)) await writeFile(p, body)
    else await pipeline(body, createWriteStream(p))
  }

  async url(key: string): Promise<string> {
    // the api serves it, so the shape matches a SAS url and nothing downstream
    // has to know which store it got
    return `${this.mount}/${this.container}/${key}`
  }

  async get(key: string): Promise<Readable | null> {
    try {
      await stat(this.path(key))
      return createReadStream(this.path(key))
    } catch {
      return null
    }
  }

  async delete(key: string): Promise<void> {
    await rm(this.path(key), { force: true })
  }

  async exists(key: string): Promise<boolean> {
    try {
      await stat(this.path(key))
      return true
    } catch {
      return false
    }
  }
}

export const fsBlobRoot = (base: string, container: string) => join(base, container)
