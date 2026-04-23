const API = "/api/v1";

const state = {
  token: localStorage.getItem("gabinete_mandato_token"),
  user: null,
  overview: null,
  demands: [],
  contacts: [],
  users: [],
  teams: [],
  territories: [],
  interactions: [],
  agenda: [],
  sentiment: null,
  currentView: "executivo",
  selectedDemandId: null,
  executiveDrilldown: null,
  contextList: null,
  territoryDetail: null,
  teamDetail: null,
  geoMapFocusId: null,
  viewHistory: [{ view: "executivo", label: "Painel" }],
  viewLabels: {
    executivo: "Painel",
    operacional: "Operacoes",
    lista: "Lista",
    territorio: "Territorio",
    equipe: "Equipe",
  },
  demandFilters: {
    status: "",
    priority: "",
    responsibleUserId: "",
  },
};

const DESTINATION_MAP = {
  kpi: {
    demandas_abertas: { web: { section: "atendimento", label: "Abrir atendimento no sistema" } },
    contatos: { web: { section: "crm", label: "Abrir relacionamento no sistema" } },
    agenda: { web: { section: "agenda", label: "Abrir agenda no sistema" } },
    relacionamento: { web: { section: "crm", label: "Abrir relacionamento no sistema" } },
  },
  relationship: {
    leaders: { web: { section: "crm", label: "Abrir relacionamento no sistema" } },
    mobilized: { web: { section: "crm", label: "Abrir relacionamento no sistema" } },
    voteCertain: { web: { section: "crm", label: "Abrir relacionamento no sistema" } },
  },
  territory: {
    default: { web: { section: "executivo", label: "Abrir comando central" } },
  },
  team: {
    default: { web: { section: "cadastros", label: "Abrir cadastros no sistema" } },
  },
  citizen: {
    default: { web: { section: "crm", label: "Abrir CRM no sistema" } },
  },
  demand: {
    default: { web: { section: "atendimento", label: "Abrir atendimento no sistema" } },
  },
};

const $ = (selector) => document.querySelector(selector);

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setMessage(selector, text, error = false) {
  const element = $(selector);
  if (!element) return;
  element.textContent = text || "";
  element.classList.toggle("error", error);
}

function formatDateTime(value) {
  if (!value) return "Sem data";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return "Sem data";
  return new Intl.DateTimeFormat("pt-BR", { dateStyle: "short", timeStyle: "short" }).format(parsed);
}

function percentage(value) {
  return `${Math.round(Number(value || 0))}%`;
}

function labelStatus(status) {
  const map = {
    ABERTA: "Nova",
    EM_TRIAGEM: "Triagem",
    EM_ATENDIMENTO: "Em instrucao",
    ENCAMINHADA: "Encaminhada",
    AGUARDANDO_RETORNO: "Aguardando orgao",
    CONCLUIDA: "Concluida",
    REABERTA: "Reaberta",
    ARQUIVADA: "Arquivada",
    CANCELADA: "Cancelada",
    VENCIDO: "Vencido",
    EM_RISCO: "Em risco",
    BAIXA: "Baixa",
    MEDIA: "Media",
    ALTA: "Alta",
    CRITICA: "Critica",
    FORTE: "Forte",
    FRIO: "Frio",
    MORNO: "Morno",
    CONTATO: "Contato",
    LIDERANCA: "Lideranca",
    VOTO_CERTO: "Voto certo",
    INDEFINIDO: "Indefinido",
    ALTO: "Alto",
    BAIXO: "Baixo",
    SAUDAVEL: "Saudavel",
    POSITIVO: "Positivo",
    NEUTRAL: "Estavel",
  };
  return map[String(status || "").toUpperCase()] || String(status || "Sem status");
}

function pillClass(kind) {
  if (["VENCIDO", "ALTA", "CRITICA"].includes(String(kind || "").toUpperCase())) return "danger";
  if (["EM_RISCO", "MEDIA", "MEDIA_PRESSAO", "MEDIA PRESSAO"].includes(String(kind || "").toUpperCase())) return "warning";
  if (["SAUDAVEL", "POSITIVO", "CONCLUIDA", "CONCLUIDO_NO_PRAZO"].includes(String(kind || "").toUpperCase())) return "success";
  return "neutral";
}

function levelLabel(score) {
  if (score >= 80) return "Mandato em alta temperatura";
  if (score >= 60) return "Mandato atento e competitivo";
  if (score >= 40) return "Mandato sob observacao";
  return "Mandato em alerta de mobilizacao";
}

function clampPercent(value) {
  return Math.max(0, Math.min(100, Number(value || 0)));
}

function sentimentPercent(sentiment, tone) {
  const aliases = {
    positive: ["positivos_percentual", "positivo"],
    neutral: ["neutros_percentual", "neutro"],
    negative: ["negativos_percentual", "negativo"],
  };
  for (const key of aliases[tone] || []) {
    if (sentiment?.[key] !== undefined && sentiment?.[key] !== null) {
      return clampPercent(sentiment[key]);
    }
  }
  return 0;
}

function pressureTone(level) {
  const key = String(level || "").toUpperCase();
  if (["ALTA", "VENCIDO", "CRITICA"].includes(key)) return "danger";
  if (["MEDIA", "EM_RISCO"].includes(key)) return "warning";
  if (["BAIXA", "SAUDAVEL", "POSITIVO"].includes(key)) return "success";
  return "neutral";
}

function renderThermometerVisual(score) {
  const root = $("#thermometer-visual");
  if (!root) return;
  const safeScore = clampPercent(score);
  const circumference = 2 * Math.PI * 48;
  const progress = circumference - (safeScore / 100) * circumference;
  root.innerHTML = `
    <svg viewBox="0 0 120 120" class="thermometer-ring" aria-hidden="true">
      <circle cx="60" cy="60" r="48" class="thermometer-track"></circle>
      <circle cx="60" cy="60" r="48" class="thermometer-progress" style="stroke-dasharray:${circumference};stroke-dashoffset:${progress};"></circle>
      <circle cx="60" cy="60" r="34" class="thermometer-core"></circle>
      <text x="60" y="57" text-anchor="middle" class="thermometer-center-value">${Math.round(safeScore)}</text>
      <text x="60" y="74" text-anchor="middle" class="thermometer-center-label">indice</text>
    </svg>
  `;
}

function renderSentimentVisual(sentiment) {
  const root = $("#sentiment-visual");
  if (!root) return;
  const positive = sentimentPercent(sentiment, "positive");
  const neutral = sentimentPercent(sentiment, "neutral");
  const negative = sentimentPercent(sentiment, "negative");
  const rows = [
    ["Positivo", positive, "success"],
    ["Neutro", neutral, "neutral"],
    ["Negativo", negative, "danger"],
  ];
  root.innerHTML = rows
    .map(
      ([label, value, tone]) => `
        <div class="sentiment-bar-row">
          <span>${escapeHtml(label)}</span>
          <div class="sentiment-bar-track"><div class="sentiment-bar-fill ${tone}" style="width:${value}%"></div></div>
          <strong>${Math.round(value)}%</strong>
        </div>
      `,
    )
    .join("");
}

function buildGeoMapNodes(limit = 5) {
  const positions = [
    { left: 18, top: 28 },
    { left: 62, top: 20 },
    { left: 44, top: 52 },
    { left: 76, top: 60 },
    { left: 24, top: 72 },
  ];
  return ((state.overview?.heatmap || []).slice(0, limit) || []).map((item, index) => ({
    ...item,
    position: positions[index] || { left: 50, top: 50 },
  }));
}

function ensureGeoMapFocus() {
  const nodes = buildGeoMapNodes();
  if (state.geoMapFocusId && nodes.some((item) => item.territorio_id === state.geoMapFocusId)) {
    return state.geoMapFocusId;
  }
  state.geoMapFocusId = nodes[0]?.territorio_id || null;
  return state.geoMapFocusId;
}

function renderGeoMap() {
  const root = $("#geo-map-stage");
  if (!root) return;
  const nodes = buildGeoMapNodes();
  const activeId = ensureGeoMapFocus();
  const focused = nodes.find((item) => item.territorio_id === activeId) || null;
  $("#geo-map-summary").textContent = focused
    ? `${focused.territorio_nome} em destaque com ${focused.demandas} demanda(s)`
    : "Sem territorios com leitura pronta";
  $("#geo-map-copy").textContent = focused
    ? `Clique em uma area do mapa para abrir demandas registradas na regional. A camada esta pronta para evoluir para mapa georreferenciado real do cadastro.`
    : "Assim que houver leitura territorial, o app mostrara hotspots clicaveis para demandas e cadastros por area.";
  root.innerHTML = nodes.length
    ? `
        <div class="geo-map-canvas">
          <div class="geo-map-backdrop"></div>
          ${nodes
            .map(
              (item) => `
                <button
                  type="button"
                  class="geo-map-node ${item.territorio_id === activeId ? "active" : ""} ${pressureTone(item.nivel_pressao)}"
                  data-map-territory-id="${escapeHtml(item.territorio_id || "")}" 
                  style="left:${item.position.left}%;top:${item.position.top}%;"
                >
                  <span class="geo-map-node-pulse"></span>
                  <span class="geo-map-node-label">${escapeHtml(item.territorio_nome)}</span>
                </button>
              `,
            )
            .join("")}
          <div class="geo-map-overlay-card">
            <p class="eyebrow">Area em foco</p>
            <strong>${escapeHtml(focused?.territorio_nome || "Sem territorio")}</strong>
            <p>${focused ? `${labelStatus(focused.nivel_pressao || "NEUTRAL")} com ${focused.demandas} demanda(s), ${focused.contatos} cadastro(s) e ${focused.liderancas} lideranca(s).` : "Sem dados territoriais para exibir."}</p>
          </div>
        </div>
      `
    : '<p class="message">Nenhum hotspot territorial disponivel para o mapa.</p>';
  $("#geo-map-open-demands").disabled = !focused;
  $("#geo-map-open-territory").disabled = !focused;
}

function setGeoMapFocus(territoryId, options = {}) {
  if (!territoryId) return;
  state.geoMapFocusId = territoryId;
  renderGeoMap();
  if (options.openDemands) {
    openTerritoryDemandList(territoryId);
  }
}

