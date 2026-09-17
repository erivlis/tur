import { exec } from "child_process";
import { promisify } from "util";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const execAsync = promisify(exec);

// Ambient execution environment helper: guarantees TUR_AGENT_ID is always resolved
function getTurEnv(): NodeJS.ProcessEnv {
  return {
    ...process.env,
    TUR_AGENT_ID: process.env.TUR_AGENT_ID || "pi",
  };
}

export default function (pi: ExtensionAPI) {
  let idleTimer: NodeJS.Timeout | null = null;

  // --- I. THE AWAKENING (before_agent_start) ---
  // Injects Ariel's compiled System Prompt (Constitution) dynamically on every turn.
  pi.on("before_agent_start", async (event, ctx) => {
    try {
      ctx.ui.setWorkingIndicator("Waking Ariel...");

      const { stdout } = await execAsync("uv run --no-sync tur wake", {
        cwd: event.cwd,
        env: getTurEnv(),
      });

      ctx.ui.setWorkingIndicator(null);

      return {
        systemPrompt: event.systemPrompt + "\n\n" + stdout.trim(),
      };
    } catch (error: any) {
      ctx.ui.setWorkingIndicator(null);
      ctx.ui.notify(
        `Failed to wake Tur: ${error.message || String(error)}`,
        "error"
      );
    }
  });

  // --- II. THE BIOLOGICAL CYCLE HOOKS ---

  // 1. Session Wake (session_start)
  pi.on("session_start", async (_event, ctx) => {
    try {
      ctx.ui.setWorkingIndicator("Waking Ariel...");
      await execAsync("uv run --no-sync tur wake", {
        cwd: ctx.cwd,
        env: getTurEnv(),
      });
      ctx.ui.setWorkingIndicator(null);
      ctx.ui.notify("Ariel online. Cognitive State hydrated.", "success");
    } catch (err: any) {
      ctx.ui.setWorkingIndicator(null);
      ctx.ui.notify(`Wake failed: ${err.message}`, "error");
    }
  });

  // 2. The Yawns (Tired / Background dreaming on user idle)
  pi.on("input", (_event, ctx) => {
    if (idleTimer) {
      clearTimeout(idleTimer);
    }

    // Set a 5-minute inactivity trigger to run staged dreaming in the background
    idleTimer = setTimeout(async () => {
      ctx.ui.setStatus("tur-circadian", "💤 digesting context...");
      try {
        await execAsync("uv run --no-sync tur tired", {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setStatus("tur-circadian", "💤 digested");
      } catch {
        ctx.ui.setStatus("tur-circadian", null);
      }
    }, 300000); // 5 minutes
  });

  // 3. Sleep on Exit (session_shutdown)
  // Ensures zero context loss: automatically dehydrates logs and seals memories on TUI shutdown.
  pi.on("session_shutdown", async (_event, ctx) => {
    if (idleTimer) {
      clearTimeout(idleTimer);
    }

    const sessionFile = ctx.sessionManager.getSessionFile();
    if (sessionFile) {
      try {
        ctx.ui.setStatus("tur-circadian", "💾 sealing state...");
        await execAsync(
          `uv run --no-sync tur sleep "${sessionFile}" -n "Auto-sleep on shutdown."`,
          {
            cwd: ctx.cwd,
            env: getTurEnv(),
          }
        );
      } catch {
        // Silent catch to prevent blocking Pi's final exit process
      }
    }
  });

  // 4. Symmetrical Boundary Quarantine (The Shield)
  // Prevents the agent from hallucinating direct file modifications inside the .tur/ state store.
  pi.on("tool_call", async (event, ctx) => {
    const targetPath = event.input.path || event.input.command;
    if (targetPath && (targetPath.includes(".tur/") || targetPath.includes(".tur\\"))) {
      ctx.ui.notify("Symmetrical Isolation Blocked: Direct .tur/ write.", "error");
      return {
        block: true,
        reason:
          "Access Denied: Symmetrical Isolation Invariant. AI agents must NEVER perform direct filesystem modifications inside the .tur/ state directory. All state actions must run through Tur commands.",
      };
    }
  });

  // --- III. INTERACTIVE COMMANDS (Two-Tier EP-0149 Taxonomy) ---

  // 1. Status panel widget (Tier 1 Core Verb)
  pi.registerCommand("tur-status", {
    description: "Show current Tur persona, session, and memory status",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.setWorkingIndicator("Fetching status...");
        const { stdout } = await execAsync("uv run --no-sync tur status", {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.setWidget("tur-status", stdout.trim().split("\n"));
        ctx.ui.notify("Tur status loaded above editor.", "success");
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Failed to fetch status: ${error.message}`, "error");
      }
    },
  });

  // 2. Hide status widget
  pi.registerCommand("tur-hide", {
    description: "Hide the Tur status widget",
    handler: async (_args, ctx) => {
      ctx.ui.setWidget("tur-status", null);
      ctx.ui.notify("Tur status widget hidden.", "info");
    },
  });

  // 3. Append note (Tier 2 Subsystem: note write)
  pi.registerCommand("tur-note", {
    description: "Append a transient note to active Tur session notes",
    handler: async (args, ctx) => {
      try {
        let note = args;
        if (!note) {
          note = await ctx.ui.input("Enter Note:", "Enter note content...");
          if (!note) return;
        }

        ctx.ui.setWorkingIndicator("Saving note...");
        await execAsync(`uv run --no-sync tur note write ${JSON.stringify(note)}`, {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify("Note appended to active session.", "success");
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Failed to save note: ${error.message}`, "error");
      }
    },
  });

  // 4. Formally learn persistent memory (Tier 2 Subsystem: memory learn)
  pi.registerCommand("tur-learn", {
    description: "Formally learn a persistent memory for active persona",
    handler: async (args, ctx) => {
      try {
        let content = args;
        if (!content) {
          content = await ctx.ui.input("Memory Content:", "Enter memory content...");
          if (!content) return;
        }

        const type = await ctx.ui.select("Memory Type:", [
          "insight",
          "fact",
          "preference",
          "axiom",
          "event",
        ]);
        if (!type) return;

        const scope = await ctx.ui.select("Memory Scope:", [
          "incarnation",
          "persona",
          "user",
          "universal",
        ]);
        if (!scope) return;

        ctx.ui.setWorkingIndicator("Saving memory...");
        await execAsync(
          `uv run --no-sync tur memory learn --type ${type} --scope ${scope} ${JSON.stringify(content)}`,
          {
            cwd: ctx.cwd,
            env: getTurEnv(),
          }
        );
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify("Memory consolidated successfully.", "success");
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Failed to save memory: ${error.message}`, "error");
      }
    },
  });

  // 5. Trigger Council Introspection (Tier 2 Subsystem: memory introspect)
  pi.registerCommand("tur-introspect", {
    description: "Compress L1 memories into L2 Cognitive Map (Council Assembly)",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.setWorkingIndicator("Assembling Council...");
        await execAsync("uv run --no-sync tur memory introspect", {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify("Introspection complete. L2 Cognitive Map updated.", "success");
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Introspection failed: ${error.message}`, "error");
      }
    },
  });

  // 6. Verify cryptographic integrity (Tier 2 Subsystem: memory verify)
  pi.registerCommand("tur-verify", {
    description: "Verify cryptographic Merkle seals of all memory files",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.setWorkingIndicator("Verifying Merkle seals...");
        const { stdout } = await execAsync("uv run --no-sync tur memory verify", {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify("Symmetrical verification complete.", "success");
        ctx.ui.setWidget("tur-status", stdout.trim().split("\n"));
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Verification failed: ${error.message}`, "error");
      }
    },
  });

  // 7. List swarm manifestations (Tier 2 Subsystem: agent list)
  const handleAgentList = async (_args: string, ctx: any) => {
    try {
      ctx.ui.setWorkingIndicator("Listing manifestations...");
      const { stdout } = await execAsync("uv run --no-sync tur agent list", {
        cwd: ctx.cwd,
        env: getTurEnv(),
      });
      ctx.ui.setWorkingIndicator(null);
      ctx.ui.setWidget("tur-status", stdout.trim().split("\n"));
      ctx.ui.notify("Swarm nodes displayed.", "info");
    } catch (error: any) {
      ctx.ui.setWorkingIndicator(null);
      ctx.ui.notify(`Failed to list agents: ${error.message}`, "error");
    }
  };

  pi.registerCommand("tur-agent-list", {
    description: "List active manifestations in the current swarm (EP-0149)",
    handler: handleAgentList,
  });

  // Backwards-compatible alias for Pi user keybindings
  pi.registerCommand("tur-list-agents", {
    description: "List active manifestations in the current swarm (alias for tur-agent-list)",
    handler: handleAgentList,
  });

  // 8. Agent identity inspection (Tier 2 Subsystem: agent whoami)
  pi.registerCommand("tur-agent-whoami", {
    description: "Display current ambient agent identity and session context (EP-0149)",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.setWorkingIndicator("Resolving identity...");
        const { stdout } = await execAsync("uv run --no-sync tur agent whoami", {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.setWidget("tur-status", stdout.trim().split("\n"));
        ctx.ui.notify("Agent identity resolved.", "info");
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Failed to resolve identity: ${error.message}`, "error");
      }
    },
  });

  // 9. Inspect Session Board (Tier 2 Subsystem: board list)
  pi.registerCommand("tur-board-list", {
    description: "List parameters and keys currently on the shared session board (EP-0149)",
    handler: async (_args, ctx) => {
      try {
        ctx.ui.setWorkingIndicator("Reading session board...");
        const { stdout } = await execAsync("uv run --no-sync tur board list", {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.setWidget("tur-status", stdout.trim().split("\n"));
        ctx.ui.notify("Session board loaded.", "info");
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Failed to read board: ${error.message}`, "error");
      }
    },
  });

  // 10. Session dehydration / sleep (Tier 1 Core Verb)
  pi.registerCommand("tur-sleep", {
    description: "Sleep the session, dehydrate logs, and shutdown gracefully",
    handler: async (args, ctx) => {
      try {
        const sessionFile = ctx.sessionManager.getSessionFile();
        if (!sessionFile) {
          ctx.ui.notify("No active session file found to parse.", "error");
          return;
        }

        let note = args;
        if (!note) {
          note = await ctx.ui.input("Final note:", "Session completed and consolidated.");
          if (!note) return;
        }

        const confirm = await ctx.ui.confirm("Are you sure?", "Sleep the session and exit?");
        if (!confirm) return;

        ctx.ui.setWorkingIndicator("Dehydrating session log...");
        await execAsync(`uv run --no-sync tur sleep "${sessionFile}" -n ${JSON.stringify(note)}`, {
          cwd: ctx.cwd,
          env: getTurEnv(),
        });
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify("Session dehydrated. Dreaming initiated.", "success");

        setTimeout(() => {
          ctx.shutdown();
        }, 1000);
      } catch (error: any) {
        ctx.ui.setWorkingIndicator(null);
        ctx.ui.notify(`Failed to execute sleep: ${error.message}`, "error");
      }
    },
  });
}
