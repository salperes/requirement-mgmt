from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/ui/module-3", response_class=HTMLResponse)
def module3_ui() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RMS Module-3 Traceability</title>
    <style>
      :root {
        --bg: #f2efe8;
        --ink: #1b1b1b;
        --panel: #fffdf7;
        --accent: #234b7a;
        --accent-2: #8a3b1f;
        --muted: #6f6f6f;
      }
      * { box-sizing: border-box; font-family: "Spectral", "IBM Plex Sans", serif; }
      body { margin: 0; background: radial-gradient(circle at 20% 20%, #f5e8d6, #eef4ff 60%, #f9f0e3); color: var(--ink); }
      header { padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; gap: 16px; }
      h1 { margin: 0; font-size: 28px; letter-spacing: 0.4px; }
      main { display: grid; grid-template-columns: 1.1fr 0.9fr; gap: 24px; padding: 0 32px 32px; }
      section { background: var(--panel); border: 1px solid #e0d5c2; border-radius: 16px; padding: 16px; box-shadow: 0 10px 24px rgba(0,0,0,0.06); }
      section h2 { margin-top: 0; font-size: 18px; }
      label { display: block; margin: 8px 0 4px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.7px; color: var(--muted); }
      input, select, textarea { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #d6c7b0; background: #fff; }
      textarea { min-height: 80px; resize: vertical; }
      button { margin-top: 8px; padding: 8px 12px; border: none; border-radius: 10px; background: var(--accent); color: white; cursor: pointer; }
      button.secondary { background: #2f2f2f; }
      button.warn { background: var(--accent-2); }
      pre { background: #1e1f24; color: #f6f3ea; padding: 10px; border-radius: 10px; overflow: auto; }
      .row { display: flex; gap: 8px; flex-wrap: wrap; }
      .token { display: flex; align-items: center; gap: 8px; }
      .token input { width: 320px; }
      .full { grid-column: span 2; }
    </style>
  </head>
  <body>
    <header>
      <h1>Module-3 Traceability + Impact</h1>
      <div class="token">
        <label for="token">Bearer</label>
        <input id="token" placeholder="paste access token" />
      </div>
    </header>
    <main>
      <section>
        <h2>RTM View</h2>
        <label>Baseline ID (optional)</label>
        <input id="rtm-baseline" />
        <label>Discipline</label>
        <input id="rtm-discipline" placeholder="Software" />
        <label>Type</label>
        <input id="rtm-type" placeholder="Functional" />
        <label>Suspect Only</label>
        <select id="rtm-suspect">
          <option value="">All</option>
          <option value="true">True</option>
          <option value="false">False</option>
        </select>
        <div class="row">
          <button onclick="loadRtm('json')">Load RTM</button>
          <button class="secondary" onclick="loadRtm('csv')">Export CSV</button>
          <button class="secondary" onclick="loadRtm('md')">Export MD</button>
        </div>
        <pre id="rtm-out"></pre>
      </section>

      <section>
        <h2>Impact Analysis</h2>
        <label>Requirement ID</label>
        <input id="impact-req" />
        <button onclick="loadImpact()">Load Impact</button>
        <pre id="impact-out"></pre>
      </section>

      <section>
        <h2>Link Management</h2>
        <label>Source Type</label>
        <select id="link-source-type">
          <option>Requirement</option>
          <option>Test</option>
          <option>Design</option>
          <option>Standard</option>
        </select>
        <label>Source ID</label>
        <input id="link-source-id" />
        <label>Target Type</label>
        <select id="link-target-type">
          <option>Requirement</option>
          <option>Test</option>
          <option>Design</option>
          <option>Standard</option>
        </select>
        <label>Target ID</label>
        <input id="link-target-id" />
        <label>Link Type</label>
        <select id="link-type">
          <option>DERIVES</option>
          <option>SATISFIES</option>
          <option>VERIFIES</option>
          <option>REFERENCES</option>
        </select>
        <div class="row">
          <button onclick="createLink()">Create Link</button>
          <button class="warn" onclick="deleteLink()">Delete Link</button>
        </div>
        <label>Delete Link ID</label>
        <input id="link-delete-id" />
        <label>List Filters</label>
        <div class="row">
          <input id="link-filter-source-type" placeholder="source_type" />
          <input id="link-filter-source-id" placeholder="source_id" />
          <input id="link-filter-target-type" placeholder="target_type" />
          <input id="link-filter-target-id" placeholder="target_id" />
          <input id="link-filter-type" placeholder="link_type" />
        </div>
        <button class="secondary" onclick="listLinks()">List Links</button>
        <pre id="link-out"></pre>
      </section>

      <section class="full">
        <h2>Suspect Clear</h2>
        <div class="row">
          <input id="suspect-entity-type" placeholder="Entity Type (Test/Design/...)" />
          <input id="suspect-entity-id" placeholder="Entity ID" />
          <button onclick="clearSuspect()">Clear Suspect</button>
        </div>
        <pre id="suspect-out"></pre>
      </section>
    </main>
    <script>
      const api = (path, opts = {}) => {
        const token = document.getElementById("token").value.trim();
        const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
        if (token) headers["Authorization"] = `Bearer ${token}`;
        return fetch(path, Object.assign({}, opts, { headers }));
      };
      const write = (id, data) => document.getElementById(id).textContent = data;

      async function loadRtm(format) {
        const baseline = document.getElementById("rtm-baseline").value.trim();
        const discipline = document.getElementById("rtm-discipline").value.trim();
        const type = document.getElementById("rtm-type").value.trim();
        const suspect = document.getElementById("rtm-suspect").value;
        const params = new URLSearchParams();
        params.set("format", format);
        if (baseline) params.set("baseline_id", baseline);
        if (discipline) params.set("discipline", discipline);
        if (type) params.set("type", type);
        if (suspect) params.set("suspect", suspect);
        const url = `/rtm?${params.toString()}`;
        const res = await api(url, { headers: { "Content-Type": "text/plain" } });
        const text = await res.text();
        write("rtm-out", text);
      }

      async function loadImpact() {
        const reqId = document.getElementById("impact-req").value.trim();
        const res = await api(`/requirements/${reqId}/impact`);
        write("impact-out", JSON.stringify(await res.json(), null, 2));
      }

      async function createLink() {
        const payload = {
          source_type: document.getElementById("link-source-type").value,
          source_id: document.getElementById("link-source-id").value,
          target_type: document.getElementById("link-target-type").value,
          target_id: document.getElementById("link-target-id").value,
          link_type: document.getElementById("link-type").value,
        };
        const res = await api("/links", { method: "POST", body: JSON.stringify(payload) });
        write("link-out", JSON.stringify(await res.json(), null, 2));
      }

      async function deleteLink() {
        const linkId = document.getElementById("link-delete-id").value.trim();
        const res = await api(`/links/${linkId}`, { method: "DELETE" });
        write("link-out", JSON.stringify(await res.json(), null, 2));
      }

      async function listLinks() {
        const params = new URLSearchParams();
        const pairs = [
          ["source_type", "link-filter-source-type"],
          ["source_id", "link-filter-source-id"],
          ["target_type", "link-filter-target-type"],
          ["target_id", "link-filter-target-id"],
          ["link_type", "link-filter-type"],
        ];
        for (const [key, id] of pairs) {
          const value = document.getElementById(id).value.trim();
          if (value) params.set(key, value);
        }
        const url = params.toString() ? `/links?${params.toString()}` : "/links";
        const res = await api(url);
        write("link-out", JSON.stringify(await res.json(), null, 2));
      }

      async function clearSuspect() {
        const entityType = document.getElementById("suspect-entity-type").value.trim();
        const entityId = document.getElementById("suspect-entity-id").value.trim();
        const res = await api(`/suspect/${entityType}/${entityId}/clear`, { method: "POST" });
        write("suspect-out", JSON.stringify(await res.json(), null, 2));
      }
    </script>
  </body>
</html>
"""
