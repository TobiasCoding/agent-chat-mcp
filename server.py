#!/usr/bin/env python3
"""A dependency-free stdio MCP server for durable agent-to-agent chat."""
import json, os, sqlite3, sys
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = Path(os.environ.get("AGENT_CHAT_DB", Path(os.environ.get("XDG_STATE_HOME", Path.home() / ".local/state")) / "agent-chat" / "messages.sqlite3"))

def db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    con.execute("""CREATE TABLE IF NOT EXISTS messages (
      id INTEGER PRIMARY KEY AUTOINCREMENT, room TEXT NOT NULL, author TEXT NOT NULL,
      body TEXT NOT NULL, recipients TEXT, metadata TEXT, created_at TEXT NOT NULL)""")
    return con

def result(data):
    return {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False, indent=2)}], "structuredContent": data}

def schema():
    return [
      {"name":"post_message", "description":"Post a durable message for other agents in a room.", "inputSchema":{"type":"object","required":["room","author","message"],"properties":{"room":{"type":"string"},"author":{"type":"string"},"message":{"type":"string"},"recipients":{"type":"array","items":{"type":"string"}},"metadata":{"type":"object"}}}},
      {"name":"list_messages", "description":"Read messages from a room in chronological order.", "inputSchema":{"type":"object","required":["room"],"properties":{"room":{"type":"string"},"after_id":{"type":"integer","minimum":0},"limit":{"type":"integer","minimum":1,"maximum":200}}}},
      {"name":"list_rooms", "description":"List chat rooms and their most recent activity.", "inputSchema":{"type":"object","properties":{"limit":{"type":"integer","minimum":1,"maximum":200}}}},
    ]

def call(name, a):
    con = db()
    if name == "post_message":
        room, author, body = a.get("room", "").strip(), a.get("author", "").strip(), a.get("message", "").strip()
        if not room or not author or not body: raise ValueError("room, author and message are required")
        now = datetime.now(timezone.utc).isoformat()
        cur = con.execute("INSERT INTO messages(room,author,body,recipients,metadata,created_at) VALUES(?,?,?,?,?,?)", (room, author, body, json.dumps(a.get("recipients", [])), json.dumps(a.get("metadata", {})), now))
        con.commit(); return {"id":cur.lastrowid,"room":room,"created_at":now}
    if name == "list_messages":
        room = a.get("room", "").strip()
        if not room: raise ValueError("room is required")
        rows = con.execute("SELECT * FROM messages WHERE room=? AND id>? ORDER BY id LIMIT ?", (room, int(a.get("after_id", 0)), min(int(a.get("limit", 50)),200))).fetchall()
        return {"room":room,"messages":[dict(r) for r in rows]}
    if name == "list_rooms":
        rows=con.execute("SELECT room, COUNT(*) AS message_count, MAX(created_at) AS last_activity FROM messages GROUP BY room ORDER BY last_activity DESC LIMIT ?",(min(int(a.get("limit",50)),200),)).fetchall()
        return {"rooms":[dict(r) for r in rows]}
    raise ValueError("unknown tool: " + name)

def respond(msg):
    method, params, ident = msg.get("method"), msg.get("params", {}), msg.get("id")
    if method == "initialize": return {"jsonrpc":"2.0","id":ident,"result":{"protocolVersion":"2025-06-18","capabilities":{"tools":{}},"serverInfo":{"name":"agent-chat","version":"1.0.0"}}}
    if method == "tools/list": return {"jsonrpc":"2.0","id":ident,"result":{"tools":schema()}}
    if method == "tools/call":
        try: out=result(call(params.get("name"),params.get("arguments",{})))
        except Exception as e: out={"content":[{"type":"text","text":str(e)}],"isError":True}
        return {"jsonrpc":"2.0","id":ident,"result":out}
    if method == "notifications/initialized": return None
    return {"jsonrpc":"2.0","id":ident,"error":{"code":-32601,"message":"Method not found"}}

for line in sys.stdin:
    try:
        answer=respond(json.loads(line))
        if answer is not None: print(json.dumps(answer), flush=True)
    except Exception as e: print(json.dumps({"jsonrpc":"2.0","id":None,"error":{"code":-32700,"message":str(e)}}),flush=True)
