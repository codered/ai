"""hashline integration: hash-anchored file editing over the hashline MCP server.

hashline speaks MCP over stdio (`hashline mcp`), so this integration subclasses
`rlm.McpIntegration` and overrides `_open_session` to use the stdio transport
instead of the default streamable-HTTP one. That means no `mcpServers` entry, no
OAuth, and no bearer token: the server is a local subprocess spawned per call.

Usage in the kernel:

    import hashline
    print(await hashline.read("src/auth.py"))
    print(await hashline.patch("src/auth.py", "SWAP 3:a3:\\n+    return decoded"))
"""

from __future__ import annotations

import os
import shutil
from contextlib import AsyncExitStack
from typing import Any

from rlm import McpIntegration

__all__ = ["Hashline", "hashline", "resolve_binary"]

#: Fallback locations probed when `hashline` is not on PATH.
_FALLBACK_PATHS = (
    os.path.expanduser("~/.local/bin/hashline"),
    "/usr/local/bin/hashline",
)


def resolve_binary() -> str:
    """Absolute path to the hashline binary.

    `HASHLINE_BIN` wins, then PATH, then the usual install locations. Raising here
    (rather than letting the subprocess spawn fail deep inside the MCP transport)
    keeps the error legible to the agent.
    """
    override = os.environ.get("HASHLINE_BIN", "").strip()
    if override:
        return override
    found = shutil.which("hashline")
    if found:
        return found
    for path in _FALLBACK_PATHS:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path
    raise RuntimeError(
        "hashline binary not found. Install it, or set HASHLINE_BIN to its path."
    )


class Hashline(McpIntegration):
    """The hashline MCP server, spoken over stdio.

    Tools (`read`, `patch`, `write`, `find_block`, `remove_file`, `rename_file`)
    are auto-discovered and also wrapped below with their real argument names, so
    `help()` is useful even when the installed `mcp` SDK renames `inputSchema`.
    """

    server = "hashline"
    url = None  # stdio transport; no endpoint

    async def _open_session(self, stack: AsyncExitStack):
        from mcp import ClientSession, StdioServerParameters  # noqa: PLC0415
        from mcp.client.stdio import stdio_client  # noqa: PLC0415

        params = StdioServerParameters(
            command=resolve_binary(),
            args=["mcp"],
            # Inherit cwd and env so the agent's relative paths resolve against the
            # project it is actually working in.
            cwd=os.getcwd(),
            env=dict(os.environ),
        )
        read, write, *_ = await stack.enter_async_context(stdio_client(params))
        session = await stack.enter_async_context(ClientSession(read, write))
        await session.initialize()
        return session

    # -- typed wrappers -----------------------------------------------------
    # The server's parameter is `file`, not `path`; wrapping it keeps call sites
    # from guessing and gives every tool a docstring.

    async def read(self, file: str, json: bool = False) -> Any:
        """Read a file as `[path#HASH]` plus `line:hash|content` numbered lines."""
        return await self.call_tool("read", {"file": file, "json": json})

    async def patch(self, file: str, patch: str, dry_run: bool = False) -> Any:
        """Apply a hashline patch string (SWAP / DEL / INS.* ops) to `file`."""
        return await self.call_tool(
            "patch", {"file": file, "patch": patch, "dry_run": dry_run}
        )

    async def write(self, file: str, content: str, force: bool = False) -> Any:
        """Create `file` with `content`; `force=True` to overwrite an existing file."""
        return await self.call_tool(
            "write", {"file": file, "content": content, "force": force}
        )

    async def find_block(self, file: str, anchor: str) -> Any:
        """Return the structural block (function, class, braces) around `line:hash`."""
        return await self.call_tool("find_block", {"file": file, "anchor": anchor})

    async def remove_file(self, file: str) -> Any:
        """Delete `file`."""
        return await self.call_tool("remove_file", {"file": file})

    async def rename_file(self, src: str, dst: str) -> Any:
        """Rename (move) `src` to `dst`."""
        return await self.call_tool("rename_file", {"src": src, "dst": dst})


hashline = Hashline()


# Names the kernel bootstrap probes to decide if a module is a callable skill.
# Forwarding `run` would make it wrap the module as callable and break
# `await hashline.<tool>()` dispatch.
_RESERVED = {"run", "__wrapped__", "__call__"}


def __getattr__(name: str):
    # Forward bare module-level access (`import hashline; await hashline.read(...)`)
    # to the singleton instance.
    if name.startswith("_") or name in _RESERVED:
        raise AttributeError(name)
    return getattr(hashline, name)
