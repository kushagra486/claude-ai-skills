import type { Register } from 'claude-code'

const PROTECTED = /(^|\/)\.env(\.|$)|(^|\/)id_(rsa|ed25519)$/
const RISKY: ReadonlyArray<readonly [RegExp, string]> = [
  [/\brm\s+(-[a-z]*r[a-z]*f|-[a-z]*f[a-z]*r)\b.*(\s\/(\s|$)|\s~|\s\*|\$HOME)/, 'recursive force delete of a broad path'],
  [/\bgit\s+push\b.*(--force\b|\s-f\b)(?!-with-lease)/, 'force push (use --force-with-lease)'],
  [/\bgit\s+reset\s+--hard\b/, 'git reset --hard discards work'],
  [/\bgit\s+clean\s+-[a-z]*f/, 'git clean -f deletes untracked files'],
  [/\b(curl|wget)\b[^|]*\|\s*(sudo\s+)?(ba)?sh\b/, 'piping a download into a shell'],
  [/\bdrop\s+(table|database)\b/i, 'dropping a database object'],
  [/\bchmod\s+-R\s+777\b/, 'chmod -R 777'],
]

export const register: Register = on => {
  on('tool.call', { tool: 'Bash' }, ($, e, next) => {
    const hit = RISKY.find(([pattern]) => pattern.test(e.command))

    return hit === undefined
      ? next(e)
      : { deny: `${$.plugin.name}: blocked (${hit[1]}). Ask the person first.` }
  }).catch(($, e, next) =>
    next.called ? next(e) : { deny: `${$.plugin.name}: its guard failed, so the command was held.` },
  )

  for (const tool of ['Edit', 'Write'] as const) {
    on('tool.call', { tool }, ($, e, next) =>
      PROTECTED.test(e.file_path)
        ? { deny: `${$.plugin.name}: ${e.file_path} holds secrets and is protected.` }
        : next(e),
    )
  }
}
