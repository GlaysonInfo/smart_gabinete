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
  selectedDemandId: null,
  selectedContactId: null,
  editingDemandId: null,
  editingContactId: null,
  editingUserId: null,
  globalSearch: "",
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

function demandStatusLabel(status) {
  return STATUS_LABELS[status] || status || "Sem situacao";
}

function labelCode(value) {
  if (!value) return "Nao informado";
  const known = {
    PLANEJADO: "Planejado",
    CONFIRMADO: "Confirmado",
    REALIZADO: "Realizado",
    CANCELADO: "Cancelado",
    INDICACAO: "Indicacao",
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

function userOptions(selected) {
  return (
    '<option value="">Sem responsavel</option>' +
    state.users
      .map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === selected ? "selected" : ""}>${escapeHtml(item.nome)}</option>`)
      .join("")
  );
}

function territoryOptions(selected) {
  return (
    '<option value="">Sem territorio</option>' +
    state.territories
      .map((item) => `<option value="${escapeHtml(item.id)}" ${item.id === selected ? "selected" : ""}>${escapeHtml(item.nome)} - ${escapeHtml(item.tipo)}</option>`)
      .join("")
  );
}

function selectedDemand() {
  return state.demands.find((item) => item.id === state.selectedDemandId) || state.demands[0] || null;
}

function selectedContact() {
  return state.contacts.find((item) => item.id === state.selectedContactId) || state.contacts[0] || null;
}

function renderSelectedDemand() {
  const demand = selectedDemand();
  if (!demand) {
    $("#selected-demand-label").textContent = "Nenhuma demanda selecionada.";
    return;
  }
  $("#selected-demand-label").textContent = `${demand.titulo} - ${demand.cidadao_nome || "demandante pendente"}`;
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

function renderMetrics() {
  const cards = state.overview?.cards || {};
  const items = [
    ["Demandas abertas", cards.demandas_abertas ?? 0],
    ["Contatos", cards.contatos ?? 0],
    ["Liderancas", cards.liderancas ?? 0],
    ["Oficios pendentes", cards.oficios_pendentes ?? 0],
  ];
  $("#metric-grid").innerHTML = items
    .map(
      ([label, value]) => `
        <article class="metric">
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
          <article class="heat-cell" data-level="${level}">
            <strong>${escapeHtml(item.territorio_nome)}</strong>
            <span>${Number(item.demandas || 0)} demandas</span>
            <span>${Number(item.contatos || 0)} contatos</span>
            <span>${Number(item.liderancas || 0)} liderancas</span>
          </article>
        `;
      })
      .join("") || "<p>Nenhum dado territorial registrado.</p>";
}

function renderSentiment() {
  const sentiment = state.overview?.sentimento || {};
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
    <p>${escapeHtml(sentiment.alerta || "Sem alerta de sentimento.")}</p>
  `;
}

function renderAmendmentSummary() {
  const totals = state.overview?.emendas || {};
  const indicated = Number(totals.valor_indicado || 0);
  const paid = Number(totals.valor_pago || 0);
  const paidPercent = indicated ? Math.round((paid / indicated) * 100) : 0;
  $("#amendment-summary").innerHTML = `
    <div class="budget-numbers">
      <article><span>Indicado</span><strong>${formatCurrency(indicated)}</strong></article>
      <article><span>Pago</span><strong>${formatCurrency(paid)}</strong></article>
      <article><span>Empenhado</span><strong>${formatCurrency(totals.valor_empenhado)}</strong></article>
      <article><span>Liquidado</span><strong>${formatCurrency(totals.valor_liquidado)}</strong></article>
    </div>
    <div>
      <p>${paidPercent}% pago sobre o total indicado</p>
      <span class="budget-track"><span class="budget-fill" style="width:${Math.min(paidPercent, 100)}%; background: var(--emerald)"></span></span>
    </div>
  `;
}

function renderAlerts() {
  const alerts = state.overview?.alertas || [];
  $("#alert-list").innerHTML =
    alerts
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.titulo || item.tipo)}</h3>
              <p>${escapeHtml(item.descricao || "")}</p>
            </div>
            <span class="status warning">${escapeHtml(item.tipo || "ALERTA")}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum alerta critico no momento.</p>";
}

function renderCommandCenter() {
  renderMetrics();
  renderHeatmap();
  renderSentiment();
  renderAmendmentSummary();
  renderAlerts();
}

