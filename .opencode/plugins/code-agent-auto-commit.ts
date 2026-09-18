import type { Plugin } from "@opencode-ai/plugin"

const TARGET_WORKTREE = "/mnt/c/AI"
const CONFIG_PATH = "/home/user/.config/code-agent-auto-commit/config.json"
const RUNNER_COMMAND = "cac"

export const ChatAutoCommitPlugin: Plugin = async ({ $, client, worktree }) => {
  const done = new Set<string>()

  return {
    event: async ({ event }) => {
      if (event.type !== "session.status") return
      if (worktree !== TARGET_WORKTREE) return

      if (event.properties.status.type === "busy") {
        done.delete(event.properties.sessionID)
        return
      }

      if (event.properties.status.type !== "idle") return
      if (done.has(event.properties.sessionID)) return

      const result = await $`${RUNNER_COMMAND} run --tool opencode --worktree ${worktree} --config ${CONFIG_PATH} --session-id ${event.properties.sessionID}`.quiet().nothrow()
      if (result.exitCode !== 0) {
        await client.app.log({
          body: {
            service: "code-agent-auto-commit",
            level: "warn",
            message: "auto-commit runner failed",
            extra: {
              sessionID: event.properties.sessionID,
              stderr: result.stderr.toString(),
            },
          },
        })
        done.add(event.properties.sessionID)
        return
      }

      done.add(event.properties.sessionID)
      await client.app.log({
        body: {
          service: "code-agent-auto-commit",
          level: "info",
          message: "auto-commit runner finished",
          extra: {
            sessionID: event.properties.sessionID,
          },
        },
      })
    },
  }
}