async function api(path, options = {}) {
  const headers = { ...(options.headers || {}) };
  if (!(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }
  if (state.token) headers.Authorization = `Bearer ${state.token}`;
  const response = await fetch(`${API}${path}`, { ...options, headers });
  if (response.status === 204) return null;
  const payload = await response.json();
  if (!response.ok) throw new Error(payload?.error?.message || "Falha na requisicao.");
  return payload;
}

function showApp() {
  $("#login-view").classList.add("hidden");
  $("#app-view").classList.remove("hidden");
}

function showLogin() {
  $("#app-view").classList.add("hidden");
  $("#login-view").classList.remove("hidden");
}

function renderBreadcrumb() {
  const root = $("#mobile-breadcrumb");
  if (!root) return;
  root.innerHTML = state.viewHistory
    .map(
      (item, index) => `
        <button type="button" class="breadcrumb-item ${index === state.viewHistory.length - 1 ? "active" : ""}" data-breadcrumb-index="${index}">${escapeHtml(item.label || state.viewLabels[item.view] || item.view)}</button>
      `,
    )
    .join('<span class="breadcrumb-separator">/</span>');
}

function setCurrentView(view, options = {}) {
  state.currentView = view;
  if (!options.skipHistory) {
    const label = options.label || state.viewLabels[view] || view;
    if (options.replaceHistory) {
      state.viewHistory[state.viewHistory.length - 1] = { view, label };
    } else {
      const last = state.viewHistory[state.viewHistory.length - 1];
      if (!last || last.view !== view || last.label !== label) {
        state.viewHistory = [...state.viewHistory, { view, label }].slice(-6);
      }
    }
  }
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.classList.toggle("active", button.dataset.view === view);
  });
  document.querySelectorAll(".app-view-panel").forEach((panel) => {
    panel.classList.toggle("active", panel.id === `view-${view}`);
  });
  renderBreadcrumb();
}

function navigateBreadcrumb(index) {
  if (index < 0 || index >= state.viewHistory.length) return;
  const target = state.viewHistory[index];
  state.viewHistory = state.viewHistory.slice(0, index + 1);
  setCurrentView(target.view, { skipHistory: true });
}

function sortByName(items, field = "nome") {
  return [...items].sort((left, right) => String(left?.[field] || "").localeCompare(String(right?.[field] || ""), "pt-BR"));
}

function toIsoValue(value) {
  if (!value) return null;
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return null;
  return parsed.toISOString();
}

function buildAppLink(section, params = {}) {
  const query = new URLSearchParams({ section, ...params });
  return `/app/?${query.toString()}`;
}

function destinationSpec(type, key, params = {}) {
  const entry = DESTINATION_MAP[type]?.[key] || DESTINATION_MAP[type]?.default;
  if (!entry?.web) {
    return { label: "Abrir sistema principal", href: buildAppLink("executivo", params) };
  }
  return {
    label: entry.web.label,
    href: buildAppLink(entry.web.section, { focus: key, ...params }),
  };
}

function renderDetailEntries(items) {
  return items
    .map(
      (item) => `
        <article class="stack-card ${item.entityType && item.entityId ? "actionable" : ""}" ${item.entityType && item.entityId ? `data-context-open-type="${escapeHtml(item.entityType)}" data-context-open-id="${escapeHtml(item.entityId)}" tabindex="0" role="button"` : ""}>
          <header>
            <div>
              <small>${escapeHtml(item.eyebrow || "Contexto")}</small>
              <strong>${escapeHtml(item.title || "Sem titulo")}</strong>
            </div>
          </header>
          <p>${escapeHtml(item.body || "Sem detalhamento adicional.")}</p>
          ${item.tags?.length ? `<div class="stack-meta">${item.tags.map((tag) => `<div class="meta-tag">${escapeHtml(tag)}</div>`).join("")}</div>` : ""}
        </article>
      `,
    )
    .join("");
}

function renderContextList() {
  const detail = state.contextList;
  $("#context-list-eyebrow").textContent = detail?.eyebrow || "Leitura filtrada";
  $("#context-list-title").textContent = detail?.title || "Lista contextual";
  $("#context-list-summary").textContent = detail?.summary || "Abra um indicador do painel para ver a lista correspondente.";
  $("#context-list-meta").innerHTML = (detail?.meta || []).map((item) => `<div class="meta-tag">${escapeHtml(item)}</div>`).join("");
  $("#context-list-content").innerHTML = detail?.items?.length ? renderDetailEntries(detail.items) : `<p class="message">${escapeHtml(detail?.emptyMessage || "Nenhum registro encontrado para este contexto.")}</p>`;
  const button = $("#context-list-primary-action");
  button.textContent = detail?.primaryAction?.label || "Abrir contexto";
  button.disabled = !detail?.primaryAction;
  const link = $("#context-list-web-link");
  link.href = detail?.webLink?.href || "/app/";
  link.textContent = detail?.webLink?.label || "Abrir sistema principal";
}

function setContextList(detail) {
  state.contextList = detail;
  renderContextList();
}

function openContextList(detail) {
  setContextList(detail);
  setCurrentView("lista", { label: detail.title || "Lista" });
}

function territoryRecord(territoryId) {
  return (state.overview?.heatmap || []).find((item) => item.territorio_id === territoryId) || state.territories.find((item) => item.id === territoryId) || null;
}

function territoryNameFromId(territoryId) {
  const territory = territoryRecord(territoryId);
  return territory?.territorio_nome || territory?.nome || "Sem territorio";
}

function territoryScopedContacts(territoryId) {
  const territoryName = territoryNameFromId(territoryId);
  return state.contacts.filter((item) => item.territorio_id === territoryId || item.territorio_nome === territoryName || item.bairro === territoryName);
}

function territoryScopedDemands(territoryId) {
  const territoryName = territoryNameFromId(territoryId);
  return state.demands.filter((item) => item.territorio_id === territoryId || item.territorio_nome === territoryName);
}

function teamMembers(teamId, fallbackUserId = "") {
  const members = state.users.filter((item) => item.equipe_id === teamId && item.ativo !== false);
  if (members.length || !fallbackUserId) return members;
  const user = state.users.find((item) => item.id === fallbackUserId);
  return user ? [user] : [];
}

function teamScopedContacts(teamId, fallbackUserId = "") {
  const memberIds = new Set(teamMembers(teamId, fallbackUserId).map((item) => item.id));
  return state.contacts.filter((item) => item.equipe_id === teamId || memberIds.has(item.cadastrado_por_usuario_id));
}

function teamScopedDemands(teamId, fallbackUserId = "") {
  const memberIds = new Set(teamMembers(teamId, fallbackUserId).map((item) => item.id));
  return state.demands.filter((item) => item.equipe_id === teamId || memberIds.has(item.gerada_por_usuario_id) || memberIds.has(item.responsavel_usuario_id));
}

function openDemandListInMandato({ title, eyebrow, summary, chip, meta = [], webLink, filter }) {
  const items = state.demands
    .filter((item) => !["CONCLUIDA", "ARQUIVADA", "CANCELADA", "EXCLUIDO"].includes(item.status))
    .filter(filter)
    .sort((left, right) => String(right.updated_at || right.created_at || right.data_abertura || "").localeCompare(String(left.updated_at || left.created_at || left.data_abertura || "")))
    .map((item) => ({
      entityType: "demand",
      entityId: item.id,
      eyebrow: item.territorio_nome || "Sem territorio",
      title: item.titulo,
      body: `${item.cidadao_nome || "Sem demandante"} · ${labelStatus(item.status)} · ${item.responsavel_nome || "Sem responsavel"}`,
      tags: [labelStatus(item.prioridade), labelStatus(item.sla_status || item.status)],
    }));
  openContextList({
    title,
    eyebrow,
    summary,
    chip,
    meta: [...meta, `${items.length} item(ns)`],
    items,
    emptyMessage: "Nenhuma demanda encontrada para este recorte.",
    primaryAction: { label: "Abrir operacoes do mandato", run: () => openOperationalView() },
    webLink,
  });
}

function openContactListInMandato({ title, eyebrow, summary, chip, meta = [], webLink, filter }) {
  const items = state.contacts
    .filter((item) => item.status !== "EXCLUIDO" && item.tipo_contato !== "COLABORADOR")
    .filter(filter)
    .sort((left, right) => String(left.nome || "").localeCompare(String(right.nome || ""), "pt-BR"))
    .map((item) => ({
      entityType: "contact",
      entityId: item.id,
      eyebrow: item.territorio_nome || item.bairro || "Sem territorio",
      title: item.nome,
      body: `${item.telefone_principal || "Sem telefone"} · ${labelStatus(item.engajamento || "FRIO")}`,
      tags: [labelStatus(item.nivel_relacionamento || "CONTATO"), labelStatus(item.voto_2028 || "INDEFINIDO")],
    }));
  openContextList({
    title,
    eyebrow,
    summary,
    chip,
    meta: [...meta, `${items.length} nome(s)`],
    items,
    emptyMessage: "Nenhum cadastro encontrado para este recorte.",
    primaryAction: { label: "Voltar ao painel executivo", run: () => setCurrentView("executivo") },
    webLink,
  });
}

function openAgendaListInMandato({ title, eyebrow, summary, chip, meta = [], webLink, filter }) {
  const items = state.agenda
    .filter(filter)
    .sort((left, right) => String(left.data_inicio || "").localeCompare(String(right.data_inicio || "")))
    .map((item) => ({
      entityType: "agenda",
      entityId: item.id,
      eyebrow: item.tipo_agenda || "Agenda",
      title: item.titulo,
      body: `${formatDateTime(item.data_inicio)} · ${item.local_texto || item.territorio_nome || "Local a definir"}`,
      tags: [item.eh_agenda_vereador ? "Vereador" : "Equipe", labelStatus(item.status || "PLANEJADO")],
    }));
  openContextList({
    title,
    eyebrow,
    summary,
    chip,
    meta: [...meta, `${items.length} compromisso(s)`],
    items,
    emptyMessage: "Nenhum compromisso encontrado para este recorte.",
    primaryAction: { label: "Abrir operacoes do mandato", run: () => openOperationalView() },
    webLink,
  });
}

function openTerritoryDemandList(territoryId) {
  if (!territoryId) return;
  const territoryName = territoryNameFromId(territoryId);
  openDemandListInMandato({
    title: `Demandas em ${territoryName}`,
    eyebrow: "Territorio",
    summary: "Fila filtrada das demandas registradas na regional selecionada.",
    chip: territoryName,
    meta: ["Pressao territorial"],
    webLink: destinationSpec("territory", "territorio", { territorio_id: territoryId }),
    filter: (item) => territoryScopedDemands(territoryId).some((entry) => entry.id === item.id),
  });
}

function renderTerritoryDetailView() {
  const detail = state.territoryDetail;
  $("#territory-detail-title").textContent = detail?.title || "Sem territorio selecionado";
  $("#territory-detail-summary").textContent = detail?.summary || "Abra uma regional ou bairro no painel para ver a composicao territorial.";
  $("#territory-detail-meta").innerHTML = (detail?.meta || []).map((item) => `<div class="meta-tag">${escapeHtml(item)}</div>`).join("");
  $("#territory-demand-list").innerHTML = detail?.demands?.length ? renderDetailEntries(detail.demands) : '<p class="message">Nenhuma demanda relevante neste territorio.</p>';
  $("#territory-contact-list").innerHTML = detail?.contacts?.length ? renderDetailEntries(detail.contacts) : '<p class="message">Nenhum cadastro relevante neste territorio.</p>';
  $("#territory-web-link").href = detail?.webLink?.href || "/app/";
  $("#territory-web-link").textContent = detail?.webLink?.label || "Abrir no sistema principal";
}

