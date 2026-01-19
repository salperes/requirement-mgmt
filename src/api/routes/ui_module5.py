from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/ui/module-5", response_class=HTMLResponse)
def module5_ui() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RMS Module-5 Import & Parsing</title>
    <style>
      :root {
        --bg: #f8f5f1;
        --ink: #1e1b16;
        --panel: #fffdf9;
        --accent: #c65d3b;
        --accent-dark: #8f3f27;
        --muted: #6b5d4f;
        --line: #e1d5c8;
      }
      * { box-sizing: border-box; font-family: "Manrope", "SF Pro Text", sans-serif; }
      body {
        margin: 0;
        color: var(--ink);
        background:
          radial-gradient(circle at 15% 10%, rgba(255,214,165,0.45), transparent 45%),
          radial-gradient(circle at 80% 20%, rgba(255,201,192,0.35), transparent 50%),
          linear-gradient(120deg, #f7efe6, #f1ece5 55%, #efe6dc);
      }
      header {
        padding: 28px 36px 18px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }
      h1 {
        margin: 0;
        font-family: "DM Serif Display", "Times New Roman", serif;
        font-size: 30px;
        letter-spacing: 0.4px;
      }
      .token {
        display: flex;
        gap: 10px;
        align-items: center;
      }
      .token input {
        width: 320px;
        padding: 8px 10px;
        border-radius: 10px;
        border: 1px solid var(--line);
      }
      main {
        padding: 0 36px 36px;
        display: grid;
        gap: 20px;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
      }
      section {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 16px 24px rgba(31, 20, 8, 0.08);
      }
      section h2 {
        margin: 0 0 12px;
        font-size: 18px;
      }
      label {
        display: block;
        margin: 10px 0 6px;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.9px;
        color: var(--muted);
      }
      input, select, textarea {
        width: 100%;
        padding: 8px 10px;
        border-radius: 10px;
        border: 1px solid var(--line);
        background: #fff;
      }
      textarea { min-height: 80px; resize: vertical; }
      button {
        margin-top: 10px;
        padding: 8px 12px;
        border: none;
        border-radius: 10px;
        background: var(--accent);
        color: white;
        cursor: pointer;
      }
      button.secondary {
        background: #f1e1d9;
        color: var(--accent-dark);
      }
      .inline {
        display: grid;
        gap: 10px;
        grid-template-columns: 1fr 1fr;
      }
      pre {
        background: #1c1511;
        color: #f8f2ea;
        padding: 10px;
        border-radius: 10px;
        overflow: auto;
      }
    </style>
  </head>
  <body>
    <header>
      <h1>Import & Clause Review</h1>
      <div class="token">
        <label for="token">Bearer</label>
        <input id="token" placeholder="paste access token" />
      </div>
    </header>
    <main>
      <section>
        <h2>Upload Document</h2>
        <label>File (PDF/DOCX/XLSX)</label>
        <input id="import-file" type="file" />
        <button onclick="uploadImport()">Upload</button>
        <pre id="import-out"></pre>
      </section>
      <section>
        <h2>Browse Imports</h2>
        <button class="secondary" onclick="listImports()">List Imports</button>
        <label>Import ID</label>
        <input id="import-id" placeholder="import session id" />
        <button onclick="loadImport()">Load Import</button>
        <button onclick="loadClauses()">Load Clauses</button>
        <pre id="clauses-out"></pre>
      </section>
      <section>
        <h2>Clause Review</h2>
        <label>Clause ID</label>
        <input id="clause-id" placeholder="clause id" />
        <div class="inline">
          <div>
            <label>Discipline</label>
            <select id="clause-discipline">
              <option value="">Default</option>
              <option>System</option>
              <option>Mechanical</option>
              <option>Software</option>
              <option>Electronics</option>
              <option>Automation</option>
              <option>Optics</option>
              <option>Other</option>
            </select>
          </div>
          <div>
            <label>Primary Type</label>
            <select id="clause-type">
              <option value="">Default</option>
              <option>Functional</option>
              <option>Performance</option>
              <option>Safety</option>
              <option>Security</option>
              <option>Regulatory</option>
              <option>Interface</option>
              <option>Constraint</option>
            </select>
          </div>
        </div>
        <label>Title (optional)</label>
        <input id="clause-title" />
        <label>Edit Text (optional)</label>
        <textarea id="clause-edit"></textarea>
        <button onclick="acceptClause()">Accept</button>
        <button class="secondary" onclick="rejectClause()">Reject</button>
        <pre id="review-out"></pre>
      </section>
      <section>
        <h2>Requirement Source</h2>
        <label>Requirement ID</label>
        <input id="source-req-id" placeholder="requirement id" />
        <button onclick="loadSource()">Load Source</button>
        <pre id="source-out"></pre>
      </section>
    </main>
    <script>
      const api = (path, opts = {}) => {
        const token = document.getElementById("token").value.trim();
        const headers = Object.assign({}, opts.headers || {});
        if (!(opts.body instanceof FormData)) {
          headers["Content-Type"] = "application/json";
        }
        if (token) headers["Authorization"] = `Bearer ${token}`;
        return fetch(path, Object.assign({}, opts, { headers }));
      };
      const write = (id, data) => {
        document.getElementById(id).textContent = JSON.stringify(data, null, 2);
      };

      async function uploadImport() {
        const fileInput = document.getElementById("import-file");
        if (!fileInput.files.length) return;
        const data = new FormData();
        data.append("file", fileInput.files[0]);
        const res = await api("/imports", { method: "POST", body: data });
        write("import-out", await res.json());
      }

      async function listImports() {
        const res = await api("/imports");
        write("clauses-out", await res.json());
      }

      async function loadImport() {
        const importId = document.getElementById("import-id").value.trim();
        if (!importId) return;
        const res = await api(`/imports/${importId}`);
        write("clauses-out", await res.json());
      }

      async function loadClauses() {
        const importId = document.getElementById("import-id").value.trim();
        if (!importId) return;
        const res = await api(`/imports/${importId}/clauses`);
        write("clauses-out", await res.json());
      }

      async function acceptClause() {
        const importId = document.getElementById("import-id").value.trim();
        const clauseId = document.getElementById("clause-id").value.trim();
        if (!importId || !clauseId) return;
        const payload = {
          title: document.getElementById("clause-title").value || null,
          edited_text: document.getElementById("clause-edit").value || null,
          discipline: document.getElementById("clause-discipline").value || null,
          req_type_primary: document.getElementById("clause-type").value || null,
        };
        const res = await api(`/imports/${importId}/clauses/${clauseId}/accept`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        write("review-out", await res.json());
      }

      async function rejectClause() {
        const importId = document.getElementById("import-id").value.trim();
        const clauseId = document.getElementById("clause-id").value.trim();
        if (!importId || !clauseId) return;
        const res = await api(`/imports/${importId}/clauses/${clauseId}/reject`, { method: "POST" });
        write("review-out", await res.json());
      }

      async function loadSource() {
        const reqId = document.getElementById("source-req-id").value.trim();
        if (!reqId) return;
        const res = await api(`/requirements/${reqId}/source`);
        write("source-out", await res.json());
      }
    </script>
  </body>
</html>
"""
