import { getAuthTables } from 'better-auth/db'
import { organization } from 'better-auth/plugins'

/**
 * The auth schema, generated from the installed library.
 *
 * Not from `@better-auth/cli`: that package stopped at 1.5 while the library is
 * on 1.7, and the skew silently produced a schema missing a column the runtime
 * needed. Reading the table definitions out of the same package the server
 * imports means the two can never disagree.
 *
 *   npx tsx src/db/gen-auth-schema.ts > migrations/00N_auth.sql
 */
const PG: Record<string, string> = {
  string: 'text', number: 'integer', boolean: 'boolean',
  date: 'timestamptz', json: 'jsonb',
}

const tables = getAuthTables({
  emailAndPassword: { enabled: true },
  socialProviders: {},
  plugins: [organization()],
} as Parameters<typeof getAuthTables>[0])

const q = (s: string) => `"${s}"`
const out: string[] = []
const indexes: string[] = []

for (const [, table] of Object.entries(tables)) {
  const name = table.modelName
  const cols = [`${q('id')} text not null primary key`]
  for (const [field, def] of Object.entries(table.fields)) {
    const col = def.fieldName ?? field
    const type = Array.isArray(def.type) ? 'text' : PG[def.type as string] ?? 'text'
    let line = `${q(col)} ${type}`
    if (def.required) line += ' not null'
    if (def.unique) line += ' unique'
    if (def.references) {
      line += ` references ${q(def.references.model)} (${q(def.references.field)})`
      if (def.references.onDelete) line += ` on delete ${def.references.onDelete}`
    }
    if (def.defaultValue !== undefined && typeof def.defaultValue !== 'function') {
      line += ` default ${typeof def.defaultValue === 'string' ? `'${def.defaultValue}'` : def.defaultValue}`
    }
    cols.push(line)
    // foreign keys are the columns every session lookup filters on
    if (def.references) indexes.push(`create index ${q(`${name}_${col}_idx`)} on ${q(name)} (${q(col)});`)
  }
  out.push(`create table ${q(name)} (\n  ${cols.join(',\n  ')}\n);`)
}

console.log(`-- generated: npx tsx src/db/gen-auth-schema.ts
-- from better-auth's own table definitions, so it cannot skew from the runtime.
-- regenerate as a NEW migration when the auth config gains a plugin.
`)
console.log(out.join('\n\n'))
console.log('\n' + indexes.join('\n'))
