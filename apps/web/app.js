const API = "/api/v1";

const DEMAND_STATUS = [
  "ABERTA",
  "EM_TRIAGEM",
  "EM_ATENDIMENTO",
  "ENCAMINHADA",
  "AGUARDANDO_RETORNO",
  "CONCLUIDA",
  "SUSPENSA",
  "CANCELADA",
  "REABERTA",
  "ARQUIVADA",
];

const STATUS_LABELS = {
  ABERTA: "Nova",
  EM_TRIAGEM: "Em triagem",
  EM_ATENDIMENTO: "Em instrucao",
  ENCAMINHADA: "Encaminhada",
  AGUARDANDO_RETORNO: "Aguardando orgao",
  CONCLUIDA: "Concluida",
  SUSPENSA: "Suspensa",
  CANCELADA: "Cancelada",
  REABERTA: "Reaberta",
  ARQUIVADA: "Arquivada",
  EXCLUIDO: "Excluida",
};

const DEMAND_COLUMNS = [
  ["ABERTA", "Novas"],
  ["EM_ATENDIMENTO", "Em instrucao"],
  ["AGUARDANDO_RETORNO", "Aguardando orgao"],
  ["CONCLUIDA", "Concluidas"],
];

const AGENDA_TYPES = {
  REUNIAO_BASE: "Reuniao da Base",
  VISITA_BAIRRO: "Visita de Bairro",
  AGENDA_LIDERANCAS: "Agenda com Liderancas",
  ACAO_SAUDE: "Acao de Saude",
  AULA_ABERTA: "Aula Aberta",
  MUTIRAO_SOCIAL: "Mutirao Social",
  EVENTO_GRANDE: "Evento Grande",
  ATENDIMENTO_COMUNITARIO: "Atendimento Comunitario",
};

const LEGISLATIVE_STAGES = [
  ["REDACAO", "Redacao"],
  ["COMISSAO", "Comissao"],
  ["PLENARIO", "Plenario"],
  ["SANCAO_VETO", "Sancao/Veto"],
];

const TERRITORY_TYPE_ORDER = {
  REGIAO: 0,
  BAIRRO: 1,
  MICROAREA: 2,
};

const state = {
  token: localStorage.getItem("gabinete_token"),
  user: null,
  demands: [],
  contacts: [],
  users: [],
  agenda: [],
  territories: [],
  dashboard: null,
  overview: null,
  interactions: [],
  propositions: [],
  amendments: [],
  offices: [],
  audit: [],
  syncHistory: [],
  reportCatalog: [],
  selectedDemandId: null,
  selectedContactId: null,
  editingDemandId: null,
  editingContactId: null,
  editingUserId: null,
  globalSearch: "",
  currentSection: "executivo",
  previousSection: "executivo",
  assistantContext: null,
  assistantInsight: null,
  assistantLoading: false,
  sentimentSnapshot: null,
  sentimentFilters: {
    canal: "",
    periodo: "",
    territorio: "",
  },
  moduleContext: {
    atendimento: null,
    crm: null,
    agenda: null,
  },
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

function isCompactSidebar() {
  return window.matchMedia("(max-width: 920px)").matches;
}

function openSidebar() {
  if (!isCompactSidebar()) return;
  $(".sidebar")?.classList.add("open");
  $("#sidebar-overlay")?.classList.remove("hidden");
  $("#sidebar-toggle")?.setAttribute("aria-expanded", "true");
}

function closeSidebar() {
  $(".sidebar")?.classList.remove("open");
  $("#sidebar-overlay")?.classList.add("hidden");
  $("#sidebar-toggle")?.setAttribute("aria-expanded", "false");
}

function toggleSidebar() {
  if ($(".sidebar")?.classList.contains("open")) {
    closeSidebar();
    return;
  }
  openSidebar();
}

function updateMobileBackButton() {
  const button = $("#mobile-back");
  if (!button) return;
  const shouldShow = state.currentSection !== "executivo";
  button.classList.toggle("hidden", !shouldShow);
  button.textContent = "Voltar ao menu";
  button.setAttribute("aria-label", "Voltar ao menu inicial");
}

function goBackFromMobileView() {
  goToInitialMenu();
}

function goToInitialMenu() {
  navigateTo("executivo");
  refreshAssistantContext(defaultAssistantContext("executivo"), { force: true });
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setMessage(selector, text) {
  const el = $(selector);
  if (el) el.textContent = text || "";
}

function normalizePublicAssetUrl(url) {
  if (!url) return "";
  const rendered = String(url).replaceAll("\\", "/").trim();
  if (!rendered) return "";
  if (
    rendered.startsWith("http://") ||
    rendered.startsWith("https://") ||
    rendered.startsWith("blob:") ||
    rendered.startsWith("data:") ||
    rendered.startsWith("/uploads-public/")
  ) {
    return rendered;
  }
  if (rendered.startsWith("data/uploads/")) {
    const parts = rendered.split("/");
    return `/uploads-public/${parts[parts.length - 1]}`;
  }
  if (!rendered.includes("/")) {
    return `/uploads-public/${rendered}`;
  }
  return rendered.startsWith("/") ? rendered : `/${rendered.replace(/^\/+/, "")}`;
}

function setMediaLink(selector, url, fileName, defaultText = "Abrir arquivo atual") {
  const link = $(selector);
  if (!link) return;
  const normalizedUrl = normalizePublicAssetUrl(url);
  if (!normalizedUrl) {
    link.classList.add("hidden");
    link.removeAttribute("href");
    link.textContent = defaultText;
    return;
  }
  link.href = normalizedUrl;
  link.textContent = fileName ? `${defaultText.replace(" atual", "")}: ${fileName}` : defaultText;
  link.classList.remove("hidden");
}

function setImagePreview(selector, url, altText = "Foto do perfil") {
  const image = $(selector);
  if (!image) return;
  const normalizedUrl = normalizePublicAssetUrl(url);
  if (!normalizedUrl) {
    image.classList.add("hidden");
    image.removeAttribute("src");
    image.alt = altText;
    return;
  }
  image.src = normalizedUrl;
  image.alt = altText;
  image.classList.remove("hidden");
}

function previewLocalImage(file, imageSelector, linkSelector) {
  if (!file) return;
  const objectUrl = URL.createObjectURL(file);
  setImagePreview(imageSelector, objectUrl, `Pre-visualizacao de ${file.name}`);
  setMediaLink(linkSelector, objectUrl, file.name, "Abrir foto atual");
}

function buildQuery(params = {}) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") {
      query.set(key, value);
    }
  });
  const rendered = query.toString();
  return rendered ? `?${rendered}` : "";
}

function requestedContextFromUrl() {
  const params = new URLSearchParams(window.location.search);
  return {
    section: params.get("section") || "",
    focus: params.get("focus") || "",
    demandId: params.get("demanda_id") || "",
    contactId: params.get("contato_id") || "",
    territoryId: params.get("territorio_id") || "",
    teamId: params.get("equipe_id") || "",
    userId: params.get("usuario_id") || "",
  };
}

function contextMetaList(context, fallback = []) {
  return [...(context?.meta || []), ...fallback].filter(Boolean);
}

function setModuleContext(moduleId, context) {
  if (!state.moduleContext[moduleId]) {
    state.moduleContext[moduleId] = null;
  }
  state.moduleContext[moduleId] = context || null;
}

function clearModuleContext(moduleId) {
  if (!state.moduleContext[moduleId]) return;
  state.moduleContext[moduleId] = null;
  if (moduleId === "atendimento") {
    renderDemands();
    return;
  }
  if (moduleId === "crm") {
    renderCRM();
    return;
  }
  if (moduleId === "agenda") {
    renderAgenda();
  }
}

function renderModuleContext(moduleId, count, emptyLabel) {
  const panel = $(`#${moduleId}-context`);
  if (!panel) return;
  const context = state.moduleContext[moduleId];
  if (!context) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }
  const meta = contextMetaList(context, [typeof count === "number" ? `${count} item(ns)` : "", emptyLabel]).filter(Boolean);
  panel.classList.remove("hidden");
  panel.innerHTML = `
    <div>
      <p class="eyebrow">${escapeHtml(context.eyebrow || "Filtro aplicado")}</p>
      <strong>${escapeHtml(context.title || "Contexto ativo")}</strong>
      <p>${escapeHtml(context.description || "A visualizacao atual esta filtrada a partir de um contexto vindo do painel ou do app do vereador.")}</p>
      <div class="module-context-meta">${meta.map((item) => `<span class="module-context-chip">${escapeHtml(item)}</span>`).join("")}</div>
    </div>
    <button type="button" class="secondary" data-clear-module-context="${escapeHtml(moduleId)}">Limpar filtro</button>
  `;
}

function demandMatchesModuleContext(item) {
  const context = state.moduleContext.atendimento;
  if (!context) return true;
  if (context.statuses?.length && !context.statuses.includes(item.status)) return false;
  if (context.territory && !sameTerritoryScope(demandTerritory(item), context.territory)) return false;
  if (typeof context.predicate === "function" && !context.predicate(item)) return false;
  return true;
}

function contactMatchesModuleContext(item) {
  const context = state.moduleContext.crm;
  if (!context) return true;
  if (context.onlyLeadership && !isLeadershipContact(item)) return false;
  if (context.engagements?.length && !context.engagements.includes(item.engajamento)) return false;
  if (context.territory && !sameTerritoryScope(item.territorio_nome || item.bairro || "Sem territorio", context.territory)) return false;
  if (typeof context.predicate === "function" && !context.predicate(item)) return false;
  return true;
}

function agendaMatchesModuleContext(item) {
  const context = state.moduleContext.agenda;
  if (!context) return true;
  if (context.onlyPending && ["REALIZADO", "CANCELADO"].includes(item.status)) return false;
  if (typeof context.predicate === "function" && !context.predicate(item)) return false;
  return true;
}

function openDemandModuleContext(filters = {}) {
  setModuleContext("atendimento", {
    title: filters.title || "Demandas",
    eyebrow: filters.eyebrow || "Acompanhamento e acoes",
    description: filters.description || "A fila de atendimento foi filtrada no proprio modulo para preservar contexto, selecao e operacao.",
    statuses: filters.statuses || null,
    territory: filters.territory || "",
    predicate: filters.predicate,
    meta: contextMetaList(filters, []),
  });
  navigateTo("atendimento");
  renderDemands();
}

function openContactModuleContext(filters = {}) {
  setModuleContext("crm", {
    title: filters.title || "Contatos",
    eyebrow: filters.eyebrow || "Relacionamento politico",
    description: filters.description || "A base de relacionamento foi filtrada no proprio modulo para manter leitura e navegacao no mesmo fluxo.",
    onlyLeadership: Boolean(filters.onlyLeadership),
    engagements: filters.engagements || null,
    territory: filters.territory || "",
    predicate: filters.predicate,
    meta: contextMetaList(filters, []),
  });
  navigateTo("crm");
  renderCRM();
}

function openAgendaModuleContext(filters = {}) {
  setModuleContext("agenda", {
    title: filters.title || "Agenda",
    eyebrow: filters.eyebrow || "Agenda politica",
    description: filters.description || "A agenda foi filtrada no proprio modulo para manter o encadeamento com compromissos e relatorios.",
    onlyPending: Boolean(filters.onlyPending),
    predicate: filters.predicate,
    meta: contextMetaList(filters, []),
  });
  navigateTo("agenda");
  renderAgenda();
}

function bindElementEvent(selector, eventName, handler) {
  const element = $(selector);
  if (element) {
    element.addEventListener(eventName, handler);
  }
}

async function api(path, options = {}) {
  const headers = {
    ...(options.headers || {}),
  };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (state.token) {
    headers.Authorization = `Bearer ${state.token}`;
  }
  const response = await fetch(`${API}${path}`, {
    ...options,
    headers,
  });
  if (response.status === 204) return null;
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload?.error?.message || "Falha na requisicao.");
  }
  return payload;
}

function showApp() {
  $("#login").classList.add("hidden");
  $("#app").classList.remove("hidden");
}

function showLogin() {
  $("#app").classList.add("hidden");
  $("#login").classList.remove("hidden");
}

async function onLogout() {
  try {
    if (state.token) {
      await api("/auth/logout", { method: "POST", body: JSON.stringify({ origem: "web" }) });
    }
  } catch (error) {
    console.error(error);
  } finally {
    state.token = null;
    state.user = null;
    state.currentSection = "executivo";
    state.previousSection = "executivo";
    localStorage.removeItem("gabinete_token");
    showLogin();
    setMessage("#login-message", "Sessao encerrada.");
  }
}

function statusClass(value) {
  return String(value || "").toLowerCase().replaceAll("_", "-");
}

function formatCurrency(value) {
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL", maximumFractionDigits: 0 }).format(
    Number(value || 0),
  );
}

function formatDate(value) {
  if (!value) return "Sem data";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "Sem data";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(date);
}

function initials(name) {
  return String(name || "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0])
    .join("")
    .toUpperCase();
}

function avatarMarkup(name, url, className = "") {
  const classes = ["avatar", ...String(className || "").split(/\s+/).filter(Boolean)];
  const normalizedUrl = normalizePublicAssetUrl(url);
  if (normalizedUrl) {
    return `<span class="${escapeHtml(classes.join(" "))}"><img class="avatar-photo" src="${escapeHtml(normalizedUrl)}" alt="Foto de ${escapeHtml(name || "perfil")}" loading="lazy" /></span>`;
  }
  return `<span class="${escapeHtml(classes.join(" "))}">${escapeHtml(initials(name))}</span>`;
}

function demandStatusLabel(status) {
  return STATUS_LABELS[status] || status || "Sem situacao";
}

function isLeadershipContact(contact) {
  return contact?.nivel_relacionamento === "LIDERANCA" || contact?.influencia === "ALTA";
}

function isStrongEngagementContact(contact) {
  return ["FORTE", "ALTO"].includes(contact?.engajamento);
}

function labelCode(value) {
  if (!value) return "Nao informado";
  const known = {
    PLANEJADO: "Planejado",
    CONFIRMADO: "Confirmado",
    REALIZADO: "Realizado",
    CANCELADO: "Cancelado",
    INDICACAO: "Indicacao",
    INDICACAO_VAGA: "Indicacao para vaga",
    ESPECIALISTA: "Especialista",
    ADMINISTRATIVO: "Administrativo",
    OUTROS: "Outros",
    EMPENHO: "Empenho",
    LIQUIDACAO: "Liquidacao",
    PAGAMENTO: "Pagamento",
    ENTREGUE: "Entregue",
    RASCUNHO: "Rascunho",
    ENVIADO: "Enviado",
    RESPONDIDO: "Respondido",
    CONCLUIDO: "Concluido",
    ARQUIVADO: "Arquivado",
    ATIVO: "Ativo",
    INATIVO: "Inativo",
  };
  if (known[value]) return known[value];
  return String(value).toLowerCase().replaceAll("_", " ").replace(/(^|\s)\S/g, (letter) => letter.toUpperCase());
}

function contactForDemand(demand) {
  return state.contacts.find((item) => item.id === demand.cidadao_id) || null;
}

function demandTerritory(demand) {
  const contact = contactForDemand(demand);
  return demand.territorio_nome || contact?.territorio_nome || contact?.bairro || "Sem territorio";
}

function normalizeTerritoryLabel(value) {
  return String(value || "")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "")
    .toLowerCase()
    .replace(/^(regional|regiao)\s+/, "")
    .replace(/-/g, " ")
    .replace(/\s+/g, " ")
    .trim();
}

function sameTerritoryScope(left, right) {
  const leftKey = normalizeTerritoryLabel(left);
  const rightKey = normalizeTerritoryLabel(right);
  return Boolean(leftKey && rightKey && leftKey === rightKey);
}

function territoryOptionLabel(item) {
  if (item.tipo === "REGIAO") return item.nome;
  return `${item.nome} · ${labelCode(item.tipo)}`;
}

function territoryOptionGroups() {
  return [
    ["REGIAO", "Regionais"],
    ["BAIRRO", "Bairros"],
    ["MICROAREA", "Microareas"],
  ];
}

function demandanteTypeLabel(value) {
  const labels = {
    CIDADAO: "Cidadao",
    LIDERANCA: "Lideranca",
    VEREADOR: "Vereador",
    COLABORADOR: "Colaborador",
  };
  return labels[value] || labelCode(value || "CIDADAO");
}

function activeDemandanteContacts() {
  return state.contacts.filter((item) => item.tipo_contato !== "ORGAO_PUBLICO" && !["EXCLUIDO", "INATIVO"].includes(item.status));
}

function internalDemandanteUsers() {
  return state.users.filter((item) => item.ativo);
}

function linkedContactForUser(userId) {
  return activeDemandanteContacts().find((item) => item.usuario_id === userId) || null;
}

function isWithinDays(value, maxAgeDays, minAgeDays = 0) {
  if (!value) return false;
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return false;
  const ageDays = (Date.now() - date.getTime()) / 86400000;
  return ageDays <= maxAgeDays && ageDays > minAgeDays;
}

function percentageDelta(current, previous) {
  if (!previous) return current ? 100 : 0;
  return Math.round(((current - previous) / previous) * 100);
}

function isGenericTerritoryLabel(value) {
  const normalized = normalizeTerritoryLabel(value);
  return ["", "geral", "todos os territorios", "todo territorio", "sem territorio"].includes(normalized);
}

function sentimentTerritoryFocus() {
  const selectedTerritory = state.sentimentFilters.territorio || "";
  return isGenericTerritoryLabel(selectedTerritory) ? "" : selectedTerritory;
}

function isVacancyDemand(type) {
  return type === "INDICACAO_VAGA";
}

function syncVacancyFields(form, mode) {
  if (!form) return;
  const demandType = form.elements.tipo_demanda?.value;
  const vacancyWrap = form.querySelector(`[data-vacancy-fields="${mode}"]`);
  const othersWrap = form.querySelector(`[data-vaga-outros-wrap="${mode}"]`);
  const showVacancy = isVacancyDemand(demandType);
  vacancyWrap?.classList.toggle("hidden", !showVacancy);
  if (!showVacancy) {
    if (form.elements.tipo_vaga_pretendida) form.elements.tipo_vaga_pretendida.value = "";
    if (form.elements.vaga_outros_descricao) form.elements.vaga_outros_descricao.value = "";
    if (mode === "create" && form.elements.cv_file) form.elements.cv_file.value = "";
  }
  const showOthers = showVacancy && form.elements.tipo_vaga_pretendida?.value === "OUTROS";
  othersWrap?.classList.toggle("hidden", !showOthers);
}

function setCvLink(selector, url, fileName) {
  setMediaLink(selector, url, fileName, "Abrir CV atual");
}

function setProfilePhotoState(prefix, url, fileName, altText) {
  setImagePreview(`#${prefix}-photo-preview`, url, altText);
  setMediaLink(`#${prefix}-photo-link`, url, fileName, "Abrir foto atual");
}

