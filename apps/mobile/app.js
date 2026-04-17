const API_BASE = `${window.location.origin}/api/v1`;
const DRAFT_KEY = "gabinete_mobile_cadastro_draft";

const state = {
  step: 1,
  token: null,
  territories: [],
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function formData() {
  return Object.fromEntries(new FormData($("#cadastro-form")).entries());
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
  select.innerHTML =
    '<option value="">Sem territorio definido</option>' +
    state.territories.map((item) => `<option value="${item.id}">${item.nome} - ${item.tipo}</option>`).join("");
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
  localStorage.setItem(DRAFT_KEY, JSON.stringify(data));
  $("#sync-state").textContent = "Rascunho salvo neste aparelho";
  setMessage("Rascunho salvo.");
}

function loadDraft() {
  const raw = localStorage.getItem(DRAFT_KEY);
  if (!raw) return;
  const data = JSON.parse(raw);
  Object.entries(data).forEach(([key, value]) => {
    const input = $(`[name="${key}"]`);
    if (input) input.value = value;
  });
  $("#sync-state").textContent = "Rascunho recuperado";
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
    const contato = await api("/contatos", {
      method: "POST",
      body: JSON.stringify({
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
      }),
    });
    await api(`/contatos/${contato.data.id}/consentimentos`, {
      method: "POST",
      body: JSON.stringify({
        canal: data.canal_whatsapp ? "WHATSAPP" : "TELEFONE",
        consentido: data.consentido === "true",
        finalidade: data.finalidade,
        forma_registro: data.forma_registro,
        observacao: data.observacoes || null,
      }),
    });
    localStorage.removeItem(DRAFT_KEY);
    $("#cadastro-form").reset();
    state.step = 1;
    updateStep();
    $("#sync-state").textContent = "Cadastro sincronizado";
    setMessage("Cadastro enviado com sucesso.");
  } catch (error) {
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
