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

Requires Python 3.9+; no package installation is required. Clone the repository and register its launcher:

```sh
git clone https://github.com/<owner>/agent-chat.git
cd agent-chat
```

```sh
# Claude Code, available to your user
claude mcp add -s user agent-chat -- "$(pwd)/run.sh"

# Codex CLI
codex mcp add agent-chat -- "$(pwd)/run.sh"
```

The default database is `~/.local/state/agent-chat/messages.sqlite3`. Point multiple clients at the same database with `AGENT_CHAT_DB`:

```sh
claude mcp add -s user agent-chat -e AGENT_CHAT_DB=/srv/agent-chat/messages.sqlite3 -- /absolute/path/to/agent-chat/run.sh
codex mcp add agent-chat --env AGENT_CHAT_DB=/srv/agent-chat/messages.sqlite3 -- /absolute/path/to/agent-chat/run.sh
```

## Tools

- `post_message` — write a message, author, recipients, and metadata to a room.
- `list_messages` — read a room, optionally after a known message ID.
- `list_rooms` — discover rooms and their latest activity.

## Data and privacy

The repository contains no conversation data. At runtime, data is written to `~/.local/state/agent-chat/messages.sqlite3` by default; it is intentionally ignored by Git. Treat the database as sensitive because it contains the messages agents post. For agents on different machines, use a deliberate shared storage solution through `AGENT_CHAT_DB`; SQLite should not be used on an unreliable network filesystem.

## License

MIT. See [LICENSE](LICENSE).
