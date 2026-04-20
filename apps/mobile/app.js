const API_BASE = `${window.location.origin}/api/v1`;
const DRAFT_KEY = "gabinete_mobile_cadastro_draft";

const state = {
  step: 1,
  token: null,
  territories: [],
  draftSyncId: null,
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function newClientGeneratedId() {
  if (window.crypto?.randomUUID) return `mobile-${window.crypto.randomUUID()}`;
  return `mobile-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

function formData() {
  return Object.fromEntries(new FormData($("#cadastro-form")).entries());
}

function currentDraftEnvelope() {
  const raw = localStorage.getItem(DRAFT_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

function persistDraft(data) {
  const envelope = {
    sync_id: state.draftSyncId || newClientGeneratedId(),
    data,
  };
  state.draftSyncId = envelope.sync_id;
  localStorage.setItem(DRAFT_KEY, JSON.stringify(envelope));
}

function clearDraft() {
  state.draftSyncId = null;
  localStorage.removeItem(DRAFT_KEY);
}

function setMessage(text, error = false) {
  const message = $("#message");
  message.textContent = text || "";
  message.classList.toggle("error", error);
}

async function api(path, options = {}) {
  const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
  const payload = await response.json();
  if (!response.ok) throw new Error(payload?.error?.message || "Falha na API.");
  return payload;
}

async function connect() {
  try {
    const response = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ email_login: "assessor@gabineteia.local", senha: "Senha@123" }),
    });
    state.token = response.data.access_token;
    $("#connection").textContent = "Online";
    $("#connection").classList.remove("offline");
    await loadTerritories();
  } catch (error) {
    $("#connection").textContent = "Offline";
    $("#connection").classList.add("offline");
    $("#sync-state").textContent = "Modo rascunho ativo";
  }
}

async function loadTerritories() {
  const response = await api("/territorios?page_size=100");
  state.territories = response.data;
  const select = $("#territory-select");
  const current = select.value;
  const ordered = [...state.territories].sort((left, right) => {
    const typeOrder = { REGIAO: 0, BAIRRO: 1, MICROAREA: 2 };
    const leftOrder = typeOrder[left.tipo] ?? 99;
    const rightOrder = typeOrder[right.tipo] ?? 99;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return String(left.nome || "").localeCompare(String(right.nome || ""), "pt-BR");
  });
  const groups = [
    ["REGIAO", "Regionais"],
    ["BAIRRO", "Bairros"],
    ["MICROAREA", "Microareas"],
  ];
  select.innerHTML =
    '<option value="">Sem territorio definido</option>' +
    groups
      .map(([type, label]) => {
        const items = ordered.filter((item) => item.tipo === type);
        if (!items.length) return "";
        return `<optgroup label="${label}">${items.map((item) => `<option value="${item.id}">${item.nome} - ${item.tipo}</option>`).join("")}</optgroup>`;
      })
      .join("");
  if (state.territories.some((item) => item.id === current)) select.value = current;
}

function updateStep() {
  $$(".steps button").forEach((button) => {
    button.classList.toggle("active", Number(button.dataset.step) === state.step);
  });
  $$(".step").forEach((panel) => {
    panel.classList.toggle("active", Number(panel.dataset.panel) === state.step);
  });
  $("#back").disabled = state.step === 1;
  $("#step-back-top")?.classList.toggle("hidden", state.step === 1);
  $("#next").textContent = state.step === 3 ? "Enviar" : "Avancar";
  if (state.step === 3) renderReview();
}

function renderReview() {
  const data = formData();
  $("#review").innerHTML = [
    ["Nome", data.nome || "Nao informado"],
    ["Telefone", data.telefone_principal || "Nao informado"],
    ["Bairro", data.bairro || "Nao informado"],
    ["Territorio", $("#territory-select").selectedOptions[0]?.textContent || "Nao informado"],
    ["Consentimento", data.consentido === "true" ? "Sim" : "Nao"],
    ["Finalidade", data.finalidade || "Atendimento institucional"],
    ["Perfil", `${data.nivel_relacionamento || "CONTATO"} / ${data.engajamento || "FRIO"}`],
    ["Influencia", data.influencia || "BAIXA"],
    ["Voto 2028", data.voto_2028 || "INDEFINIDO"],
  ]
    .map(([label, value]) => `<div class="review-row"><strong>${label}</strong><span>${value}</span></div>`)
    .join("");
}

function saveDraft() {
  const data = formData();
  persistDraft(data);
  $("#sync-state").textContent = "Rascunho salvo neste aparelho";
  setMessage("Rascunho salvo.");
}

function loadDraft() {
  const envelope = currentDraftEnvelope();
  if (!envelope?.data) return;
  state.draftSyncId = envelope.sync_id || newClientGeneratedId();
  const data = envelope.data;
  Object.entries(data).forEach(([key, value]) => {
    const input = $(`[name="${key}"]`);
    if (input) input.value = value;
  });
  $("#sync-state").textContent = "Rascunho recuperado";
}

async function syncContact(data) {
  const clientGeneratedId = state.draftSyncId || newClientGeneratedId();
  state.draftSyncId = clientGeneratedId;
  persistDraft(data);
  const payload = {
    items: [
      {
        client_generated_id: clientGeneratedId,
        entidade: "contato",
        payload: {
          nome: data.nome,
          telefone_principal: data.telefone_principal || null,
          email: data.email || null,
          cpf: data.cpf || null,
          bairro: data.bairro || null,
          territorio_id: data.territorio_id || null,
          logradouro: data.logradouro || null,
          observacoes: data.observacoes || null,
          nivel_relacionamento: data.nivel_relacionamento || "CONTATO",
          engajamento: data.engajamento || "FRIO",
          voto_2028: data.voto_2028 || "INDEFINIDO",
          influencia: data.influencia || "BAIXA",
          prioridade_politica: data.engajamento === "FORTE" || data.influencia === "ALTA" ? "ALTA" : "MEDIA",
          origem_politica: data.origem_politica || "DECLARADO",
          origem_cadastro: "MOBILE_CAMPO",
          tipo_contato: "CIDADAO",
        },
      },
    ],
  };
  const response = await api("/mobile/sync", {
    method: "POST",
    body: JSON.stringify(payload),
  });
  const processed = response.data.processed?.[0];
  if (!processed?.entidade_id) throw new Error("Sincronizacao mobile nao retornou o contato criado.");
  return processed.entidade_id;
}

async function ensureConsent(contactId, data) {
  const existing = await api(`/contatos/${contactId}/consentimentos`);
  const channel = data.canal_whatsapp ? "WHATSAPP" : "TELEFONE";
  const hasEquivalent = existing.data.some(
    (item) =>
      item.canal === channel &&
      Boolean(item.consentido) === (data.consentido === "true") &&
      item.finalidade === data.finalidade,
  );
  if (hasEquivalent) return;
  await api(`/contatos/${contactId}/consentimentos`, {
    method: "POST",
    body: JSON.stringify({
      canal: channel,
      consentido: data.consentido === "true",
      finalidade: data.finalidade,
      forma_registro: data.forma_registro,
      observacao: data.observacoes || null,
    }),
  });
}

async function submitCadastro(event) {
  event.preventDefault();
  setMessage("Enviando cadastro...");
  const data = formData();
  if (!data.nome) {
    setMessage("Informe o nome completo.", true);
    state.step = 1;
    updateStep();
    return;
  }
  try {
    if (!state.token) await connect();
    if (!state.token) throw new Error("Sem conexao com a API. Salve como rascunho.");
    const contactId = await syncContact(data);
    await ensureConsent(contactId, data);
    clearDraft();
    $("#cadastro-form").reset();
    state.step = 1;
    updateStep();
    $("#sync-state").textContent = "Cadastro sincronizado via fila mobile";
    setMessage("Cadastro enviado com sucesso.");
  } catch (error) {
    persistDraft(data);
    setMessage(error.message, true);
  }
}

function bindEvents() {
  $$(".steps button").forEach((button) => {
    button.addEventListener("click", () => {
      state.step = Number(button.dataset.step);
      updateStep();
    });
  });
  $("#next").addEventListener("click", () => {
    if (state.step === 3) {
      $("#cadastro-form").requestSubmit();
      return;
    }
    state.step += 1;
    updateStep();
  });
  $("#back").addEventListener("click", () => {
    state.step = Math.max(1, state.step - 1);
    updateStep();
  });
  $("#step-back-top")?.addEventListener("click", () => {
    state.step = Math.max(1, state.step - 1);
    updateStep();
  });
  $("#save-draft").addEventListener("click", saveDraft);
  $("#cadastro-form").addEventListener("submit", submitCadastro);
  $("#cadastro-form").addEventListener("input", () => {
    if (state.step === 3) renderReview();
  });
}

loadDraft();
bindEvents();
updateStep();
connect();
