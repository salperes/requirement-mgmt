from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/ui/module-2", response_class=HTMLResponse)
def module2_ui() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RMS Module-2 Workflow</title>
    <style>
      :root {
        --bg: #f3efe7;
        --ink: #1a1a1a;
        --panel: #fffaf1;
        --accent: #3f4c8a;
        --accent-2: #c8572a;
        --muted: #6b6b6b;
      }
      * { box-sizing: border-box; font-family: "Fraunces", "IBM Plex Sans", serif; }
      body { margin: 0; background: linear-gradient(120deg, #f5ead5, #f1f6ff 60%, #f9efe6); color: var(--ink); }
      header { padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
      h1 { margin: 0; font-size: 28px; letter-spacing: 0.4px; }
      main { display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 24px; padding: 0 32px 32px; }
      section { background: var(--panel); border: 1px solid #dfd4c0; border-radius: 16px; padding: 16px; box-shadow: 0 10px 24px rgba(0,0,0,0.06); }
      section h2 { margin-top: 0; font-size: 18px; }
      label { display: block; margin: 8px 0 4px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.7px; color: var(--muted); }
      input, select, textarea { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #d6c7b0; background: #fff; }
      textarea { min-height: 80px; resize: vertical; }
      button { margin-top: 8px; padding: 8px 12px; border: none; border-radius: 10px; background: var(--accent); color: white; cursor: pointer; }
      button.secondary { background: #2f2f2f; }
      button.warn { background: var(--accent-2); }
      pre { background: #1e1f24; color: #f6f3ea; padding: 10px; border-radius: 10px; overflow: auto; }
      .stack { display: grid; gap: 12px; }
      .status { padding: 10px 12px; border-radius: 12px; background: #e9e2d4; font-weight: 600; }
      .full { grid-column: span 2; }
      .row { display: flex; gap: 8px; flex-wrap: wrap; }
      .token { display: flex; align-items: center; gap: 8px; }
      .token input { width: 320px; }
    </style>
  </head>
  <body>
    <header>
      <h1>Module-2 Workflow + Collaboration</h1>
      <div class="token">
        <label for="token">Bearer</label>
        <input id="token" placeholder="paste access token" />
      </div>
    </header>
    <main>
      <section class="stack">
        <h2>Requirement Detail</h2>
        <label>Requirement ID</label>
        <input id="req-id" />
        <button onclick="loadRequirement()">Load Requirement</button>
        <div class="status" id="req-status">Status: -</div>
        <div class="row">
          <button onclick="changeStatus('Review')">Request Review</button>
          <button class="secondary" onclick="changeStatus('Draft')">Send Back to Draft</button>
        </div>
        <div class="row">
          <button onclick="approve('APPROVE')">Approve</button>
          <button class="warn" onclick="approve('REJECT')">Reject</button>
        </div>
        <label>Reason (optional for Review/Draft, required for Reject)</label>
        <textarea id="req-reason"></textarea>
        <pre id="req-out"></pre>
      </section>

      <section class="stack">
        <h2>Approval Panel</h2>
        <button onclick="loadApprovals()">Load Approvals</button>
        <pre id="approval-out"></pre>
      </section>

      <section class="stack">
        <h2>Comments</h2>
        <button onclick="loadComments()">Refresh Comments</button>
        <label>New Comment</label>
        <textarea id="comment-text" placeholder="Type comment, use @email or @username"></textarea>
        <button onclick="createComment()">Post Comment</button>
        <label>Edit Comment ID</label>
        <input id="comment-id" />
        <label>Edit Text</label>
        <textarea id="comment-edit-text"></textarea>
        <div class="row">
          <button class="secondary" onclick="editComment()">Edit</button>
          <button class="warn" onclick="deleteComment()">Delete</button>
        </div>
        <pre id="comment-out"></pre>
      </section>

      <section class="stack">
        <h2>Notifications Inbox</h2>
        <div class="row">
          <button onclick="loadNotifications()">Load Notifications</button>
          <button class="secondary" onclick="loadNotifications(true)">Unread Only</button>
        </div>
        <label>Mark Read (Notification ID)</label>
        <input id="notif-id" />
        <button onclick="markRead()">Mark Read</button>
        <pre id="notif-out"></pre>
      </section>

      <section class="full">
        <h2>Quick Status</h2>
        <pre id="status-out"></pre>
      </section>
    </main>
    <script>
      const api = (path, opts = {}) => {
        const token = document.getElementById("token").value.trim();
        const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
        if (token) headers["Authorization"] = `Bearer ${token}`;
        return fetch(path, Object.assign({}, opts, { headers }));
      };
      const write = (id, data) => document.getElementById(id).textContent = JSON.stringify(data, null, 2);

      async function loadRequirement() {
        const reqId = document.getElementById("req-id").value.trim();
        const res = await api(`/requirements/${reqId}`);
        const data = await res.json();
        write("req-out", data);
        document.getElementById("req-status").textContent = `Status: ${data.status || "-"}`;
      }

      async function changeStatus(toStatus) {
        const reqId = document.getElementById("req-id").value.trim();
        const reason = document.getElementById("req-reason").value || null;
        const res = await api(`/requirements/${reqId}/status`, {
          method: "POST",
          body: JSON.stringify({ to_status: toStatus, reason }),
        });
        const data = await res.json();
        write("req-out", data);
        document.getElementById("req-status").textContent = `Status: ${data.status || "-"}`;
      }

      async function approve(decision) {
        const reqId = document.getElementById("req-id").value.trim();
        const reason = document.getElementById("req-reason").value || null;
        const payload = { decision, reason };
        const res = await api(`/requirements/${reqId}/approve`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        const data = await res.json();
        write("req-out", data);
        document.getElementById("req-status").textContent = `Status: ${data.status || "-"}`;
      }

      async function loadApprovals() {
        const reqId = document.getElementById("req-id").value.trim();
        const res = await api(`/requirements/${reqId}/approvals`);
        write("approval-out", await res.json());
      }

      async function loadComments() {
        const reqId = document.getElementById("req-id").value.trim();
        const res = await api(`/requirements/${reqId}/comments`);
        write("comment-out", await res.json());
      }

      async function createComment() {
        const reqId = document.getElementById("req-id").value.trim();
        const text = document.getElementById("comment-text").value;
        const res = await api(`/requirements/${reqId}/comments`, {
          method: "POST",
          body: JSON.stringify({ text }),
        });
        write("comment-out", await res.json());
      }

      async function editComment() {
        const commentId = document.getElementById("comment-id").value.trim();
        const text = document.getElementById("comment-edit-text").value;
        const res = await api(`/comments/${commentId}`, {
          method: "PATCH",
          body: JSON.stringify({ text }),
        });
        write("comment-out", await res.json());
      }

      async function deleteComment() {
        const commentId = document.getElementById("comment-id").value.trim();
        const res = await api(`/comments/${commentId}`, { method: "DELETE" });
        write("comment-out", await res.json());
      }

      async function loadNotifications(unreadOnly = false) {
        const url = unreadOnly ? "/notifications?unread_only=true" : "/notifications";
        const res = await api(url);
        write("notif-out", await res.json());
      }

      async function markRead() {
        const notifId = document.getElementById("notif-id").value.trim();
        const res = await api(`/notifications/${notifId}/read`, { method: "POST" });
        write("notif-out", await res.json());
      }
    </script>
  </body>
</html>
"""
