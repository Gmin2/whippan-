import type { Pool } from 'pg'

/**
 * The film a new workspace starts with.
 *
 * Without it, signing up lands you on "empty registry" with nothing to open,
 * which is a dead end. One scene is enough: the editor has something to render,
 * and every tool is immediately usable on it.
 *
 * The numbers are the corpus defaults from BLOCKS.md rather than invented ones,
 * so the first thing anyone sees is already in the house style: title 84 at
 * weight 700 in near-black, sub at half that in the mid-grey tier, both on the
 * centre line where 12.7% of all nodes in the reference films sit.
 */
const STARTER = {
  stage: {
    fps: 30,
    size: [1920, 1080],
    scenes: [{
      id: 's1',
      dur: 2.4,
      bg: '#ffffff',
      note: 'the opening beat. one thought per scene.',
      nodes: [
        {
          id: 'title', type: 'text', x: 960, y: 540, text: 'Your first film',
          color: '#161616', font: { family: 'inter', weight: 700, size: 84 },
        },
        {
          id: 'sub', type: 'text', x: 960, y: 652, text: 'press play, then change something',
          color: '#8a8a8a', font: { family: 'inter', weight: 400, size: 42 },
        },
      ],
    }],
  },
  // entrances rather than raw keys, so the first thing opened in motion mode is
  // legible: one word per node instead of a wall of keyframes
  anim: {
    tracks: [
      { target: 'title', at: 0.08, enter: 'rise-fade' },
      { target: 'sub', at: 0.14, enter: 'rise-fade' },
    ],
  },
}

export async function seedWorkspace(pool: Pool, workspace: string): Promise<void> {
  await pool.query(
    `insert into films (workspace_id, slug, title, grp, stage, anim)
          values ($1, 'first-film', 'Your first film', 'films', $2, $3)
     on conflict (workspace_id, slug) do nothing`,
    [workspace, JSON.stringify(STARTER.stage), JSON.stringify(STARTER.anim)],
  )
}