function renderTeamDetailView() {
  const detail = state.teamDetail;
  $("#team-detail-title").textContent = detail?.title || "Sem equipe selecionada";
  $("#team-detail-summary").textContent = detail?.summary || "Abra uma equipe no painel para ver cobertura territorial e produtividade detalhada.";
  $("#team-detail-meta").innerHTML = (detail?.meta || []).map((item) => `<div class="meta-tag">${escapeHtml(item)}</div>`).join("");
  $("#team-member-list").innerHTML = detail?.members?.length ? renderDetailEntries(detail.members) : '<p class="message">Nenhum membro ativo localizado.</p>';
  $("#team-output-list").innerHTML = detail?.output?.length ? renderDetailEntries(detail.output) : '<p class="message">Nenhuma entrega relevante encontrada.</p>';
  $("#team-web-link").href = detail?.webLink?.href || "/app/";
  $("#team-web-link").textContent = detail?.webLink?.label || "Abrir no sistema principal";
}

function openTerritoryDetail(territoryId) {
  const territory = territoryRecord(territoryId);
  if (!territory) return;
  const demands = territoryScopedDemands(territoryId).slice(0, 5);
  const contacts = territoryScopedContacts(territoryId).slice(0, 5);
  state.territoryDetail = {
    territoryId,
    title: territory.territorio_nome || territory.nome || "Territorio",
    summary: "Leitura dedicada do territorio com fila local, base ativa, liderancas e sinais de pressao para orientar a presenca do vereador.",
    meta: [
      `${territory.demandas || demands.length} demandas`,
      `${territory.contatos || contacts.length} cadastros`,
      `${territory.liderancas || 0} liderancas`,
      labelStatus(territory.nivel_pressao || "NEUTRAL"),
    ],
    demands: demands.map((item) => ({
      entityType: "demand",
      entityId: item.id,
      eyebrow: item.cidadao_nome || "Demandante",
      title: item.titulo,
      body: `${labelStatus(item.status)} · ${item.responsavel_nome || "Sem responsavel"}`,
      tags: [labelStatus(item.prioridade), labelStatus(item.sla_status || item.status)],
    })),
    contacts: contacts.map((item) => ({
      entityType: "contact",
      entityId: item.id,
      eyebrow: labelStatus(item.nivel_relacionamento || "CONTATO"),
      title: item.nome,
      body: `${item.telefone_principal || "Sem telefone"} · ${labelStatus(item.engajamento || "FRIO")}`,
      tags: [labelStatus(item.voto_2028 || "INDEFINIDO")],
    })),
    webLink: destinationSpec("territory", "territorio", { territorio_id: territoryId }),
  };
  renderTerritoryDetailView();
  setCurrentView("territorio", { label: state.territoryDetail.title || "Territorio" });
}

function openTeamDetail(teamId, fallbackUserId = "") {
  const team = state.teams.find((entry) => entry.id === teamId);
  const members = teamMembers(teamId, fallbackUserId).slice(0, 5);
  const contacts = teamScopedContacts(teamId, fallbackUserId);
  const demands = teamScopedDemands(teamId, fallbackUserId);
  state.teamDetail = {
    teamId,
    fallbackUserId,
    title: team?.nome || members[0]?.nome || "Equipe operacional",
    summary: "Leitura dedicada da equipe com membros ativos, producao de campo, qualidade cadastral e sinais de gargalo operacional.",
    meta: [
      `${members.length} membro(s) exibidos`,
      `${contacts.length} cadastros`,
      `${demands.length} demandas`,
      team?.produtividade ? `${Math.round(team.produtividade.completude_media || 0)}% de completude` : "Leitura individual",
    ],
    members: members.map((item) => ({
      eyebrow: item.perfil || "COLABORADOR",
      title: item.nome,
      body: `${item.email_login || "Sem e-mail"} · ${item.telefone || "Sem telefone"}`,
      tags: [item.equipe_id ? "Equipe vinculada" : "Sem equipe"],
    })),
    output: [
      {
        eyebrow: team?.supervisor_nome || "Supervisao",
        title: (team?.produtividade?.territorios_nomes || []).join(" · ") || "Sem territorio vinculado",
        body: `${contacts.length} cadastros e ${demands.length} demandas vinculadas a esta frente de campo.`,
        tags: [
          team?.produtividade ? `Engaj. ${Math.round(team.produtividade.engajamento_medio || 0)}` : "Sem media consolidada",
          team?.produtividade ? `${team.produtividade.demandas_abertas || 0} abertas` : `${demands.filter((item) => !["CONCLUIDA", "ARQUIVADA", "CANCELADA"].includes(item.status)).length} abertas`,
        ],
      },
      ...demands.slice(0, 3).map((item) => ({
        entityType: "demand",
        entityId: item.id,
        eyebrow: item.territorio_nome || "Sem territorio",
        title: item.titulo,
        body: `${item.cidadao_nome || "Sem demandante"} · ${labelStatus(item.status)}`,
        tags: [labelStatus(item.prioridade)],
      })),
    ],
    webLink: destinationSpec("team", "equipe", { equipe_id: teamId, usuario_id: fallbackUserId || undefined }),
  };
  renderTeamDetailView();
  setCurrentView("equipe", { label: state.teamDetail.title || "Equipe" });
}

function renderExecutiveDrilldown() {
  const panel = $("#executive-detail");
  const detail = state.executiveDrilldown;
  if (!panel || !detail) {
    panel?.classList.add("hidden");
    return;
  }
  panel.classList.remove("hidden");
  $("#detail-title").textContent = detail.title;
  $("#detail-chip").textContent = detail.chip || "Leitura pronta";
  $("#detail-summary").textContent = detail.summary;
  $("#detail-meta").innerHTML = (detail.meta || []).map((item) => `<div class="meta-tag">${escapeHtml(item)}</div>`).join("");
  $("#detail-list").innerHTML = detail.items?.length ? renderDetailEntries(detail.items) : '<p class="message">Sem itens detalhados para esta leitura.</p>';
  const primaryButton = $("#detail-primary-action");
  primaryButton.textContent = detail.primaryAction?.label || "Abrir contexto";
  primaryButton.disabled = !detail.primaryAction;
  const webLink = $("#detail-web-link");
  webLink.href = detail.webLink?.href || "/app/";
  webLink.textContent = detail.webLink?.label || "Abrir sistema principal";
}

function setExecutiveDrilldown(detail) {
  state.executiveDrilldown = detail;
  renderExecutiveDrilldown();
}

