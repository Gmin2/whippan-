import { spawn } from 'node:child_process'
import type { ChildProcess } from 'node:child_process'
import { access, mkdir, mkdtemp, rm, stat, writeFile, readdir } from 'node:fs/promises'
import { constants } from 'node:fs'
import { tmpdir } from 'node:os'
import { join } from 'node:path'
import { randomUUID } from 'node:crypto'
import { createReadStream } from 'node:fs'
import type { Job, JobStatus, JobView, ExportOptions } from './types.js'
import type { BlobStore } from '../blob/types.js'
import { exportKey } from '../blob/types.js'

export interface RunnerConfig {
  /** the compiled native renderer */
  bin: string
  /** the renderer resolves fonts relative to its working directory */
  cwd: string
  /** where finished mp4s land */
  outDir: string
  /** how many renders may run at once; rendering is CPU-bound so this is low */
  concurrency: number
  /** a runaway render is killed after this long */
  timeoutMs: number
  /** finished artifacts older than this are swept */
  retentionMs: number
}

/** the renderer's own summary line: "out.mp4: 834 frames at 1920x1080 in 4.1s" */
const SUMMARY = /(\d+)\s+frames\s+at\s+(\d+)x(\d+)/
/** the renderer emits "progress 120/834" as it walks the timeline */
const PROGRESS = /^progress\s+(\d+)\/(\d+)/

export class ExportQueue {
  private jobs = new Map<string, Job>()
  private running = new Map<string, { child: ChildProcess; dir: string }>()
  private waiting: string[] = []
  private files = new Map<string, string>()
  private sweeper?: ReturnType<typeof setInterval>

  /**
   * The finished mp4 goes to blob storage rather than staying on this box.
   *
   * Without it the file only exists on the instance that rendered it, which is
   * fine on one machine and wrong the moment there are two, or one that scales
   * to zero. `blobs` stays optional so a local run with no storage configured
   * still works off disk.
   */
  constructor(
    private readonly config: RunnerConfig,
    private readonly blobs?: BlobStore,
  ) {}

  /** where a finished render lives in blob storage, once it is uploaded */
  private keys = new Map<string, string>()

  keyOf(id: string): string | null {
    const j = this.jobs.get(id)
    return j?.status === 'done' ? this.keys.get(id) ?? null : null
  }

  /** fail fast and legibly if the toolchain is not actually present */
  async preflight(): Promise<{ ok: boolean; reason?: string }> {
    try {
      await access(this.config.bin, constants.X_OK)
    } catch {
      return {
        ok: false,
        reason: `renderer not found or not executable at ${this.config.bin}. `
          + 'build it with: cargo build --release -p whippan-engine --bin export',
      }
    }
    const hasFfmpeg = await new Promise<boolean>(res => {
      const probe = spawn('ffmpeg', ['-version'], { stdio: 'ignore' })
      probe.on('error', () => res(false))
      probe.on('close', code => res(code === 0))
    })
    if (!hasFfmpeg) return { ok: false, reason: 'ffmpeg is not on PATH' }
    return { ok: true }
  }

  start(): void {
    // sweep finished artifacts so a long-lived server does not fill its disk
    this.sweeper ??= setInterval(() => void this.sweep(), 60_000)
    this.sweeper.unref?.()
  }

  async stop(): Promise<void> {
    if (this.sweeper) clearInterval(this.sweeper)
    for (const id of [...this.running.keys()]) this.cancel(id, 'server shutting down')
  }

  list(): JobView[] {
    return [...this.jobs.values()]
      .sort((a, b) => b.queuedAt - a.queuedAt)
      .map(j => this.view(j))
  }

  get(id: string): JobView | null {
    const j = this.jobs.get(id)
    return j ? this.view(j) : null
  }

  fileOf(id: string): string | null {
    const j = this.jobs.get(id)
    return j?.status === 'done' ? this.files.get(id) ?? null : null
  }