function resetContactFormState() {
  state.editingContactId = null;
  const form = $("#contact-form");
  if (!form) return;
  form.reset();
  if (form.elements.foto_upload_id) form.elements.foto_upload_id.value = "";
  if (form.elements.foto_url) form.elements.foto_url.value = "";
  $("#contact-submit").textContent = "Salvar cadastro";
  setProfilePhotoState("contact", null, null, "Foto do cadastro");
}

function resetUserFormState() {
  state.editingUserId = null;
  const form = $("#user-form");
  if (!form) return;
  form.reset();
  if (form.elements.foto_upload_id) form.elements.foto_upload_id.value = "";
  if (form.elements.foto_url) form.elements.foto_url.value = "";
  $("#user-submit").textContent = "Salvar colaborador";
  setProfilePhotoState("user", null, null, "Foto do colaborador");
}

function demandSlaLabel(item) {
  if (!item?.sla_data_calculada) return "Prazo a definir";
  return `Prazo ${formatDate(item.sla_data_calculada)}`;
}

function compactAssistantLabel(label) {
  const replacements = {
    "Atualizar contexto": "Atualizar IA",
    "Resumir contexto": "Resumir",
    "Sugerir proxima etapa": "Proxima acao",
    "Definir responsavel": "Atribuir",
    "Abrir relacionamento": "Abrir CRM",
    "Nova agenda orientada": "Nova agenda",
    "Abrir execucao": "Ver emendas",
    "Abrir emendas": "Ver emendas",
    "Abrir fluxo": "Abrir",
  };
  return replacements[label] || label;
}

function upsertById(items, nextItem) {
  if (!nextItem?.id) return items;
  const remaining = items.filter((item) => item.id !== nextItem.id);
  return [nextItem, ...remaining];
}

function userOptions(selected) {
  return (
    '<option value="">Sem responsavel</option>' +
    state.users
      .map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === selected ? "selected" : ""}>${escapeHtml(item.nome)}</option>`)
      .join("")
  );
}

function territoryOptions(selected) {
  const sortedTerritories = [...state.territories].sort((left, right) => {
    const leftOrder = TERRITORY_TYPE_ORDER[left.tipo] ?? 99;
    const rightOrder = TERRITORY_TYPE_ORDER[right.tipo] ?? 99;
    if (leftOrder !== rightOrder) return leftOrder - rightOrder;
    return String(left.nome || "").localeCompare(String(right.nome || ""), "pt-BR");
  });
  const groupedOptions = territoryOptionGroups()
    .map(([type, label]) => {
      const items = sortedTerritories.filter((item) => item.tipo === type);
      if (!items.length) return "";
      return `
        <optgroup label="${escapeHtml(label)}">
          ${items
            .map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === selected ? "selected" : ""}>${escapeHtml(territoryOptionLabel(item))}</option>`)
            .join("")}
        </optgroup>
      `;
    })
    .join("");
  return (
    '<option value="">Sem territorio</option>' +
    groupedOptions
  );
}

function selectedDemand() {
  return state.demands.find((item) => item.id === state.selectedDemandId) || state.demands[0] || null;
}

function selectedContact() {
  return state.contacts.find((item) => item.id === state.selectedContactId) || state.contacts[0] || null;
}

function selectedAgenda() {
  return state.agenda.find((item) => item.status !== "REALIZADO" && item.status !== "CANCELADO") || state.agenda[0] || null;
}

function selectedOffice() {
  return state.offices.find((item) => !["RESPONDIDO", "CONCLUIDO"].includes(item.status)) || state.offices[0] || null;
}

function selectedAmendment() {
  return (
    [...state.amendments]
      .sort((left, right) => {
        const rightDate = right.data_empenho || "";
        const leftDate = left.data_empenho || "";
        if (rightDate !== leftDate) return rightDate.localeCompare(leftDate);
        return Number(right.valor_empenhado || 0) - Number(left.valor_empenhado || 0);
      })[0] || null
  );
}

function renderSelectedDemand() {
  const label = $("#selected-demand-label");
  if (!label) return;
  const contextLabel = state.assistantInsight?.contexto?.rotulo;
  if (contextLabel) {
    label.textContent = contextLabel;
    return;
  }
  const demand = selectedDemand();
  if (!demand) {
    label.textContent = "Nenhum contexto selecionado.";
    return;
  }
  const vacancyLabel = isVacancyDemand(demand.tipo_demanda)
    ? ` - ${labelCode(demand.tipo_vaga_pretendida || "OUTROS")}${demand.vaga_outros_descricao ? ` (${demand.vaga_outros_descricao})` : ""}`
    : "";
  label.textContent = `${demand.titulo} - ${demand.cidadao_nome || "demandante pendente"}${vacancyLabel}`;
}

function assistantContextKey(context) {
  return JSON.stringify([
    context?.contexto_tipo || "",
    context?.contexto_id || "",
    context?.modulo || "",
    context?.origem || "",
    context?.filtro || "",
    context?.canal || "",
    context?.periodo || "",
    context?.territorio || "",
  ]);
}

function hasEntityForAssistantContext(context) {
  if (!context?.contexto_tipo) return false;
  if (!context.contexto_id) return true;
  if (context.contexto_tipo === "demanda") return state.demands.some((item) => item.id === context.contexto_id);
  if (context.contexto_tipo === "contato") return state.contacts.some((item) => item.id === context.contexto_id);
  if (context.contexto_tipo === "agenda") return state.agenda.some((item) => item.id === context.contexto_id);
  if (context.contexto_tipo === "oficio") return state.offices.some((item) => item.id === context.contexto_id);
  if (context.contexto_tipo === "emenda") return state.amendments.some((item) => item.id === context.contexto_id);
  return true;
}

function defaultAssistantContext(sectionId = state.currentSection) {
  const section = sectionId === "list-view" ? state.previousSection || "executivo" : sectionId || "executivo";
  if (section === "atendimento" && selectedDemand()) {
    return {
      contexto_tipo: "demanda",
      contexto_id: selectedDemand().id,
      modulo: "atendimento",
      origem: "modulo",
    };
  }
  if (section === "crm" && selectedContact()) {
    return {
      contexto_tipo: "contato",
      contexto_id: selectedContact().id,
      modulo: "crm",
      origem: "modulo",
    };
  }
  if (section === "agenda" && selectedAgenda()) {
    return {
      contexto_tipo: "agenda",
      contexto_id: selectedAgenda().id,
      modulo: "agenda",
      origem: "modulo",
    };
  }
  if (section === "oficios" && selectedOffice()) {
    return {
      contexto_tipo: "oficio",
      contexto_id: selectedOffice().id,
      modulo: "oficios",
      origem: "modulo",
    };
  }
  if (section === "emendas" && selectedAmendment()) {
    return {
      contexto_tipo: "emenda",
      contexto_id: selectedAmendment().id,
      modulo: "emendas",
      origem: "modulo",
    };
  }
  return {
    contexto_tipo: "modulo",
    modulo: section,
    origem: "modulo",
  };
}

function normalizeAssistantContext(nextContext = null) {
  const merged = {
    ...(defaultAssistantContext(nextContext?.modulo || state.currentSection)),
    ...(state.assistantContext || {}),
    ...(nextContext || {}),
  };
  if (!hasEntityForAssistantContext(merged)) {
    return defaultAssistantContext(merged.modulo || state.currentSection);
  }
  return {
    contexto_tipo: merged.contexto_tipo || "modulo",
    contexto_id: merged.contexto_id || null,
    modulo: merged.modulo || state.currentSection || "executivo",
    origem: merged.origem || "modulo",
    filtro: merged.filtro || null,
    canal: merged.canal || null,
    periodo: merged.periodo || null,
    territorio: merged.territorio || null,
  };
}

function renderAssistantPanel() {
  const title = $("#assistant-title");
  const subtitle = $("#assistant-subtitle");
  const output = $("#ai-output");
  const suggestions = $("#assistant-suggestions");
  const insight = state.assistantInsight;

  if (title) {
    title.textContent = state.assistantLoading ? "IA Assistiva" : insight?.titulo || "Apoio operacional";
  }
  renderSelectedDemand();
  if (subtitle) {
    subtitle.textContent = state.assistantLoading
      ? "Analisando o modulo e a selecao atual..."
      : insight?.subtitulo || "Selecione um item, card ou alerta para orientar a IA.";
  }
  if (output) {
    output.textContent = state.assistantLoading
      ? "A IA esta consolidando sinais do contexto atual e preparando proximas acoes manuais." 
      : insight?.resumo || "A IA nao altera estado automaticamente. Ela organiza contexto, prioriza a proxima acao manual e aponta o fluxo mais util.";
  }
  if (suggestions) {
    const items = insight?.sugestoes || [];
    suggestions.innerHTML = items.length
      ? items
          .map(
            (item) => `
              <article class="assistant-suggestion">
                <strong>${escapeHtml(item.titulo)}</strong>
                <p>${escapeHtml(item.descricao)}</p>
                <button
                  type="button"
                  class="secondary"
                  data-ai-execute-action="${escapeHtml(item.action)}"
                  data-ai-section="${escapeHtml(item.section || "")}" 
                  data-ai-entity-id="${escapeHtml(item.entity_id || "")}">
                  ${escapeHtml(compactAssistantLabel(item.label || "Abrir"))}
                </button>
              </article>
            `,
          )
          .join("")
      : '<div class="assistant-empty">Nenhuma sugestao contextual disponivel para este ponto do fluxo.</div>';
  }
}

async function refreshAssistantContext(nextContext = null, options = {}) {
  const context = normalizeAssistantContext(nextContext);
  const sameContext = assistantContextKey(context) === assistantContextKey(state.assistantContext);
  if (sameContext && state.assistantInsight && !options.force) {
    renderAssistantPanel();
    return;
  }
  state.assistantContext = context;
  state.assistantLoading = true;
  renderAssistantPanel();
  try {
    const payload = await api("/ai/contexto-operacional", {
      method: "POST",
      body: JSON.stringify(context),
    });
    state.assistantInsight = payload.data;
  } catch (error) {
    state.assistantInsight = {
      titulo: "IA Assistiva",
      subtitulo: "Falha ao analisar o contexto atual",
      resumo: error.message,
      contexto: {
        rotulo: "Contexto indisponivel",
      },
      sugestoes: [],
    };
  } finally {
    state.assistantLoading = false;
    renderAssistantPanel();
  }
}

function focusElement(selector) {
  const element = $(selector);
  if (!element) return;
  element.scrollIntoView({ behavior: "smooth", block: "start" });
  if (typeof element.focus === "function") {
    element.focus({ preventScroll: true });
  }
}

function territoryFromAssistantContext() {
  if ((state.assistantContext?.contexto_tipo || state.assistantInsight?.contexto?.tipo) === "sentimento") {
    return {
      id: "",
      name: state.assistantContext?.territorio || state.sentimentFilters.territorio || "Sem territorio",
    };
  }
  const territoryId = state.assistantContext?.contexto_id || state.assistantInsight?.contexto?.id || null;
  const territoryName = state.assistantContext?.filtro || state.assistantInsight?.contexto?.filtro || state.assistantInsight?.contexto?.rotulo || null;
  const territory = territoryId ? state.territories.find((item) => item.id === territoryId) : null;
  return {
    id: territory?.id || territoryId || "",
    name: territory?.nome || territoryName || "Sem territorio",
  };
}

function sentimentFromAssistantContext() {
  return {
    focus: state.assistantContext?.filtro || state.assistantInsight?.contexto?.filtro || "negative",
    title: state.assistantInsight?.subtitulo || "Humor publico",
    summary: state.assistantInsight?.resumo || "",
    channel: state.assistantContext?.canal || state.sentimentFilters.canal || "",
    period: state.assistantContext?.periodo || state.sentimentFilters.periodo || "",
    territory: state.assistantContext?.territorio || state.sentimentFilters.territorio || "",
  };
}

function currentSentiment() {
  return state.sentimentSnapshot || state.overview?.sentimento || {};
}

function buildAlertAssistantContext(meta = {}) {
  const action = meta.action || "";
  const entityId = meta.entityId || null;
  const section = meta.section || state.currentSection || "executivo";
  const territory = meta.territory || null;
  const territoryId = meta.territoryId || null;
  const filter = meta.filter || null;

  if (action === "open-demand" && entityId) {
    return {
      contexto_tipo: "demanda",
      contexto_id: entityId,
      modulo: section || "atendimento",
      origem: "alerta",
      filtro: filter,
      territorio,
    };
  }
  if (action === "open-office" && entityId) {
    return {
      contexto_tipo: "oficio",
      contexto_id: entityId,
      modulo: section || "oficios",
      origem: "alerta",
      filtro: filter,
      territorio,
    };
  }
  if (action === "open-emendas") {
    return {
      contexto_tipo: "dashboard_card",
      contexto_id: null,
      modulo: section || "emendas",
      origem: "alerta",
      filtro: filter || "amendments",
      territorio,
    };
  }
  if (territory || territoryId) {
    return {
      contexto_tipo: "territorio",
      contexto_id: territoryId,
      modulo: "executivo",
      origem: "alerta",
      filtro: territory,
      territorio,
    };
  }
  return {
    contexto_tipo: "modulo",
    contexto_id: null,
    modulo: section,
    origem: "alerta",
    filtro: filter,
  };
}

async function refreshSentimentSummary(options = {}) {
  const query = buildQuery(state.sentimentFilters);
  try {
    const payload = await api(`/sentimento-social/resumo${query}`);
    state.sentimentSnapshot = payload.data;
  } catch (error) {
    if (!options.silent) {
      console.error(error);
    }
    state.sentimentSnapshot = state.overview?.sentimento || null;
  }
  if (options.render !== false) {
    renderSentiment();
  }
}

async function onSentimentFilterChange(event) {
  const { sentimentFilter } = event.currentTarget.dataset;
  if (!sentimentFilter) return;
  state.sentimentFilters[sentimentFilter] = event.currentTarget.value || "";
  await refreshSentimentSummary();
  await refreshAssistantContext(
    {
      contexto_tipo: "sentimento",
      modulo: "executivo",
      origem: "sentimento-filtro",
      filtro: state.assistantContext?.filtro || "negative",
      canal: state.sentimentFilters.canal || null,
      periodo: state.sentimentFilters.periodo || null,
      territorio: state.sentimentFilters.territorio || null,
    },
    { force: true },
  );
}

function prefillDemandForm({ contactId = "", territoryId = "", title = "", description = "", beneficiary = "", priority = "" } = {}) {
  const form = $("#demand-form");
  if (!form) return;
  form.reset();
  renderContactOptions();
  renderUserOptions();
  renderTerritoryOptions();
  if (contactId && form.elements.cidadao_id) form.elements.cidadao_id.value = contactId;
  if (territoryId && form.elements.territorio_id) form.elements.territorio_id.value = territoryId;
  if (title && form.elements.titulo) form.elements.titulo.value = title;
  if (description && form.elements.descricao) form.elements.descricao.value = description;
  if (beneficiary && form.elements.beneficiario_nome) form.elements.beneficiario_nome.value = beneficiary;
  if (priority && form.elements.prioridade) form.elements.prioridade.value = priority;
}

function prefillContactForm({ territoryId = "", bairro = "", notes = "", relationship = "", engagement = "", influence = "" } = {}) {
  const form = $("#contact-form");
  if (!form) return;
  navigateCadastroTab("pessoas");
  resetContactFormState();
  renderTerritoryOptions();
  if (territoryId && form.elements.territorio_id) form.elements.territorio_id.value = territoryId;
  if (bairro && form.elements.bairro) form.elements.bairro.value = bairro;
  if (notes && form.elements.observacoes) form.elements.observacoes.value = notes;
  if (relationship && form.elements.nivel_relacionamento) form.elements.nivel_relacionamento.value = relationship;
  if (engagement && form.elements.engajamento) form.elements.engajamento.value = engagement;
  if (influence && form.elements.influencia) form.elements.influencia.value = influence;
}

function prefillAgendaForm({ title = "", description = "", location = "" } = {}) {
  const form = $("#agenda-form");
  if (!form) return;
  form.reset();
  renderUserOptions();
  if (title && form.elements.titulo) form.elements.titulo.value = title;
  if (description && form.elements.descricao) form.elements.descricao.value = description;
  if (location && form.elements.local_texto) form.elements.local_texto.value = location;
}

function prefillOfficeForm({ demandId = "", title = "", subject = "", followUp = "", destination = "" } = {}) {
  const form = $("#office-form");
  if (!form) return;
  form.reset();
  renderOfficeDemandOptions();
  if (demandId && form.elements.demanda_id) form.elements.demanda_id.value = demandId;
  if (title && form.elements.titulo) form.elements.titulo.value = title;
  if (subject && form.elements.assunto) form.elements.assunto.value = subject;
  if (followUp && form.elements.follow_up) form.elements.follow_up.value = followUp;
  if (destination && form.elements.orgao_destino) form.elements.orgao_destino.value = destination;
}

