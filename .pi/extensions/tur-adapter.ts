import { exec } from "child_process";
import { promisify } from "util";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const execAsync = promisify(exec);

export default function (pi: ExtensionAPI) {
  // We use before_agent_start to inject the Tur persona into the system prompt
  // before the LLM processes the turn.
  pi.on("before_agent_start", async (event, ctx) => {
    try {
      // Show an indicator in the TUI while Tur compiles the persona
      ctx.ui.setWorkingIndicator("Waking Tur...");

      // Execute the tur wake command. We assume the environment is set up.
      // We use 'uv run tur wake' as the default command pattern.
      const { stdout } = await execAsync("uv run tur wake", {
        cwd: event.cwd,
        env: process.env,
      });

      // Tur's output contains the compiled System Prompt.
      // We append it to the Harness's system prompt options via the returned object
      return {
        systemPrompt: event.systemPrompt + "\n\n" + stdout.trim()
      };

      ctx.ui.setWorkingIndicator(null);
    } catch (error: any) {
      ctx.ui.setWorkingIndicator(null);
      // If Tur fails (e.g., not installed, no persona), we log it but don't crash Pi.
      ctx.ui.notify(
        `Failed to wake Tur: ${error.message || String(error)}`,
        "error"
      );
    }
  });

  // Optional: Add a command to manually force a wake/reload if needed.
  pi.registerCommand("tur-wake", {
    handler: async (_args, ctx) => {
      ctx.ui.notify("Tur wake is handled automatically before each turn.", "info");
    },
  });
}