  private view(j: Job): JobView {
    const progress = j.status === 'done' ? 1
      : j.totalFrames && j.frames ? Math.min(0.99, j.frames / j.totalFrames)
      : null
    return {
      ...j,
      log: j.log.join('\n'),
      progress,
      downloadUrl: j.status === 'done' ? `/api/exports/${j.id}/file` : undefined,
    }
  }

  enqueue(
    slug: string, stage: unknown, anim: unknown, opts: ExportOptions, workspace?: string,
  ): Job {
    const id = randomUUID()
    const job: Job = {
      id,
      slug,
      workspace,
      status: 'queued',
      options: {
        fps: opts.fps ?? 30,
        supersample: opts.supersample === 2 ? 2 : 1,
      },
      queuedAt: Date.now(),
      log: [],
    }
    this.jobs.set(id, job)
    this.waiting.push(id)
    // hold the payload only until the job actually starts
    this.payloads.set(id, { stage, anim })
    queueMicrotask(() => void this.pump())
    return job
  }

  private payloads = new Map<string, { stage: unknown; anim: unknown }>()

  cancel(id: string, reason = 'cancelled'): boolean {
    const job = this.jobs.get(id)
    if (!job) return false
    if (job.status === 'queued') {
      this.waiting = this.waiting.filter(w => w !== id)
      this.payloads.delete(id)
      this.finish(job, 'cancelled', reason)
      return true
    }
    const live = this.running.get(id)
    if (!live) return false
    // mark it before killing: the run loop reads this to tell a cancellation
    // apart from a genuine failure, and to bin the half-written file
    job.status = 'cancelled'
    job.error = reason
    ExportQueue.signal(live.child.pid, 'SIGTERM')
    setTimeout(() => ExportQueue.signal(live.child.pid, 'SIGKILL'), 2000).unref?.()
    return true
  }

  /** signal the whole process group, so ffmpeg goes down with the renderer */
  private static signal(pid: number | undefined, sig: NodeJS.Signals): void {
    if (!pid) return
    try {
      process.kill(-pid, sig)
    } catch {
      // no group (or already gone): fall back to the process itself
      try { process.kill(pid, sig) } catch { /* already exited */ }
    }
  }

  private finish(job: Job, status: JobStatus, error?: string) {
    job.status = status
    job.finishedAt = Date.now()
    if (error) job.error = error
  }

  private async pump(): Promise<void> {
    while (this.running.size < this.config.concurrency && this.waiting.length) {
      const id = this.waiting.shift()!
      const job = this.jobs.get(id)
      if (!job || job.status !== 'queued') continue
      void this.run(job)
    }
  }

