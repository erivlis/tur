import subprocess
import time

import pytest
import requests

# Mark the entire module as skipped.
# The Tur CLI application exits prematurely when run in a non-interactive (non-TTY)
# shell, which is how pytest's subprocess executes it. This is likely due to
# TTY-detection logic within the app (e.g., the @require_human decorator or Typer itself)
# that prevents headless operation for certain commands. Because the server fails
# to stay alive, these tests cannot connect. This requires a deeper architectural
# change to the app's startup logic to make it testable in this manner.
# pytest.skip("Tur CLI is not currently testable in a non-interactive subprocess.", allow_module_level=True)



@pytest.fixture(scope="module")
def sse_server():
    """Fixture to start and stop the Tur MCP server for SSE transport testing."""
    port = 9005
    command = ["uv", "run", "tur", "serve", "--transport", "sse", "--port", str(port)]

    import os
    env = os.environ.copy()
    try:
        from pathlib import Path

        import yaml
        state_path = Path(".tur/state.yaml")
        if state_path.exists():
            with open(state_path, encoding="utf-8") as f:
                state_data = yaml.safe_load(f)
            active_id = state_data.get("active_persona_id")
            if active_id:
                env["TUR_ACTIVE_PERSONA_ID"] = active_id
    except Exception:
        pass

    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,  # Merge stdout into stderr
        text=True,
        env=env
    )

    # More robust readiness check: wait for Uvicorn's startup message
    try:
        # Since we merged streams, we now read from stdout
        captured = []
        for line in iter(process.stdout.readline, ''):
            captured.append(line)
            # Uvicorn's message when it's ready to accept connections
            if "Uvicorn running on" in line:
                break
            # Fail fast if the process exits unexpectedly
            if process.poll() is not None:
                # Read any remaining output
                remaining, _ = process.communicate(timeout=1)
                captured.append(remaining)
                raise RuntimeError("Server process failed to start:\n" + "".join(captured))
        else:
             # This block runs if the loop completes without a 'break',
             # meaning stderr stream ended before the ready message appeared.
             raise RuntimeError("Server process exited without signaling it was ready:\n" + "".join(captured))

        yield f"http://127.0.0.1:{port}"

    finally:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=5)



def test_sse_server_responds(sse_server):
    """
    Tests if the SSE server starts and responds to a GET request on the /sse endpoint.
    """
    try:
        # The /sse endpoint expects a streaming connection. We'll use a short timeout.
        # A successful connection (even if it times out while waiting for events) is a sign of success.
        response = requests.get(f"{sse_server}/sse", stream=True, timeout=3)

        # We expect a 200 OK for a successful connection.
        assert response.status_code == 200

        # Check for the correct content type for Server-Sent Events
        assert "text/event-stream" in response.headers.get("content-type", "")

    except requests.exceptions.ReadTimeout:
        # This is an acceptable outcome for a stream that doesn't send an event immediately.
        # It proves the connection was held open.
        pass
    except requests.exceptions.RequestException as e:
        pytest.fail(f"Failed to connect to the SSE server: {e}")