function executeAssistantAction(action, section, entityId) {
  if (!action) return;
  if (["open-demands", "contacts", "leadership", "strong-engagement", "pending-agenda", "pending-offices", "amendments", "legislative"].includes(action)) {
    handleDashboardAction(action);
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "ia", filtro: action }, { force: true });
    return;
  }
  if (action === "open-demand" && entityId) {
    state.selectedDemandId = entityId;
    navigateTo("atendimento");
    renderDemands();
    refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: entityId, modulo: "atendimento", origem: "ia" }, { force: true });
    return;
  }
  if (action === "focus-demand-assignee" && entityId) {
    state.selectedDemandId = entityId;
    navigateTo("atendimento");
    renderDemands();
    refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: entityId, modulo: "atendimento", origem: "ia" }, { force: true });
    requestAnimationFrame(() => focusElement(`[data-demand-responsible="${entityId}"]`));
    return;
  }
  if (action === "focus-demand-edit" && entityId) {
    state.selectedDemandId = entityId;
    navigateTo("atendimento");
    renderDemands();
    startDemandEdit(entityId);
    refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: entityId, modulo: "atendimento", origem: "ia" }, { force: true });
    return;
  }
  if (action === "open-contact" && entityId) {
    state.selectedContactId = entityId;
    navigateTo("crm");
    renderCRM();
    refreshAssistantContext({ contexto_tipo: "contato", contexto_id: entityId, modulo: "crm", origem: "ia" }, { force: true });
    return;
  }
  if (action === "focus-contact-edit" && entityId) {
    state.selectedContactId = entityId;
    navigateTo("cadastros");
    startContactEdit(entityId);
    refreshAssistantContext({ contexto_tipo: "contato", contexto_id: entityId, modulo: "cadastros", origem: "ia" }, { force: true });
    return;
  }
  if (action === "focus-user-edit" && entityId) {
    navigateTo("cadastros");
    startUserEdit(entityId);
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "cadastros", origem: "ia" }, { force: true });
    return;
  }
  if (action === "focus-interaction-form" && entityId) {
    state.selectedContactId = entityId;
    navigateTo("crm");
    renderCRM();
    if ($("#interaction-contact-select")) {
      $("#interaction-contact-select").value = entityId;
    }
    refreshAssistantContext({ contexto_tipo: "contato", contexto_id: entityId, modulo: "crm", origem: "ia" }, { force: true });
    requestAnimationFrame(() => focusElement("#interaction-form"));
    return;
  }
  if (action === "focus-demand-create" && entityId) {
    navigateTo("atendimento");
    renderDemands();
    prefillDemandForm({ contactId: entityId });
    refreshAssistantContext({ contexto_tipo: "contato", contexto_id: entityId, modulo: "atendimento", origem: "ia" }, { force: true });
    requestAnimationFrame(() => focusElement("#demand-form"));
    return;
  }
  if (action === "focus-demand-create-territory") {
    const territory = territoryFromAssistantContext();
    navigateTo("atendimento");
    renderDemands();
    prefillDemandForm({
      territoryId: territory.id,
      title: `Nova demanda em ${territory.name}`,
      description: `Registro orientado pela IA a partir da leitura territorial de ${territory.name}.`,
      beneficiary: territory.name,
    });
    refreshAssistantContext({ contexto_tipo: "territorio", contexto_id: territory.id || null, modulo: "atendimento", origem: "ia", filtro: territory.name }, { force: true });
    requestAnimationFrame(() => focusElement("#demand-form"));
    return;
  }
  if (action === "focus-contact-create-territory") {
    const territory = territoryFromAssistantContext();
    navigateTo("cadastros");
    prefillContactForm({
      territoryId: territory.id,
      bairro: territory.name,
      notes: `Cadastro orientado pela IA para ampliar a base politica em ${territory.name}.`,
      relationship: "CONTATO",
      engagement: "MORNO",
      influence: "MEDIA",
    });
    refreshAssistantContext({ contexto_tipo: "territorio", contexto_id: territory.id || null, modulo: "cadastros", origem: "ia", filtro: territory.name }, { force: true });
    requestAnimationFrame(() => focusElement("#contact-form"));
    return;
  }
  if (action === "open-agenda" && entityId) {
    navigateTo("agenda");
    renderAgenda();
    refreshAssistantContext({ contexto_tipo: "agenda", contexto_id: entityId, modulo: "agenda", origem: "ia" }, { force: true });
    return;
  }
  if (action === "focus-agenda-create-sentiment") {
    const sentiment = sentimentFromAssistantContext();
    navigateTo("agenda");
    renderAgenda();
    prefillAgendaForm({
      title: `Agenda de resposta - ${sentiment.title}`,
      description: `Compromisso sugerido pela IA para tratar o contexto de sentimento ${sentiment.focus}. ${sentiment.summary}`,
      location: sentiment.territory || state.assistantInsight?.contexto?.rotulo || "Base territorial a confirmar",
    });
    refreshAssistantContext(
      {
        contexto_tipo: "sentimento",
        modulo: "agenda",
        origem: "ia",
        filtro: sentiment.focus,
        canal: sentiment.channel || null,
        periodo: sentiment.period || null,
        territorio: sentiment.territory || null,
      },
      { force: true },
    );
    requestAnimationFrame(() => focusElement("#agenda-form"));
    return;
  }
  if (action === "focus-agenda-report" && entityId) {
    navigateTo("agenda");
    renderAgenda();
    if ($("#agenda-report-select")) {
      $("#agenda-report-select").value = entityId;
    }
    refreshAssistantContext({ contexto_tipo: "agenda", contexto_id: entityId, modulo: "agenda", origem: "ia" }, { force: true });
    requestAnimationFrame(() => focusElement("#agenda-report-form"));
    return;
  }
  if (action === "open-office") {
    navigateTo("oficios");
    renderOffices();
    refreshAssistantContext(
      entityId
        ? { contexto_tipo: "oficio", contexto_id: entityId, modulo: "oficios", origem: "ia" }
        : { contexto_tipo: "modulo", modulo: "oficios", origem: "ia" },
      { force: true },
    );
    requestAnimationFrame(() => focusElement("#office-list"));
    return;
  }
  if (action === "focus-office-create-demand" && entityId) {
    const demand = state.demands.find((item) => item.id === entityId);
    navigateTo("oficios");
    renderOffices();
    prefillOfficeForm({
      demandId: entityId,
      title: `Oficio para ${demand?.titulo || "demanda selecionada"}`,
      subject: demand?.titulo || "Encaminhamento institucional",
      followUp: "Sugestao da IA: registrar envio e acompanhar retorno formal do orgao.",
    });
    refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: entityId, modulo: "oficios", origem: "ia" }, { force: true });
    requestAnimationFrame(() => focusElement("#office-form"));
    return;
  }
  if (action === "open-territory-demand-list") {
    const territory = territoryFromAssistantContext();
    openDemandModuleContext({
      title: `Demandas em ${territory.name}`,
      eyebrow: "Territorio priorizado",
      description: `Leitura territorial aberta no modulo de atendimento para ${territory.name}.`,
      territory: territory.name,
      meta: [territory.name],
    });
    refreshAssistantContext({ contexto_tipo: "territorio", contexto_id: territory.id || null, modulo: "executivo", origem: "ia", filtro: territory.name }, { force: true });
    return;
  }
  if (action === "open-territory-contact-list") {
    const territory = territoryFromAssistantContext();
    openContactModuleContext({
      title: `Contatos em ${territory.name}`,
      eyebrow: "Base territorial",
      description: `Base territorial filtrada no CRM para ${territory.name}.`,
      territory: territory.name,
      meta: [territory.name],
    });
    refreshAssistantContext({ contexto_tipo: "territorio", contexto_id: territory.id || null, modulo: "executivo", origem: "ia", filtro: territory.name }, { force: true });
    return;
  }
  if (action === "open-emendas") {
    navigateTo("emendas");
    renderAmendments();
    refreshAssistantContext(
      entityId
        ? { contexto_tipo: "emenda", contexto_id: entityId, modulo: "emendas", origem: "ia" }
        : { contexto_tipo: "modulo", modulo: "emendas", origem: "ia" },
      { force: true },
    );
    return;
  }
  if (action === "open-legislative") {
    navigateTo("legislativo");
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "legislativo", origem: "ia" }, { force: true });
    return;
  }
  if (action === "open-compliance") {
    navigateTo("compliance");
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "compliance", origem: "ia" }, { force: true });
    return;
  }
  if (action === "open-mobile") {
    navigateTo("mobile");
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "mobile", origem: "ia" }, { force: true });
    return;
  }
  if (section) {
    navigateTo(section);
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: section, origem: "ia" }, { force: true });
  }
}

function getSearchMatches() {
  const query = state.globalSearch.trim().toLowerCase();
  if (!query) {
    return { query, contacts: [], demands: [], offices: [] };
  }
  const includesQuery = (values) => values.some((value) => String(value || "").toLowerCase().includes(query));
  return {
    query,
    contacts: state.contacts
      .filter((item) => item.status !== "EXCLUIDO")
      .filter((item) => includesQuery([item.nome, item.cpf, item.telefone_principal, item.email, item.bairro, item.observacoes]))
      .slice(0, 6),
    demands: state.demands
      .filter((item) => item.status !== "EXCLUIDO")
      .filter((item) => includesQuery([item.titulo, item.descricao, item.cidadao_nome, item.tipo_demanda, item.protocolo, item.codigo]))
      .slice(0, 6),
    offices: state.offices
      .filter((item) => includesQuery([item.numero, item.titulo, item.assunto, item.orgao_destino, item.follow_up]))
      .slice(0, 4),
  };
}

function renderSearchResults() {
  const panel = $("#search-results");
  if (!panel) return;
  const { query, contacts, demands, offices } = getSearchMatches();
  if (!query) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }
  const total = contacts.length + demands.length + offices.length;
  panel.classList.remove("hidden");
  panel.innerHTML = `
    <div class="search-results-head">
      <strong>Busca rápida</strong>
      <span>${escapeHtml(total)} resultado(s) para "${escapeHtml(state.globalSearch)}"</span>
    </div>
    <div class="search-result-grid">
      <article class="search-group">
        <h3>Contatos</h3>
        ${
          contacts
            .map(
              (item) => `
                <button type="button" class="search-result-item" data-search-kind="contact" data-search-id="${escapeHtml(item.id)}">
                  <strong>${escapeHtml(item.nome)}</strong>
                  <span>${escapeHtml(item.telefone_principal || item.cpf || item.bairro || "Sem contato")}</span>
                  <small>${escapeHtml(item.tipo_contato === "ORGAO_PUBLICO" ? "Órgão público" : "Relacionamento")}</small>
                </button>
              `,
            )
            .join("") || '<p class="search-empty">Nenhum contato encontrado.</p>'
        }
      </article>
      <article class="search-group">
        <h3>Demandas</h3>
        ${
          demands
            .map(
              (item) => `
                <button type="button" class="search-result-item" data-search-kind="demand" data-search-id="${escapeHtml(item.id)}">
                  <strong>${escapeHtml(item.titulo)}</strong>
                  <span>${escapeHtml(item.cidadao_nome || "Sem demandante")}</span>
                  <small>${escapeHtml(demandStatusLabel(item.status))}</small>
                </button>
              `,
            )
            .join("") || '<p class="search-empty">Nenhuma demanda encontrada.</p>'
        }
      </article>
      <article class="search-group">
        <h3>Ofícios</h3>
        ${
          offices
            .map(
              (item) => `
                <button type="button" class="search-result-item" data-search-kind="office" data-search-id="${escapeHtml(item.id)}">
                  <strong>${escapeHtml(item.numero || "Sem número")}</strong>
                  <span>${escapeHtml(item.titulo || item.assunto || "Sem título")}</span>
                  <small>${escapeHtml(item.orgao_destino || "Sem órgão")}</small>
                </button>
              `,
            )
            .join("") || '<p class="search-empty">Nenhum ofício encontrado.</p>'
        }
      </article>
    </div>
  `;

  $$('[data-search-kind="contact"]').forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedContactId = button.dataset.searchId;
      navigateTo("crm");
      renderCRM();
    });
  });
  $$('[data-search-kind="demand"]').forEach((button) => {
    button.addEventListener("click", () => {
      state.selectedDemandId = button.dataset.searchId;
      navigateTo("atendimento");
      renderDemands();
    });
  });
  $$('[data-search-kind="office"]').forEach((button) => {
    button.addEventListener("click", () => {
      navigateTo("oficios");
      document.getElementById("office-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
}

function renderListViewItem(title, details, badge, dataset = "") {
  return `
    <article class="row" ${dataset}>
      <div>
        <h3>${escapeHtml(title)}</h3>
        ${details.map((detail) => `<p>${escapeHtml(detail)}</p>`).join("")}
      </div>
      ${badge ? `<span class="status ${statusClass(badge)}">${escapeHtml(labelCode(badge))}</span>` : ""}
    </article>
  `;
}

function showListView({ title, eyebrow, items, emptyMessage = "Nenhum registro encontrado." }) {
  const content = $("#list-view-content");
  if (!content) return;
  state.previousSection = state.currentSection === "list-view" ? state.previousSection : state.currentSection;
  $("#list-view-title").textContent = title;
  $("#list-view-eyebrow").textContent = eyebrow;
  content.innerHTML = items.length ? items.join("") : `<p>${escapeHtml(emptyMessage)}</p>`;
  navigateTo("list-view");
  $(".topbar h1").textContent = title;
}

function hideListView() {
  goToInitialMenu();
}

function openDemandList(filters = {}) {
  const items = state.demands
    .filter((item) => item.status !== "ARQUIVADA" && item.status !== "EXCLUIDO")
    .filter((item) => {
      if (filters.statuses?.length) return filters.statuses.includes(item.status);
      return true;
    })
    .filter((item) => {
      if (!filters.territory) return true;
      return sameTerritoryScope(demandTerritory(item), filters.territory);
    })
    .filter((item) => {
      if (typeof filters.predicate !== "function") return true;
      return filters.predicate(item);
    })
    .map((item) =>
      renderListViewItem(
        item.titulo,
        [
          `Demandante: ${item.cidadao_nome || "Sem demandante"}`,
          `Territorio: ${demandTerritory(item)}`,
          `Responsavel: ${item.responsavel_nome || "Sem responsavel"}`,
          `SLA: ${labelCode(item.sla_status || "SEM_PRAZO")}${typeof item.sla_horas_restantes === "number" ? ` - ${item.sla_horas_restantes >= 0 ? `${Math.round(item.sla_horas_restantes)}h restantes` : `${Math.abs(Math.round(item.sla_horas_restantes))}h em atraso`}` : ""}`,
        ],
        item.status,
        `data-open-demand="${escapeHtml(item.id)}"`,
      ),
    );

  showListView({
    title: filters.title || "Demandas",
    eyebrow: filters.eyebrow || "Acompanhamento e acoes",
    items,
    emptyMessage: "Nenhuma demanda encontrada para este filtro.",
  });
}

function openContactList(filters = {}) {
  const items = state.contacts
    .filter((item) => !["EXCLUIDO", "INATIVO"].includes(item.status))
    .filter((item) => {
      if (!filters.onlyLeadership) return true;
      return isLeadershipContact(item);
    })
    .filter((item) => {
      if (!filters.engagements?.length) return true;
      return filters.engagements.includes(item.engajamento);
    })
    .filter((item) => {
      if (!filters.territory) return true;
      return sameTerritoryScope(item.territorio_nome || item.bairro || "Sem territorio", filters.territory);
    })
    .filter((item) => {
      if (typeof filters.predicate !== "function") return true;
      return filters.predicate(item);
    })
    .map((item) =>
      renderListViewItem(
        item.nome,
        [
          `${item.telefone_principal || "Sem telefone"} - ${item.email || "Sem e-mail"}`,
          `Territorio: ${item.territorio_nome || item.bairro || "Sem territorio"}`,
          `Relacionamento: ${item.nivel_relacionamento || "CONTATO"}`,
        ],
        item.tipo_contato,
        `data-open-contact="${escapeHtml(item.id)}"`,
      ),
    );

  showListView({
    title: filters.title || "Contatos",
    eyebrow: filters.eyebrow || "Relacionamento politico",
    items,
    emptyMessage: "Nenhum contato encontrado para este filtro.",
  });
}

async function applyRequestedContextFromUrl() {
  const context = requestedContextFromUrl();
  if (!context.section && !context.focus && !context.demandId && !context.contactId && !context.territoryId && !context.teamId && !context.userId) {
    return false;
  }

  if (context.section && document.getElementById(context.section)) {
    navigateTo(context.section);
  }

  if (context.demandId && state.demands.some((item) => item.id === context.demandId)) {
    state.selectedDemandId = context.demandId;
    navigateTo("atendimento");
    renderDemands();
    await refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: context.demandId, modulo: "atendimento", origem: "deep-link" }, { force: true });
    return true;
  }

  if (context.contactId && state.contacts.some((item) => item.id === context.contactId)) {
    state.selectedContactId = context.contactId;
    navigateTo("crm");
    renderCRM();
    await refreshAssistantContext({ contexto_tipo: "contato", contexto_id: context.contactId, modulo: "crm", origem: "deep-link" }, { force: true });
    return true;
  }

  const territory = context.territoryId ? state.territories.find((item) => item.id === context.territoryId) : null;
  const territoryName = territory?.nome || "";

  if (context.focus === "demandas_abertas") {
    openDemandModuleContext({
      title: "Demandas abertas",
      eyebrow: "Acompanhamento e acoes",
      description: "Fila viva do mandato com demandas ainda em curso, sem sair da tela de atendimento.",
      statuses: ["ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"],
      meta: ["Recorte vindo do painel do vereador"],
    });
    await refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "atendimento", origem: "deep-link", filtro: context.focus }, { force: true });
    return true;
  }

  if (context.focus === "agenda") {
    openAgendaModuleContext({
      title: "Agenda do mandato",
      eyebrow: "Compromissos em acompanhamento",
      description: "Compromissos pendentes filtrados dentro do modulo de agenda.",
      onlyPending: true,
      meta: ["Recorte vindo do painel do vereador"],
    });
    await refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "agenda", origem: "deep-link", filtro: context.focus }, { force: true });
    return true;
  }

  if (context.focus === "contatos") {
    openContactModuleContext({
      title: "Base cidada",
      eyebrow: "Relacionamento politico",
      description: "Base de relacionamento aberta no proprio CRM com filtro persistente.",
      meta: ["Recorte vindo do painel do vereador"],
    });
    await refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "crm", origem: "deep-link", filtro: context.focus }, { force: true });
    return true;
  }

  if (context.focus === "relacionamento" || context.focus === "mobilized") {
    openContactModuleContext({
      title: "Base mobilizada",
      eyebrow: "Relacionamento politico",
      description: "Contatos com maior propensao de resposta e mobilizacao, filtrados no CRM.",
      engagements: ["FORTE", "ALTO"],
      meta: ["Engajamento forte"],
    });
    await refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "crm", origem: "deep-link", filtro: context.focus }, { force: true });
    return true;
  }

  if (context.focus === "leaders") {
    openContactModuleContext({
      title: "Liderancas territoriais",
      eyebrow: "Relacionamento politico",
      description: "Recorte de liderancas territoriais mantido no CRM.",
      onlyLeadership: true,
      meta: ["Recorte de liderancas"],
    });
    await refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "crm", origem: "deep-link", filtro: context.focus }, { force: true });
    return true;
  }

  if (context.focus === "territorio" && territoryName) {
    openDemandModuleContext({
      title: `Demandas em ${territoryName}`,
      eyebrow: "Territorio priorizado",
      description: `Demandas ligadas ao territorio ${territoryName}, mantendo a operacao dentro do atendimento.`,
      territory: territoryName,
      meta: [territoryName],
    });
    await refreshAssistantContext({ contexto_tipo: "territorio", contexto_id: context.territoryId, modulo: "executivo", origem: "deep-link", filtro: territoryName, territorio: territoryName }, { force: true });
    return true;
  }

  if (context.section === "cadastros" && (context.teamId || context.userId)) {
    await refreshAssistantContext({
      contexto_tipo: context.teamId ? "equipe" : "usuario",
      contexto_id: context.teamId || context.userId,
      modulo: "cadastros",
      origem: "deep-link",
    }, { force: true });
    return true;
  }

  return Boolean(context.section);
}

