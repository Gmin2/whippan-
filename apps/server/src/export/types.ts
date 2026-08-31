export type JobStatus = 'queued' | 'running' | 'done' | 'failed' | 'cancelled'

export interface ExportOptions {
  /** frames per second; the document's own fps when omitted */
  fps?: number
  /** 1 renders at document size, 2 supersamples to 4K from a 1080p doc */
  supersample?: 1 | 2
}

export interface Job {
  id: string
  slug: string
  /** whose render this is; keys are workspace-scoped so tenants cannot collide */
  workspace?: string
  status: JobStatus
  options: Required<ExportOptions>
  queuedAt: number
  startedAt?: number
  finishedAt?: number
  /** bytes of the finished file */
  bytes?: number
  /** what the renderer said, kept for diagnosis when a job fails */
  log: string[]
  error?: string
  /** frames written so far, parsed out of the renderer's own output */
  frames?: number
  totalFrames?: number
}

/** what a client sees; the file path never leaves the server */
export interface JobView extends Omit<Job, 'log'> {
  log: string
  /** 0..1, or null when the renderer has not reported yet */
  progress: number | null
  downloadUrl?: string
}