function renderDemands() {
  if (
    (!state.selectedDemandId || !state.demands.some((item) => item.id === state.selectedDemandId)) &&
    state.demands[0]
  ) {
    state.selectedDemandId = state.demands[0].id;
  }
  const query = state.globalSearch.trim().toLowerCase();
  const activeDemands = state.demands.filter((item) => {
    if (item.status === "ARQUIVADA" || item.status === "EXCLUIDO") return false;
    if (!query) return true;
    return [item.titulo, item.descricao, item.cidadao_nome, item.tipo_demanda, demandTerritory(item), item.responsavel_nome].some((value) =>
      String(value || "").toLowerCase().includes(query),
    );
  });
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
      $("#ai-output").textContent = "Demanda selecionada. Gere um resumo ou uma sugestao de proxima etapa.";
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
        <span class="avatar small">${escapeHtml(initials(item.cidadao_nome))}</span>
        <div>
          <h3>${escapeHtml(item.titulo)}</h3>
          <p>${escapeHtml(item.cidadao_nome || "Demandante pendente")}</p>
        </div>
      </div>
      <p>${escapeHtml(item.tipo_demanda || "Nao classificada")} - ${escapeHtml(demandTerritory(item))}</p>
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
      <div>
        <h3>${escapeHtml(item.titulo)}</h3>
        <p>Demandante: ${escapeHtml(item.cidadao_nome || "Pendente de regularizacao")} - Tipo: ${escapeHtml(item.tipo_demanda || "Nao classificada")}</p>
        <p>Territorio: ${escapeHtml(demandTerritory(item))} - Responsavel: ${escapeHtml(item.responsavel_nome || "Sem responsavel")}</p>
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
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderContacts() {
  const query = state.globalSearch.trim().toLowerCase();
  const matches = (item) => {
    if (!query) return true;
    return [item.nome, item.cpf, item.telefone_principal, item.email, item.bairro, item.observacoes]
      .some((value) => String(value || "").toLowerCase().includes(query));
  };
  const people = state.contacts.filter((item) => item.tipo_contato !== "ORGAO_PUBLICO" && item.status !== "EXCLUIDO" && matches(item));
  const publicBodies = state.contacts.filter((item) => item.tipo_contato === "ORGAO_PUBLICO" && item.status !== "EXCLUIDO" && matches(item));
  const renderContactCard = (item) => `
    <article class="row" data-crm-open="${escapeHtml(item.id)}">
      <div>
        <h3>${escapeHtml(item.nome)}</h3>
        <p>${escapeHtml(item.telefone_principal || "Sem telefone")} - ${escapeHtml(item.bairro || item.territorio_nome || "Sem bairro")}</p>
        <p>Perfil: ${escapeHtml(item.nivel_relacionamento || "CONTATO")} - Engajamento: ${escapeHtml(item.engajamento || "FRIO")} - Voto 2028: ${escapeHtml(item.voto_2028 || "INDEFINIDO")}</p>
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
  $("#contact-submit").textContent = "Salvar alteracoes";
  form.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderContactOptions() {
  const demandanteContacts = state.contacts.filter((item) => item.tipo_contato !== "ORGAO_PUBLICO" && item.status !== "EXCLUIDO");
  const options =
    '<option value="">Selecione</option>' +
    demandanteContacts
      .map((item) => `<option value="${escapeHtml(item.id)}">${escapeHtml(item.nome)} - ${escapeHtml(item.telefone_principal || item.bairro || "sem contato")}</option>`)
      .join("");
  ["#demand-contact-select", "#crm-contact-select", "#interaction-contact-select"].forEach((selector) => {
    const select = $(selector);
    if (!select) return;
    const current = select.value || (selector === "#crm-contact-select" ? state.selectedContactId : "");
    select.innerHTML = options;
    if (state.contacts.some((item) => item.id === current)) {
      select.value = current;
    }
  });
}

function renderCRM() {
  if ((!state.selectedContactId || !state.contacts.some((item) => item.id === state.selectedContactId)) && state.contacts[0]) {
    state.selectedContactId = state.contacts[0].id;
  }
  const contact = selectedContact();
  renderContactOptions();
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
      <div class="avatar">${escapeHtml(initials(contact.nome))}</div>
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
          <article class="row">
            <div>
              <h3>${escapeHtml(item.nome)}</h3>
              <p>${escapeHtml(item.email_login)} - ${escapeHtml(item.perfil)} - ${item.ativo ? "Ativo" : "Inativo"}</p>
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
  $("#agenda-list").innerHTML =
    state.agenda
      .map(
        (item) => `
          <article class="row">
            <div>
              <h3>${item.titulo}</h3>
              <p>${AGENDA_TYPES[item.tipo_agenda] || item.tipo_agenda || "Compromisso"} - ${item.local_texto || "Sem local"}</p>
              <p>Situacao: ${labelCode(item.status)} - Publico estimado: ${item.publico_estimado || 0}</p>
              ${item.relatorio_execucao ? `<p>Relatorio: ${item.relatorio_execucao}</p>` : ""}
            </div>
            <div class="row-actions">
              <button type="button" data-agenda-report="${item.id}" class="secondary">Relatorio</button>
              <button type="button" data-agenda-done="${item.id}">Realizado</button>
            </div>
            <span class="status">${item.eh_agenda_vereador ? "Parlamentar" : "Equipe"}</span>
          </article>
        `,
      )
      .join("") || "<p>Nenhum evento cadastrado.</p>";
  const first = state.agenda[0];
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
    state.agenda.map((item) => `<option value="${item.id}">${item.titulo} - ${labelCode(item.status)}</option>`).join("");
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
        const percent = Number(item.percentual_pago || 0);
        const committed = Number(item.percentual_empenhado || 0);
        return `
          <article class="row">
            <div>
              <h3>${escapeHtml(item.titulo)}</h3>
              <p>${escapeHtml(item.numero)} - ${escapeHtml(item.area || "Sem area")} - ${escapeHtml(item.beneficiario || "Sem beneficiario")}</p>
              <p>${escapeHtml(item.objeto || "Sem objeto detalhado.")}</p>
              <span class="budget-track">
                <span class="budget-fill" style="width:${Math.min(committed, 100)}%; background: var(--lime)"></span>
              </span>
              <small>${committed}% empenhado - ${percent}% pago</small>
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
  const activeContacts = state.contacts.filter((item) => item.status !== "INATIVO").length;
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
}

function renderUser() {
  $("#user-chip").textContent = state.user ? `${state.user.nome} - ${state.user.perfil}` : "Sem usuario";
}

function renderAll() {
  renderUser();
  renderCommandCenter();
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
}

async function loadData() {
  const [me, overview, demands, contacts, users, territories, agenda, interactions, propositions, amendments, offices, audit] = await Promise.all([
    api("/auth/me"),
    api("/political-os/overview"),
    api("/demandas?page_size=20"),
    api("/contatos?page_size=30"),
    api("/usuarios?page_size=20"),
    api("/territorios?page_size=100"),
    api("/agenda?page_size=20"),
    api("/interacoes?page_size=30"),
    api("/proposicoes?page_size=30"),
    api("/emendas?page_size=30"),
    api("/oficios?page_size=30"),
    api("/auditoria?page_size=12"),
  ]);
  state.user = me.data;
  state.overview = overview.data;
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
  renderAll();
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
  if (!data.territorio_id) delete data.territorio_id;
  try {
    const endpoint = state.editingContactId ? `/contatos/${state.editingContactId}` : "/contatos";
    const method = state.editingContactId ? "PUT" : "POST";
    const saved = await api(endpoint, { method, body: JSON.stringify(data) });
    state.selectedContactId = saved.data.id;
    state.editingContactId = null;
    form.reset();
    $("#contact-submit").textContent = "Salvar cadastro";
    setMessage("#contact-message", "Cadastro salvo.");
    await loadData();
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
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.cidadao_id) {
    setMessage("#demand-message", "Selecione um demandante cadastrado antes de criar a demanda.");
    return;
  }
  if (!data.territorio_id) delete data.territorio_id;
  if (!data.responsavel_usuario_id) delete data.responsavel_usuario_id;
  try {
    const created = await api("/demandas", { method: "POST", body: JSON.stringify(data) });
    form.reset();
    state.selectedDemandId = created.data.id;
    setMessage("#demand-message", "Demanda criada.");
    await loadData();
  } catch (error) {
    setMessage("#demand-message", error.message);
  }
}

async function saveDemandEdit(event) {
  event.preventDefault();
  if (!state.editingDemandId) return;
  const form = event.currentTarget;
  setMessage("#demand-edit-message", "Salvando...");
  const data = Object.fromEntries(new FormData(form).entries());
  if (!data.territorio_id) data.territorio_id = null;
  if (!data.responsavel_usuario_id) data.responsavel_usuario_id = null;
  try {
    await api(`/demandas/${state.editingDemandId}`, { method: "PUT", body: JSON.stringify(data) });
    state.editingDemandId = null;
    form.reset();
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
    const endpoint = state.editingUserId ? `/usuarios/${state.editingUserId}` : "/usuarios";
    const method = state.editingUserId ? "PUT" : "POST";
    await api(endpoint, { method, body: JSON.stringify(data) });
    state.editingUserId = null;
    form.reset();
    $("#user-submit").textContent = "Salvar colaborador";
    setMessage("#user-message", method === "POST" ? "Colaborador salvo. Senha inicial: Senha@123." : "Colaborador atualizado.");
    await loadData();
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
  const demand = selectedDemand();
  if (!demand) {
    $("#ai-output").textContent = "Nenhuma demanda disponivel.";
    return;
  }
  const payload = await api("/ai/resumir-contexto", {
    method: "POST",
    body: JSON.stringify({ contexto_tipo: "demanda", contexto_id: demand.id }),
  });
  $("#ai-output").textContent = payload.data.resumo;
}

async function suggestNextStep() {
  const demand = selectedDemand();
  if (!demand) {
    $("#ai-output").textContent = "Nenhuma demanda disponivel.";
    return;
  }
  const payload = await api("/ai/sugerir-proxima-etapa", {
    method: "POST",
    body: JSON.stringify({ contexto_tipo: "demanda", contexto_id: demand.id }),
  });
  $("#ai-output").textContent = `${payload.data.sugestao} ${payload.data.justificativa}`;
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
  $$(".module-nav button").forEach((item) => item.classList.toggle("active", item.dataset.section === sectionId));
  $$(".module").forEach((item) => item.classList.toggle("active", item.id === sectionId));
  const button = $(`.module-nav button[data-section="${sectionId}"]`);
  if (button) $(".topbar h1").textContent = button.textContent;
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
  $$(".module-nav button").forEach((button) => {
    button.addEventListener("click", () => navigateTo(button.dataset.section));
  });
  $("#crm-contact-select").addEventListener("change", (event) => {
    state.selectedContactId = event.currentTarget.value;
    renderCRM();
  });
  $$("[data-cadastro-tab]").forEach((button) => {
    button.addEventListener("click", () => navigateCadastroTab(button.dataset.cadastroTab));
  });
}

function bindEvents() {
  $("#login-form").addEventListener("submit", login);
  $("#contact-form").addEventListener("submit", createContact);
  $("#public-body-form").addEventListener("submit", createPublicBody);
  $("#interaction-form").addEventListener("submit", createInteraction);
  $("#demand-form").addEventListener("submit", createDemand);
  $("#demand-edit-form").addEventListener("submit", saveDemandEdit);
  $("#user-form").addEventListener("submit", createUser);
  $("#agenda-form").addEventListener("submit", createAgenda);
  $("#agenda-report-form").addEventListener("submit", saveAgendaReport);
  $("#proposition-form").addEventListener("submit", createProposition);
  $("#amendment-form").addEventListener("submit", createAmendment);
  $("#office-form").addEventListener("submit", createOffice);
  $("#refresh").addEventListener("click", loadData);
  $("#ai-first-demand").addEventListener("click", summarizeFirstDemand);
  $("#ai-summarize").addEventListener("click", summarizeFirstDemand);
  $("#ai-suggest").addEventListener("click", suggestNextStep);
  $("#sync-form").addEventListener("submit", syncCadastro);
  $("#global-search").addEventListener("input", (event) => {
    state.globalSearch = event.currentTarget.value;
    renderDemands();
    renderContacts();
    renderSearchResults();
  });
  $("#cancel-demand-edit").addEventListener("click", () => {
    state.editingDemandId = null;
    $("#demand-edit-form").reset();
    $("#demand-edit-form").classList.add("hidden");
  });
  $("#sidebar-toggle")?.addEventListener("click", toggleSidebar);
  $("#sidebar-overlay")?.addEventListener("click", closeSidebar);
  window.addEventListener("resize", () => {
    if (!isCompactSidebar()) closeSidebar();
  });
  $("#logout").addEventListener("click", () => {
    state.token = null;
    localStorage.removeItem("gabinete_token");
    showLogin();
  });
  bindNavigation();
}

bindEvents();

if (state.token) {
  showApp();
  loadData().catch(() => {
    localStorage.removeItem("gabinete_token");
    showLogin();
  });
}