function openAgendaList(filters = {}) {
  const items = state.agenda
    .filter((item) => {
      if (!filters.onlyPending) return true;
      return !["REALIZADO", "CANCELADO"].includes(item.status);
    })
    .map((item) =>
      renderListViewItem(
        item.titulo || "Compromisso",
        [
          `${AGENDA_TYPES[item.tipo_agenda] || item.tipo_agenda || "Agenda"} - ${item.local_texto || "Sem local"}`,
          `Situacao: ${labelCode(item.status)} - Inicio: ${formatDate(item.data_inicio)}`,
          `Equipe: ${item.eh_agenda_vereador ? "Parlamentar" : "Equipe"}`,
        ],
        item.status,
        `data-open-agenda="${escapeHtml(item.id)}"`,
      ),
    );

  showListView({
    title: filters.title || "Agenda",
    eyebrow: filters.eyebrow || "Agenda politica",
    items,
    emptyMessage: "Nenhum compromisso encontrado para este filtro.",
  });
}

function openAmendmentList() {
  const items = state.amendments.map((item) =>
    renderListViewItem(
      item.titulo || "Emenda",
      [
        `${item.numero || "Sem numero"} - ${item.area || "Sem area"}`,
        `Beneficiario: ${item.beneficiario || "Nao informado"}`,
        `Pleiteado: ${formatCurrency(item.valor_indicado)} - Aprovado: ${formatCurrency(item.valor_aprovado)}`,
        `Empenhado: ${formatCurrency(item.valor_empenhado)}${item.data_empenho ? ` - ${formatDate(item.data_empenho)}` : ""}`,
      ],
      item.status_execucao,
    ),
  );

  showListView({
    title: "Emendas pleiteadas",
    eyebrow: "Orcamento e captação",
    items,
    emptyMessage: "Nenhuma emenda cadastrada.",
  });
}

function openOfficeList() {
  const items = state.offices
    .filter((item) => !["RESPONDIDO", "CONCLUIDO", "ARQUIVADO"].includes(item.status))
    .map((item) =>
      renderListViewItem(
        `${item.numero || "Sem numero"} - ${item.titulo || item.assunto || "Oficio"}`,
        [
          `Destino: ${item.orgao_destino || "Nao informado"}`,
          `Demanda vinculada: ${item.demanda_titulo || "Nao vinculada"}`,
          `Acompanhamento: ${item.follow_up || "Sem observacao"}`,
        ],
        item.status,
        `data-open-office="${escapeHtml(item.id)}"`,
      ),
    );

  showListView({
    title: "Oficios pendentes",
    eyebrow: "Acompanhamento institucional",
    items,
    emptyMessage: "Nenhum oficio pendente no momento.",
  });
}

function handleDashboardAction(action) {
  if (action === "open-demands") {
    openDemandModuleContext({
      title: "Demandas abertas",
      statuses: ["ABERTA", "EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA", "AGUARDANDO_RETORNO", "REABERTA"],
      meta: ["Fila viva do mandato"],
    });
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "contacts") {
    openContactModuleContext({ title: "Contatos", meta: ["Base completa"] });
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "leadership") {
    openContactModuleContext({ title: "Liderancas", onlyLeadership: true, meta: ["Recorte de liderancas"] });
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "pending-offices") {
    openOfficeList();
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "sla-risk") {
    openDemandModuleContext({
      title: "Demandas em risco de SLA",
      eyebrow: "Prazos quase vencendo",
      description: "Fila filtrada pelas demandas que exigem resposta rapida para evitar vencimento.",
      predicate: (item) => item.sla_status === "EM_RISCO",
      meta: ["SLA em risco"],
    });
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "atendimento", origem: "sla-risk" }, { force: true });
    return;
  }
  if (action === "sla-overdue") {
    openDemandModuleContext({
      title: "Demandas com SLA vencido",
      eyebrow: "Risco operacional imediato",
      description: "Fila filtrada pelas demandas ja vencidas no SLA.",
      predicate: (item) => item.sla_status === "VENCIDO",
      meta: ["SLA vencido"],
    });
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "atendimento", origem: "sla-overdue" }, { force: true });
    return;
  }
  if (action === "strong-engagement") {
    openContactModuleContext({
      title: "Engajamento forte",
      eyebrow: "Base mobilizada",
      engagements: ["FORTE", "ALTO"],
      meta: ["Alta resposta politica"],
    });
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "treat-risk") {
    const territory = sentimentTerritoryFocus();
    openDemandModuleContext({
      title: territory ? `Demandas em risco de SLA em ${territory}` : "Demandas em risco de SLA",
      eyebrow: "Resposta orientada por sentimento",
      territory: territory || undefined,
      predicate: (item) => item.sla_status === "EM_RISCO",
      description: territory ? `Resposta filtrada por territorio ${territory} para demandas em risco.` : "Resposta filtrada para demandas em risco de SLA.",
      meta: [territory || "Todos os territorios"],
    });
    refreshAssistantContext({
      contexto_tipo: "sentimento",
      modulo: "executivo",
      origem: "dashboard-action",
      filtro: "negative",
      canal: state.sentimentFilters.canal || null,
      periodo: state.sentimentFilters.periodo || null,
      territorio: territory || null,
    }, { force: true });
    return;
  }
  if (action === "treat-overdue") {
    const territory = sentimentTerritoryFocus();
    openDemandModuleContext({
      title: territory ? `Demandas com SLA vencido em ${territory}` : "Demandas com SLA vencido",
      eyebrow: "Resposta orientada por sentimento",
      territory: territory || undefined,
      predicate: (item) => item.sla_status === "VENCIDO",
      description: territory ? `Resposta filtrada por territorio ${territory} para demandas vencidas.` : "Resposta filtrada para demandas com SLA vencido.",
      meta: [territory || "Todos os territorios"],
    });
    refreshAssistantContext({
      contexto_tipo: "sentimento",
      modulo: "executivo",
      origem: "dashboard-action",
      filtro: "negative-overdue",
      canal: state.sentimentFilters.canal || null,
      periodo: state.sentimentFilters.periodo || null,
      territorio: territory || null,
    }, { force: true });
    return;
  }
  if (action === "activate-base") {
    const territory = sentimentTerritoryFocus();
    openContactModuleContext({
      title: territory ? `Base para ativar em ${territory}` : "Base para ativar",
      eyebrow: "Mobilizacao orientada por sentimento",
      engagements: ["FORTE", "ALTO"],
      territory: territory || undefined,
      meta: [territory || "Todos os territorios"],
    });
    refreshAssistantContext({
      contexto_tipo: "sentimento",
      modulo: "executivo",
      origem: "dashboard-action",
      filtro: "positive",
      canal: state.sentimentFilters.canal || null,
      periodo: state.sentimentFilters.periodo || null,
      territorio: territory || null,
    }, { force: true });
    return;
  }
  if (action === "pending-agenda") {
    openAgendaModuleContext({
      title: "Agenda pendente",
      eyebrow: "Compromissos em acompanhamento",
      onlyPending: true,
      meta: ["Execucao pendente"],
    });
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "amendments") {
    openAmendmentList();
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "legislative") {
    navigateTo("legislativo");
    refreshAssistantContext({ contexto_tipo: "dashboard_card", modulo: "executivo", origem: "dashboard-card", filtro: action }, { force: true });
    return;
  }
  if (action === "dashboard") {
    navigateTo("executivo");
    refreshAssistantContext({ contexto_tipo: "modulo", modulo: "executivo", origem: "dashboard-card" }, { force: true });
    return;
  }
}