  private async run(job: Job): Promise<void> {
    const payload = this.payloads.get(job.id)
    this.payloads.delete(job.id)
    if (!payload) return this.finish(job, 'failed', 'payload missing')

    job.status = 'running'
    job.startedAt = Date.now()

    let dir: string | undefined
    try {
      await mkdir(this.config.outDir, { recursive: true })
      dir = await mkdtemp(join(tmpdir(), 'whippan-export-'))
      const stagePath = join(dir, 'stage.json')
      const animPath = join(dir, 'anim.json')
      const outPath = join(this.config.outDir, `${job.slug}-${job.id}.mp4`)
      // a film with audio is rendered to an intermediate first and muxed after;
      // the renderer only cleans that up when it finishes normally
      const partials = [outPath, `${outPath}.video.mp4`]
      const discard = async () => {
        for (const f of partials) await rm(f, { force: true }).catch(() => {})
      }

      await writeFile(stagePath, JSON.stringify(payload.stage), 'utf8')
      await writeFile(animPath, JSON.stringify(payload.anim), 'utf8')

      // the total is known up front, so progress is real rather than a guess
      const scenes = (payload.stage as { scenes?: { dur?: number }[] }).scenes ?? []
      const seconds = scenes.reduce((a, s) => a + (s.dur ?? 3), 0)
      job.totalFrames = Math.max(1, Math.round(seconds * job.options.fps))

      const child = spawn(this.config.bin, [
        stagePath, animPath, outPath,
        String(job.options.fps), String(job.options.supersample),
      ], {
        cwd: this.config.cwd,
        stdio: ['ignore', 'pipe', 'pipe'],
        // its own process group: the renderer spawns ffmpeg as a child, and
        // signalling only the renderer would orphan ffmpeg to carry on writing
        detached: true,
      })

      this.running.set(job.id, { child, dir })

      const timer = setTimeout(() => {
        this.cancel(job.id, `render exceeded ${Math.round(this.config.timeoutMs / 1000)}s`)
      }, this.config.timeoutMs)
      timer.unref?.()

      const take = (chunk: Buffer) => {
        const text = chunk.toString()
        for (const line of text.split(/\r?\n|\r/)) {
          const t = line.trim()
          if (!t) continue
          // keep the log bounded, and keep progress chatter out of it so a
          // failure log is only the useful lines
          if (!t.startsWith('progress ') && job.log.length < 400) job.log.push(t)
          const pr = PROGRESS.exec(t)
          if (pr) {
            job.frames = Number(pr[1])
            job.totalFrames = Number(pr[2])
            continue
          }
          const s = SUMMARY.exec(t)
          if (s) job.frames = Number(s[1])
        }
      }
      child.stdout?.on('data', take)
      child.stderr?.on('data', take)

      const code: number | null = await new Promise(res => {
        child.on('error', e => {
          job.log.push(String(e))
          res(-1)
        })
        child.on('close', c => res(c))
      })

      clearTimeout(timer)
      this.running.delete(job.id)

      // cancel() can flip the status from another turn of the loop while the
      // child was running, so this has to be read fresh rather than narrowed
      if ((job.status as JobStatus) === 'cancelled') {
        // the group is down, so nothing can still be writing to these
        await discard()
        job.finishedAt = Date.now()
      } else if (code === 0) {
        const info = await stat(outPath).catch(() => null)
        if (!info || info.size === 0) {
          await discard()
          this.finish(job, 'failed', 'the renderer exited cleanly but wrote no file')
        } else {
          job.bytes = info.size
          job.frames = job.totalFrames
          if (this.blobs) {
            // the local copy is a staging file; the durable one is the blob
            const key = exportKey(job.workspace ?? 'default', job.id)
            await this.blobs.put(key, createReadStream(outPath), 'video/mp4')
            this.keys.set(job.id, key)
            await discard()
          } else {
            this.files.set(job.id, outPath)
          }
          this.finish(job, 'done')
        }
      } else {
        await discard()
        this.finish(job, 'failed',
          job.error ?? `renderer exited with ${code}. ${job.log.slice(-2).join(' ')}`)
      }
    } catch (e) {
      this.running.delete(job.id)
      this.finish(job, 'failed', String(e))
    } finally {
      if (dir) await rm(dir, { recursive: true, force: true }).catch(() => {})
      void this.pump()
    }
  }

  /** drop artifacts and job records past their retention window */
  private async sweep(): Promise<void> {
    const cutoff = Date.now() - this.config.retentionMs
    for (const [id, job] of this.jobs) {
      if (job.status === 'running' || job.status === 'queued') continue
      if ((job.finishedAt ?? job.queuedAt) > cutoff) continue
      const file = this.files.get(id)
      if (file) await rm(file, { force: true }).catch(() => {})
      this.files.delete(id)
      this.jobs.delete(id)
    }
    // also clear orphans left behind by a crash, which no job record covers
    const known = new Set(this.files.values())
    const entries = await readdir(this.config.outDir).catch(() => [])
    for (const name of entries) {
      const path = join(this.config.outDir, name)
      if (known.has(path)) continue
      const info = await stat(path).catch(() => null)
      if (info && info.mtimeMs < cutoff) await rm(path, { force: true }).catch(() => {})
    }
  }
}
