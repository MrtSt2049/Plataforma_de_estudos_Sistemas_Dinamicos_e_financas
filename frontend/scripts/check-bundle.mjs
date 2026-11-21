// Fails if the production bundle contains a real secret (plan F8).
//
// Words such as "sb_secret_" or "service_role" appear in the bundle on purpose, because
// src/services/config.ts uses them to REFUSE such keys. So this looks for the keys
// themselves: a complete `sb_secret_...` key, and a JWT whose role claim is service_role.
//
// Usage: node scripts/check-bundle.mjs [directory]   (default: dist)
import { readdirSync, readFileSync, statSync } from 'node:fs'
import { join } from 'node:path'

const SECRET_KEY = /sb_secret_[A-Za-z0-9_-]{20,}/
const JWT = /eyJ[A-Za-z0-9_-]{10,}\.([A-Za-z0-9_-]{10,})\.[A-Za-z0-9_-]{10,}/g

function* files(directory) {
  for (const name of readdirSync(directory)) {
    const path = join(directory, name)
    if (statSync(path).isDirectory()) yield* files(path)
    else yield path
  }
}

function jwtRole(payload) {
  try {
    const claims = JSON.parse(Buffer.from(payload, 'base64url').toString('utf8'))
    return typeof claims === 'object' && claims !== null ? claims.role : undefined
  } catch {
    return undefined
  }
}

const directory = process.argv[2] ?? 'dist'
const problems = []
let scanned = 0

for (const path of files(directory)) {
  scanned += 1
  const text = readFileSync(path, 'utf8')
  if (SECRET_KEY.test(text)) problems.push(`${path}: contains a secret key (sb_secret_...)`)
  for (const match of text.matchAll(JWT)) {
    if (jwtRole(match[1]) === 'service_role') problems.push(`${path}: contains a service_role JWT`)
  }
}

if (problems.length > 0) {
  // Never print the value, only where it is.
  console.error(problems.join('\n'))
  process.exit(1)
}
console.log(`check-bundle: ${scanned} files in ${directory}, no secrets found.`)
