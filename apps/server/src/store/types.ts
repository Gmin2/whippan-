/** a film's two layers, as stored */
export interface FilmDoc {
  stage: unknown
  anim: unknown
}

export interface FilmEntry {
  slug: string
  title: string
  dur: number
  size: [number, number]
  group: string
  [k: string]: unknown
}

/**
 * Where films live. The API never touches a filesystem directly, so moving to
 * object storage or a database is a new implementation of this interface and
 * nothing else. Slugs are validated before they reach a store, but a store is
 * still responsible for never resolving one outside its own namespace.
 */
export interface Asset {
  /** the path a document's `src` refers to, eg /assets/solder/home.png */
  src: string
  bytes: number
}

export interface DocStore {
  /** the registry every client reads to know what exists */
  list(): Promise<FilmEntry[]>
  get(slug: string): Promise<FilmDoc | null>
  put(slug: string, doc: FilmDoc): Promise<void>
  /** true if the film exists at all */
  has(slug: string): Promise<boolean>
  /** images a document can reference, for the editor's insert picker */
  assets(): Promise<Asset[]>
}
