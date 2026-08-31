import {
  BlobSASPermissions, BlobServiceClient, StorageSharedKeyCredential,
  generateBlobSASQueryParameters,
} from '@azure/storage-blob'
import type { ContainerClient } from '@azure/storage-blob'
import type { Readable } from 'node:stream'
import type { BlobStore } from './types.js'

/**
 * Azure Blob Storage.
 *
 * Verified against Azurite, Microsoft's own emulator, which docker-compose
 * runs locally. That matters: a storage layer first exercised in production is
 * a storage layer whose SAS signing you find out about at the worst moment.
 *
 * Containers are private. A browser is handed a short-lived SAS url instead,
 * which needs the account key, so this only works with a connection string
 * rather than a managed identity. When that changes, the signing moves to a
 * user delegation key and nothing else here does.
 */
export class AzureBlobStore implements BlobStore {
  private readonly container: ContainerClient
  private readonly credential: StorageSharedKeyCredential | null
  private ready: Promise<unknown> | null = null

  constructor(connection: string, private readonly name: string) {
    const service = BlobServiceClient.fromConnectionString(connection)
    this.container = service.getContainerClient(name)
    // the credential is only needed to SIGN urls; reads and writes go through
    // the service client either way
    const cred = (service as unknown as { credential?: unknown }).credential
    this.credential = cred instanceof StorageSharedKeyCredential ? cred : null
  }

  get description(): string {
    return `azure blob ${this.name}`
  }

  /** create the container once per process rather than on every write */
  private ensure(): Promise<unknown> {
    this.ready ??= this.container.createIfNotExists()
    return this.ready
  }

  async put(key: string, body: Buffer | Readable, mime: string): Promise<void> {
    await this.ensure()
    const blob = this.container.getBlockBlobClient(key)
    const headers = { blobHTTPHeaders: { blobContentType: mime } }
    if (Buffer.isBuffer(body)) await blob.uploadData(body, headers)
    else await blob.uploadStream(body, undefined, undefined, headers)
  }

  async url(key: string, ttl = 600): Promise<string> {
    await this.ensure()
    const blob = this.container.getBlockBlobClient(key)
    if (!this.credential) return blob.url
    const sas = generateBlobSASQueryParameters({
      containerName: this.name,
      blobName: key,
      permissions: BlobSASPermissions.parse('r'),
      // a little slack so a clock skew between our box and azure's does not
      // hand out a url that is somehow not valid yet
      startsOn: new Date(Date.now() - 60_000),
      expiresOn: new Date(Date.now() + ttl * 1000),
    }, this.credential)
    return `${blob.url}?${sas}`
  }

  async get(key: string): Promise<Readable | null> {
    await this.ensure()
    try {
      const res = await this.container.getBlockBlobClient(key).download()
      return (res.readableStreamBody as Readable) ?? null
    } catch {
      return null
    }
  }

  async delete(key: string): Promise<void> {
    await this.ensure()
    await this.container.getBlockBlobClient(key).deleteIfExists()
  }

  async exists(key: string): Promise<boolean> {
    await this.ensure()
    return await this.container.getBlockBlobClient(key).exists()
  }
}