function focusDemandInOperations(demandId) {
  state.selectedDemandId = demandId;
  state.currentView = "operacional";
  setCurrentView("operacional", { label: "Operacoes" });
  renderRecentOperations();
  $("#demand-edit-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openOperationalView() {
  state.currentView = "operacional";
  setCurrentView("operacional", { label: "Operacoes" });
  $("#recent-demand-list")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openContactRecord(contactId) {
  const detail = buildCitizenDrilldown(contactId);
  if (!detail) return;
  setExecutiveDrilldown(detail);
  setCurrentView("executivo", { label: detail.title || "Painel" });
  $("#executive-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function openAgendaRecord(agendaId) {
  const item = state.agenda.find((entry) => entry.id === agendaId);
  if (!item) return;
  openContextList({
    title: item.titulo || "Compromisso",
    eyebrow: item.tipo_agenda || "Agenda",
    summary: "Leitura detalhada do compromisso selecionado a partir da lista filtrada do app do vereador.",
    chip: labelStatus(item.status || "PLANEJADO"),
    meta: [formatDateTime(item.data_inicio), item.local_texto || item.territorio_nome || "Local a definir"],
    items: [
      {
        eyebrow: item.eh_agenda_vereador ? "Vereador" : "Equipe",
        title: item.titulo,
        body: item.descricao || "Sem descricao adicional para este compromisso.",
        tags: [item.tipo_agenda || "Agenda", labelStatus(item.status || "PLANEJADO")],
      },
    ],
    primaryAction: { label: "Abrir operacoes do mandato", run: () => openOperationalView() },
    webLink: destinationSpec("kpi", "agenda", { agenda_id: agendaId }),
  });
}

function openContextEntity(type, id) {
  if (type === "demand") {
    focusDemandInOperations(id);
    return;
  }
  if (type === "contact") {
    openContactRecord(id);
    return;
  }
  if (type === "agenda") {
    openAgendaRecord(id);
  }
}

function topOpenDemands(limit = 5) {
  return [...state.demands]
    .filter((item) => !["CONCLUIDA", "ARQUIVADA", "CANCELADA", "EXCLUIDO"].includes(item.status))
    .sort((left, right) => String(right.updated_at || right.created_at || right.data_abertura || "").localeCompare(String(left.updated_at || left.created_at || left.data_abertura || "")))
    .slice(0, limit);
}

function buildKpiDrilldown(key) {
  const cards = state.overview?.cards || {};
  if (key === "demandas_abertas") {
    const openDemands = topOpenDemands();
    return {
      title: "Demandas abertas",
      chip: `${cards.demandas_abertas || 0} em curso`,
      summary: `O vereador abriu este indicador para entender a fila viva do mandato e priorizar cobranca, retorno e presencia territorial.`,
      meta: [`${cards.sla_em_risco || 0} em risco`, `${cards.sla_vencido || 0} vencidas`, `${openDemands.length} exibidas agora`],
      items: openDemands.map((item) => ({
        eyebrow: item.territorio_nome || "Sem territorio",
        title: item.titulo,
        body: `${item.cidadao_nome || "Sem demandante"} · ${labelStatus(item.status)} · ${item.responsavel_nome || "Sem responsavel"}`,
        tags: [labelStatus(item.prioridade), labelStatus(item.sla_status || "NEUTRAL")],
      })),
      primaryAction: {
        label: "Abrir lista filtrada",
        run: () =>
          openDemandListInMandato({
            title: "Demandas abertas",
            eyebrow: "Fila operacional",
            summary: "Lista filtrada das demandas que ainda exigem tratamento, devolutiva ou encaminhamento.",
            chip: `${cards.demandas_abertas || 0} em curso`,
            meta: [`${cards.sla_em_risco || 0} em risco`, `${cards.sla_vencido || 0} vencidas`],
            webLink: destinationSpec("kpi", key),
            filter: (item) => !["CONCLUIDA", "ARQUIVADA", "CANCELADA", "EXCLUIDO"].includes(item.status),
          }),
      },
      webLink: destinationSpec("kpi", key),
    };
  }
  if (key === "contatos") {
    const leaders = state.contacts.filter((item) => item.nivel_relacionamento === "LIDERANCA" || item.influencia === "ALTA").slice(0, 5);
    return {
      title: "Base cidada",
      chip: `${cards.contatos || 0} registros`,
      summary: `Este numero pede leitura da base que sustenta o mandato: quantidade, distribuicao territorial e liderancas mobilizaveis.`,
      meta: [`${cards.liderancas || 0} liderancas`, `${leaders.length} destaques`],
      items: leaders.map((item) => ({
        eyebrow: item.territorio_nome || item.bairro || "Sem territorio",
        title: item.nome,
        body: `${item.telefone_principal || "Sem telefone"} · ${labelStatus(item.engajamento || "FRIO")}`,
        tags: [labelStatus(item.nivel_relacionamento || "CONTATO"), labelStatus(item.voto_2028 || "INDEFINIDO")],
      })),
      primaryAction: {
        label: "Abrir lista filtrada",
        run: () =>
          openContactListInMandato({
            title: "Base cidada priorizada",
            eyebrow: "Relacionamento",
            summary: "Lista filtrada dos cadastros com maior potencial politico ou relevancia territorial.",
            chip: `${cards.contatos || 0} registros`,
            meta: [`${cards.liderancas || 0} liderancas`],
            webLink: destinationSpec("kpi", key),
            filter: (item) => item.status !== "EXCLUIDO",
          }),
      },
      webLink: destinationSpec("kpi", key),
    };
  }
  if (key === "agenda") {
    const agenda = [...state.agenda].sort((left, right) => String(left.data_inicio || "").localeCompare(String(right.data_inicio || ""))).slice(0, 5);
    return {
      title: "Agenda do mandato",
      chip: `${cards.agenda_pendente || agenda.length} compromissos`,
      summary: `Ao abrir este indicador, o vereador quer localizar compromissos proximos e decidir onde precisa estar pessoalmente.`,
      meta: [`${cards.agenda_pendente || 0} pendentes`, `${agenda.length} exibidos agora`],
      items: agenda.map((item) => ({
        eyebrow: item.tipo_agenda || "Agenda",
        title: item.titulo,
        body: `${formatDateTime(item.data_inicio)} · ${item.local_texto || item.territorio_nome || "Local a definir"}`,
        tags: [item.eh_agenda_vereador ? "Vereador" : "Equipe", labelStatus(item.status || "PLANEJADO")],
      })),
      primaryAction: {
        label: "Abrir lista filtrada",
        run: () =>
          openAgendaListInMandato({
            title: "Agenda do mandato",
            eyebrow: "Compromissos",
            summary: "Lista filtrada dos compromissos do vereador e da equipe, com foco no que ainda precisa de presenca e confirmacao.",
            chip: `${cards.agenda_pendente || agenda.length} compromissos`,
            meta: [`${state.agenda.filter((item) => item.eh_agenda_vereador).length} do vereador`],
            webLink: destinationSpec("kpi", key),
            filter: (item) => !["REALIZADO", "CANCELADO"].includes(item.status),
          }),
      },
      webLink: destinationSpec("kpi", key),
    };
  }
  const mobilized = state.contacts.filter((item) => ["FORTE", "ALTO"].includes(item.engajamento)).slice(0, 5);
  return {
    title: "Relacionamento mobilizado",
    chip: `${cards.engajamento_forte || mobilized.length} fortes`,
    summary: `Esse recorte mostra quem esta pronto para ativacao, mobilizacao e recorrencia politica.`,
    meta: [`${cards.liderancas || 0} liderancas`, `${mobilized.length} contatos com alta resposta`],
    items: mobilized.map((item) => ({
      eyebrow: item.territorio_nome || item.bairro || "Sem territorio",
      title: item.nome,
      body: `${labelStatus(item.engajamento || "FRIO")} · ${labelStatus(item.voto_2028 || "INDEFINIDO")}`,
      tags: [labelStatus(item.nivel_relacionamento || "CONTATO"), item.telefone_principal || "Sem telefone"],
    })),
    primaryAction: {
      label: "Abrir lista filtrada",
      run: () =>
        openContactListInMandato({
          title: "Base mobilizada",
          eyebrow: "Relacionamento",
          summary: "Lista filtrada dos contatos com maior propensao de resposta, ativacao e recorrencia politica.",
          chip: `${cards.engajamento_forte || mobilized.length} fortes`,
          meta: [`${cards.liderancas || 0} liderancas`],
          webLink: destinationSpec("kpi", key),
          filter: (item) => ["FORTE", "ALTO"].includes(item.engajamento),
        }),
    },
    webLink: destinationSpec("kpi", key),
  };
}

function buildTerritoryDrilldown(territoryId) {
  const territory = (state.overview?.heatmap || []).find((item) => item.territorio_id === territoryId) || state.territories.find((item) => item.id === territoryId);
  if (!territory) return null;
  const scopedContacts = state.contacts.filter((item) => item.territorio_id === territoryId || item.territorio_nome === territory.territorio_nome || item.bairro === territory.territorio_nome).slice(0, 5);
  const scopedDemands = state.demands.filter((item) => item.territorio_id === territoryId || item.territorio_nome === territory.territorio_nome).slice(0, 5);
  return {
    title: territory.territorio_nome || territory.nome || "Territorio",
    chip: labelStatus(territory.nivel_pressao || "NEUTRAL"),
    summary: `O toque no territorio indica busca por composicao local: demandas, base, liderancas e pressao politica territorial.`,
    meta: [`${territory.demandas || scopedDemands.length} demandas`, `${territory.contatos || scopedContacts.length} cadastros`, `${territory.liderancas || 0} liderancas`],
    items: [
      ...scopedDemands.map((item) => ({
        eyebrow: "Demanda",
        title: item.titulo,
        body: `${item.cidadao_nome || "Sem demandante"} · ${labelStatus(item.status)}`,
        tags: [labelStatus(item.prioridade), item.responsavel_nome || "Sem responsavel"],
      })),
      ...scopedContacts.slice(0, Math.max(0, 5 - scopedDemands.length)).map((item) => ({
        eyebrow: "Cadastro",
        title: item.nome,
        body: `${item.telefone_principal || "Sem telefone"} · ${labelStatus(item.engajamento || "FRIO")}`,
        tags: [labelStatus(item.nivel_relacionamento || "CONTATO")],
      })),
    ],
    primaryAction: { label: "Abrir demandas da regional", run: () => openTerritoryDemandList(territoryId) },
    webLink: destinationSpec("territory", "territorio", { territorio_id: territoryId }),
  };
}

function buildDemandDrilldown(demandId) {
  const item = state.demands.find((entry) => entry.id === demandId);
  if (!item) return null;
  return {
    title: item.titulo,
    chip: labelStatus(item.sla_status || item.prioridade),
    summary: `Esta demanda ganhou foco porque exige leitura detalhada e possivelmente uma acao imediata do mandato.`,
    meta: [labelStatus(item.status), item.territorio_nome || "Sem territorio", item.responsavel_nome || "Sem responsavel"],
    items: [
      {
        eyebrow: item.cidadao_nome || "Demandante",
        title: item.descricao || "Sem descricao detalhada",
        body: `${item.cidadao_telefone || "Sem telefone"} · ${Number(item.sla_horas_restantes || 0)}h restantes de SLA`,
        tags: [labelStatus(item.prioridade), labelStatus(item.status)],
      },
    ],
    primaryAction: { label: "Editar demanda no mobile", run: () => focusDemandInOperations(demandId) },
    webLink: destinationSpec("demand", "demanda", { demanda_id: demandId }),
  };
}

function buildRelationshipDrilldown(key) {
  const activeContacts = state.contacts.filter((item) => item.status !== "EXCLUIDO");
  const map = {
    leaders: {
      title: "Liderancas territoriais",
      chip: `${activeContacts.filter((item) => item.nivel_relacionamento === "LIDERANCA" || item.influencia === "ALTA").length} liderancas`,
      contacts: activeContacts.filter((item) => item.nivel_relacionamento === "LIDERANCA" || item.influencia === "ALTA"),
    },
    mobilized: {
      title: "Base mobilizada",
      chip: `${activeContacts.filter((item) => ["FORTE", "ALTO"].includes(item.engajamento)).length} mobilizados`,
      contacts: activeContacts.filter((item) => ["FORTE", "ALTO"].includes(item.engajamento)),
    },
    voteCertain: {
      title: "Voto certo",
      chip: `${activeContacts.filter((item) => item.voto_2028 === "VOTO_CERTO").length} certos`,
      contacts: activeContacts.filter((item) => item.voto_2028 === "VOTO_CERTO"),
    },
  };
  const entry = map[key];
  if (!entry) return null;
  return {
    title: entry.title,
    chip: entry.chip,
    summary: `Ao tocar neste bloco, o vereador quer saber quem compoe esse recorte e onde estao as pessoas mais relevantes para a estrategia.`,
    meta: [`${entry.contacts.length} nomes localizados`],
    items: entry.contacts.slice(0, 5).map((item) => ({
      eyebrow: item.territorio_nome || item.bairro || "Sem territorio",
      title: item.nome,
      body: `${item.telefone_principal || "Sem telefone"} · ${labelStatus(item.engajamento || "FRIO")}`,
      tags: [labelStatus(item.nivel_relacionamento || "CONTATO"), labelStatus(item.voto_2028 || "INDEFINIDO")],
    })),
    primaryAction: {
      label: "Abrir lista filtrada",
      run: () =>
        openContactListInMandato({
          title: entry.title,
          eyebrow: "Relacionamento",
          summary: "Lista filtrada derivada do dashboard, pronta para leitura politica mais profunda dentro do proprio app do vereador.",
          chip: entry.chip,
          meta: [`${entry.contacts.length} nomes localizados`],
          webLink: destinationSpec("relationship", key),
          filter: (item) => entry.contacts.some((contact) => contact.id === item.id),
        }),
    },
    webLink: destinationSpec("relationship", key),
  };
}

function buildCitizenDrilldown(contactId) {
  const item = state.contacts.find((entry) => entry.id === contactId);
  if (!item) return null;
  const relatedDemands = state.demands.filter((entry) => entry.cidadao_id === contactId).slice(0, 3);
  return {
    title: item.nome,
    chip: labelStatus(item.engajamento || item.influencia || "NEUTRAL"),
    summary: `Este contato entrou no radar executivo por potencial politico, capacidade de influencia ou necessidade de acompanhamento dedicado.`,
    meta: [item.territorio_nome || item.bairro || "Sem territorio", labelStatus(item.voto_2028 || "INDEFINIDO")],
    items: [
      {
        eyebrow: "Perfil",
        title: item.telefone_principal || "Sem telefone principal",
        body: `${labelStatus(item.nivel_relacionamento || "CONTATO")} · ${labelStatus(item.engajamento || "FRIO")}`,
        tags: [labelStatus(item.influencia || "BAIXA")],
      },
      ...relatedDemands.map((demand) => ({
        eyebrow: "Demanda vinculada",
        title: demand.titulo,
        body: `${labelStatus(demand.status)} · ${demand.responsavel_nome || "Sem responsavel"}`,
        tags: [labelStatus(demand.prioridade)],
      })),
    ],
    primaryAction: {
      label: "Abrir demandas do cidadao",
      run: () =>
        openDemandListInMandato({
          title: `Demandas de ${item.nome}`,
          eyebrow: "Atendimento",
          summary: "Lista filtrada das demandas vinculadas a este cadastro priorizado.",
          chip: `${relatedDemands.length} demanda(s)`,
          meta: [item.territorio_nome || item.bairro || "Sem territorio"],
          webLink: destinationSpec("citizen", "contato", { contato_id: contactId }),
          filter: (entry) => entry.cidadao_id === contactId,
        }),
    },
    webLink: destinationSpec("citizen", "contato", { contato_id: contactId }),
  };
}

function buildTeamDrilldown(teamId, fallbackUserId = "") {
  const team = state.teams.find((entry) => entry.id === teamId);
  if (team?.produtividade) {
    return {
      title: team.nome || "Equipe",
      chip: `${team.produtividade.cadastros || 0} cadastros`,
      summary: `O vereador abriu esta equipe para enxergar produtividade, cobertura territorial e qualidade de cadastramento em campo.`,
      meta: [
        `${team.produtividade.membros_ativos || 0} membro(s)`,
        `${team.produtividade.demandas || 0} demandas`,
        `${Math.round(team.produtividade.completude_media || 0)}% de completude`,
      ],
      items: [
        {
          eyebrow: team.supervisor_nome || "Supervisao",
          title: (team.produtividade.territorios_nomes || []).join(" · ") || "Sem territorio vinculado",
          body: `${team.produtividade.cadastros_qualificados || 0} cadastros qualificados e ${team.produtividade.engajamento_forte || 0} contato(s) fortes.`,
          tags: [`Engaj. ${Math.round(team.produtividade.engajamento_medio || 0)}`, `${team.produtividade.demandas_abertas || 0} abertas`],
        },
      ],
      primaryAction: { label: "Abrir tela da equipe", run: () => openTeamDetail(teamId) },
      webLink: destinationSpec("team", "equipe", { equipe_id: teamId }),
    };
  }
  const user = state.users.find((entry) => entry.id === fallbackUserId);
  if (!user) return null;
  const ownedDemands = state.demands.filter((item) => item.responsavel_usuario_id === user.id).slice(0, 3);
  return {
    title: user.nome,
    chip: user.perfil || "COLABORADOR",
    summary: `Ainda sem metricas consolidadas de equipe para este caso. A leitura abaixo usa a operacao individual do colaborador.`,
    meta: [user.email_login || "Sem e-mail"],
    items: ownedDemands.map((item) => ({
      eyebrow: item.territorio_nome || "Sem territorio",
      title: item.titulo,
      body: `${labelStatus(item.status)} · ${labelStatus(item.prioridade)}`,
      tags: [labelStatus(item.sla_status || "NEUTRAL")],
    })),
    primaryAction: { label: "Abrir tela da equipe", run: () => openTeamDetail(teamId, fallbackUserId) },
    webLink: destinationSpec("team", "equipe", { equipe_id: teamId, usuario_id: user.id }),
  };
}

function buildExecutiveDrilldown(type, key, extra = {}) {
  if (type === "kpi") return buildKpiDrilldown(key);
  if (type === "territory") return buildTerritoryDrilldown(key);
  if (type === "demand") return buildDemandDrilldown(key);
  if (type === "relationship") return buildRelationshipDrilldown(key);
  if (type === "citizen") return buildCitizenDrilldown(key);
  if (type === "team") return buildTeamDrilldown(key, extra.userId);
  return null;
}

function openExecutiveDrilldown(type, key, extra = {}) {
  if (type === "territory") {
    openTerritoryDemandList(key);
    return;
  }
  const detail = buildExecutiveDrilldown(type, key, extra);
  if (!detail) return;
  setExecutiveDrilldown(detail);
  $("#executive-detail")?.scrollIntoView({ behavior: "smooth", block: "start" });
}

function currentSelectedDemand() {
  const selected = filteredDemands().find((item) => item.id === state.selectedDemandId);
  if (selected) return selected;
  const filtered = filteredDemands();
  return [...filtered].find((item) => !["ARQUIVADA", "CANCELADA", "EXCLUIDO"].includes(item.status)) || filtered[0] || null;
}

function selectDemand(demandId) {
  state.selectedDemandId = demandId;
  renderRecentOperations();
}

function filteredDemands() {
  return [...state.demands].filter((item) => {
    if (state.demandFilters.status && item.status !== state.demandFilters.status) return false;
    if (state.demandFilters.priority && item.prioridade !== state.demandFilters.priority) return false;
    if (state.demandFilters.responsibleUserId && (item.responsavel_usuario_id || "") !== state.demandFilters.responsibleUserId) return false;
    return true;
  });
}

function clearDemandFilters() {
  state.demandFilters.status = "";
  state.demandFilters.priority = "";
  state.demandFilters.responsibleUserId = "";
  state.selectedDemandId = null;
  renderOperationalOptions();
  renderRecentOperations();
}

function computeMandateScore() {
  const cards = state.overview?.cards || {};
  const baseContacts = Number(cards.contatos || 0);
  const leaders = Number(cards.liderancas || 0);
  const openDemands = Number(cards.demandas_abertas || 0);
  const atRisk = Number(cards.sla_em_risco || 0);
  const overdue = Number(cards.sla_vencido || 0);
  const positive = sentimentPercent(state.sentiment, "positive");
  const engagement = baseContacts ? Math.min(100, Math.round((leaders / Math.max(baseContacts, 1)) * 240)) : 0;
  const delivery = openDemands ? Math.max(0, 100 - Math.round(((atRisk + overdue * 2) / openDemands) * 100)) : 85;
  return Math.max(0, Math.min(100, Math.round(positive * 0.4 + engagement * 0.3 + delivery * 0.3)));
}

function renderHero() {
  const score = computeMandateScore();
  const topTerritory = (state.overview?.heatmap || [])[0];
  const sentiment = state.sentiment || {};
  const pressure = topTerritory?.nivel_pressao || "Sem leitura";
  $("#user-chip").textContent = state.user ? `${state.user.nome} - ${state.user.perfil}` : "Sem sessao";
  $("#hero-summary").textContent = topTerritory
    ? `${topTerritory.territorio_nome} lidera a pressao territorial com ${topTerritory.demandas} demanda(s), ${topTerritory.contatos} contato(s) e ${topTerritory.liderancas} lideranca(s).`
    : "A base ainda nao possui leitura territorial suficiente para priorizacao.";
  $("#thermometer-score").textContent = score;
  $("#thermometer-label").textContent = `${levelLabel(score)} com ${Number(state.overview?.cards?.contatos || 0)} contato(s) ativos e ${Number(state.overview?.cards?.demandas_abertas || 0)} demanda(s) em aberto.`;
  $("#pressure-focus").textContent = topTerritory?.territorio_nome || "Sem foco";
  $("#pressure-copy").textContent = topTerritory
    ? `${labelStatus(pressure)} com score ${topTerritory.score}. Priorize agenda, devolutiva e presenca territorial.`
    : "Sem territorios classificados no momento.";
  $("#sentiment-score").textContent = percentage(sentimentPercent(sentiment, "positive"));
  $("#sentiment-copy").textContent = sentiment.amostras
    ? `${sentiment.amostras} amostra(s) agregada(s); ${percentage(sentimentPercent(sentiment, "negative"))} negativo(s) e ${percentage(sentimentPercent(sentiment, "neutral"))} neutro(s).`
    : "Sem amostras agregadas de sentimento publico.";
  $("#last-sync").textContent = `Atualizado em ${formatDateTime(new Date().toISOString())}`;
  $("#operations-summary").textContent = `${state.contacts.length} contato(s), ${state.demands.length} demanda(s), ${state.agenda.length} agenda(s) e ${state.interactions.length} interacao(oes) disponiveis no celular.`;
  renderThermometerVisual(score);
  renderSentimentVisual(sentiment);
}

function renderKpis() {
  const cards = state.overview?.cards || {};
  const items = [
    ["Demandas abertas", cards.demandas_abertas || 0, `${cards.sla_em_risco || 0} em risco`, cards.sla_vencido ? "VENCIDO" : "NEUTRAL", "demandas_abertas"],
    ["Base cidada", cards.contatos || 0, `${cards.liderancas || 0} liderancas`, cards.liderancas ? "POSITIVO" : "NEUTRAL", "contatos"],
    ["Agenda do mandato", cards.agenda_pendente || 0, `${state.agenda.filter((item) => item.eh_agenda_vereador).length} compromisso(s) do vereador`, cards.agenda_pendente ? "MEDIA" : "NEUTRAL", "agenda"],
    ["Relacionamento mobilizado", cards.engajamento_forte || 0, `${state.contacts.filter((item) => item.voto_2028 === "VOTO_CERTO").length} voto(s) certo(s)`, cards.engajamento_forte ? "POSITIVO" : "NEUTRAL", "relacionamento"],
  ];
  $("#kpi-grid").innerHTML = items
    .map(
      ([label, value, detail, tone, key]) => `
        <article class="kpi-card actionable" data-drilldown-type="kpi" data-drilldown-key="${escapeHtml(key)}" tabindex="0" role="button">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <p>${escapeHtml(detail)}</p>
          <div class="pill ${pillClass(tone)}">${escapeHtml(labelStatus(tone))}</div>
        </article>
      `,
    )
    .join("");
}

function renderTerritories() {
  const heatmap = (state.overview?.heatmap || []).slice(0, 6);
  $("#territory-grid").innerHTML = heatmap.length
    ? heatmap
        .map(
          (item) => `
            <article class="territory-card actionable" data-drilldown-type="territory" data-drilldown-key="${escapeHtml(item.territorio_id || item.id || "")}" tabindex="0" role="button">
              <span>${escapeHtml(item.tipo || "Territorio")}</span>
              <strong>${escapeHtml(item.territorio_nome)}</strong>
              <p>${escapeHtml(labelStatus(item.nivel_pressao || ""))} com ${item.demandas} demanda(s), ${item.contatos} cadastro(s) e ${item.liderancas} lideranca(s).</p>
              <div class="territory-meta">
                <div class="meta-tag">Score ${escapeHtml(item.score)}</div>
                <div class="meta-tag">${escapeHtml(item.demandas)} demandas</div>
                <div class="meta-tag">${escapeHtml(item.contatos)} base ativa</div>
              </div>
              <div class="pill ${pillClass(item.nivel_pressao)}">${escapeHtml(labelStatus(item.nivel_pressao || ""))}</div>
            </article>
          `,
        )
        .join("")
    : '<p class="message">Nenhum territorio com leitura de pressao disponivel.</p>';
  renderGeoMap();
}

function renderDemands() {
  const urgent = [...state.demands]
    .filter((item) => ["VENCIDO", "EM_RISCO"].includes(item.sla_status) || ["CRITICA", "ALTA"].includes(item.prioridade))
    .sort((left, right) => {
      const leftScore = (left.sla_status === "VENCIDO" ? 3 : left.sla_status === "EM_RISCO" ? 2 : 0) + (left.prioridade === "CRITICA" ? 2 : left.prioridade === "ALTA" ? 1 : 0);
      const rightScore = (right.sla_status === "VENCIDO" ? 3 : right.sla_status === "EM_RISCO" ? 2 : 0) + (right.prioridade === "CRITICA" ? 2 : right.prioridade === "ALTA" ? 1 : 0);
      return rightScore - leftScore;
    })
    .slice(0, 5);
  $("#demand-summary").textContent = `${state.demands.filter((item) => !["CONCLUIDA", "ARQUIVADA", "CANCELADA", "EXCLUIDO"].includes(item.status)).length} demanda(s) em curso`;
  $("#demand-focus").innerHTML = urgent.length
    ? urgent
        .map(
          (item) => `
            <article class="stack-card actionable" data-drilldown-type="demand" data-drilldown-key="${escapeHtml(item.id)}" tabindex="0" role="button">
              <header>
                <div>
                  <small>${escapeHtml(item.territorio_nome || "Sem territorio")}</small>
                  <strong>${escapeHtml(item.titulo)}</strong>
                </div>
                <div class="pill ${pillClass(item.sla_status || item.prioridade)}">${escapeHtml(labelStatus(item.sla_status || item.prioridade))}</div>
              </header>
              <p>${escapeHtml(item.cidadao_nome || "Sem demandante")} · ${escapeHtml(item.responsavel_nome || "Sem responsavel")}</p>
              <div class="stack-meta">
                <div class="meta-tag">${escapeHtml(labelStatus(item.status))}</div>
                <div class="meta-tag">Prioridade ${escapeHtml(labelStatus(item.prioridade))}</div>
                <div class="meta-tag">${Number(item.sla_horas_restantes || 0)}h restantes</div>
              </div>
            </article>
          `,
        )
        .join("")
    : '<p class="message">Nenhuma demanda critica ou em risco neste momento.</p>';
}

function renderRelationship() {
  const activeContacts = state.contacts.filter((item) => item.status !== "EXCLUIDO");
  const leaders = activeContacts.filter((item) => item.nivel_relacionamento === "LIDERANCA" || item.influencia === "ALTA");
  const mobilized = activeContacts.filter((item) => ["FORTE", "ALTO"].includes(item.engajamento));
  const voteCertain = activeContacts.filter((item) => item.voto_2028 === "VOTO_CERTO");
  $("#relationship-summary").textContent = `${activeContacts.length} contato(s), ${leaders.length} lideranca(s) e ${voteCertain.length} voto(s) certo(s)`;
  $("#relationship-panel").innerHTML = [
    ["Liderancas territoriais", leaders.length, leaders[0] ? `${leaders[0].nome} puxa leitura em ${leaders[0].territorio_nome || leaders[0].bairro || "territorio nao definido"}.` : "Sem liderancas destacadas.", "leaders"],
    ["Base mobilizada", mobilized.length, mobilized.length ? `${mobilized.length} pessoa(s) com engajamento forte para ativacao politica.` : "Sem base fortemente mobilizada.", "mobilized"],
    ["Voto certo", voteCertain.length, voteCertain.length ? `${voteCertain.length} registro(s) prontos para nutricao e recorrencia.` : "Ainda sem voto certo consolidado.", "voteCertain"],
  ]
    .map(
      ([label, value, detail, key]) => `
        <article class="relationship-card actionable" data-drilldown-type="relationship" data-drilldown-key="${escapeHtml(key)}" tabindex="0" role="button">
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
          <p>${escapeHtml(detail)}</p>
        </article>
      `,
    )
    .join("");
}

function renderCitizens() {
  const citizens = [...state.contacts]
    .filter((item) => item.tipo_contato !== "COLABORADOR" && item.status !== "EXCLUIDO")
    .sort((left, right) => {
      const leftScore = (left.nivel_relacionamento === "LIDERANCA" ? 3 : 0) + (left.influencia === "ALTA" ? 2 : 0) + (["FORTE", "ALTO"].includes(left.engajamento) ? 1 : 0);
      const rightScore = (right.nivel_relacionamento === "LIDERANCA" ? 3 : 0) + (right.influencia === "ALTA" ? 2 : 0) + (["FORTE", "ALTO"].includes(right.engajamento) ? 1 : 0);
      return rightScore - leftScore;
    })
    .slice(0, 5);
  $("#citizen-summary").textContent = `${citizens.length} nome(s) sob acompanhamento prioritario`;
  $("#citizen-list").innerHTML = citizens.length
    ? citizens
        .map(
          (item) => `
            <article class="stack-card actionable" data-drilldown-type="citizen" data-drilldown-key="${escapeHtml(item.id)}" tabindex="0" role="button">
              <header>
                <div>
                  <small>${escapeHtml(item.territorio_nome || item.bairro || "Sem territorio")}</small>
                  <strong>${escapeHtml(item.nome)}</strong>
                </div>
                <div class="pill ${pillClass(item.influencia || item.engajamento)}">${escapeHtml(labelStatus(item.influencia || item.engajamento))}</div>
              </header>
              <p>${escapeHtml(item.telefone_principal || "Sem telefone")} · ${escapeHtml(item.voto_2028 || "INDEFINIDO")}</p>
              <div class="stack-meta">
                <div class="meta-tag">${escapeHtml(labelStatus(item.nivel_relacionamento || "CONTATO"))}</div>
                <div class="meta-tag">${escapeHtml(labelStatus(item.engajamento || "FRIO"))}</div>
              </div>
            </article>
          `,
        )
        .join("")
    : '<p class="message">Nenhum cidadao priorizado no momento.</p>';
}

function renderTeam() {
  const activeUsers = state.users.filter((item) => item.ativo !== false);
  const teamMetrics = [...(state.overview?.equipes_produtividade || state.teams || [])]
    .filter((item) => item && item.produtividade)
    .sort(
      (left, right) =>
        (right.produtividade?.cadastros || 0) + (right.produtividade?.demandas || 0) - ((left.produtividade?.cadastros || 0) + (left.produtividade?.demandas || 0)),
    )
    .slice(0, 5);
  const teamRows = activeUsers
    .map((user) => {
      const ownedDemands = state.demands.filter((item) => item.responsavel_usuario_id === user.id);
      const completedDemands = ownedDemands.filter((item) => item.status === "CONCLUIDA").length;
      const riskDemands = ownedDemands.filter((item) => item.sla_status === "EM_RISCO" || item.sla_status === "VENCIDO").length;
      const agendaCount = state.agenda.filter((item) => item.responsavel_usuario_id === user.id).length;
      const score = completedDemands * 3 + agendaCount * 2 + Math.max(0, ownedDemands.length - riskDemands);
      return { user, ownedDemands: ownedDemands.length, completedDemands, riskDemands, agendaCount, score };
    })
    .sort((left, right) => right.score - left.score)
    .slice(0, 5);
  $("#team-summary").textContent = teamMetrics.length
    ? `${teamMetrics.length} equipe(s) com produtividade monitorada e ${activeUsers.length} colaborador(es) ativos`
    : `${activeUsers.length} colaborador(es) ativos e ${state.teams.length} equipe(s) cadastrada(s)`;
  $("#team-list").innerHTML = teamMetrics.length
    ? teamMetrics
        .map(
          (team) => `
            <article class="stack-card actionable" data-drilldown-type="team" data-drilldown-key="${escapeHtml(team.id)}" tabindex="0" role="button">
              <header>
                <div>
                  <small>${escapeHtml(team.supervisor_nome || "Sem supervisor")}</small>
                  <strong>${escapeHtml(team.nome || "Equipe sem nome")}</strong>
                </div>
                <div class="pill ${pillClass((team.produtividade?.engajamento_medio || 0) >= 70 ? "SAUDAVEL" : "EM_RISCO")}">${escapeHtml(percentage(team.produtividade?.completude_media || 0))}</div>
              </header>
              <p>${escapeHtml((team.produtividade?.territorios_nomes || []).join(" · ") || "Sem territorio vinculado")} · ${team.produtividade?.membros_ativos || 0} membro(s)</p>
              <div class="stack-meta">
                <div class="meta-tag">${team.produtividade?.cadastros || 0} cadastros</div>
                <div class="meta-tag">${team.produtividade?.demandas || 0} demandas</div>
                <div class="meta-tag">${team.produtividade?.cadastros_qualificados || 0} qualificados</div>
              </div>
              <div class="stack-meta">
                <div class="meta-tag">Engaj. ${escapeHtml(String(Math.round(team.produtividade?.engajamento_medio || 0)))}</div>
                <div class="meta-tag">${team.produtividade?.engajamento_forte || 0} forte(s)</div>
                <div class="meta-tag">${team.produtividade?.demandas_abertas || 0} abertas</div>
              </div>
            </article>
          `,
        )
        .join("")
    : teamRows.length
    ? teamRows
        .map(
          (item) => `
            <article class="stack-card actionable" data-drilldown-type="team" data-drilldown-key="" data-drilldown-user-id="${escapeHtml(item.user.id)}" tabindex="0" role="button">
              <header>
                <div>
                  <small>${escapeHtml(item.user.perfil || "COLABORADOR")}</small>
                  <strong>${escapeHtml(item.user.nome)}</strong>
                </div>
                <div class="pill ${pillClass(item.riskDemands ? "EM_RISCO" : "SAUDAVEL")}">Score ${escapeHtml(item.score)}</div>
              </header>
              <p>${escapeHtml(item.user.email_login || "Sem e-mail")} · ${item.ownedDemands} demanda(s) sob responsabilidade</p>
              <div class="stack-meta">
                <div class="meta-tag">${item.completedDemands} concluidas</div>
                <div class="meta-tag">${item.riskDemands} em risco</div>
                <div class="meta-tag">${item.agendaCount} agenda(s)</div>
              </div>
            </article>
          `,
        )
        .join("")
    : '<p class="message">Nenhum colaborador ativo para leitura de desempenho.</p>';
}

function renderRecentOperations() {
  const recentDemands = filteredDemands()
    .sort((left, right) => String(right.updated_at || right.created_at || right.data_abertura || "").localeCompare(String(left.updated_at || left.created_at || left.data_abertura || "")))
    .slice(0, 5);
  const recentAgenda = [...state.agenda]
    .sort((left, right) => String(right.data_inicio || right.created_at || "").localeCompare(String(left.data_inicio || left.created_at || "")))
    .slice(0, 5);
  const selectedDemand = currentSelectedDemand();
  if (selectedDemand && !state.selectedDemandId) {
    state.selectedDemandId = selectedDemand.id;
  }

  const filtersApplied = [state.demandFilters.status, state.demandFilters.priority, state.demandFilters.responsibleUserId].filter(Boolean).length;
  $("#recent-demand-summary").textContent = filtersApplied
    ? `${recentDemands.length} item(ns) filtrados`
    : `${recentDemands.length} item(ns) mais recentes`;
  $("#recent-agenda-summary").textContent = `${recentAgenda.length} compromisso(s) em destaque`;

  $("#recent-demand-list").innerHTML = recentDemands.length
    ? recentDemands
        .map(
          (item) => `
            <article class="stack-card ${item.id === state.selectedDemandId ? "selected" : ""}" data-demand-id="${escapeHtml(item.id)}">
              <header>
                <div>
                  <small>${escapeHtml(item.territorio_nome || "Sem territorio")}</small>
                  <strong>${escapeHtml(item.titulo)}</strong>
                </div>
                <div class="pill ${pillClass(item.sla_status || item.prioridade)}">${escapeHtml(labelStatus(item.sla_status || item.prioridade))}</div>
              </header>
              <p class="tight">${escapeHtml(item.cidadao_nome || "Sem demandante")} · ${escapeHtml(item.responsavel_nome || "Sem responsavel")}</p>
              <div class="stack-meta">
                <div class="meta-tag">${escapeHtml(labelStatus(item.status))}</div>
                <div class="meta-tag">${formatDateTime(item.updated_at || item.created_at || item.data_abertura)}</div>
              </div>
              <div class="row-actions">
                <button type="button" class="secondary" data-select-demand="${escapeHtml(item.id)}">Editar</button>
              </div>
            </article>
          `,
        )
        .join("")
    : '<p class="message">Nenhuma demanda recente.</p>';

  const editForm = $("#demand-edit-form");
  const statusLabel = $("#demand-edit-status");
  const titleLabel = $("#demand-edit-title");
  if (!editForm || !statusLabel || !titleLabel) return;
  if (!selectedDemand) {
    editForm.reset();
    editForm.elements.demanda_id.value = "";
    titleLabel.textContent = "Selecione uma demanda";
    statusLabel.textContent = "Sem selecao";
    return;
  }
  editForm.elements.demanda_id.value = selectedDemand.id;
  editForm.elements.titulo.value = selectedDemand.titulo || "";
  editForm.elements.descricao.value = selectedDemand.descricao || "";
  editForm.elements.prioridade.value = selectedDemand.prioridade || "MEDIA";
  editForm.elements.responsavel_usuario_id.value = selectedDemand.responsavel_usuario_id || "";
  titleLabel.textContent = selectedDemand.titulo || "Demanda selecionada";
  statusLabel.textContent = `${labelStatus(selectedDemand.status)} · ${labelStatus(selectedDemand.sla_status || selectedDemand.prioridade)}`;

  $("#recent-agenda-list").innerHTML = recentAgenda.length
    ? recentAgenda
        .map(
          (item) => `
            <article class="stack-card">
              <header>
                <div>
                  <small>${escapeHtml(item.tipo_agenda || "AGENDA")}</small>
                  <strong>${escapeHtml(item.titulo)}</strong>
                </div>
                <div class="pill ${pillClass(item.status === "REALIZADO" ? "SAUDAVEL" : "NEUTRAL")}">${escapeHtml(labelStatus(item.status || "AGENDADO"))}</div>
              </header>
              <p class="tight">${escapeHtml(item.local_texto || item.territorio_nome || "Local a definir")}</p>
              <div class="stack-meta">
                <div class="meta-tag">${formatDateTime(item.data_inicio)}</div>
                <div class="meta-tag">${item.eh_agenda_vereador ? "Vereador" : "Equipe"}</div>
              </div>
            </article>
          `,
        )
        .join("")
    : '<p class="message">Nenhum compromisso recente.</p>';
}

function fillSelect(selectId, items, formatter, options = {}) {
  const select = $(selectId);
  if (!select) return;
  const placeholder = options.placeholder || "Selecione";
  const includeEmpty = options.includeEmpty !== false;
  select.innerHTML = `${includeEmpty ? `<option value="">${escapeHtml(placeholder)}</option>` : ""}${items
    .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(formatter(item))}</option>`)
    .join("")}`;
}

function renderOperationalOptions() {
  const activeContacts = sortByName(state.contacts.filter((item) => item.status !== "EXCLUIDO" && item.tipo_contato !== "COLABORADOR"));
  const activeUsers = sortByName(state.users.filter((item) => item.ativo !== false));
  const territories = sortByName(state.territories);

  fillSelect("#quick-contact-territory", territories, (item) => `${item.nome} - ${item.tipo}`, { placeholder: "Sem territorio definido" });
  fillSelect("#quick-demand-contact", activeContacts, (item) => `${item.nome} - ${item.bairro || item.territorio_nome || "Sem territorio"}`, { includeEmpty: false });
  fillSelect("#quick-demand-user", activeUsers, (item) => `${item.nome} - ${item.perfil}`, { placeholder: "Responsavel automatico" });
  fillSelect("#quick-edit-demand-user", activeUsers, (item) => `${item.nome} - ${item.perfil}`, { placeholder: "Sem responsavel" });
  fillSelect("#quick-interaction-contact", activeContacts, (item) => `${item.nome} - ${item.telefone_principal || "Sem telefone"}`, { includeEmpty: false });
  fillSelect("#demand-filter-user", activeUsers, (item) => `${item.nome} - ${item.perfil}`, { placeholder: "Todos" });
  $("#demand-filter-status").value = state.demandFilters.status;
  $("#demand-filter-priority").value = state.demandFilters.priority;
  $("#demand-filter-user").value = state.demandFilters.responsibleUserId;
}

function renderAll() {
  renderHero();
  renderKpis();
  renderExecutiveDrilldown();
  renderContextList();
  renderTerritoryDetailView();
  renderTeamDetailView();
  renderTerritories();
  renderDemands();
  renderRelationship();
  renderCitizens();
  renderTeam();
  renderRecentOperations();
  renderOperationalOptions();
  if (!state.executiveDrilldown) {
    setExecutiveDrilldown(buildKpiDrilldown("demandas_abertas"));
  }
  setCurrentView(state.currentView, { skipHistory: true });
}

async function loadData() {
  const [me, overview, demands, contacts, users, teams, territories, interactions, agenda, sentiment] = await Promise.all([
    api("/auth/me"),
    api("/political-os/overview"),
    api("/demandas?page_size=200"),
    api("/contatos?page_size=200"),
    api("/usuarios?page_size=200"),
    api("/equipes"),
    api("/territorios?page_size=200&sort_by=nome&sort_order=asc"),
    api("/interacoes?page_size=200"),
    api("/agenda?page_size=200"),
    api("/sentimento-social/resumo"),
  ]);
  state.user = me.data;
  state.overview = overview.data;
  state.demands = demands.data;
  state.contacts = contacts.data;
  state.users = users.data;
  state.teams = teams.data;
  state.territories = territories.data;
  state.interactions = interactions.data;
  state.agenda = agenda.data;
  state.sentiment = sentiment.data;
  renderAll();
}

async function createContact(event) {
  event.preventDefault();
  setMessage("#quick-contact-message", "Salvando cidadao...");
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.territorio_id) delete data.territorio_id;
  data.origem_cadastro = "MOBILE_VEREADOR";
  data.tipo_contato = "CIDADAO";
  try {
    await api("/contatos", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    setMessage("#quick-contact-message", "Cidadao registrado no mandato.");
    await loadData();
    setCurrentView("operacional");
  } catch (error) {
    setMessage("#quick-contact-message", error.message, true);
  }
}

async function createDemand(event) {
  event.preventDefault();
  setMessage("#quick-demand-message", "Abrindo demanda...");
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.responsavel_usuario_id) delete data.responsavel_usuario_id;
  data.origem_cadastro = "MOBILE_VEREADOR";
  try {
    await api("/demandas", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    setMessage("#quick-demand-message", "Demanda aberta e enviada para a fila.");
    await loadData();
    setCurrentView("operacional");
  } catch (error) {
    setMessage("#quick-demand-message", error.message, true);
  }
}

async function createAgenda(event) {
  event.preventDefault();
  setMessage("#quick-agenda-message", "Registrando compromisso...");
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  const payload = {
    ...data,
    status: "AGENDADO",
    eh_agenda_vereador: true,
    data_inicio: toIsoValue(data.data_inicio),
    data_fim: toIsoValue(data.data_fim),
  };
  try {
    await api("/agenda-eventos", { method: "POST", body: JSON.stringify(payload) });
    form.reset();
    setMessage("#quick-agenda-message", "Compromisso registrado na agenda do vereador.");
    await loadData();
    setCurrentView("operacional");
  } catch (error) {
    setMessage("#quick-agenda-message", error.message, true);
  }
}

async function createInteraction(event) {
  event.preventDefault();
  setMessage("#quick-interaction-message", "Registrando interacao...");
  const form = event.currentTarget;
  const data = Object.fromEntries(new FormData(form).entries());
  data.origem_registro = "MOBILE_VEREADOR";
  try {
    await api("/interacoes", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    setMessage("#quick-interaction-message", "Interacao registrada com sucesso.");
    await loadData();
    setCurrentView("operacional");
  } catch (error) {
    setMessage("#quick-interaction-message", error.message, true);
  }
}

async function saveDemandEdits(event) {
  event.preventDefault();
  const form = event.currentTarget;
  const demandId = form.elements.demanda_id.value;
  if (!demandId) {
    setMessage("#demand-edit-message", "Selecione uma demanda para editar.", true);
    return;
  }
  setMessage("#demand-edit-message", "Salvando ajustes da demanda...");
  const payload = Object.fromEntries(new FormData(form).entries());
  delete payload.demanda_id;
  if (!payload.responsavel_usuario_id) delete payload.responsavel_usuario_id;
  try {
    await api(`/demandas/${demandId}`, { method: "PUT", body: JSON.stringify(payload) });
    setMessage("#demand-edit-message", "Demanda atualizada no celular.");
    await loadData();
    state.currentView = "operacional";
    state.selectedDemandId = demandId;
    setCurrentView("operacional");
  } catch (error) {
    setMessage("#demand-edit-message", error.message, true);
  }
}

async function changeDemandStatus(action) {
  const demand = currentSelectedDemand();
  if (!demand) {
    setMessage("#demand-edit-message", "Selecione uma demanda primeiro.", true);
    return;
  }
  setMessage("#demand-edit-message", `Aplicando acao ${action}...`);
  try {
    if (action === "assumir") {
      await api(`/demandas/${demand.id}/assumir`, { method: "POST", body: JSON.stringify({}) });
    } else if (action === "concluir") {
      await api(`/demandas/${demand.id}/concluir`, { method: "POST", body: JSON.stringify({ observacao: "Concluida pelo app mobile do vereador." }) });
    } else if (action === "reabrir") {
      await api(`/demandas/${demand.id}/reabrir`, { method: "POST", body: JSON.stringify({ motivo_reabertura: "Reaberta pelo app mobile do vereador." }) });
    } else if (action === "arquivar") {
      await api(`/demandas/${demand.id}/arquivar`, { method: "POST", body: JSON.stringify({ motivo: "Arquivada pelo app mobile do vereador." }) });
    }
    setMessage("#demand-edit-message", `Acao ${action} aplicada com sucesso.`);
    await loadData();
    state.currentView = "operacional";
    state.selectedDemandId = demand.id;
    setCurrentView("operacional");
  } catch (error) {
    setMessage("#demand-edit-message", error.message, true);
  }
}

async function login(event) {
  event.preventDefault();
  setMessage("#login-message", "Entrando...");
  const data = Object.fromEntries(new FormData(event.currentTarget).entries());
  try {
    const payload = await api("/auth/login", { method: "POST", body: JSON.stringify(data) });
    state.token = payload.data.access_token;
    localStorage.setItem("gabinete_mandato_token", state.token);
    showApp();
    await loadData();
    setMessage("#login-message", "");
  } catch (error) {
    setMessage("#login-message", error.message, true);
  }
}

async function logout() {
  try {
    if (state.token) {
      await api("/auth/logout", { method: "POST", body: JSON.stringify({ origem: "mandato-mobile" }) });
    }
  } catch (error) {
    console.error(error);
  } finally {
    state.token = null;
    state.user = null;
    localStorage.removeItem("gabinete_mandato_token");
    showLogin();
  }
}

function bindEvents() {
  $("#login-form").addEventListener("submit", login);
  $("#refresh").addEventListener("click", async () => {
    setMessage("#login-message", "");
    await loadData();
  });
  $("#logout").addEventListener("click", logout);
  $("#quick-contact-form").addEventListener("submit", createContact);
  $("#quick-demand-form").addEventListener("submit", createDemand);
  $("#demand-edit-form").addEventListener("submit", saveDemandEdits);
  $("#quick-agenda-form").addEventListener("submit", createAgenda);
  $("#quick-interaction-form").addEventListener("submit", createInteraction);
  document.querySelectorAll("[data-view]").forEach((button) => {
    button.addEventListener("click", () => setCurrentView(button.dataset.view, { label: state.viewLabels[button.dataset.view] || button.textContent }));
  });
  document.querySelectorAll(".quick-nav").forEach((button) => {
    button.addEventListener("click", () => {
      setCurrentView("operacional", { label: "Operacoes" });
      document.getElementById(button.dataset.focusTarget)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  });
  $("#recent-demand-list").addEventListener("click", (event) => {
    const action = event.target.closest("[data-select-demand]");
    if (!action) return;
    selectDemand(action.dataset.selectDemand);
    $("#demand-edit-form")?.scrollIntoView({ behavior: "smooth", block: "start" });
  });
  document.querySelectorAll("[data-demand-transition]").forEach((button) => {
    button.addEventListener("click", () => changeDemandStatus(button.dataset.demandTransition));
  });
  $("#demand-filter-status").addEventListener("change", (event) => {
    state.demandFilters.status = event.target.value;
    state.selectedDemandId = null;
    renderRecentOperations();
  });
  $("#demand-filter-priority").addEventListener("change", (event) => {
    state.demandFilters.priority = event.target.value;
    state.selectedDemandId = null;
    renderRecentOperations();
  });
  $("#demand-filter-user").addEventListener("change", (event) => {
    state.demandFilters.responsibleUserId = event.target.value;
    state.selectedDemandId = null;
    renderRecentOperations();
  });
  $("#clear-demand-filters").addEventListener("click", clearDemandFilters);
  document.querySelectorAll("[data-return-view]").forEach((button) => {
    button.addEventListener("click", () => navigateBreadcrumb(Math.max(0, state.viewHistory.length - 2)));
  });
  $("#mobile-breadcrumb").addEventListener("click", (event) => {
    const item = event.target.closest("[data-breadcrumb-index]");
    if (!item) return;
    navigateBreadcrumb(Number(item.dataset.breadcrumbIndex));
  });
  $("#view-executivo").addEventListener("click", (event) => {
    const card = event.target.closest("[data-drilldown-type]");
    if (!card) return;
    openExecutiveDrilldown(card.dataset.drilldownType, card.dataset.drilldownKey, { userId: card.dataset.drilldownUserId });
  });
  $("#view-executivo").addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const card = event.target.closest("[data-drilldown-type]");
    if (!card) return;
    event.preventDefault();
    openExecutiveDrilldown(card.dataset.drilldownType, card.dataset.drilldownKey, { userId: card.dataset.drilldownUserId });
  });
  $("#detail-primary-action").addEventListener("click", () => {
    state.executiveDrilldown?.primaryAction?.run?.();
  });
  $("#context-list-primary-action").addEventListener("click", () => {
    state.contextList?.primaryAction?.run?.();
  });
  $("#geo-map-stage").addEventListener("click", (event) => {
    const item = event.target.closest("[data-map-territory-id]");
    if (!item) return;
    setGeoMapFocus(item.dataset.mapTerritoryId, { openDemands: true });
  });
  $("#geo-map-stage").addEventListener("keydown", (event) => {
    if (event.key !== "Enter" && event.key !== " ") return;
    const item = event.target.closest("[data-map-territory-id]");
    if (!item) return;
    event.preventDefault();
    setGeoMapFocus(item.dataset.mapTerritoryId, { openDemands: true });
  });
  $("#geo-map-open-demands").addEventListener("click", () => {
    if (!state.geoMapFocusId) return;
    openTerritoryDemandList(state.geoMapFocusId);
  });
  $("#geo-map-open-territory").addEventListener("click", () => {
    if (!state.geoMapFocusId) return;
    openTerritoryDetail(state.geoMapFocusId);
  });
  ["#context-list-content", "#territory-demand-list", "#territory-contact-list", "#team-output-list"].forEach((selector) => {
    $(selector)?.addEventListener("click", (event) => {
      const item = event.target.closest("[data-context-open-type]");
      if (!item) return;
      openContextEntity(item.dataset.contextOpenType, item.dataset.contextOpenId);
    });
  });
  ["#context-list-content", "#territory-demand-list", "#territory-contact-list", "#team-output-list"].forEach((selector) => {
    $(selector)?.addEventListener("keydown", (event) => {
      if (event.key !== "Enter" && event.key !== " ") return;
      const item = event.target.closest("[data-context-open-type]");
      if (!item) return;
      event.preventDefault();
      openContextEntity(item.dataset.contextOpenType, item.dataset.contextOpenId);
    });
  });
  $("#territory-open-demands").addEventListener("click", () => {
    const territoryId = state.territoryDetail?.territoryId;
    if (!territoryId) return;
    openDemandListInMandato({
      title: `Demandas em ${territoryNameFromId(territoryId)}`,
      eyebrow: "Territorio",
      summary: "Fila filtrada das demandas vinculadas ao territorio selecionado.",
      chip: territoryNameFromId(territoryId),
      meta: ["Pressao territorial"],
      webLink: destinationSpec("territory", "territorio", { territorio_id: territoryId }),
      filter: (item) => territoryScopedDemands(territoryId).some((entry) => entry.id === item.id),
    });
  });
  $("#territory-open-contacts").addEventListener("click", () => {
    const territoryId = state.territoryDetail?.territoryId;
    if (!territoryId) return;
    openContactListInMandato({
      title: `Cadastros em ${territoryNameFromId(territoryId)}`,
      eyebrow: "Territorio",
      summary: "Lista filtrada da base cidada vinculada ao territorio selecionado.",
      chip: territoryNameFromId(territoryId),
      meta: ["Base territorial"],
      webLink: destinationSpec("territory", "territorio", { territorio_id: territoryId }),
      filter: (item) => territoryScopedContacts(territoryId).some((entry) => entry.id === item.id),
    });
  });
  $("#team-open-demands").addEventListener("click", () => {
    const teamId = state.teamDetail?.teamId;
    const fallbackUserId = state.teamDetail?.fallbackUserId || "";
    if (!teamId && !fallbackUserId) return;
    openDemandListInMandato({
      title: `Demandas de ${state.teamDetail?.title || "equipe"}`,
      eyebrow: "Equipe",
      summary: "Fila filtrada das demandas geradas ou atendidas pela equipe selecionada.",
      chip: state.teamDetail?.title || "Equipe",
      meta: ["Produtividade operacional"],
      webLink: destinationSpec("team", "equipe", { equipe_id: teamId, usuario_id: fallbackUserId || undefined }),
      filter: (item) => teamScopedDemands(teamId, fallbackUserId).some((entry) => entry.id === item.id),
    });
  });
  $("#team-open-contacts").addEventListener("click", () => {
    const teamId = state.teamDetail?.teamId;
    const fallbackUserId = state.teamDetail?.fallbackUserId || "";
    if (!teamId && !fallbackUserId) return;
    openContactListInMandato({
      title: `Cadastros de ${state.teamDetail?.title || "equipe"}`,
      eyebrow: "Equipe",
      summary: "Lista filtrada dos cadastros vinculados a esta frente de campo.",
      chip: state.teamDetail?.title || "Equipe",
      meta: ["Qualidade cadastral"],
      webLink: destinationSpec("team", "equipe", { equipe_id: teamId, usuario_id: fallbackUserId || undefined }),
      filter: (item) => teamScopedContacts(teamId, fallbackUserId).some((entry) => entry.id === item.id),
    });
  });
}

async function bootstrap() {
  bindEvents();
  if (!state.token) {
    showLogin();
    return;
  }
  try {
    showApp();
    await loadData();
  } catch (error) {
    console.error(error);
    state.token = null;
    localStorage.removeItem("gabinete_mandato_token");
    showLogin();
    setMessage("#login-message", "Sua sessao expirou. Entre novamente.", true);
  }
}

bootstrap();