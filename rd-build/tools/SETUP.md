# Tooling setup for the local build

The local Cursor agent drives RealDash with a screenshot -> decide -> click/type ->
verify loop using `automation_helper.py` (PyAutoGUI). This is the only tool required.
**No MCP server or remote-desktop connector is needed** when the agent and RealDash
run on the same machine.

## 1. Python + PyAutoGUI

    pip install -r tools/requirements.txt

Per-OS extras:
- **Windows:** nothing extra. Run the agent/terminal as the same logged-in user that
  has RealDash open on the physical screen.
- **macOS:** grant your terminal app (and/or the Cursor app) permission under
  System Settings -> Privacy & Security -> **Accessibility** and **Screen Recording**.
  Without both, clicks/typing or screenshots silently fail.
- **Linux (X11):** `sudo apt install scrot python3-tk python3-dev`. Run inside the
  real X11 desktop session (not headless). Wayland users: PyAutoGUI needs an X11
  session (or XWayland); global input injection may be restricted under pure Wayland.

## 2. Verify

    python tools/automation_helper.py size
    python tools/automation_helper.py screenshot rd_check.png   # then open/read it
    python tools/automation_helper.py pixel 10 10

If `size` prints your real resolution and the screenshot shows your desktop, you're
ready. See the docstring at the top of `automation_helper.py` for the full command list.

## 3. Confirm RealDash renders (critical)

Launch RealDash, log in with `CREDENTIALS.md`, and confirm it reaches the **Garage**
screen. If it hangs on a loading spinner, you're on a software-GL / headless display
and must fix that first (see `../FINDINGS.md`). On a normal GPU-backed desktop this
just works.

## Optional: MCP-based computer use

You do NOT need this. If you prefer an MCP tool over the terminal + helper approach,
you can register a desktop-control MCP server in Cursor. `mcp.example.json` shows the
shape of such a config (pointing at a hypothetical stdio server). The shipped helper
is simpler and has no external dependencies beyond PyAutoGUI, so it is the recommended
path.

## Remote option (only if the agent is NOT on the RealDash PC)

If you must run the Cursor agent on a different machine than RealDash, expose the
RealDash desktop over VNC (a server that mirrors the live GPU session) and have the
agent connect with a VNC client, tunneling via Tailscale or `ngrok tcp`. Prefer VNC of
the live console session over RDP (RDP's virtual session can fall back to software GL).
This is more complex than the local setup and is not needed if the agent runs on the
RealDash PC.
