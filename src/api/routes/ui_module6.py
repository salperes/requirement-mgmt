from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/ui/module-6", response_class=HTMLResponse)
def module6_ui() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RMS Module-6 Compliance Matrix</title>
    <style>
      :root {
        --bg: #f7f3ee;
        --ink: #1a1a1a;
        --panel: #fffaf6;
        --accent: #2d6a4f;
        --accent-2: #f4b860;
        --muted: #6b6b6b;
        --line: #ded2c4;
      }
      * { box-sizing: border-box; font-family: "Sora", "Avenir Next", sans-serif; }
      body {
        margin: 0;
        color: var(--ink);
        background:
          radial-gradient(circle at 10% 10%, rgba(244,184,96,0.18), transparent 45%),
          radial-gradient(circle at 85% 20%, rgba(45,106,79,0.15), transparent 50%),
          linear-gradient(120deg, #f5efe7, #f1ece6 55%, #efe6dd);
      }
      header {
        padding: 26px 36px 16px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 16px;
      }
      h1 {
        margin: 0;
        font-family: "Bodoni Moda", "Times New Roman", serif;
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
        grid-template-columns: repeat(auto-fit, minmax(290px, 1fr));
      }
      section {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 16px;
        padding: 16px;
        box-shadow: 0 16px 24px rgba(31, 20, 8, 0.08);
      }
      section h2 { margin: 0 0 12px; font-size: 18px; }
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
        background: #efe1d0;
        color: #4a3a2a;
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
      <h1>Compliance Matrix</h1>
      <div class="token">
        <label for="token">Bearer</label>
        <input id="token" placeholder="paste access token" />
      </div>
    </header>
    <main>
      <section>
        <h2>Standards Library</h2>
        <label>Code</label>
        <input id="std-code" placeholder="ISO 26262" />
        <label>Title</label>
        <input id="std-title" placeholder="Road vehicles - Functional safety" />
        <div class="inline">
          <div>
            <label>Version</label>
            <input id="std-version" placeholder="2018" />
          </div>
          <div>
            <label>Year</label>
            <input id="std-year" type="number" />
          </div>
        </div>
        <label>Publisher</label>
        <input id="std-publisher" placeholder="ISO" />
        <button onclick="createStandard()">Create Standard</button>
        <button class="secondary" onclick="listStandards()">List Standards</button>
        <pre id="std-out"></pre>
      </section>

      <section>
        <h2>Standard Clauses</h2>
        <label>Standard ID</label>
        <input id="clause-standard-id" />
        <label>Clause Code</label>
        <input id="clause-code" placeholder="5.4.3" />
        <label>Title</label>
        <input id="clause-title" placeholder="Safety goal" />
        <label>Text</label>
        <textarea id="clause-text"></textarea>
        <button onclick="createClause()">Add Clause</button>
        <button class="secondary" onclick="listClauses()">List Clauses</button>
        <pre id="clause-out"></pre>
      </section>

      <section>
        <h2>Compliance Mapping</h2>
        <label>Requirement ID</label>
        <input id="map-req" />
        <label>Standard Clause ID</label>
        <input id="map-clause" />
        <label>Status</label>
        <select id="map-status">
          <option>COMPLIANT</option>
          <option>NON_COMPLIANT</option>
          <option>PARTIAL</option>
          <option>NOT_APPLICABLE</option>
        </select>
        <label>Justification</label>
        <textarea id="map-justification"></textarea>
        <button onclick="createMapping()">Save Mapping</button>
        <pre id="map-out"></pre>
      </section>

      <section>
        <h2>Compliance Matrix</h2>
        <label>Baseline ID (optional)</label>
        <input id="matrix-baseline" />
        <label>Standard ID (optional)</label>
        <input id="matrix-standard" />
        <div class="inline">
          <button onclick="loadMatrix()">Load Matrix</button>
          <button class="secondary" onclick="exportMatrix()">Export CSV</button>
        </div>
        <pre id="matrix-out"></pre>
      </section>

      <section>
        <h2>Gap Analysis</h2>
        <button onclick="loadGaps()">Analyze Gaps</button>
        <pre id="gap-out"></pre>
      </section>
    </main>
    <script>
      const api = (path, opts = {}) => {
        const token = document.getElementById("token").value.trim();
        const headers = Object.assign({ "Content-Type": "application/json" }, opts.headers || {});
        if (token) headers["Authorization"] = `Bearer ${token}`;
        return fetch(path, Object.assign({}, opts, { headers }));
      };
      const write = (id, data) => {
        document.getElementById(id).textContent = JSON.stringify(data, null, 2);
      };

      async function createStandard() {
        const payload = {
          code: document.getElementById("std-code").value,
          title: document.getElementById("std-title").value,
          version: document.getElementById("std-version").value || null,
          publication_year: document.getElementById("std-year").value || null,
          publisher: document.getElementById("std-publisher").value || null,
        };
        const res = await api("/standards", { method: "POST", body: JSON.stringify(payload) });
        write("std-out", await res.json());
      }

      async function listStandards() {
        const res = await api("/standards");
        write("std-out", await res.json());
      }

      async function createClause() {
        const standardId = document.getElementById("clause-standard-id").value.trim();
        const payload = {
          clause_code: document.getElementById("clause-code").value,
          title: document.getElementById("clause-title").value || null,
          text: document.getElementById("clause-text").value,
        };
        const res = await api(`/standards/${standardId}/clauses`, {
          method: "POST",
          body: JSON.stringify(payload),
        });
        write("clause-out", await res.json());
      }

      async function listClauses() {
        const standardId = document.getElementById("clause-standard-id").value.trim();
        const res = await api(`/standards/${standardId}/clauses`);
        write("clause-out", await res.json());
      }

      async function createMapping() {
        const payload = {
          requirement_id: document.getElementById("map-req").value,
          standard_clause_id: document.getElementById("map-clause").value,
          compliance_status: document.getElementById("map-status").value,
          justification: document.getElementById("map-justification").value || null,
        };
        const res = await api("/compliance-mappings", { method: "POST", body: JSON.stringify(payload) });
        write("map-out", await res.json());
      }

      function buildQuery() {
        const baseline = document.getElementById("matrix-baseline").value.trim();
        const standard = document.getElementById("matrix-standard").value.trim();
        const params = new URLSearchParams();
        if (baseline) params.append("baseline_id", baseline);
        if (standard) params.append("standard_id", standard);
        const suffix = params.toString();
        return suffix ? `?${suffix}` : "";
      }

      async function loadMatrix() {
        const res = await api(`/compliance${buildQuery()}`);
        write("matrix-out", await res.json());
      }

      async function exportMatrix() {
        const query = buildQuery();
        const suffix = query ? `${query}&format=csv` : "?format=csv";
        const res = await api(`/compliance/export${suffix}`);
        document.getElementById("matrix-out").textContent = await res.text();
      }

      async function loadGaps() {
        const res = await api(`/compliance${buildQuery()}`);
        const data = await res.json();
        write("gap-out", data.gap_analysis || {});
      }
    </script>
  </body>
</html>
"""