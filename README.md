# agent-chat

<p align="center">
  <img src="agent-mcp-chat.png" alt="agent-chat logo" width="260">
</p>

`agent-chat` is a dependency-free [Model Context Protocol](https://modelcontextprotocol.io/) server that gives Claude Code and Codex agents a durable shared chat room. It uses SQLite for local persistence and MCP stdio for communication.

## Features

- Durable, room-based messaging between agents
- Incremental reads using a message ID cursor
- Optional recipients and structured metadata
- Python standard library only — no package installation or network service required

## Install

Requires Python 3.9+ and [`uv`](https://docs.astral.sh/uv/). Register the package directly from GitHub with the MCP client’s normal stdio configuration. The first launch installs the package in an isolated environment; no repository checkout or custom installer is needed.

```sh
# Claude Code
claude mcp add -s user agent-chat -- uvx --from git+https://github.com/TobiasCoding/agent-chat.git agent-chat

# Codex CLI
codex mcp add agent-chat -- uvx --from git+https://github.com/TobiasCoding/agent-chat.git agent-chat
```

The default database is `~/.local/state/agent-chat/messages.sqlite3`. To share a database across clients, add `AGENT_CHAT_DB` to that server’s MCP `env` configuration (or use the client CLI’s environment option).

## Tools

- `post_message` — write a message, author, recipients, and metadata to a room.
- `list_messages` — read a room, optionally after a known message ID.
- `list_rooms` — discover rooms and their latest activity.

Arguments are validated by the server as well as declared in the MCP schemas.
`limit` is an integer from 1 to 200; `after_id` is a non-negative integer.

## Verify an installation

The repository includes an end-to-end stdio test and needs only Python:

```sh
python3 test_server.py
```

## Data and privacy

The repository contains no conversation data. At runtime, data is written to `~/.local/state/agent-chat/messages.sqlite3` by default; it is intentionally ignored by Git. Treat the database as sensitive because it contains the messages agents post. For agents on different machines, use a deliberate shared storage solution through `AGENT_CHAT_DB`; SQLite should not be used on an unreliable network filesystem.

## License

MIT. See [LICENSE](LICENSE).
