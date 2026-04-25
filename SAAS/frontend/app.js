(() => {
  const apiBase = "";
  const $ = (id) => document.getElementById(id);

  $("apiBase").textContent = window.location.origin;

  function setStatus(kind, msg) {
    const el = $("status");
    el.className = kind;
    el.textContent = msg || "";
  }

  function setMeta(msg) {
    $("meta").textContent = msg || "";
  }

  function clearOutput() {
    $("output").innerHTML = "";
    setMeta("");
  }

  function renderRecommendations(recs) {
    const out = $("output");
    out.innerHTML = "";

    for (const r of recs) {
      const item = document.createElement("div");
      item.className = "item";
      const conf = Math.round((r.confidence ?? 0) * 100);
      item.innerHTML = `
        <div class="item-title">
          <strong>${escapeHtml(r.title)}</strong>
          <span class="badge">${conf}%</span>
        </div>
        <p>${escapeHtml(r.reason)}</p>
      `;
      out.appendChild(item);
    }
  }

  function renderTextPreview(preview) {
    const out = $("output");
    out.innerHTML = "";
    const item = document.createElement("div");
    item.className = "item";
    item.innerHTML = `
      <div class="item-title">
        <strong>Prévia do texto extraído</strong>
        <span class="badge mono">preview</span>
      </div>
      <p class="mono" style="white-space: pre-wrap">${escapeHtml(preview || "")}</p>
    `;
    out.appendChild(item);
  }

  function escapeHtml(str) {
    return String(str || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  async function postFile(path, file, params = {}) {
    const url = new URL(path, window.location.origin + apiBase);
    for (const [k, v] of Object.entries(params)) url.searchParams.set(k, String(v));

    const form = new FormData();
    form.append("file", file);

    const res = await fetch(url, { method: "POST", body: form });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      const msg = data?.detail || `Erro HTTP ${res.status}`;
      throw new Error(msg);
    }
    return data;
  }

  function setBusy(isBusy) {
    $("btnAnalyze").disabled = isBusy;
    $("btnExtract").disabled = isBusy;
  }

  $("btnExtract").addEventListener("click", async () => {
    clearOutput();
    setStatus("", "");

    const file = $("resume").files?.[0];
    if (!file) {
      setStatus("error", "Selecione um arquivo de currículo.");
      return;
    }

    setBusy(true);
    try {
      const data = await postFile("/resume/extract", file);
      setMeta(`${data.kind} • ${data.chars} chars`);
      renderTextPreview(data.preview);
      setStatus("ok", "Texto extraído com sucesso.");
    } catch (e) {
      setStatus("error", e?.message || "Falha ao extrair texto.");
    } finally {
      setBusy(false);
    }
  });

  $("form").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    clearOutput();
    setStatus("", "");

    const fullName = $("fullName").value.trim();
    if (fullName.length < 3) {
      setStatus("error", "Informe seu nome completo.");
      return;
    }

    const file = $("resume").files?.[0];
    if (!file) {
      setStatus("error", "Selecione um arquivo de currículo.");
      return;
    }

    setBusy(true);
    try {
      const limit = Number($("limit").value || 8);
      const data = await postFile("/recommendations", file, { limit });
      setMeta(`${data.kind} • ${data.chars} chars`);
      renderRecommendations(data.recommendations || []);
      setStatus("ok", "Recomendações geradas.");
    } catch (e) {
      setStatus("error", e?.message || "Falha ao gerar recomendações.");
    } finally {
      setBusy(false);
    }
  });
})();

