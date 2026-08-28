// the painter and canvaskit are plain js, so the app declares their shapes.
// the wasm pkg itself ships generated .d.ts and needs nothing here.
//
// only the surface the app actually touches is typed. everything deeper
// (shaders, mask filters, blend modes) is used inside painter.js and never
// reaches this side of the boundary.

interface SkSurface {
  getCanvas(): unknown
  flush(): void
  delete(): void
}

interface SkPaint {
  setAntiAlias(on: boolean): void
  delete(): void
}

interface CanvasKit {
  MakeCanvasSurface(canvas: HTMLCanvasElement): SkSurface
  MakeSWCanvasSurface?(canvas: HTMLCanvasElement): SkSurface
  MakeImageFromEncoded(bytes: Uint8Array): unknown
  Paint: new () => SkPaint
}

interface Window {
  CanvasKitInit(opts: { locateFile(file: string): string }): Promise<CanvasKit>
}

declare module '@whippan/engine-web/painter' {
  export function paintFrame(
    CK: CanvasKit,
    skc: unknown,
    paint: SkPaint,
    cmds: unknown,
    images: Map<string, unknown>,
  ): void
}

declare module '*.wasm?url' {
  const url: string
  export default url
}
