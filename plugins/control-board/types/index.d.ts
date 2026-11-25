export type Call = { id: string; tool: string; isDone: boolean }
export type Route = { task: string; kind: string; model: string; at: number }
export type Project = { path: string; summary: string; checkedAt: number }

declare module 'claude-code' {
  interface PluginState {
    'control-board': {
      calls: Shaped<Call[]>
      routes: Shaped<Route[]>
      projects: Shaped<Project[]>
      watched: Shaped<string[]>
    }
  }
}
