# Prime Agent setup

Prime Agent has a single-tool design: MCP servers are not exposed as agent tools.
An integration is a Python-backed skill that the model imports and calls from the
IPython kernel (see Prime Agent's own `docs/mcp-integrations.md`). Prime's built-in MCP
support also only reaches remote `http` servers — the host drops non-HTTP
`mcpServers` entries — and hashline speaks stdio.

So this skill ships a `McpIntegration` subclass that overrides `_open_session` to
use the stdio transport, spawning `hashline mcp` per call. No `mcpServers` entry,
no daemon, no port, and no credentials: the stdio override never reaches Prime's
bearer-token path.

## Install

Copy the skill directory into a Prime Agent skills location:

```bash
cp -r skills/hashline ~/.prime/agent/skills/
```

Prime discovers it on next start, installs it editable into the kernel venv
(pulling `mcp` as a dependency), and imports it. Verify:

```bash
prime-agent -p 'In the IPython kernel run: import hashline; print(await hashline.read("README.md"))'
```

You should get back a `[README.md#HASH]` header and `line:hash|content` lines.

If `pyproject.toml` changes later, Prime rebuilds the kernel venv automatically.

## Make it the default editing path

Prime ships a built-in `edit` skill (exact string replace). Nothing stops the
model from reaching for it, or for `open(...).write()`, unless you say so. Add
these to `~/.prime/agent/AGENTS.md` (or a project `AGENTS.md`):

```markdown
# Editing Rules
- Always route file reads, creates, edits, deletes, and renames through the `hashline` skill (`import hashline; await hashline.read(...)` / `await hashline.patch(...)`). It is an MCP server over stdio; see its SKILL.md for the patch syntax.
- Do not edit files with `edit`, `open(...).write()`, `sed`, or shell heredocs. Those bypass hashline's drift check.
- Always read the target file with `await hashline.read(path)` immediately before patching, and copy `line:hash` anchors verbatim from that read. Never invent or reuse a stale anchor.
- hashline reports failures as a returned string starting with `Error:`, not as an exception. Read the result of every patch before assuming the edit landed; on a drift rejection, re-read and rebuild the patch.
```

To remove the fallback entirely rather than just steering away from it, disable
the built-in in `~/.prime/agent/settings.json`:

```json
{ "bundledSkills": { "edit": false } }
```

## Why the wrappers exist

`src/hashline/__init__.py` defines explicit `read` / `patch` / `write` /
`find_block` / `remove_file` / `rename_file` methods rather than relying on
`McpIntegration.__getattr__` tool binding. Two reasons, both from the `mcp` 2.0
SDK renaming fields that Prime's `rlm/mcp_base.py` still reads by their old
camelCase names:

- `Tool.inputSchema` → `input_schema`, so `list_tools()` reports empty schemas
  and `help()` shows no arguments. The wrappers carry the real signatures.
- `CallToolResult.isError` → `is_error`, so `_parse_result` never raises
  `McpToolError`. **Tool failures arrive as a returned string starting with
  `Error:`.** This is why the AGENTS.md rules above tell the model to read every
  patch result.

Both are upstream-version-sensitive: if a later `rlm` handles the new field
names, the wrappers stay correct and errors start raising properly instead.