function handleAlertAction(action, entityId, section, meta = {}) {
  if (action === "open-demand" && entityId) {
    state.selectedDemandId = entityId;
    navigateTo(section || "atendimento");
    renderDemands();
    refreshAssistantContext(buildAlertAssistantContext({ ...meta, action, entityId, section }), { force: true });
    return;
  }
  if (action === "open-office") {
    navigateTo(section || "oficios");
    document.getElementById("office-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
    refreshAssistantContext(buildAlertAssistantContext({ ...meta, action, entityId, section }), { force: true });
    return;
  }
  if (action === "open-emendas") {
    navigateTo(section || "emendas");
    refreshAssistantContext(buildAlertAssistantContext({ ...meta, action, entityId, section }), { force: true });
    return;
  }
  if (section) {
    navigateTo(section);
    refreshAssistantContext(buildAlertAssistantContext({ ...meta, action, entityId, section }), { force: true });
    return;
  }
  if (action) {
    openOfficeList();
  }
}

function handleGlobalClick(event) {
  const backButton = event.target.closest("#back-to-dashboard");
  if (backButton) {
    goToInitialMenu();
    return;
  }

  const homeTrigger = event.target.closest("#brand-home");
  if (homeTrigger) {
    goToInitialMenu();
    return;
  }

  const topbarHomeTrigger = event.target.closest("#topbar-home");
  if (topbarHomeTrigger) {
    goToInitialMenu();
    return;
  }

  const navButton = event.target.closest(".module-nav button[data-section]");
  if (navButton) {
    navigateTo(navButton.dataset.section);
    refreshAssistantContext(defaultAssistantContext(navButton.dataset.section), { force: true });
    return;
  }

  const clearContextButton = event.target.closest("[data-clear-module-context]");
  if (clearContextButton) {
    clearModuleContext(clearContextButton.dataset.clearModuleContext);
    return;
  }

  const reportButton = event.target.closest("[data-report-section]");
  if (reportButton) {
    navigateTo(reportButton.dataset.reportSection);
    refreshAssistantContext(defaultAssistantContext(reportButton.dataset.reportSection), { force: true });
    return;
  }

  const reportDemandButton = event.target.closest("#reports-jobs [data-select-demand]");
  if (reportDemandButton) {
    state.selectedDemandId = reportDemandButton.dataset.selectDemand;
    navigateTo("atendimento");
    renderDemands();
    refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: state.selectedDemandId, modulo: "atendimento", origem: "relatorios" }, { force: true });
    return;
  }

  const dashboardAction = event.target.closest("[data-dashboard-action]");
  if (dashboardAction) {
    handleDashboardAction(dashboardAction.dataset.dashboardAction);
    return;
  }

  const territoryAction = event.target.closest(".heat-action[data-territory]");
  if (territoryAction) {
    const territory = territoryAction.dataset.territory;
    openDemandModuleContext({
      title: `Demandas em ${territory}`,
      eyebrow: "Territorio priorizado",
      description: `Recorte territorial aberto diretamente no modulo de atendimento para ${territory}.`,
      territory,
      meta: [territory],
    });
    refreshAssistantContext({
      contexto_tipo: "territorio",
      contexto_id: territoryAction.dataset.territoryId || null,
      modulo: "executivo",
      origem: "heatmap",
      filtro: territory,
      territorio: territory,
    }, { force: true });
    return;
  }

  const contextTrigger = event.target.closest("[data-ai-context-type]");
  if (contextTrigger) {
    refreshAssistantContext(
      {
        contexto_tipo: contextTrigger.dataset.aiContextType,
        contexto_id: contextTrigger.dataset.aiContextId || null,
        modulo: contextTrigger.dataset.aiContextModule || state.currentSection,
        origem: contextTrigger.dataset.aiContextOrigin || "painel",
        filtro: contextTrigger.dataset.aiContextFilter || null,
        canal: contextTrigger.dataset.aiContextChannel || state.sentimentFilters.canal || null,
        periodo: contextTrigger.dataset.aiContextPeriod || state.sentimentFilters.periodo || null,
        territorio: contextTrigger.dataset.aiContextTerritory || state.sentimentFilters.territorio || null,
      },
      { force: true },
    );
    return;
  }

  const demandItem = event.target.closest("[data-open-demand]");
  if (demandItem) {
    state.selectedDemandId = demandItem.dataset.openDemand;
    navigateTo("atendimento");
    renderDemands();
    refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: state.selectedDemandId, modulo: "atendimento", origem: "lista" }, { force: true });
    return;
  }

  const contactItem = event.target.closest("[data-open-contact]");
  if (contactItem) {
    state.selectedContactId = contactItem.dataset.openContact;
    navigateTo("crm");
    renderCRM();
    refreshAssistantContext({ contexto_tipo: "contato", contexto_id: state.selectedContactId, modulo: "crm", origem: "lista" }, { force: true });
    return;
  }

  const officeItem = event.target.closest("[data-open-office]");
  if (officeItem) {
    navigateTo("oficios");
    document.getElementById("office-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
    refreshAssistantContext({ contexto_tipo: "oficio", contexto_id: officeItem.dataset.openOffice, modulo: "oficios", origem: "lista" }, { force: true });
    return;
  }

  const agendaItem = event.target.closest("[data-open-agenda]");
  if (agendaItem) {
    navigateTo("agenda");
    document.getElementById("agenda-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
    refreshAssistantContext({ contexto_tipo: "agenda", contexto_id: agendaItem.dataset.openAgenda, modulo: "agenda", origem: "lista" }, { force: true });
    return;
  }

  const alertItem = event.target.closest("[data-alert-action]");
  if (alertItem) {
    handleAlertAction(alertItem.dataset.alertAction, alertItem.dataset.alertId, alertItem.dataset.alertSection, {
      filter: alertItem.dataset.alertFilter || null,
      territory: alertItem.dataset.alertTerritory || null,
      territoryId: alertItem.dataset.alertTerritoryId || null,
    });
    return;
  }

  const assistantAction = event.target.closest("[data-ai-execute-action]");
  if (assistantAction) {
    executeAssistantAction(
      assistantAction.dataset.aiExecuteAction,
      assistantAction.dataset.aiSection,
      assistantAction.dataset.aiEntityId,
    );
  }
}

function handleGlobalKeydown(event) {
  if (event.key !== "Enter" && event.key !== " ") return;
  const actionTarget = event.target.closest("[data-dashboard-action], .heat-action[data-territory], [data-alert-action], [data-ai-context-type]");
  if (!actionTarget) return;
  event.preventDefault();
  if (actionTarget.dataset.dashboardAction) {
    handleDashboardAction(actionTarget.dataset.dashboardAction);
    return;
  }
  if (actionTarget.dataset.alertAction) {
    handleAlertAction(actionTarget.dataset.alertAction, actionTarget.dataset.alertId, actionTarget.dataset.alertSection, {
      filter: actionTarget.dataset.alertFilter || null,
      territory: actionTarget.dataset.alertTerritory || null,
      territoryId: actionTarget.dataset.alertTerritoryId || null,
    });
    return;
  }
  if (actionTarget.dataset.aiContextType) {
    refreshAssistantContext(
      {
        contexto_tipo: actionTarget.dataset.aiContextType,
        contexto_id: actionTarget.dataset.aiContextId || null,
        modulo: actionTarget.dataset.aiContextModule || state.currentSection,
        origem: actionTarget.dataset.aiContextOrigin || "painel",
        filtro: actionTarget.dataset.aiContextFilter || null,
        canal: actionTarget.dataset.aiContextChannel || state.sentimentFilters.canal || null,
        periodo: actionTarget.dataset.aiContextPeriod || state.sentimentFilters.periodo || null,
        territorio: actionTarget.dataset.aiContextTerritory || state.sentimentFilters.territorio || null,
      },
      { force: true },
    );
    return;
  }
  if (actionTarget.dataset.territory) {
    openDemandModuleContext({
      title: `Demandas em ${actionTarget.dataset.territory}`,
      eyebrow: "Territorio priorizado",
      description: `Recorte territorial aberto diretamente no atendimento para ${actionTarget.dataset.territory}.`,
      territory: actionTarget.dataset.territory,
      meta: [actionTarget.dataset.territory],
    });
    refreshAssistantContext({
      contexto_tipo: "territorio",
      contexto_id: actionTarget.dataset.territoryId || null,
      modulo: "executivo",
      origem: "heatmap",
      filtro: actionTarget.dataset.territory,
      territorio: actionTarget.dataset.territory,
    }, { force: true });
  }
}

function renderMetrics() {
  const cards = state.overview?.cards || {};
  const items = [
    ["Demandas abertas", cards.demandas_abertas ?? 0, "open-demands"],
    ["SLA em risco", cards.sla_em_risco ?? 0, "sla-risk"],
    ["SLA vencido", cards.sla_vencido ?? 0, "sla-overdue"],
    ["Engajamento forte", cards.engajamento_forte ?? 0, "strong-engagement"],
    ["Agenda pendente", cards.agenda_pendente ?? 0, "pending-agenda"],
    ["Oficios pendentes", cards.oficios_pendentes ?? 0, "pending-offices"],
  ];
  $("#metric-grid").innerHTML = items
    .map(
      ([label, value, action]) => `
        <article class="metric metric-action" data-dashboard-action="${action}" role="button" tabindex="0" aria-label="Abrir ${escapeHtml(label)}">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `,
    )
    .join("");
}

function renderHeatmap() {
  const items = state.overview?.heatmap || [];
  const max = Math.max(1, ...items.map((item) => Number(item.score || 0)));
  $("#heatmap-grid").innerHTML =
    items
      .map((item) => {
        const ratio = Number(item.score || 0) / max;
        const level = ratio > 0.76 ? 4 : ratio > 0.51 ? 3 : ratio > 0.25 ? 2 : 1;
        return `
          <article class="heat-cell heat-action" data-level="${level}" data-territory="${escapeHtml(item.territorio_nome)}" data-territory-id="${escapeHtml(item.territorio_id || "")}" role="button" tabindex="0" aria-label="Abrir territorio ${escapeHtml(item.territorio_nome)}">
            <strong>${escapeHtml(item.territorio_nome)}</strong>
            <span>Pressao ${escapeHtml(labelCode(item.nivel_pressao || "BAIXA"))}</span>
            <span>${Number(item.demandas || 0)} demandas</span>
            <span>${Number(item.contatos || 0)} contatos</span>
            <span>${Number(item.liderancas || 0)} liderancas</span>
          </article>
        `;
      })
      .join("") || "<p>Nenhum dado territorial registrado.</p>";
}

function renderSentiment() {
  const sentiment = currentSentiment();
  const catalog = state.overview?.sentimento || sentiment;
  const channelOptions = [{ canal: "", quantidade: catalog.amostras || 0, label: "Todos os canais" }].concat(
    (catalog.canais || []).map((item) => ({ ...item, label: `${item.canal} (${item.quantidade})` })),
  );
  const periodOptions = [{ periodo: "", quantidade: catalog.amostras || 0, label: "Todos os periodos" }].concat(
    (catalog.periodos || []).map((item) => ({ ...item, label: `${item.periodo} (${item.quantidade})` })),
  );
  const territoryOptions = [{ territorio: "", quantidade: catalog.amostras || 0, label: "Todos os territorios" }].concat(
    (catalog.territorios || []).map((item) => ({ ...item, label: `${item.territorio} (${item.quantidade})` })),
  );
  const rows = [
    ["Positivo", Number(sentiment.positivo || 0), "positive"],
    ["Neutro", Number(sentiment.neutro || 0), "neutral"],
    ["Negativo", Number(sentiment.negativo || 0), "negative"],
  ];
  $("#sentiment-panel").innerHTML = `
    ${rows
      .map(
        ([label, value, kind]) => `
          <div class="sentiment-row">
            <strong>${label}</strong>
            <span class="sentiment-track"><span class="sentiment-fill ${kind}" style="width:${Math.min(value, 100)}%"></span></span>
            <span>${value}%</span>
          </div>
        `,
      )
      .join("")}
    <div class="sentiment-filters">
      <label>
        Canal
        <select id="sentiment-channel-filter" data-sentiment-filter="canal">
          ${channelOptions
            .map((item) => `<option value="${escapeHtml(item.canal)}" ${item.canal === state.sentimentFilters.canal ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
            .join("")}
        </select>
      </label>
      <label>
        Periodo
        <select id="sentiment-period-filter" data-sentiment-filter="periodo">
          ${periodOptions
            .map((item) => `<option value="${escapeHtml(item.periodo)}" ${item.periodo === state.sentimentFilters.periodo ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
            .join("")}
        </select>
      </label>
      <label>
        Territorio
        <select id="sentiment-territory-filter" data-sentiment-filter="territorio">
          ${territoryOptions
            .map((item) => `<option value="${escapeHtml(item.territorio)}" ${item.territorio === state.sentimentFilters.territorio ? "selected" : ""}>${escapeHtml(item.label)}</option>`)
            .join("")}
        </select>
      </label>
    </div>
    <div class="sentiment-meta">
      <strong>${escapeHtml(sentiment.tema || "Sem tema monitorado")}</strong>
      <span>${escapeHtml(sentiment.canal || "Canal nao informado")} - ${escapeHtml(sentiment.periodo || "Janela nao informada")}${sentiment.coletado_em ? ` - atualizado em ${escapeHtml(formatDate(sentiment.coletado_em))}` : ""}</span>
      <span>${escapeHtml(sentiment.amostras || 0)} amostra(s) agregada(s)${sentiment.territorios?.[0]?.territorio ? ` - foco territorial: ${escapeHtml(sentiment.territorios[0].territorio)}` : ""}</span>
    </div>
    <p class="sentiment-alert">${escapeHtml(sentiment.alerta || "Sem alerta de sentimento.")}</p>
    <div class="dashboard-inline-actions">
      <button type="button" class="secondary" data-dashboard-action="leadership">Ver liderancas</button>
      <button type="button" class="secondary" data-dashboard-action="strong-engagement">Ver base mobilizada</button>
      <button type="button" class="secondary" data-dashboard-action="treat-risk">Tratar risco</button>
      <button type="button" class="secondary" data-dashboard-action="treat-overdue">Tratar vencidas</button>
      <button type="button" class="secondary" data-dashboard-action="activate-base">Ativar base</button>
    </div>
  `;
}

function renderAmendmentSummary() {
  const totals = state.overview?.emendas || {};
  const indicated = Number(totals.valor_indicado || 0);
  const approved = Number(totals.valor_aprovado || 0);
  const committed = Number(totals.valor_empenhado || 0);
  const committedPercent = approved ? Math.round((committed / approved) * 100) : 0;
  $("#amendment-summary").innerHTML = `
    <div class="budget-numbers">
      <article><span>Pleiteado</span><strong>${formatCurrency(indicated)}</strong></article>
      <article><span>Aprovado</span><strong>${formatCurrency(approved)}</strong></article>
      <article><span>Empenhado</span><strong>${formatCurrency(committed)}</strong></article>
    </div>
    <div>
      <p class="budget-status">${totals.aprovadas || 0} aprovadas • ${totals.empenhadas || 0} com empenho${totals.ultima_data_empenho ? ` • ultimo empenho ${formatDate(totals.ultima_data_empenho)}` : ""}</p>
      <span class="budget-track"><span class="budget-fill" style="width:${Math.min(committedPercent, 100)}%; background: var(--emerald)"></span></span>
    </div>
    <div class="dashboard-inline-actions">
      <button type="button" class="secondary" data-dashboard-action="amendments">Ver emendas</button>
    </div>
  `;
}

function renderAlerts() {
  const alerts = state.overview?.alertas || [];
  $("#alert-list").innerHTML =
    alerts
      .map(
        (item) => `
          <article class="row interactive-row" data-alert-action="${escapeHtml(item.action || "")}" data-alert-id="${escapeHtml(item.entity_id || "")}" data-alert-section="${escapeHtml(item.section || "")}" data-alert-filter="${escapeHtml(item.filtro_contexto || "")}" data-alert-territory="${escapeHtml(item.territorio_nome || "")}" data-alert-territory-id="${escapeHtml(item.territorio_id || "")}" role="button" tabindex="0" aria-label="Abrir alerta ${escapeHtml(item.titulo || item.tipo)}">
            <div>
              <h3>${escapeHtml(item.titulo || item.tipo)}</h3>
              <p>${escapeHtml(item.descricao || "")}</p>
              ${item.territorio_nome ? `<small>Territorio: ${escapeHtml(item.territorio_nome)}</small>` : ""}
            </div>
            <span class="status warning">${escapeHtml(item.tipo || "ALERTA")}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum alerta critico no momento.</p>";
}

function renderCommandCenter() {
  renderMetrics();
  renderSlaPanel();
  renderHeatmap();
  renderSentiment();
  renderAmendmentSummary();
  renderAlerts();
}

function renderSlaPanel() {
  const sla = state.overview?.sla || {};
  const config = sla.configuracao || {};
  const summary = sla.resumo || {};
  const queue = sla.fila || [];
  const configurationItems = [
    ["Critica", config.critica_horas],
    ["Alta", config.alta_horas],
    ["Media", config.media_horas],
    ["Baixa", config.baixa_horas],
  ];
  $("#sla-panel").innerHTML = `
    <div class="sla-config-list">
      ${configurationItems
        .map(
          ([label, hours]) => `
            <article>
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(hours ?? 0)}h</strong>
            </article>
          `,
        )
        .join("")}
    </div>
    <div class="sla-summary-grid">
      <article><span>Monitoradas</span><strong>${escapeHtml(summary.monitoradas ?? 0)}</strong></article>
      <article><span>No prazo</span><strong>${escapeHtml(summary.no_prazo ?? 0)}</strong></article>
      <article><span>Em risco</span><strong>${escapeHtml(summary.em_risco ?? 0)}</strong></article>
      <article><span>Vencidas</span><strong>${escapeHtml(summary.vencidas ?? 0)}</strong></article>
      <article><span>Concluidas no prazo</span><strong>${escapeHtml(summary.concluidas_no_prazo ?? 0)}</strong></article>
      <article><span>Concluidas em atraso</span><strong>${escapeHtml(summary.concluidas_em_atraso ?? 0)}</strong></article>
    </div>
    <div class="sla-queue">
      ${queue.length
        ? queue
            .map(
              (item) => `
                <article class="sla-queue-item interactive-row" data-open-demand="${escapeHtml(item.id || "")}" role="button" tabindex="0" aria-label="Abrir demanda ${escapeHtml(item.titulo || "Demanda")}">
                  <div>
                    <strong>${escapeHtml(item.titulo || "Demanda")}</strong>
                    <p>${escapeHtml(item.cidadao_nome || "Sem demandante")} - ${escapeHtml(item.territorio_nome || "Sem territorio")}</p>
                    <p>Prioridade ${escapeHtml(labelCode(item.prioridade || "MEDIA"))} - ${escapeHtml(labelCode(item.sla_status || "SEM_PRAZO"))}</p>
                  </div>
                  <span class="status ${statusClass(item.sla_status || "")}">${escapeHtml(typeof item.horas_restantes === "number" ? (item.horas_restantes >= 0 ? `${Math.round(item.horas_restantes)}h` : `${Math.abs(Math.round(item.horas_restantes))}h`) : labelCode(item.sla_status || "SEM_PRAZO"))}</span>
                </article>
              `,
            )
            .join("")
        : '<div class="assistant-empty">Nenhuma demanda monitorada por SLA no momento.</div>'}
    </div>
  `;
}

function renderDemands() {
  const query = state.globalSearch.trim().toLowerCase();
  const activeDemands = state.demands.filter((item) => {
    if (item.status === "ARQUIVADA" || item.status === "EXCLUIDO") return false;
    if (!demandMatchesModuleContext(item)) return false;
    if (!query) return true;
    return [item.titulo, item.descricao, item.cidadao_nome, item.tipo_demanda, demandTerritory(item), item.responsavel_nome].some((value) =>
      String(value || "").toLowerCase().includes(query),
    );
  });
  if ((!state.selectedDemandId || !activeDemands.some((item) => item.id === state.selectedDemandId)) && activeDemands[0]) {
    state.selectedDemandId = activeDemands[0].id;
  }
  if (!activeDemands.length) {
    state.selectedDemandId = null;
  }
  renderModuleContext("atendimento", activeDemands.length, activeDemands.length ? "" : "Nenhuma demanda neste recorte");
  const board = $("#demand-board");
  if (board) {
    board.innerHTML = DEMAND_COLUMNS.map(([status, title]) => {
      const items =
        status === "EM_ATENDIMENTO"
          ? activeDemands.filter((item) => ["EM_TRIAGEM", "EM_ATENDIMENTO", "ENCAMINHADA"].includes(item.status))
          : activeDemands.filter((item) => item.status === status);
      return `
        <section class="demand-column">
          <div class="demand-column-title">
            <h3>${title}</h3>
            <span>${items.length}</span>
          </div>
          ${items.map(renderDemandCard).join("") || '<p class="empty-note">Sem demandas.</p>'}
        </section>
      `;
    }).join("");
  }
  const list = $("#demand-list");
  if (list) {
    list.innerHTML = activeDemands.map(renderDemandRow).join("") || "<p>Nenhuma demanda cadastrada.</p>";
  }

  $$("[data-select-demand], [data-select]").forEach((element) => {
    element.addEventListener("click", () => {
      state.selectedDemandId = element.dataset.selectDemand || element.dataset.select;
      renderDemands();
      renderSelectedDemand();
      $("#ai-output").textContent = "Demanda selecionada. A IA esta pronta para resumir o contexto ou orientar a proxima acao.";
      refreshAssistantContext({ contexto_tipo: "demanda", contexto_id: state.selectedDemandId, modulo: "atendimento", origem: "fila" }, { force: true });
    });
  });

  $$("[data-start]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      state.selectedDemandId = button.dataset.start;
      await api(`/demandas/${button.dataset.start}/assumir`, { method: "POST", body: JSON.stringify({}) });
      await loadData();
    });
  });
  $$("[data-demand-status]").forEach((select) => {
    select.addEventListener("click", (event) => event.stopPropagation());
    select.addEventListener("change", async (event) => {
      event.stopPropagation();
      const demandId = select.dataset.demandStatus;
      await api(`/demandas/${demandId}`, {
        method: "PUT",
        body: JSON.stringify({ status: select.value, observacao: "Situacao atualizada pela tela de atendimento." }),
      });
      state.selectedDemandId = demandId;
      await loadData();
    });
  });

  $$("[data-demand-responsible]").forEach((select) => {
    select.addEventListener("click", (event) => event.stopPropagation());
    select.addEventListener("change", async (event) => {
      event.stopPropagation();
      await api(`/demandas/${select.dataset.demandResponsible}`, {
        method: "PUT",
        body: JSON.stringify({ responsavel_usuario_id: select.value || null }),
      });
      await loadData();
    });
  });

  $$("[data-demand-territory]").forEach((select) => {
    select.addEventListener("click", (event) => event.stopPropagation());
    select.addEventListener("change", async (event) => {
      event.stopPropagation();
      await api(`/demandas/${select.dataset.demandTerritory}`, {
        method: "PUT",
        body: JSON.stringify({ territorio_id: select.value || null }),
      });
      await loadData();
    });
  });

  $$("[data-edit-demand]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      startDemandEdit(button.dataset.editDemand);
    });
  });

  $$("[data-archive-demand]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await api(`/demandas/${button.dataset.archiveDemand}/arquivar`, { method: "POST", body: JSON.stringify({ motivo: "Arquivada pela tela de atendimento." }) });
      await loadData();
    });
  });

  $$("[data-delete-demand]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (!window.confirm("Excluir esta demanda da fila? O registro ficara preservado na auditoria.")) return;
      await api(`/demandas/${button.dataset.deleteDemand}`, { method: "DELETE" });
      await loadData();
    });
  });

  renderSelectedDemand();
}

function renderDemandCard(item) {
  const selected = item.id === state.selectedDemandId ? " selected" : "";
  return `
    <article class="demand-card${selected}" data-select-demand="${escapeHtml(item.id)}">
      <div class="demand-card-head">
        ${avatarMarkup(item.cidadao_nome, item.cidadao_foto_url, "small")}
        <div>
          <h3>${escapeHtml(item.titulo)}</h3>
          <p>${escapeHtml(item.cidadao_nome || "Demandante pendente")}</p>
        </div>
      </div>
      <p>${escapeHtml(item.tipo_demanda || "Nao classificada")} - ${escapeHtml(demandTerritory(item))}</p>
      <p class="demand-meta-line"><span class="demand-person">${avatarMarkup(item.responsavel_nome || "Sem responsavel", item.responsavel_foto_url, "tiny")}<strong>${escapeHtml(item.responsavel_nome || "Sem responsavel")}</strong></span><span>${escapeHtml(demandSlaLabel(item))}</span></p>
      ${isVacancyDemand(item.tipo_demanda) ? `<p>Vaga: ${escapeHtml(labelCode(item.tipo_vaga_pretendida || "OUTROS"))}${item.vaga_outros_descricao ? ` - ${escapeHtml(item.vaga_outros_descricao)}` : ""}${item.cv_nome_arquivo ? ` - CV: ${escapeHtml(item.cv_nome_arquivo)}` : " - CV pendente"}</p>` : ""}
      <label class="compact-field">Responsavel
        <select data-demand-responsible="${escapeHtml(item.id)}">${userOptions(item.responsavel_usuario_id)}</select>
      </label>
      <label class="compact-field">Territorio
        <select data-demand-territory="${escapeHtml(item.id)}">${territoryOptions(item.territorio_id)}</select>
      </label>
      <label class="compact-field">Situacao
        <select data-demand-status="${escapeHtml(item.id)}">
          ${DEMAND_STATUS.map((status) => `<option value="${status}" ${status === item.status ? "selected" : ""}>${demandStatusLabel(status)}</option>`).join("")}
        </select>
      </label>
      <div class="card-footer">
        <span class="status ${statusClass(item.prioridade)}">${escapeHtml(item.prioridade || "MEDIA")}</span>
        <button type="button" class="secondary" data-edit-demand="${escapeHtml(item.id)}">Editar</button>
        <button type="button" class="secondary" data-archive-demand="${escapeHtml(item.id)}">Arquivar</button>
        <button type="button" class="danger" data-delete-demand="${escapeHtml(item.id)}">Excluir</button>
      </div>
    </article>
  `;
}

function renderDemandRow(item) {
  return `
    <article class="row demand-row" data-select-demand="${escapeHtml(item.id)}">
      <div class="row-main">
        ${avatarMarkup(item.cidadao_nome, item.cidadao_foto_url, "small")}
        <div>
          <h3>${escapeHtml(item.titulo)}</h3>
        <p>Demandante: ${escapeHtml(item.cidadao_nome || "Pendente de regularizacao")} - Tipo: ${escapeHtml(item.tipo_demanda || "Nao classificada")}</p>
        ${isVacancyDemand(item.tipo_demanda) ? `<p>Vaga: ${escapeHtml(labelCode(item.tipo_vaga_pretendida || "OUTROS"))}${item.vaga_outros_descricao ? ` - ${escapeHtml(item.vaga_outros_descricao)}` : ""}</p>` : ""}
          <p>Territorio: ${escapeHtml(demandTerritory(item))} - Responsavel: ${escapeHtml(item.responsavel_nome || "Sem responsavel")} - ${escapeHtml(demandSlaLabel(item))}</p>
        </div>
      </div>
      <span class="status ${statusClass(item.status)}">${escapeHtml(demandStatusLabel(item.status))}</span>
    </article>
  `;
}

function startDemandEdit(demandId) {
  const demand = state.demands.find((item) => item.id === demandId);
  if (!demand) return;
  state.editingDemandId = demand.id;
  const form = $("#demand-edit-form");
  form.classList.remove("hidden");
  form.elements.titulo.value = demand.titulo || "";
  form.elements.descricao.value = demand.descricao || "";
  form.elements.tipo_demanda.value = demand.tipo_demanda || "OUTRA";
  form.elements.prioridade.value = demand.prioridade || "MEDIA";
  form.elements.status.value = demand.status || "ABERTA";
  form.elements.responsavel_usuario_id.value = demand.responsavel_usuario_id || "";
  form.elements.territorio_id.value = demand.territorio_id || "";
  if (form.elements.tipo_vaga_pretendida) form.elements.tipo_vaga_pretendida.value = demand.tipo_vaga_pretendida || "";
  if (form.elements.vaga_outros_descricao) form.elements.vaga_outros_descricao.value = demand.vaga_outros_descricao || "";
  if (form.elements.cv_upload_id) form.elements.cv_upload_id.value = demand.cv_upload_id || "";
  if (form.elements.cv_url) form.elements.cv_url.value = demand.cv_url_publica || demand.cv_url || "";
  setCvLink("#demand-edit-cv-link", demand.cv_url_publica || demand.cv_url, demand.cv_nome_arquivo);
  syncVacancyFields(form, "edit");
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderContacts() {
  const query = state.globalSearch.trim().toLowerCase();
  const matches = (item) => {
    if (!query) return true;
    return [item.nome, item.cpf, item.telefone_principal, item.email, item.bairro, item.observacoes]
      .some((value) => String(value || "").toLowerCase().includes(query));
  };
  const people = state.contacts.filter((item) => item.tipo_contato !== "ORGAO_PUBLICO" && !["EXCLUIDO", "INATIVO"].includes(item.status) && matches(item));
  const publicBodies = state.contacts.filter((item) => item.tipo_contato === "ORGAO_PUBLICO" && !["EXCLUIDO", "INATIVO"].includes(item.status) && matches(item));
  const renderContactCard = (item) => `
    <article class="row profile-row" data-crm-open="${escapeHtml(item.id)}">
      <div class="row-main">
        ${avatarMarkup(item.nome, item.foto_url_publica, "small")}
        <div>
          <h3>${escapeHtml(item.nome)}</h3>
          <p>${escapeHtml(item.telefone_principal || "Sem telefone")} - ${escapeHtml(item.bairro || item.territorio_nome || "Sem bairro")}</p>
          <p>Perfil: ${escapeHtml(item.nivel_relacionamento || "CONTATO")} - Engajamento: ${escapeHtml(item.engajamento || "FRIO")} - Voto 2028: ${escapeHtml(item.voto_2028 || "INDEFINIDO")}</p>
        </div>
      </div>
      <div class="row-actions">
        <button type="button" class="secondary" data-edit-contact="${escapeHtml(item.id)}">Editar</button>
        <button type="button" class="secondary" data-archive-contact="${escapeHtml(item.id)}">Arquivar</button>
        <button type="button" class="danger" data-delete-contact="${escapeHtml(item.id)}">Excluir</button>
      </div>
      <span class="status">${escapeHtml(item.prioridade_politica || labelCode(item.status))}</span>
    </article>
  `;
  $("#contact-list").innerHTML =
    people
      .map(renderContactCard)
      .join("") || "<p>Nenhum cidadao ou lideranca cadastrado.</p>";
  const publicBodyList = $("#public-body-list");
  if (publicBodyList) {
    publicBodyList.innerHTML =
      publicBodies
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.nome)}</h3>
              <p>${escapeHtml(item.email || "Sem e-mail")} - ${escapeHtml(item.telefone_principal || "Sem telefone")}</p>
              <p>${escapeHtml(item.bairro || item.territorio_nome || "Sem territorio")}</p>
            </div>
            <div class="row-actions">
              <button type="button" class="secondary" data-edit-contact="${escapeHtml(item.id)}">Editar</button>
              <button type="button" class="secondary" data-archive-contact="${escapeHtml(item.id)}">Arquivar</button>
              <button type="button" class="danger" data-delete-contact="${escapeHtml(item.id)}">Excluir</button>
            </div>
            <span class="status">${escapeHtml(labelCode(item.status))}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum orgao publico cadastrado.</p>";
  }
  $$("[data-crm-open]").forEach((row) => {
    row.addEventListener("click", () => {
      state.selectedContactId = row.dataset.crmOpen;
      navigateTo("crm");
      renderCRM();
    });
  });
  $$("[data-edit-contact]").forEach((button) => {
    button.addEventListener("click", (event) => {
      event.stopPropagation();
      startContactEdit(button.dataset.editContact);
    });
  });
  $$("[data-archive-contact]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      await api(`/contatos/${button.dataset.archiveContact}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: "ARQUIVADO" }),
      });
      await loadData();
    });
  });
  $$("[data-delete-contact]").forEach((button) => {
    button.addEventListener("click", async (event) => {
      event.stopPropagation();
      if (!window.confirm("Excluir este cadastro da lista ativa? O registro ficara preservado na auditoria.")) return;
      await api(`/contatos/${button.dataset.deleteContact}`, { method: "DELETE" });
      await loadData();
    });
  });
  renderContactOptions();
}

