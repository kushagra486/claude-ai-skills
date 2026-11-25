import type { Register } from 'claude-code'

import { makeColors } from './make-colors.js'

// Obsidian board: near-black surfaces, champagne-gold accent, cool teal success.
const { theme, problems } = makeColors({
  label: 'Obsidian board',
  roles: { accent: '#c9a45c', danger: '#d9534f', success: '#3fb5a3', warning: '#e0a030', pro: '#8f7ad6' },
  light: {
    gray: {
      anchors: {
        'surface-0': '#f3f1ec',
        'surface-1': '#f8f6f1',
        'surface-2': '#fcfbf8',
        'text-primary': '#1b1a17',
        'text-secondary': '#46433b',
        'text-muted': '#615d52',
      },
    },
  },
  dark: {
    gray: {
      anchors: {
        'surface-0': '#0c0d10',
        'surface-1': '#14161a',
        'surface-2': '#1b1e23',
        'surface-3': '#12141a',
        'text-primary': '#ecebe6',
        'text-secondary': '#c3c1b8',
        'text-muted': '#9d9b92',
      },
    },
  },
})

export const register: Register = on => {
  on('session.start', async ($, e, next) => {
    const unpainted = problems.find(line => line.startsWith("Desktop won't paint"))

    if (unpainted !== undefined) {
      $.ui.toast(unpainted)
    }

    const set = await $.theme.set({
      colors: theme,
      style: {
        UserMessage: { backgroundColor: '#1b1e23', radius: 14, paddingX: 14, paddingY: 10, borderColor: '#c9a45c', borderWidth: 1 },
        AssistantMessage: { fontSize: 15, lineHeight: 24 },
        Heading: { fontWeight: 'semibold', color: '#c9a45c' },
      },
    })

    if (!set.isDrawn) {
      $.ui.status(set.reason)
    }

    return next(e)
  })
}
