from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["ui"])


@router.get("/ui/module-4", response_class=HTMLResponse)
def module4_ui() -> str:
    return """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>RMS Module-4 Verification</title>
    <style>
      :root {
        --bg: #f6f0e6;
        --ink: #1f1f1f;
        --panel: #fff6e8;
        --accent: #2c6e49;
        --muted: #6b6b6b;
      }
      * { box-sizing: border-box; font-family: "Space Grotesk", "IBM Plex Sans", sans-serif; }
      body { margin: 0; background: radial-gradient(circle at 20% 20%, #fff2da, #f3eadb 55%, #ece3d5); color: var(--ink); }
      header { padding: 24px 32px; display: flex; justify-content: space-between; align-items: center; }
      h1 { margin: 0; font-size: 28px; letter-spacing: 0.5px; }
      .token { display: flex; gap: 8px; align-items: center; }
      .token input { width: 320px; padding: 8px 10px; border-radius: 6px; border: 1px solid #d7c7b3; }
      main { display: grid; grid-template-columns: 1fr 1fr; gap: 24px; padding: 0 32px 32px; }
      section { background: var(--panel); border: 1px solid #dbcbb4; border-radius: 14px; padding: 16px; box-shadow: 0 8px 20px rgba(0,0,0,0.05); }
      section h2 { margin-top: 0; font-size: 18px; }
      label { display: block; margin: 8px 0 4px; font-size: 12px; text-transform: uppercase; letter-spacing: 0.8px; color: var(--muted); }
      input, select, textarea { width: 100%; padding: 8px 10px; border-radius: 8px; border: 1px solid #d7c7b3; background: #fff; }
      textarea { min-height: 80px; resize: vertical; }
      button { margin-top: 10px; padding: 8px 12px; border: none; border-radius: 8px; background: var(--accent); color: white; cursor: pointer; }
      pre { background: #1f1f1f; color: #f7f3ed; padding: 10px; border-radius: 8px; overflow: auto; }
      .full { grid-column: span 2; }
    </style>
  </head>
  <body>
    <header>
      <h1>Module-4 Verification & Evidence</h1>
      <div class="token">
        <label for="token">Bearer</label>
        <input id="token" placeholder="paste access token" />
      </div>
    </header>
    <main>
      <section>
        <h2>Create Test Case</h2>
        <label>Title</label>
        <input id="tc-title" />
        <label>Description</label>
        <textarea id="tc-desc"></textarea>
        <label>Verification Method</label>
        <select id="tc-method">
          <option>TEST</option>
          <option>ANALYSIS</option>
          <option>INSPECTION</option>
          <option>DEMONSTRATION</option>
        </select>
        <button onclick="createTestCase()">Create</button>
        <pre id="tc-out"></pre>
      </section>
      <section>
        <h2>Record Verification Result</h2>
        <label>Requirement ID</label>
        <input id="vr-req" />
        <label>Test Case ID</label>
        <input id="vr-test" />
        <label>Status</label>
        <select id="vr-status">
          <option>PASS</option>
          <option>FAIL</option>
          <option>BLOCKED</option>
          <option>NOT_RUN</option>
        </select>
        <label>Comment</label>
        <textarea id="vr-comment"></textarea>
        <button onclick="createVerification()">Submit</button>
        <pre id="vr-out"></pre>
      </section>
      <section>
        <h2>Attach Evidence</h2>
        <label>Related Type</label>
        <select id="ev-related-type">
          <option>VerificationResult</option>
          <option>TestCase</option>
        </select>
        <label>Related ID</label>
        <input id="ev-related-id" />
        <label>Evidence Type</label>
        <select id="ev-type">
          <option>FILE</option>
          <option>LINK</option>
          <option>NOTE</option>
        </select>
        <label>URI or Text</label>
        <textarea id="ev-uri"></textarea>
        <button onclick="attachEvidence()">Attach</button>
        <pre id="ev-out"></pre>
      </section>
      <section>
        <h2>RTM Preview</h2>
        <label>Baseline ID (optional)</label>
        <input id="rtm-baseline" />
        <button onclick="loadRtm()">Load RTM</button>
        <pre id="rtm-out"></pre>
      </section>
      <section class="full">
        <h2>Quick List Endpoints</h2>
        <button onclick="listTestCases()">List Test Cases</button>
        <button onclick="listVerification()">List Verification Results</button>
        <button onclick="listEvidence()">List Evidence</button>
        <pre id="list-out"></pre>
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

      async function createTestCase() {
        const payload = {
          title: document.getElementById("tc-title").value,
          description: document.getElementById("tc-desc").value || null,
          verification_method: document.getElementById("tc-method").value,
        };
        const res = await api("/test-cases", { method: "POST", body: JSON.stringify(payload) });
        write("tc-out", await res.json());
      }

      async function createVerification() {
        const payload = {
          requirement_id: document.getElementById("vr-req").value,
          test_case_id: document.getElementById("vr-test").value,
          status: document.getElementById("vr-status").value,
          comment: document.getElementById("vr-comment").value || null,
        };
        const res = await api("/verification-results", { method: "POST", body: JSON.stringify(payload) });
        write("vr-out", await res.json());
      }

      async function attachEvidence() {
        const payload = {
          related_type: document.getElementById("ev-related-type").value,
          related_id: document.getElementById("ev-related-id").value,
          evidence_type: document.getElementById("ev-type").value,
          uri_or_text: document.getElementById("ev-uri").value,
        };
        const res = await api("/evidence", { method: "POST", body: JSON.stringify(payload) });
        write("ev-out", await res.json());
      }

      async function loadRtm() {
        const baseline = document.getElementById("rtm-baseline").value.trim();
        const url = baseline ? `/rtm?format=json&baseline_id=${baseline}` : "/rtm?format=json";
        const res = await api(url);
        write("rtm-out", await res.json());
      }

      async function listTestCases() {
        const res = await api("/test-cases");
        write("list-out", await res.json());
      }

      async function listVerification() {
        const res = await api("/verification-results");
        write("list-out", await res.json());
      }

      async function listEvidence() {
        const res = await api("/evidence");
        write("list-out", await res.json());
      }
    </script>
  </body>
</html>
"""
