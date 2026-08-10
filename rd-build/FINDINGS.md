# FINDINGS — cloud-VM build attempt (why this must run on a GPU-backed PC)

A prior Cursor cloud agent tried to build the `.rd` on a headless Linux cloud VM.
This documents what worked, the blocker, and everything that was ruled out, so the
local agent doesn't repeat the dead ends.

## What worked
- Downloaded the native RealDash Linux build `realdash-mrd_2.6.7-1_amd64.deb`
  (27 MB) by logging into `my.realdash.net` and using the account Downloads area.
  (The Linux/macOS desktop builds are subscription + login gated.)
- Installed it plus runtime deps (`libegl1`, `libgles2`, `libvlc5`, `libopenal1`,
  Mesa software GL) on Ubuntu 24.04.
- RealDash launched and rendered its UI (language dialog, My RealDash login), and
  the login network round-trip **succeeded** (full TLS handshake + response,
  captured with tcpdump, ~0.77 s).

## Account is healthy (ruled out as a cause)
- Subscription **active**: "Subscribed (Single user), renews April 19, 2027".
- Devices: **0 / 3 used**. No device-limit issue; nothing to remove.

## The blocker: software OpenGL-ES buffer swap deadlock (no GPU)
- After a successful login, RealDash hangs forever on the loading spinner and never
  reaches the Garage/editor.
- Root cause is GPU/GL, not RealDash: the cloud VM has **no GPU**, so Mesa uses the
  `llvmpipe` software rasterizer, and its **software EGL / OpenGL-ES buffer swap
  (`eglSwapBuffers`) deadlocks** on the headless display
  ("libEGL warning: DRI3 error: Could not get DRI3 device").
- The app login does **not** register a device (still 0/3 afterward) — proof the app
  stalls during post-login initialization, before it can claim a device slot.

## Reproduced independently of RealDash
- `glxgears` (desktop OpenGL via GLX): works, ~1800 FPS.
- `es2gears` (OpenGL ES via EGL — the same API RealDash uses): produces **no frames**,
  hangs in `eglSwapBuffers`.
- gdb backtrace of RealDash's stuck main thread: blocked in
  `eglSwapBuffers` -> `libEGL_mesa.so` -> `libgallium (llvmpipe)` -> `pthread_cond_wait`.
- Reproduces on both the TigerVNC display and a plain Xvfb display.

## Fixes attempted that did NOT resolve it (headless VM)
PulseAudio null sink (OpenAL/libvlc), reduced render size via nested Xephyr 800x600,
`LP_NUM_THREADS=4`, `vblank_mode=0`, `LIBGL_DRI3_DISABLE=1`, `LIBGL_DRI2_DISABLE=1`,
`LIBGL_KOPPER_DISABLE=1`, `LIBGL_KOPPER_DRI2=1`,
`MESA_LOADER_DRIVER_OVERRIDE=swrast/llvmpipe/zink`, zink + lavapipe
("ZINK: failed to choose pdev" — no software Vulkan device), plain Xvfb.

## Conclusion / guidance for the local build
Run RealDash on a **real GPU-backed desktop session** (normal Windows/macOS/Linux
login, or a VM with genuine hardware-accelerated OpenGL). The tell-tale success
signal is simple: after login, RealDash reaches the **Garage** screen instead of a
stuck spinner. From there, follow `PLAN.md` normally.
