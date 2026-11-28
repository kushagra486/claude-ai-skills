import { atom, read, update } from 'claude-code'
import type { Engine, Register } from 'claude-code'

type Dollar = Engine

import type { Call, Project, Route } from '../types'

const PANE = 'control-board'
const DAY = 24 * 60 * 60 * 1000

const calls = atom({ plugin: 'control-board', key: 'calls' } as const, [], { shape: 'calls-1' })
const routes = atom({ plugin: 'control-board', key: 'routes' } as const, [], { shape: 'routes-1' })
const projects = atom({ plugin: 'control-board', key: 'projects' } as const, [], { shape: 'projects-1' })
const watched = atom({ plugin: 'control-board', key: 'watched' } as const, [], { shape: 'watched-1' })

// Use case -> model. Edit this table to taste.
const ROUTES: ReadonlyArray<{ kind: string; model: string; test: RegExp }> = [
  { kind: 'deep reasoning / architecture', model: 'opus', test: /\b(architect|design|trade-?off|root cause|why does|plan)\b/i },
  { kind: 'debug / fix errors', model: 'sonnet', test: /\b(bug|error|fix|stack ?trace|crash|failing|exception)\b/i },
  { kind: 'code generation / refactor', model: 'sonnet', test: /\b(implement|build|refactor|write|add|create)\b/i },
  { kind: 'quick lookup / summary', model: 'haiku', test: /\b(summari[sz]e|explain|what is|list|find|rename)\b/i },
]

const pickRoute = (text: string) =>
  ROUTES.find(r => r.test.test(text)) ?? { kind: 'general', model: 'sonnet', test: /./ }

const check = async ($: Dollar, path: string): Promise<Project> => {
  await $.process.run(['git', '-C', path, 'fetch', '--quiet'], { timeoutMs: 60_000 }).catch(() => undefined)
  const st = await $.process.run(['git', '-C', path, 'status', '-sb', '--porcelain'], { timeoutMs: 20_000 }).catch(() => undefined)
  const lines = st?.stdout.trim().split('\n') ?? []
  const dirty = Math.max(0, lines.length - 1)
  const head = lines[0] ?? 'not a git repository'
  const behind = /behind (\d+)/.exec(head)?.[1]
  const hints = [
    dirty > 0 ? `${dirty} uncommitted change(s): commit or stash` : '',
    behind ? `${behind} commit(s) behind upstream: pull/merge` : '',
    /ahead/.test(head) ? 'unpushed commits: push' : '',
  ].filter(Boolean)

  return { path, summary: hints.length ? hints.join('; ') : 'clean and up to date', checkedAt: await $.clock.now() }
}

const runChecks = async ($: Dollar) => {
  const paths = ['.', ...(await read($, watched))]
  const out: Project[] = []

  for (const path of paths) {
    out.push(await check($, path))
  }
  await update($, projects, () => out)
  const needs = out.filter(p => p.summary !== 'clean and up to date').length
  $.ui.status(needs ? `${needs} project(s) need attention` : 'projects clean')

  return out
}



export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    for (const [name, description] of [
      ['route', 'Route a task to a model by use case and run it as a subagent: /route <task>'],
      ['watch', 'Add a project folder to the daily check: /watch <path>'],
      ['daily-check', 'Check all watched projects now and suggest next steps'],
      ['board', 'Open the control board pane'],
    ] as const) {
      await $.command.register({ name, description })
    }
    void $.ui.open({ id: PANE, title: 'Control board' })
    $.clock.every(DAY, async () => { await runChecks($) })

    return next(e)
  })

  on('command.run', { command: 'board' }, async $ => {
    await $.ui.open({ id: PANE, title: 'Control board' })

    return { text: 'Control board opened.' }
  })

  on('command.run', { command: 'watch' }, async ($, e) => {
    const path = e.args.trim()

    if (!path) {
      return { text: 'Usage: /watch <path to a project folder>' }
    }
    await update($, watched, list => (list.includes(path) ? list : [...list, path]))

    return { text: `Watching ${path}. Checked daily and on /daily-check (until this session ends).` }
  })

  on('command.run', { command: 'daily-check' }, async $ => {
    const out = await runChecks($)

    return { text: out.map(p => `${p.path}: ${p.summary}`).join('\n') }
  })

  on('command.run', { command: 'route' }, async ($, e) => {
    const task = e.args.trim()

    if (!task) {
      return { text: 'Usage: /route <task>. Picks a model by use case and runs a subagent.' }
    }
    const pick = pickRoute(task)
    const route: Route = { task: task.slice(0, 60), kind: pick.kind, model: pick.model, at: await $.clock.now() }
    await update($, routes, list => [...list, route].slice(-30))
    const spawned = await $.agent.spawn({ prompt: task, model: pick.model })

    return { text: 'deny' in spawned ? `Not started: ${String(spawned.deny)}` : `Started a ${pick.model} subagent for: ${pick.kind}.` }
  })

  on('prompt.submit', async ($, e, next) => {
    if (!e.command) {
      const pick = pickRoute(e.text)
      $.ui.toast(`Suggested model: ${pick.model} (${pick.kind}). Use /route to run it there.`)
    }

    return next(e)
  })

  on('tool.call', async ($, e, next) => {
    const call: Call = { id: e.tool_use_id, tool: e.tool, isDone: false }
    await update($, calls, list => [...list, call].slice(-100))
    const ran = await next(e)
    await update($, calls, list => list.map(c => (c.id === call.id ? { ...c, isDone: true } : c)))

    return ran
  })

  on('turn.complete', async ($, e, next) => {
    const list = await read($, calls)
    $.ui.status(`${list.filter(c => c.isDone).length} tool calls this session`)

    return next(e)
  })

  on('ui.render', { component: 'Pane', requestId: PANE }, async ($, e) => {
    const { Box, Text } = $.ui.resolve(e)
    const [list, rs, ps] = await Promise.all([read($, calls), read($, routes), read($, projects)])
    const agents = await $.agent.list()
    const room = Math.max(3, (e.viewport?.rows ?? 30) - 20)

    return (
      <Box flexDirection="column">
        <Text bold>Agents ({agents.length})</Text>
        {agents.length === 0 && <Text dimColor>none running</Text>}
        {agents.slice(0, 6).map(a => (
          <Text dimColor>{a.id}</Text>
        ))}
        <Text bold>Model routing</Text>
        {rs.length === 0 && <Text dimColor>/route &lt;task&gt; to start one</Text>}
        {rs.slice(-5).map(r => (
          <Text>{r.model.padEnd(7)} {r.kind}: {r.task}</Text>
        ))}
        <Text bold>Daily suggestions</Text>
        {ps.length === 0 && <Text dimColor>/watch &lt;path&gt;, then /daily-check</Text>}
        {ps.map(p => (
          <Text>{p.path}: {p.summary}</Text>
        ))}
        <Text bold>Tool calls</Text>
        {list.slice(-room).map(c => (
          <Text dimColor={c.isDone}>{c.isDone ? 'done' : 'runs'} {c.tool}</Text>
        ))}
      </Box>
    )
  })
}