function startContactEdit(contactId) {
  const contact = state.contacts.find((item) => item.id === contactId);
  if (!contact) return;
  state.editingContactId = contact.id;
  if (contact.tipo_contato === "ORGAO_PUBLICO") {
    navigateCadastroTab("orgaos");
    const form = $("#public-body-form");
    form.elements.nome.value = contact.nome || "";
    form.elements.telefone_principal.value = contact.telefone_principal || "";
    form.elements.email.value = contact.email || "";
    form.elements.bairro.value = contact.bairro || "";
    form.elements.territorio_id.value = contact.territorio_id || "";
    form.elements.observacoes.value = contact.observacoes || "";
    $("#public-body-submit").textContent = "Salvar alteracoes";
    form.scrollIntoView({ behavior: "smooth", block: "start" });
    return;
  }
  const form = $("#contact-form");
  navigateCadastroTab("pessoas");
  form.elements.tipo_contato.value = contact.tipo_contato || "CIDADAO";
  form.elements.nome.value = contact.nome || "";
  form.elements.telefone_principal.value = contact.telefone_principal || "";
  form.elements.email.value = contact.email || "";
  form.elements.bairro.value = contact.bairro || "";
  form.elements.territorio_id.value = contact.territorio_id || "";
  form.elements.nivel_relacionamento.value = contact.nivel_relacionamento || "CONTATO";
  form.elements.engajamento.value = contact.engajamento || "FRIO";
  form.elements.influencia.value = contact.influencia || "BAIXA";
  form.elements.voto_2028.value = contact.voto_2028 || "INDEFINIDO";
  form.elements.prioridade_politica.value = contact.prioridade_politica || "MEDIA";
  if (form.elements.foto_upload_id) form.elements.foto_upload_id.value = contact.foto_upload_id || "";
  if (form.elements.foto_url) form.elements.foto_url.value = contact.foto_url_publica || contact.foto_url || "";
  setProfilePhotoState("contact", contact.foto_url_publica || contact.foto_url, contact.foto_nome_arquivo, `Foto de ${contact.nome || "contato"}`);
  $("#contact-submit").textContent = "Salvar alteracoes";
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderContactOptions() {
  const crmContacts = state.contacts.filter((item) => item.tipo_contato !== "ORGAO_PUBLICO" && !["EXCLUIDO", "INATIVO"].includes(item.status) && contactMatchesModuleContext(item));
  const demandanteContacts = activeDemandanteContacts();
  const contactOptions =
    '<option value="">Selecione</option>' +
    demandanteContacts
      .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.nome)} - ${escapeHtml(demandanteTypeLabel(item.tipo_contato || "CIDADAO"))}</option>`)
      .join("");
  const internalUserOptions = internalDemandanteUsers()
    .filter((item) => !linkedContactForUser(item.id))
    .map((item) => `<option value="user:${escapeHtml(item.id)}">${escapeHtml(item.nome)} - ${escapeHtml(item.perfil === "VEREADOR" ? "Vereador" : "Colaborador interno")}</option>`)
    .join("");
  const demandSelect = $("#demand-contact-select");
  if (demandSelect) {
    const current = demandSelect.value || "";
    demandSelect.innerHTML = contactOptions + internalUserOptions;
    if (current && (current.startsWith("user:") || demandanteContacts.some((item) => item.id === current))) {
      demandSelect.value = current;
    }
  }
  ["#crm-contact-select", "#interaction-contact-select"].forEach((selector) => {
    const select = $(selector);
    if (!select) return;
    const current = select.value || (selector === "#crm-contact-select" ? state.selectedContactId : "");
    const optionsMarkup =
      '<option value="">Selecione</option>' +
      crmContacts
        .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.nome)} - ${escapeHtml(demandanteTypeLabel(item.tipo_contato || "CIDADAO"))}</option>`)
        .join("");
    select.innerHTML = selector === "#crm-contact-select" ? optionsMarkup : contactOptions;
    if ((selector === "#crm-contact-select" ? crmContacts : state.contacts).some((item) => item.id === current)) {
      select.value = current;
    }
  });
}

function renderCRM() {
  const visibleContacts = state.contacts.filter((item) => item.tipo_contato !== "ORGAO_PUBLICO" && !["EXCLUIDO", "INATIVO"].includes(item.status) && contactMatchesModuleContext(item));
  if ((!state.selectedContactId || !visibleContacts.some((item) => item.id === state.selectedContactId)) && visibleContacts[0]) {
    state.selectedContactId = visibleContacts[0].id;
  }
  if (!visibleContacts.length) {
    state.selectedContactId = null;
  }
  const contact = visibleContacts.find((item) => item.id === state.selectedContactId) || visibleContacts[0] || null;
  renderContactOptions();
  renderModuleContext("crm", visibleContacts.length, visibleContacts.length ? "" : "Nenhum contato neste recorte");
  const select = $("#crm-contact-select");
  if (select && contact) select.value = contact.id;
  if (!contact) {
    $("#crm-profile").innerHTML = "<p>Nenhum contato cadastrado.</p>";
    $("#crm-timeline").innerHTML = "<p>Sem historico.</p>";
    return;
  }

  const phone = String(contact.telefone_principal || "").replace(/\D/g, "");
  const whatsapp = phone ? `https://wa.me/55${phone}` : "#";
  $("#crm-profile").innerHTML = `
    <div class="profile-hero">
      ${avatarMarkup(contact.nome, contact.foto_url_publica)}
      <div>
        <h3>${escapeHtml(contact.nome)}</h3>
        <p>${escapeHtml(contact.bairro || contact.territorio_nome || "Sem bairro")} - ${escapeHtml(contact.telefone_principal || "Sem telefone")}</p>
      </div>
    </div>
    <div class="tag-list">
      <span class="tag">${escapeHtml(contact.nivel_relacionamento || "CONTATO")}</span>
      <span class="tag">Influencia ${escapeHtml(contact.influencia || "BAIXA")}</span>
      <span class="tag">Engajamento ${escapeHtml(contact.engajamento || "FRIO")}</span>
      <span class="tag">Voto 2028 ${escapeHtml(contact.voto_2028 || "INDEFINIDO")}</span>
    </div>
    <p>${escapeHtml(contact.observacoes || "Sem observacoes registradas.")}</p>
    <div class="quick-actions">
      <a class="button-link" href="${whatsapp}" target="_blank" rel="noreferrer">WhatsApp</a>
      <button type="button" class="secondary" data-contact-demand="${escapeHtml(contact.id)}">Abrir demanda</button>
    </div>
  `;
  const demandButton = $("[data-contact-demand]");
  if (demandButton) {
    demandButton.addEventListener("click", () => {
      navigateTo("atendimento");
      $("#demand-contact-select").value = contact.id;
      $("#demand-form").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }

  const timeline = [
    ...state.interactions
      .filter((item) => item.cidadao_id === contact.id)
      .map((item) => ({
        when: item.data_contato || item.created_at,
        title: item.assunto || item.tipo_interacao,
        text: `${item.tipo_interacao || "Interacao"} - ${item.canal_contato || "Canal nao informado"}`,
      })),
    ...state.demands
      .filter((item) => item.cidadao_id === contact.id)
      .map((item) => ({
        when: item.data_abertura || item.created_at,
        title: item.titulo,
        text: `Demanda ${demandStatusLabel(item.status)} - prioridade ${item.prioridade}`,
      })),
    ...state.agenda
      .filter((item) => (item.participantes || []).some((participant) => participant.cidadao_id === contact.id))
      .map((item) => ({
        when: item.data_inicio,
        title: item.titulo,
        text: `${AGENDA_TYPES[item.tipo_agenda] || item.tipo_agenda || "Agenda"} - ${item.status}`,
      })),
  ].sort((a, b) => String(b.when || "").localeCompare(String(a.when || "")));

  $("#crm-timeline").innerHTML =
    timeline
      .map(
        (item) => `
          <article class="timeline-item">
            <strong>${escapeHtml(item.title)}</strong>
            <span>${escapeHtml(formatDate(item.when))}</span>
            <span>${escapeHtml(item.text)}</span>
          </article>
        `,
      )
      .join("") || "<p>Sem interacoes registradas para este contato.</p>";
}

function renderUserOptions() {
  const selects = ["#agenda-user-select", "#demand-user-select", "#demand-edit-user-select"];
  selects.forEach((selector) => {
    const select = $(selector);
    if (!select) return;
    const current = select.value || state.user?.id || "";
    select.innerHTML =
      '<option value="">Sem responsavel definido</option>' +
      state.users.map((item) => `<option value="${item.id}">${item.nome} - ${item.perfil}</option>`).join("");
    if (state.users.some((item) => item.id === current)) {
      select.value = current;
    }
  });
}

function renderTerritoryOptions() {
  const selectors = ["#contact-territory-select", "#public-body-territory-select", "#demand-territory-select", "#demand-edit-territory-select"];
  selectors.forEach((selector) => {
    const select = $(selector);
    if (!select) return;
    const current = select.value;
    select.innerHTML = territoryOptions(current);
    if (state.territories.some((item) => item.id === current)) {
      select.value = current;
    }
  });
}

function renderUsers() {
  $("#user-list").innerHTML =
    state.users
      .map(
        (item) => `
          <article class="row profile-row">
            <div class="row-main">
              ${avatarMarkup(item.nome, item.foto_url_publica, "small")}
              <div>
                <h3>${escapeHtml(item.nome)}</h3>
                <p>${escapeHtml(item.email_login)} - ${escapeHtml(item.perfil)} - ${item.ativo ? "Ativo" : "Inativo"}</p>
              </div>
            </div>
            <div class="row-actions">
              <button type="button" class="secondary" data-edit-user="${escapeHtml(item.id)}">Editar</button>
              <button type="button" class="secondary" data-archive-user="${escapeHtml(item.id)}">Arquivar</button>
            </div>
            <span class="status">${item.equipe_id ? "Equipe" : "Gabinete"}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum colaborador cadastrado.</p>";
  $$("[data-edit-user]").forEach((button) => {
    button.addEventListener("click", () => startUserEdit(button.dataset.editUser));
  });
  $$("[data-archive-user]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/usuarios/${button.dataset.archiveUser}/status`, { method: "PATCH", body: JSON.stringify({ ativo: false }) });
      await loadData();
    });
  });
}

function startUserEdit(userId) {
  const user = state.users.find((item) => item.id === userId);
  if (!user) return;
  state.editingUserId = user.id;
  navigateCadastroTab("colaboradores");
  const form = $("#user-form");
  form.elements.nome.value = user.nome || "";
  form.elements.email_login.value = user.email_login || "";
  form.elements.telefone.value = user.telefone || "";
  form.elements.perfil.value = user.perfil || "COLABORADOR_EXTERNO";
  if (form.elements.foto_upload_id) form.elements.foto_upload_id.value = user.foto_upload_id || "";
  if (form.elements.foto_url) form.elements.foto_url.value = user.foto_url_publica || user.foto_url || "";
  setProfilePhotoState("user", user.foto_url_publica || user.foto_url, user.foto_nome_arquivo, `Foto de ${user.nome || "colaborador"}`);
  $("#user-submit").textContent = "Salvar alteracoes";
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderTerritories() {
  const list = $("#territory-list");
  if (!list) return;
  list.innerHTML =
    state.territories
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.nome)}</h3>
              <p>${escapeHtml(item.tipo)} - ${escapeHtml(item.codigo_externo || "Sem codigo")}</p>
            </div>
            <span class="status">${item.ativo ? "Ativo" : "Inativo"}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum territorio cadastrado.</p>";
}

function renderAgenda() {
  const visibleAgenda = state.agenda.filter((item) => agendaMatchesModuleContext(item));
  renderModuleContext("agenda", visibleAgenda.length, visibleAgenda.length ? "" : "Nenhum compromisso neste recorte");
  $("#agenda-list").innerHTML =
    visibleAgenda
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.titulo)}</h3>
              <p>${escapeHtml(AGENDA_TYPES[item.tipo_agenda] || item.tipo_agenda || "Compromisso")} - ${escapeHtml(item.local_texto || "Sem local")}</p>
              <p>Situacao: ${escapeHtml(labelCode(item.status))} - Publico estimado: ${escapeHtml(item.publico_estimado || 0)}</p>
              ${item.relatorio_execucao ? `<p>Relatorio: ${escapeHtml(item.relatorio_execucao)}</p>` : ""}
            </div>
            <div class="row-actions">
              <button type="button" data-agenda-report="${escapeHtml(item.id)}" class="secondary">Relatorio</button>
              <button type="button" data-agenda-done="${escapeHtml(item.id)}">Realizado</button>
            </div>
            <span class="status">${escapeHtml(item.eh_agenda_vereador ? "Parlamentar" : "Equipe")}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum evento cadastrado.</p>";
  const first = visibleAgenda[0];
  $("#agenda-summary").textContent = first
    ? `${first.titulo} em ${first.local_texto || "local a confirmar"} - ${labelCode(first.status)}.`
    : "Nenhum compromisso encontrado.";
  $$("[data-agenda-report]").forEach((button) => {
    button.addEventListener("click", () => {
      $("#agenda-report-select").value = button.dataset.agendaReport;
      $("#agenda-report-form").scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  $$("[data-agenda-done]").forEach((button) => {
    button.addEventListener("click", async () => {
      await api(`/agenda-eventos/${button.dataset.agendaDone}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: "REALIZADO" }),
      });
      await loadData();
    });
  });
  renderAgendaOptions();
}

function renderAgendaOptions() {
  const select = $("#agenda-report-select");
  if (!select) return;
  const current = select.value;
  select.innerHTML =
    '<option value="">Selecione um compromisso</option>' +
    state.agenda
      .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.titulo)} - ${escapeHtml(labelCode(item.status))}</option>`)
      .join("");
  if (state.agenda.some((item) => item.id === current)) {
    select.value = current;
  }
}

function renderLegislative() {
  $("#legislative-kanban").innerHTML = LEGISLATIVE_STAGES.map(([stage, label]) => {
    const items = state.propositions.filter((item) => (item.etapa_kanban || item.status) === stage);
    return `
      <section class="kanban-column">
        <h3>${label}</h3>
        ${items
          .map(
            (item) => `
              <article class="kanban-card">
                <strong>${escapeHtml(item.numero || item.tipo || "Sem numero")}</strong>
                <span>${escapeHtml(item.titulo)}</span>
                <span>${escapeHtml(item.tema || "Sem tema")} - ${escapeHtml(item.posicionamento || "Sem posicao")}</span>
              </article>
            `,
          )
          .join("") || "<p>Sem proposicoes.</p>"}
      </section>
    `;
  }).join("");
}

function renderAmendments() {
  $("#amendment-list").innerHTML =
    state.amendments
      .map((item) => {
        return `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.titulo)}</h3>
              <p>${escapeHtml(item.numero)} - ${escapeHtml(item.area || "Sem area")} - ${escapeHtml(item.beneficiario || "Sem beneficiario")}</p>
              <p>${escapeHtml(item.objeto || "Sem objeto detalhado.")}</p>
              <p>Pleiteado: ${escapeHtml(formatCurrency(item.valor_indicado))} - Aprovado: ${escapeHtml(formatCurrency(item.valor_aprovado))}</p>
              <small>Empenhado: ${escapeHtml(formatCurrency(item.valor_empenhado))}${item.data_empenho ? ` - ${escapeHtml(formatDate(item.data_empenho))}` : " - sem data de empenho"}</small>
            </div>
            <span class="status ${statusClass(item.status_execucao)}">${escapeHtml(labelCode(item.status_execucao))}</span>
          </article>
        `;
      })
      .join("") || "<p>Nenhuma emenda cadastrada.</p>";
}

function renderOfficeDemandOptions() {
  const select = $("#office-demand-select");
  if (!select) return;
  const current = select.value;
  select.innerHTML =
    '<option value="">Sem demanda vinculada</option>' +
    state.demands.map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.titulo)} - ${escapeHtml(item.cidadao_nome || "sem demandante")}</option>`).join("");
  if (state.demands.some((item) => item.id === current)) {
    select.value = current;
  }
}

function renderOffices() {
  $("#office-list").innerHTML =
    state.offices
      .map((item) => {
        const late = Number(item.dias_sem_resposta || 0) >= 15 && !["RESPONDIDO", "CONCLUIDO"].includes(item.status);
        return `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.numero)} - ${escapeHtml(item.titulo)}</h3>
              <p>${escapeHtml(item.orgao_destino)} - ${escapeHtml(item.assunto)}</p>
              <p>Demanda: ${escapeHtml(item.demanda_titulo || "Nao vinculada")} - Responsavel: ${escapeHtml(item.responsavel_nome || "Nao definido")}</p>
              <p>${late ? `Sem resposta ha ${Number(item.dias_sem_resposta || 0)} dias.` : escapeHtml(item.follow_up || "Sem acompanhamento critico.")}</p>
            </div>
            <span class="status ${late ? "warning" : statusClass(item.status)}">${escapeHtml(labelCode(item.status))}</span>
          </article>
        `;
      })
      .join("") || "<p>Nenhum oficio cadastrado.</p>";
  renderOfficeDemandOptions();
}

function renderCompliance() {
  const activeUsers = state.users.filter((item) => item.ativo).length;
  const activeContacts = state.contacts.filter((item) => !["INATIVO", "EXCLUIDO"].includes(item.status)).length;
  const slaConfig = state.overview?.sla?.configuracao || {};
  const slaHistory = state.overview?.sla?.historico_mensal || [];
  const metrics = [
    ["Logs", state.audit.length],
    ["Usuarios ativos", activeUsers],
    ["Contatos ativos", activeContacts],
    ["Perfis", new Set(state.users.map((item) => item.perfil)).size],
  ];
  $("#compliance-metrics").innerHTML = metrics
    .map(
      ([label, value]) => `
        <article class="metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </article>
      `,
    )
    .join("");
  $("#audit-list").innerHTML =
    state.audit
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.acao)} - ${escapeHtml(item.entidade)}</h3>
              <p>${escapeHtml(formatDate(item.created_at))}</p>
            </div>
            <span class="status">${escapeHtml(item.entidade_id ? "Rastreado" : "Sistema")}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum log disponivel.</p>";

  const configForm = $("#sla-config-form");
  if (configForm) {
    configForm.elements.critica_horas.value = slaConfig.critica_horas ?? 4;
    configForm.elements.alta_horas.value = slaConfig.alta_horas ?? 24;
    configForm.elements.media_horas.value = slaConfig.media_horas ?? 72;
    configForm.elements.baixa_horas.value = slaConfig.baixa_horas ?? 120;
    configForm.elements.janela_risco_percentual.value = slaConfig.janela_risco_percentual ?? 0.75;
  }

  $("#sla-history-list").innerHTML =
    slaHistory
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.mes || "Sem mes")}</h3>
              <p>No prazo: ${escapeHtml(item.no_prazo || 0)} | Em risco: ${escapeHtml(item.em_risco || 0)} | Vencido: ${escapeHtml(item.vencido || 0)}</p>
              <small>Concluidas no prazo: ${escapeHtml(item.concluido_no_prazo || 0)} | Concluidas em atraso: ${escapeHtml(item.concluido_em_atraso || 0)}</small>
            </div>
            <span class="status ${item.vencido ? "vencido" : item.em_risco ? "em-risco" : "concluido-no-prazo"}">${escapeHtml(item.total || 0)} snapshot(s)</span>
          </article>
        `,
      )
      .join("") || '<p>Nenhum historico mensal de SLA disponivel.</p>';
}

function renderReports() {
  const activeContacts = activeDemandanteContacts();
  const politicalBase = activeContacts.filter((item) => item.tipo_contato !== "COLABORADOR");
  const openDemands = state.demands.filter((item) => !["CONCLUIDA", "ARQUIVADA", "EXCLUIDO", "CANCELADA"].includes(item.status));
  const closed30 = state.demands.filter((item) => item.status === "CONCLUIDA" && isWithinDays(item.updated_at || item.data_conclusao || item.created_at, 30));
  const opened30 = state.demands.filter((item) => isWithinDays(item.created_at || item.data_abertura, 30));
  const base30 = politicalBase.filter((item) => isWithinDays(item.created_at, 30));
  const basePrevious30 = politicalBase.filter((item) => isWithinDays(item.created_at, 60, 30));
  const baseGrowth = percentageDelta(base30.length, basePrevious30.length);
  const leaders = politicalBase.filter((item) => isLeadershipContact(item));
  const mobilized = politicalBase.filter((item) => isStrongEngagementContact(item));
  const voteCertain = politicalBase.filter((item) => item.voto_2028 === "VOTO_CERTO");
  const overdue = state.demands.filter((item) => item.sla_status === "VENCIDO").length;
  const risk = state.demands.filter((item) => item.sla_status === "EM_RISCO").length;
  const completionRate = opened30.length ? Math.round((closed30.length / opened30.length) * 100) : 0;
  const realizedAgenda30 = state.agenda.filter((item) => item.status === "REALIZADO" && isWithinDays(item.updated_at || item.data_fim || item.data_inicio, 30));
  const interaction30 = state.interactions.filter((item) => isWithinDays(item.created_at || item.data_contato, 30));
  const respondedOffices30 = state.offices.filter((item) => ["RESPONDIDO", "CONCLUIDO"].includes(item.status) && isWithinDays(item.updated_at || item.created_at, 30));
  const activeUsers = internalDemandanteUsers();
  const teamRows = activeUsers
    .map((user) => {
      const interactions = interaction30.filter((item) => item.responsavel_usuario_id === user.id).length;
      const completedDemands = closed30.filter((item) => item.responsavel_usuario_id === user.id).length;
      const realizedAgenda = realizedAgenda30.filter((item) => item.responsavel_usuario_id === user.id).length;
      const respondedOffices = respondedOffices30.filter((item) => item.responsavel_usuario_id === user.id).length;
      const score = completedDemands * 3 + realizedAgenda * 2 + respondedOffices * 2 + interactions;
      return { user, interactions, completedDemands, realizedAgenda, respondedOffices, score };
    })
    .sort((left, right) => right.score - left.score);
  const catalogByCode = Object.fromEntries((state.reportCatalog || []).map((item) => [item.codigo, item]));
  const jobRequests = state.demands
    .filter((item) => item.tipo_demanda === "INDICACAO_VAGA")
    .sort((left, right) => String(right.created_at || right.data_abertura || "").localeCompare(String(left.created_at || left.data_abertura || "")));

  $("#reports-highlight").innerHTML = [
    ["Base ativa", politicalBase.length, baseGrowth >= 0 ? `+${baseGrowth}% vs 30d anteriores` : `${baseGrowth}% vs 30d anteriores`],
    ["Demandas resolvidas", closed30.length, `${completionRate}% de resolutividade em 30d`],
    ["Equipe ativa", activeUsers.length, `${interaction30.length} interacoes registradas em 30d`],
  ]
    .map(
      ([label, value, detail]) => `
        <article class="metric">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <small>${escapeHtml(detail)}</small>
        </article>
      `,
    )
    .join("");

  const reportCards = [
    {
      title: "Crescimento da base politica",
      value: `${baseGrowth >= 0 ? "+" : ""}${baseGrowth}%`,
      description: "Mostra se o mandato esta ampliando contatos qualificados, liderancas e voto certo com constancia.",
      kpis: [`${politicalBase.length} registros ativos`, `${leaders.length} liderancas`, `${voteCertain.length} voto certo`],
      section: "crm",
      formats: catalogByCode.executivo?.formatos || ["json"],
      actionLabel: "Abrir relacionamento",
    },
    {
      title: "Resolutividade do atendimento",
      value: `${completionRate}%`,
      description: "Compara a fila aberta com o que foi fechado, para mostrar entrega concreta e capacidade de resposta.",
      kpis: [`${openDemands.length} abertas`, `${risk} em risco`, `${overdue} vencidas`],
      section: "atendimento",
      formats: catalogByCode.operacional?.formatos || ["json"],
      actionLabel: "Abrir atendimento",
    },
    {
      title: "Equipe proativa e produtiva",
      value: `${interaction30.length}`,
      description: "Usa interacoes, agenda realizada, oficios respondidos e demandas concluidas para medir cadencia operacional.",
      kpis: [`${realizedAgenda30.length} agendas realizadas`, `${respondedOffices30.length} oficios respondidos`, `${activeUsers.length} usuarios ativos`],
      section: "cadastros",
      formats: catalogByCode.executivo?.formatos || ["json"],
      actionLabel: "Abrir equipe",
    },
    {
      title: "Banco de curriculos",
      value: `${jobRequests.length}`,
      description: "Concentra pedidos de indicacao para vaga com CV pronto para consulta rapida da equipe.",
      kpis: [`${jobRequests.filter((item) => item.status === "CONCLUIDA").length} concluidas`, `${jobRequests.filter((item) => item.status === "ARQUIVADA").length} arquivadas`, `${jobRequests.filter((item) => item.cv_url_publica).length} com CV`],
      section: "relatorios",
      formats: catalogByCode.operacional?.formatos || ["json"],
      actionLabel: "Ver curriculos",
    },
  ];
  $("#reports-cards").innerHTML = reportCards.map((item) => `
      <article class="report-card">
        <strong>${escapeHtml(item.title)}</strong>
        <div class="report-value">${escapeHtml(item.value)}</div>
        <p>${escapeHtml(item.description)}</p>
        <div class="report-kpis">${item.kpis.map((kpi) => `<span>${escapeHtml(kpi)}</span>`).join("")}</div>
        <small>Formatos previstos: ${escapeHtml(item.formats.join(", "))}</small>
        <div class="report-actions">
          <button type="button" class="secondary" data-report-section="${escapeHtml(item.section)}">${escapeHtml(item.actionLabel)}</button>
        </div>
      </article>
    `).join("");

  const strategies = [
    {
      title: "Estrategia 1: expandir base com cobertura territorial",
      text: baseGrowth <= 0 ? "A base nao cresceu no ultimo ciclo. Priorize cadastros em territorios com calor alto e sentimento sensivel para aumentar cobertura politica." : `A base cresceu ${baseGrowth}% no ultimo ciclo. Preserve cadencia em territorio e transforme novos contatos em relacao recorrente.`,
    },
    {
      title: "Estrategia 2: transformar demanda em prova de entrega",
      text: overdue || risk ? `${overdue} demandas vencidas e ${risk} em risco pedem mutirao de resolucao. O vereador vende entrega, nao fila parada.` : "A fila esta sob controle. Use casos concluidos para narrativa de resultado e para realimentar a base politica.",
    },
    {
      title: "Estrategia 3: ativar curriculos com triagem rapida",
      text: jobRequests.length ? `Ha ${jobRequests.length} pedido(s) de vaga no banco. Classifique por tipo de vaga e use a descricao final como nota objetiva de alocacao.` : "Ainda nao ha pedido de vaga no banco de curriculos. Quando surgir, registre CV e perfil desejado no ato.",
    },
  ];
  $("#reports-strategies").innerHTML = strategies.map((item) => `
      <article class="report-strategy">
        <strong>${escapeHtml(item.title)}</strong>
        <p>${escapeHtml(item.text)}</p>
      </article>
    `).join("");

  $("#reports-team").innerHTML = teamRows.length ? teamRows.map((item) => `
        <article class="row">
          <div>
            <h3 class="report-team-title">${escapeHtml(item.user.nome)}</h3>
            <p>${escapeHtml(item.user.perfil)} - ${item.user.ativo ? "Ativo" : "Inativo"}</p>
            <p>${item.interactions} interacoes • ${item.completedDemands} demandas concluidas • ${item.realizedAgenda} agendas realizadas • ${item.respondedOffices} oficios respondidos</p>
          </div>
          <div class="row-actions">
            <button type="button" class="secondary" data-report-section="cadastros">Abrir equipe</button>
          </div>
          <span class="report-team-score">${escapeHtml(item.score)}</span>
        </article>
      `).join("") : "<p>Nenhum usuario ativo para medir produtividade.</p>";

  $("#reports-jobs").innerHTML = jobRequests.length ? jobRequests.map((item) => `
      <article class="row">
        <div>
          <h3>${escapeHtml(item.beneficiario_nome || item.cidadao_nome || "Pessoa nao identificada")}</h3>
          <p>${escapeHtml(item.cidadao_telefone || "Sem telefone")} - ${escapeHtml(labelCode(item.tipo_vaga_pretendida || "OUTROS"))}${item.tipo_vaga_pretendida === "OUTROS" && item.vaga_outros_descricao ? ` (${escapeHtml(item.vaga_outros_descricao)})` : ""}</p>
          <p>Status: ${escapeHtml(demandStatusLabel(item.status))}${item.cv_nome_arquivo ? ` - CV: ${escapeHtml(item.cv_nome_arquivo)}` : " - CV pendente"}</p>
        </div>
        <div class="row-actions">
          ${item.cv_url_publica ? `<a class="button-link secondary" href="${escapeHtml(item.cv_url_publica)}" target="_blank" rel="noreferrer">Abrir CV</a>` : ""}
          <button type="button" class="secondary" data-select-demand="${escapeHtml(item.id)}">Abrir demanda</button>
        </div>
        <span class="status ${statusClass(item.status)}">${escapeHtml(demandStatusLabel(item.status))}</span>
      </article>
    `).join("") : "<p>Nenhuma solicitacao de vaga registrada.</p>";
}

async function saveSlaConfiguration(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#sla-config-message", "Salvando parametros...");
  const data = Object.fromEntries(new FormData(form).entries());
  const payload = {
    critica_horas: Number(data.critica_horas || 0),
    alta_horas: Number(data.alta_horas || 0),
    media_horas: Number(data.media_horas || 0),
    baixa_horas: Number(data.baixa_horas || 0),
    janela_risco_percentual: Number(data.janela_risco_percentual || 0),
  };
  try {
    await api("/configuracoes/sla", { method: "PUT", body: JSON.stringify(payload) });
    setMessage("#sla-config-message", "Parametros de SLA atualizados.");
    await loadData();
  } catch (error) {
    setMessage("#sla-config-message", error.message);
  }
}

function renderUser() {
  $("#user-chip").textContent = state.user ? `${state.user.nome} - ${state.user.perfil}` : "Sem usuario";
}

function renderAll() {
  renderUser();
  renderCommandCenter();
  renderReports();
  renderDemands();
  renderContacts();
  renderCRM();
  renderUsers();
  renderTerritories();
  renderAgenda();
  renderLegislative();
  renderAmendments();
  renderOffices();
  renderCompliance();
  renderUserOptions();
  renderTerritoryOptions();
  renderSync();
  renderSearchResults();
  renderAssistantPanel();
}

async function loadData() {
  const [me, overview, demands, contacts, users, territories, agenda, interactions, propositions, amendments, offices, audit, reportCatalog] = await Promise.all([
    api("/auth/me"),
    api("/political-os/overview"),
    api("/demandas?page_size=200"),
    api("/contatos?page_size=200"),
    api("/usuarios?page_size=200"),
    api("/territorios?page_size=200&sort_by=nome&sort_order=asc"),
    api("/agenda?page_size=200"),
    api("/interacoes?page_size=200"),
    api("/proposicoes?page_size=200"),
    api("/emendas?page_size=200"),
    api("/oficios?page_size=200"),
    api("/auditoria?page_size=12"),
    api("/relatorios/catalogo"),
  ]);
  state.user = me.data;
  state.overview = overview.data;
  state.sentimentSnapshot = overview.data.sentimento;
  state.demands = demands.data;
  state.contacts = contacts.data;
  state.users = users.data;
  state.territories = territories.data;
  state.agenda = agenda.data;
  state.interactions = interactions.data;
  state.propositions = propositions.data;
  state.amendments = amendments.data;
  state.offices = offices.data;
  state.audit = audit.data;
  state.reportCatalog = reportCatalog.data;
  renderAll();
  const appliedUrlContext = await applyRequestedContextFromUrl();
  if (state.sentimentFilters.canal || state.sentimentFilters.periodo || state.sentimentFilters.territorio) {
    await refreshSentimentSummary();
  }
  if (!appliedUrlContext) {
    await refreshAssistantContext(state.assistantContext, { force: true });
  }
}

async function login(event) {
  event.preventDefault();
  setMessage("#login-message", "Entrando...");
  const data = Object.fromEntries(new FormData(event.currentTarget).entries());
  try {
    const payload = await api("/auth/login", { method: "POST", body: JSON.stringify(data) });
    state.token = payload.data.access_token;
    localStorage.setItem("gabinete_token", state.token);
    showApp();
    await loadData();
    setMessage("#login-message", "");
  } catch (error) {
    setMessage("#login-message", error.message);
  }
}

async function createContact(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#contact-message", "Salvando...");
  const data = Object.fromEntries(new FormData(form).entries());
  if (data.tipo_contato === "LIDERANCA" && (!data.nivel_relacionamento || data.nivel_relacionamento === "CONTATO")) {
    data.nivel_relacionamento = "LIDERANCA";
    data.influencia = data.influencia || "ALTA";
  }
  if (data.tipo_contato === "VEREADOR") {
    data.influencia = data.influencia || "ALTA";
    data.engajamento = data.engajamento || "FORTE";
    data.voto_2028 = data.voto_2028 === "INDEFINIDO" ? "VOTO_CERTO" : data.voto_2028;
    data.prioridade_politica = "ALTA";
  }
  if (!data.territorio_id) delete data.territorio_id;
  try {
    const uploaded = await uploadProfilePhoto(form.elements.foto_file?.files?.[0], state.editingContactId || data.nome || "contato");
    if (uploaded) {
      data.foto_upload_id = uploaded.id;
      data.foto_url = uploaded.url_publica || uploaded.url_storage;
    } else if (!data.foto_upload_id) {
      delete data.foto_upload_id;
      delete data.foto_url;
    }
    delete data.foto_file;
    const endpoint = state.editingContactId ? `/contatos/${state.editingContactId}` : "/contatos";
    const method = state.editingContactId ? "PUT" : "POST";
    const saved = await api(endpoint, { method, body: JSON.stringify(data) });
    state.contacts = upsertById(state.contacts, saved.data);
    state.selectedContactId = saved.data.id;
    resetContactFormState();
    setMessage("#contact-message", "Cadastro salvo.");
    renderContacts();
    renderCRM();
    try {
      await loadData();
    } catch (error) {
      console.error("Falha ao recarregar dados apos salvar contato", error);
      setMessage("#contact-message", "Cadastro salvo. A lista foi atualizada localmente; recarga completa pendente.");
    }
  } catch (error) {
    setMessage("#contact-message", error.message);
  }
}

async function createPublicBody(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#public-body-message", "Salvando...");
  const data = Object.fromEntries(new FormData(form).entries());
  data.tipo_contato = "ORGAO_PUBLICO";
  data.nivel_relacionamento = "ORGAO_PUBLICO";
  data.engajamento = "INSTITUCIONAL";
  data.voto_2028 = "NAO_APLICA";
  if (!data.territorio_id) delete data.territorio_id;
  try {
    const endpoint = state.editingContactId ? `/contatos/${state.editingContactId}` : "/contatos";
    const method = state.editingContactId ? "PUT" : "POST";
    await api(endpoint, { method, body: JSON.stringify(data) });
    state.editingContactId = null;
    form.reset();
    $("#public-body-submit").textContent = "Salvar orgao";
    setMessage("#public-body-message", "Orgao publico salvo.");
    await loadData();
  } catch (error) {
    setMessage("#public-body-message", error.message);
  }
}

async function createInteraction(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#interaction-message", "Registrando...");
  const data = Object.fromEntries(new FormData(form).entries());
  try {
    await api("/interacoes", { method: "POST", body: JSON.stringify(data) });
    state.selectedContactId = data.cidadao_id;
    form.reset();
    setMessage("#interaction-message", "Interacao registrada.");
    await loadData();
  } catch (error) {
    setMessage("#interaction-message", error.message);
  }
}

async function createDemand(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#demand-message", "Criando...");
  setMessage("#demand-cv-message", "");
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.cidadao_id) {
    setMessage("#demand-message", "Selecione um demandante cadastrado antes de criar a demanda.");
    return;
  }
  if (isVacancyDemand(data.tipo_demanda)) {
    if (!data.tipo_vaga_pretendida) {
      setMessage("#demand-message", "Selecione o tipo da vaga para registrar a indicacao.");
      return;
    }
    if (data.tipo_vaga_pretendida === "OUTROS" && !data.vaga_outros_descricao) {
      setMessage("#demand-message", "Descreva a vaga desejada quando escolher 'Outros'.");
      return;
    }
    const file = form.elements.cv_file?.files?.[0];
    if (!file) {
      setMessage("#demand-message", "Anexe o Curriculum Vitae para concluir a indicacao para vaga.");
      return;
    }
  } else {
    delete data.tipo_vaga_pretendida;
    delete data.vaga_outros_descricao;
  }
  if (!data.territorio_id) delete data.territorio_id;
  if (!data.responsavel_usuario_id) delete data.responsavel_usuario_id;
  try {
    if (isVacancyDemand(data.tipo_demanda)) {
      const uploaded = await uploadDemandFile(form.elements.cv_file?.files?.[0], data.titulo || data.beneficiario_nome || "vaga");
      if (uploaded) {
        data.cv_upload_id = uploaded.id;
        data.cv_url = uploaded.url_publica || uploaded.url_storage;
        if (!Array.isArray(data.anexos)) data.anexos = [];
      }
    } else {
      delete data.cv_upload_id;
      delete data.cv_url;
    }
    data.cidadao_id = await ensureDemandanteContact(data.cidadao_id);
    const created = await api("/demandas", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    syncVacancyFields(form, "create");
    state.selectedDemandId = created.data.id;
    setMessage("#demand-message", "Demanda criada.");
    await loadData();
  } catch (error) {
    setMessage("#demand-message", error.message);
  }
}

async function ensureDemandanteContact(value) {
  if (!String(value || "").startsWith("user:")) return value;
  const userId = String(value).slice(5);
  const linked = linkedContactForUser(userId);
  if (linked) return linked.id;
  const user = state.users.find((item) => item.id === userId);
  if (!user) throw new Error("Usuario interno nao encontrado para virar demandante.");
  const payload = {
    nome: user.nome,
    email: user.email_login || null,
    telefone_principal: user.telefone || null,
    bairro: "Gabinete",
    tipo_contato: user.perfil === "VEREADOR" ? "VEREADOR" : "COLABORADOR",
    usuario_id: user.id,
    origem_cadastro: "WEB_INTERNO",
    nivel_relacionamento: user.perfil === "VEREADOR" ? "VOTO_CERTO" : "CONTATO",
    influencia: user.perfil === "VEREADOR" ? "ALTA" : "MEDIA",
    engajamento: user.perfil === "VEREADOR" ? "FORTE" : "MEDIO",
    voto_2028: user.perfil === "VEREADOR" ? "VOTO_CERTO" : "NAO_APLICA",
    prioridade_politica: user.perfil === "VEREADOR" ? "ALTA" : "MEDIA",
    foto_upload_id: user.foto_upload_id || null,
    foto_url: user.foto_url_publica || user.foto_url || null,
    observacoes: `Demandante interno espelhado automaticamente do usuario ${user.perfil}.`,
  };
  const saved = await api("/contatos", { method: "POST", body: JSON.stringify(payload) });
  state.contacts = [saved.data, ...state.contacts];
  return saved.data.id;
}

async function saveDemandEdit(event) {
  event.preventDefault();
  if (!state.editingDemandId) return;
  const form = event.currentTarget;
  setMessage("#demand-edit-message", "Salvando...");
  setMessage("#demand-edit-cv-message", "");
  const data = Object.fromEntries(new FormData(form).entries());
  if (isVacancyDemand(data.tipo_demanda)) {
    if (!data.tipo_vaga_pretendida) {
      setMessage("#demand-edit-message", "Selecione o tipo da vaga.");
      return;
    }
    if (data.tipo_vaga_pretendida === "OUTROS" && !data.vaga_outros_descricao) {
      setMessage("#demand-edit-message", "Descreva a vaga desejada quando escolher 'Outros'.");
      return;
    }
    const uploaded = await uploadDemandFile(form.elements.cv_file?.files?.[0], state.editingDemandId);
    if (uploaded) {
      data.cv_upload_id = uploaded.id;
      data.cv_url = uploaded.url_publica || uploaded.url_storage;
    }
  } else {
    data.tipo_vaga_pretendida = null;
    data.vaga_outros_descricao = null;
    data.cv_upload_id = null;
    data.cv_url = null;
  }
  if (!data.territorio_id) data.territorio_id = null;
  if (!data.responsavel_usuario_id) data.responsavel_usuario_id = null;
  try {
    await api(`/demandas/${state.editingDemandId}`, { method: "PUT", body: JSON.stringify(data) });
    state.editingDemandId = null;
    form.reset();
    syncVacancyFields(form, "edit");
    setCvLink("#demand-edit-cv-link", null, null);
    form.classList.add("hidden");
    setMessage("#demand-edit-message", "Demanda atualizada.");
    await loadData();
  } catch (error) {
    setMessage("#demand-edit-message", error.message);
  }
}

function toIsoFromLocal(value) {
  if (!value) return null;
  const date = new Date(value);
  return date.toISOString();
}

async function createAgenda(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#agenda-message", "Cadastrando compromisso...");
  const data = Object.fromEntries(new FormData(form).entries());
  const payload = {
    ...data,
    status: "PLANEJADO",
    data_inicio: toIsoFromLocal(data.data_inicio),
    data_fim: toIsoFromLocal(data.data_fim),
    eh_agenda_vereador: data.eh_agenda_vereador === "true",
  };
  try {
    await api("/agenda-eventos", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    setMessage("#agenda-message", "Compromisso cadastrado.");
    await loadData();
  } catch (error) {
    setMessage("#agenda-message", error.message);
  }
}

async function uploadAgendaFile(file, eventoId) {
  if (!file) return null;
  const body = new FormData();
  body.append("file", file);
  body.append("contexto", `agenda:${eventoId}`);
  const uploaded = await api("/uploads", { method: "POST", body });
  return uploaded.data;
}

async function uploadDemandFile(file, reference) {
  if (!file) return null;
  const body = new FormData();
  body.append("file", file);
  body.append("contexto", `demanda-cv:${reference}`);
  const uploaded = await api("/uploads", { method: "POST", body });
  return uploaded.data;
}

async function uploadProfilePhoto(file, reference) {
  if (!file) return null;
  const body = new FormData();
  body.append("file", file);
  body.append("contexto", `perfil-foto:${reference}`);
  const uploaded = await api("/uploads", { method: "POST", body });
  return uploaded.data;
}

async function saveAgendaReport(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#agenda-report-message", "Salvando relatorio...");
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.evento_id) {
    setMessage("#agenda-report-message", "Selecione um compromisso.");
    return;
  }
  try {
    const file = form.elements.arquivo.files[0];
    const uploaded = await uploadAgendaFile(file, data.evento_id);
    const current = state.agenda.find((item) => item.id === data.evento_id);
    const anexos = [...(current?.anexos || [])];
    if (uploaded) anexos.push(uploaded);
    await api(`/agenda-eventos/${data.evento_id}`, {
      method: "PUT",
      body: JSON.stringify({
        status: "REALIZADO",
        publico_estimado: data.publico_estimado ? Number(data.publico_estimado) : null,
        relatorio_execucao: data.relatorio_execucao,
        anexos,
      }),
    });
    form.reset();
    setMessage("#agenda-report-message", "Relatorio salvo e compromisso marcado como realizado.");
    await loadData();
  } catch (error) {
    setMessage("#agenda-report-message", error.message);
  }
}

async function createUser(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#user-message", "Salvando...");
  const data = Object.fromEntries(new FormData(form).entries());
  data.ativo = true;
  try {
    const uploaded = await uploadProfilePhoto(form.elements.foto_file?.files?.[0], state.editingUserId || data.nome || "usuario");
    if (uploaded) {
      data.foto_upload_id = uploaded.id;
      data.foto_url = uploaded.url_publica || uploaded.url_storage;
    } else if (!data.foto_upload_id) {
      delete data.foto_upload_id;
      delete data.foto_url;
    }
    delete data.foto_file;
    const endpoint = state.editingUserId ? `/usuarios/${state.editingUserId}` : "/usuarios";
    const method = state.editingUserId ? "PUT" : "POST";
    const saved = await api(endpoint, { method, body: JSON.stringify(data) });
    state.users = upsertById(state.users, saved.data);
    resetUserFormState();
    setMessage("#user-message", method === "POST" ? "Colaborador salvo. Senha inicial: Senha@123." : "Colaborador atualizado.");
    renderUsers();
    try {
      await loadData();
    } catch (error) {
      console.error("Falha ao recarregar dados apos salvar colaborador", error);
      setMessage("#user-message", "Colaborador salvo. A lista foi atualizada localmente; recarga completa pendente.");
    }
  } catch (error) {
    setMessage("#user-message", error.message);
  }
}

async function createProposition(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#proposition-message", "Salvando...");
  const data = Object.fromEntries(new FormData(form).entries());
  data.status = data.etapa_kanban;
  try {
    await api("/proposicoes", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    setMessage("#proposition-message", "Proposicao salva.");
    await loadData();
  } catch (error) {
    setMessage("#proposition-message", error.message);
  }
}

async function createAmendment(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#amendment-message", "Salvando...");
  const data = Object.fromEntries(new FormData(form).entries());
  data.valor_indicado = Number(data.valor_indicado || 0);
  data.valor_aprovado = Number(data.valor_aprovado || 0);
  data.valor_empenhado = Number(data.valor_empenhado || 0);
  if (!data.data_empenho) delete data.data_empenho;
  try {
    await api("/emendas", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    setMessage("#amendment-message", "Emenda salva.");
    await loadData();
  } catch (error) {
    setMessage("#amendment-message", error.message);
  }
}

async function createOffice(event) {
  event.preventDefault();
  const form = event.currentTarget;
  setMessage("#office-message", "Gerando...");
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.demanda_id) delete data.demanda_id;
  if (data.status === "ENVIADO") data.data_envio = new Date().toISOString();
  try {
    await api("/oficios", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    setMessage("#office-message", "Oficio gerado.");
    await loadData();
  } catch (error) {
    setMessage("#office-message", error.message);
  }
}

async function summarizeFirstDemand() {
  const context = normalizeAssistantContext(state.assistantContext);
  $("#ai-output").textContent = "Gerando resumo contextual...";
  try {
    const payload = await api("/ai/resumir-contexto", {
      method: "POST",
      body: JSON.stringify(context),
    });
    $("#ai-output").textContent = payload.data.resumo;
  } catch (error) {
    $("#ai-output").textContent = error.message;
  }
}

async function suggestNextStep() {
  const context = normalizeAssistantContext(state.assistantContext);
  $("#ai-output").textContent = "Analisando proxima etapa recomendada...";
  try {
    const payload = await api("/ai/sugerir-proxima-etapa", {
      method: "POST",
      body: JSON.stringify(context),
    });
    $("#ai-output").textContent = `${payload.data.sugestao} ${payload.data.justificativa}`;
  } catch (error) {
    $("#ai-output").textContent = error.message;
  }
}

function renderSync() {
  $("#sync-count").textContent = String(state.syncHistory.length);
  $("#sync-errors").textContent = String(state.syncHistory.filter((item) => item.status === "ERRO").length);
  $("#sync-queue").textContent = "0";
  $("#sync-status").textContent = state.syncHistory.length ? "Sincronizado" : "Pronto";
  $("#sync-result").innerHTML =
    state.syncHistory
      .map(
        (item) => `
          <article class="sync-item">
            <div>
              <strong>${item.nome || item.entidade}</strong>
              <span>${item.client_generated_id} - ${item.entidade_id || item.message || "Aguardando"}</span>
            </div>
            <span class="sync-badge">${item.status}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum envio nesta sessao.</p>";
}

async function syncCadastro(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const clientId = `web-demo-${Date.now()}`;
  const payload = await api("/mobile/sync", {
    method: "POST",
    body: JSON.stringify({
      items: [
        {
          client_generated_id: clientId,
          entidade: "contato",
          payload: {
            nome: data.nome,
            telefone_principal: data.telefone_principal,
            bairro: data.bairro,
            nivel_relacionamento: "CONTATO",
            engajamento: "MORNO",
            voto_2028: "INDEFINIDO",
            origem_politica: "DECLARADO",
          },
        },
      ],
    }),
  });
  const processed = payload.data.processed.map((item) => ({ ...item, nome: data.nome }));
  const errors = payload.data.errors.map((item) => ({ ...item, nome: data.nome }));
  state.syncHistory = [...processed, ...errors, ...state.syncHistory].slice(0, 6);
  renderSync();
  await loadData();
}

function navigateTo(sectionId) {
  if (!sectionId) return;
  if (sectionId !== "list-view") {
    state.previousSection = sectionId;
  }
  state.currentSection = sectionId;
  $$(".module-nav button").forEach((item) => item.classList.toggle("active", item.dataset.section === sectionId));
  $$(".module").forEach((item) => item.classList.toggle("active", item.id === sectionId));
  const button = $(`.module-nav button[data-section="${sectionId}"]`);
  $(".topbar h1").textContent = button ? button.textContent : $("#list-view-title")?.textContent || "Gabinete Centralizado";
  updateMobileBackButton();
  if (isCompactSidebar()) closeSidebar();
}

function navigateCadastroTab(tabId) {
  $$("[data-cadastro-tab]").forEach((button) => {
    button.classList.toggle("active", button.dataset.cadastroTab === tabId);
  });
  $$(".cadastro-pane").forEach((pane) => {
    pane.classList.toggle("active", pane.id === `cadastro-${tabId}`);
  });
}

function bindNavigation() {
  bindElementEvent("#crm-contact-select", "change", (event) => {
    state.selectedContactId = event.currentTarget.value;
    renderCRM();
    refreshAssistantContext({ contexto_tipo: "contato", contexto_id: state.selectedContactId, modulo: "crm", origem: "seletor" }, { force: true });
  });
  $$("[data-cadastro-tab]").forEach((button) => {
    button.addEventListener("click", () => navigateCadastroTab(button.dataset.cadastroTab));
  });
}

function bindEvents() {
  bindElementEvent("#login-form", "submit", login);
  bindElementEvent("#contact-form", "submit", createContact);
  bindElementEvent("#public-body-form", "submit", createPublicBody);
  bindElementEvent("#interaction-form", "submit", createInteraction);
  bindElementEvent("#demand-form", "submit", createDemand);
  bindElementEvent("#demand-edit-form", "submit", saveDemandEdit);
  bindElementEvent("#user-form", "submit", createUser);
  bindElementEvent("#agenda-form", "submit", createAgenda);
  bindElementEvent("#agenda-report-form", "submit", saveAgendaReport);
  bindElementEvent("#proposition-form", "submit", createProposition);
  bindElementEvent("#amendment-form", "submit", createAmendment);
  bindElementEvent("#office-form", "submit", createOffice);
  bindElementEvent("#sla-config-form", "submit", saveSlaConfiguration);
  bindElementEvent("#sync-form", "submit", syncCadastro);
  bindElementEvent("#logout", "click", onLogout);
  bindElementEvent("#refresh", "click", loadData);
  bindElementEvent("#reports-refresh", "click", loadData);
  bindElementEvent("#ai-refresh-context", "click", () => refreshAssistantContext(state.assistantContext, { force: true }));
  bindElementEvent("#ai-first-demand", "click", summarizeFirstDemand);
  bindElementEvent("#ai-summarize", "click", summarizeFirstDemand);
  bindElementEvent("#ai-suggest", "click", suggestNextStep);
  bindElementEvent("#global-search", "input", (event) => {
    state.globalSearch = event.currentTarget.value;
    renderDemands();
    renderContacts();
    renderSearchResults();
  });
  document.addEventListener("change", (event) => {
    if (event.target.matches("[data-sentiment-filter]")) {
      onSentimentFilterChange(event).catch(console.error);
    }
    if (event.target.matches('#contact-form input[name="foto_file"]')) {
      previewLocalImage(event.target.files?.[0], "#contact-photo-preview", "#contact-photo-link");
    }
    if (event.target.matches('#user-form input[name="foto_file"]')) {
      previewLocalImage(event.target.files?.[0], "#user-photo-preview", "#user-photo-link");
    }
    if (event.target.matches('#demand-form select[name="tipo_demanda"], #demand-form select[name="tipo_vaga_pretendida"]')) {
      syncVacancyFields($("#demand-form"), "create");
    }
    if (event.target.matches('#demand-edit-form select[name="tipo_demanda"], #demand-edit-form select[name="tipo_vaga_pretendida"]')) {
      syncVacancyFields($("#demand-edit-form"), "edit");
    }
  });
  bindElementEvent("#cancel-demand-edit", "click", () => {
    state.editingDemandId = null;
    $("#demand-edit-form")?.reset();
    $("#demand-edit-form")?.classList.add("hidden");
    setMessage("#demand-edit-message", "");
  });
  bindElementEvent("#sidebar-toggle", "click", toggleSidebar);
  bindElementEvent("#sidebar-overlay", "click", closeSidebar);
  bindElementEvent("#mobile-back", "click", goBackFromMobileView);
  bindElementEvent("#brand-home", "click", goToInitialMenu);
  bindElementEvent("#topbar-home", "click", goToInitialMenu);
  document.addEventListener("click", handleGlobalClick);
  document.addEventListener("keydown", handleGlobalKeydown);
  window.addEventListener("resize", () => {
    if (!isCompactSidebar()) closeSidebar();
    updateMobileBackButton();
  });
  bindNavigation();
  resetContactFormState();
  resetUserFormState();
  syncVacancyFields($("#demand-form"), "create");
  syncVacancyFields($("#demand-edit-form"), "edit");
  updateMobileBackButton();
}

bindEvents();

if (state.token) {
  showApp();
  loadData().catch(() => {
    localStorage.removeItem("gabinete_token");
    showLogin();
  });
}
