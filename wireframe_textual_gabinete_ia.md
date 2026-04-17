# Wireframe textual completo — GESTÃO DE MANDATOS / GABINETE IA

## 1. Objetivo deste documento

Transformar a especificação funcional do **GABINETE IA** em uma visão textual de telas, navegação e fluxos de uso, servindo como base para:
- UX/UI
- backlog técnico
- arquitetura de frontend
- definição de APIs
- homologação funcional

Este documento trata o sistema como **produto independente**, separado do REVISA.

---

# 2. Princípios de navegação

## 2.1 Estrutura geral
O sistema terá dois grandes módulos:

1. **APP MOBILE CLIENTE**
2. **SISTEMA GABINETE WEB**

## 2.2 Padrão visual do web
- **Menu superior** = domínio principal
- **Menu lateral** = subtelas do domínio selecionado
- **Área central** = conteúdo de trabalho
- **Painel direito opcional** = histórico, alertas, IA assistiva, detalhes rápidos

## 2.3 Padrão visual do mobile
- Navegação simplificada
- Botão de ação principal em destaque
- Operação offline-first
- Sincronização visível
- Formulários curtos, em etapas

## 2.4 Perfis contemplados
- Colaborador Externo
- Supervisor de Equipe
- Assessor Nível I
- Assessor Jurídico
- Assessor Administrativo
- Chefe de Gabinete
- Vereador

## 2.5 Padrões transversais
- Busca global no topo do sistema web
- Centro de notificações
- Histórico de ações em registros sensíveis
- Widget de IA assistiva com sugestões revisáveis
- Filtros persistidos por usuário
- Badges de status com cores padronizadas

---

# 3. Mapa geral de navegação

## 3.1 APP MOBILE CLIENTE
- Login
- Home de Campo
- Novo Contato/Cidadão
- Nova Demanda
- Nova Visita
- Agenda do Dia
- Meus Registros
- Sincronização
- Perfil

## 3.2 SISTEMA GABINETE WEB
### Menu superior
- Executivo
- Cadastros
- Atendimento
- Agenda
- Jurídico
- Administrativo
- Projetos
- Territorial
- Relatórios
- Administração

### Assistente transversal
- Painel IA Assistiva
- Notificações
- Busca Global

---

# 4. APP MOBILE CLIENTE

# MOB-01 — Login
**Perfis:** Colaborador Externo, Supervisor de Equipe, Assessor Nível I autorizado para campo

```text
┌───────────────────────────────┐
│ GABINETE IA                   │
│ Acesso Mobile                 │
├───────────────────────────────┤
│ Login                         │
│ [__________________________]  │
│ Senha                         │
│ [__________________________]  │
│                               │
│ [ Entrar ]                    │
│ Recuperar acesso              │
│ Status: Online / Offline      │
└───────────────────────────────┘
```

## Objetivo
Autenticar usuários de campo com acesso restrito ao módulo mobile.

## Ações principais
- entrar
- recuperar acesso

## Observações de UX
- login simples
- aviso de conectividade
- manter sessão segura em dispositivo autorizado

---

# MOB-02 — Home de Campo
**Perfis:** Colaborador Externo, Supervisor

```text
┌──────────────────────────────────────┐
│ Olá, [Nome]                          │
│ Hoje: 6 tarefas / 2 visitas / 3 pend │
│ Conexão: Online / Offline            │
├──────────────────────────────────────┤
│ [ Novo Contato ]                     │
│ [ Nova Demanda ]                     │
│ [ Nova Visita ]                      │
├──────────────────────────────────────┤
│ Agenda do dia                        │
│ - 09:00 Visita Bairro X              │
│ - 11:00 Reunião Liderança            │
├──────────────────────────────────────┤
│ Registros recentes                   │
│ - João Pereira [Sincronizado]        │
│ - Maria Silva [Pendente]             │
│ - Demanda Rua Y [Erro]               │
├──────────────────────────────────────┤
│ [ Ir para sincronização ]            │
└──────────────────────────────────────┘
```

## Objetivo
Ser o centro operacional do trabalho de rua.

## Elementos centrais
- resumo do dia
- CTA rápido
- agenda
- registros recentes
- status de sincronização

---

# MOB-03 — Novo Contato / Cidadão
**Perfis:** Colaborador Externo, Supervisor, Assessor Nível I em campo

```text
┌────────────────────────────────────────────┐
│ Novo Contato / Cidadão                     │
├────────────────────────────────────────────┤
│ Nome completo*                             │
│ [______________________________________]   │
│ Telefone                                   │
│ [______________]                           │
│ E-mail                                     │
│ [______________________________________]   │
│ CPF                                        │
│ [______________]                           │
│ Endereço / Bairro / Cidade                 │
│ [______________________________________]   │
│ Território                                 │
│ [ Região ▼ ] [ Bairro ▼ ] [ Microárea ▼ ]  │
│ Tipo de contato                            │
│ [ cidadão ▼ ]                              │
│ Observações                                │
│ [______________________________________]   │
├────────────────────────────────────────────┤
│ [ Salvar rascunho ] [ Avançar ]            │
└────────────────────────────────────────────┘
```

## Objetivo
Registrar novo cidadão/contato de forma simples.

## Campos centrais
- nome
- telefone
- e-mail
- CPF opcional
- endereço
- território
- tipo de contato
- observações

## Regras visuais
- território em selects encadeados
- alerta de possível duplicidade por nome/telefone/CPF

---

# MOB-04 — Consentimento e Canais de Contato
**Perfis:** Colaborador Externo, Supervisor

```text
┌────────────────────────────────────────────┐
│ Consentimento e Contato                    │
├────────────────────────────────────────────┤
│ Canal permitido                            │
│ [x] Telefone   [x] WhatsApp   [ ] E-mail   │
│ Finalidade                                 │
│ [ atendimento institucional ▼ ]            │
│ Consentimento registrado?*                 │
│ ( ) Sim   ( ) Não                          │
│ Forma do registro                          │
│ [ verbal ▼ ]                               │
│ Observação                                 │
│ [______________________________________]   │
├────────────────────────────────────────────┤
│ [ Voltar ] [ Salvar ] [ Avançar ]          │
└────────────────────────────────────────────┘
```

## Objetivo
Registrar base de contato e finalidade de uso.

## Observação funcional
Sem consentimento, o contato pode existir com restrições de uso conforme política definida pelo gabinete.

---

# MOB-05 — Nova Demanda
**Perfis:** Colaborador Externo, Supervisor, Assessor Nível I

```text
┌────────────────────────────────────────────┐
│ Nova Demanda                               │
├────────────────────────────────────────────┤
│ Vincular a                                 │
│ [ Contato já cadastrado ▼ ]                │
│ Título*                                    │
│ [______________________________________]   │
│ Categoria*                                 │
│ [ saúde / urbana / social / jurídica ▼ ]   │
│ Prioridade inicial                         │
│ [ média ▼ ]                                │
│ Território                                 │
│ [ Bairro ▼ ]                               │
│ Descrição*                                 │
│ [______________________________________]   │
│ Anexo opcional                             │
│ [ adicionar foto/arquivo ]                 │
├────────────────────────────────────────────┤
│ [ Salvar rascunho ] [ Enviar ]             │
└────────────────────────────────────────────┘
```

## Objetivo
Abrir atendimento institucional a partir do campo.

## Observações
- prioridade inicial pode ser ajustada internamente depois
- entrada gera item em fila de triagem

---

# MOB-06 — Nova Visita / Atividade de Campo
**Perfis:** Colaborador Externo, Supervisor

```text
┌────────────────────────────────────────────┐
│ Nova Visita                                │
├────────────────────────────────────────────┤
│ Tipo                                       │
│ [ visita domiciliar ▼ ]                    │
│ Data/Hora                                  │
│ [__/__/____ __:__]                         │
│ Território                                 │
│ [ Região ▼ ] [ Bairro ▼ ]                  │
│ Vincular contato                           │
│ [ buscar contato ________ ]                │
│ Resultado                                  │
│ [ realizada ▼ ]                            │
│ Observação                                 │
│ [______________________________________]   │
│ Evidência                                  │
│ [ foto / arquivo ]                         │
├────────────────────────────────────────────┤
│ [ Salvar ] [ Salvar e nova ]               │
└────────────────────────────────────────────┘
```

## Objetivo
Registrar atuação territorial e histórico de campo.

---

# MOB-07 — Agenda do Dia
**Perfis:** Colaborador Externo, Supervisor

```text
┌────────────────────────────────────────────┐
│ Agenda do Dia                              │
├────────────────────────────────────────────┤
│ [ Hoje ] [ Amanhã ] [ Semana ]             │
├────────────────────────────────────────────┤
│ 09:00 - Visita Bairro São João             │
│ 10:30 - Reunião com associação             │
│ 14:00 - Retorno de demanda                 │
│ 16:00 - Evento local                       │
├────────────────────────────────────────────┤
│ [ Ver detalhes ] [ Marcar realizado ]      │
└────────────────────────────────────────────┘
```

## Objetivo
Exibir compromissos e visitas do dia.

---

# MOB-08 — Meus Registros
**Perfis:** Colaborador Externo, Supervisor

```text
┌────────────────────────────────────────────┐
│ Meus Registros                             │
├────────────────────────────────────────────┤
│ Tipo [ todos ▼ ] Status [▼] Período [▼]    │
├────────────────────────────────────────────┤
│ João Pereira      [Contato] [Sync]         │
│ Demanda Rua X     [Demanda] [Pendente]     │
│ Visita Bairro Y   [Visita] [Erro]          │
├────────────────────────────────────────────┤
│ [ Abrir ] [ Editar ] [ Reenviar ]          │
└────────────────────────────────────────────┘
```

## Objetivo
Permitir consulta e manutenção de registros próprios.

---

# MOB-09 — Sincronização
**Perfis:** Colaborador Externo, Supervisor

```text
┌────────────────────────────────────────────┐
│ Sincronização                              │
├────────────────────────────────────────────┤
│ [Pendentes] [Enviados] [Com erro]          │
├────────────────────────────────────────────┤
│ Maria Silva      [Contato] [Pendente]      │
│ Demanda Rua Z    [Demanda] [Erro]          │
│ Visita Centro    [Visita]  [Enviado]       │
├────────────────────────────────────────────┤
│ Motivo do erro: registro duplicado         │
├────────────────────────────────────────────┤
│ [ Sincronizar tudo ] [ Reenviar item ]     │
└────────────────────────────────────────────┘
```

## Objetivo
Controlar envio seguro da produção de campo.

---

# 5. SISTEMA GABINETE WEB

# 5.1 Estrutura padrão do web

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Logo | Busca global | Notificações | IA Assistiva | Usuário                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ Menu superior: Executivo | Cadastros | Atendimento | Agenda | Jurídico ...  │
├───────────────┬────────────────────────────────────────────┬─────────────────┤
│ Menu lateral  │ Área principal                              │ Painel direito  │
│ contextual    │                                             │ opcional        │
└───────────────┴────────────────────────────────────────────┴─────────────────┘
```

---

# 6. EXECUTIVO

# WEB-EXE-01 — Dashboard Geral
**Perfis:** Chefe de Gabinete, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Geral                                                         │
│ Período [ mês atual ▼ ] Território [ todos ▼ ] [ Aplicar ]             │
├──────────────────────────────────────────────────────────────────────────┤
│ Demandas abertas | SLA vencido | Projetos críticos | Protocolos pend.  │
│ Agenda do dia   | Atividade de campo | Jurídico em revisão             │
├──────────────────────────────────────────────────────────────────────────┤
│ [Gráfico demandas por status]   [Gráfico atendimentos por período]      │
├──────────────────────────────────────────────────────────────────────────┤
│ Prioridades do dia                                                     │
│ - Demanda crítica bairro X                                             │
│ - Parecer pendente                                                     │
│ - Evento às 18h                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: alertas + IA                                           │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Dar visão executiva consolidada da operação do gabinete.

---

# WEB-EXE-02 — Demandas Críticas
**Perfis:** Chefe de Gabinete, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Demandas Críticas                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Filtros: território | categoria | responsável | prazo                  │
├──────────────────────────────────────────────────────────────────────────┤
│ Título | Território | Responsável | Prazo | Status | Prioridade        │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Detalhe lateral: histórico / anexos / ação rápida                       │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Permitir acompanhamento rápido de itens críticos.

---

# WEB-EXE-03 — Agenda Estratégica
**Perfis:** Chefe de Gabinete, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Agenda Estratégica                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Hoje ] [ Semana ] [ Mês ]                                             │
│ Tipo [ todos ▼ ]                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ 09:00 Reunião institucional                                             │
│ 11:30 Atendimento liderança                                             │
│ 15:00 Sessão / protocolo                                                │
│ 19:00 Evento territorial                                                │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: prioridade / contexto / participantes                   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-EXE-04 — Projetos Prioritários
**Perfis:** Chefe de Gabinete, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Projetos Prioritários                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Projeto | Dono | Fase | Risco | Próximo marco | Status                 │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Cards: atrasados / em risco / concluídos / próximos marcos              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 7. CADASTROS

# WEB-CAD-01 — Lista de Cidadãos / Contatos
**Perfis:** Assessor Nível I, Chefe de Gabinete, Supervisor, Administrativo

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Cidadãos / Contatos                                    [ Novo Cadastro ]│
├──────────────────────────────────────────────────────────────────────────┤
│ Busca [________________] Tipo [▼] Território [▼] Status [▼] [Filtrar]  │
├──────────────────────────────────────────────────────────────────────────┤
│ Nome | Telefone | Território | Status | Último atendimento | Ações      │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: duplicidades suspeitas / histórico resumido             │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Centralizar a base institucional de cidadãos e contatos.

---

# WEB-CAD-02 — Ficha do Cidadão / Contato
**Perfis:** Assessor Nível I, Chefe, Supervisor, Jurídico em leitura quando necessário

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Ficha do Cidadão / Contato                                              │
├──────────────────────────────────────────────────────────────────────────┤
│ Aba Dados Gerais | Contatos | Consentimento | Demandas | Agenda | Docs  │
├──────────────────────────────────────────────────────────────────────────┤
│ Nome / Telefones / E-mail / Endereço / Território / Observações         │
│ Status: ATIVO                                                           │
├──────────────────────────────────────────────────────────────────────────┤
│ Ações: [ Editar ] [ Nova demanda ] [ Novo compromisso ] [ Histórico ]   │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Apresentar visão 360 institucional do contato.

---

# WEB-CAD-03 — Organizações e Lideranças
**Perfis:** Assessor Nível I, Chefe, Supervisor

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Organizações e Lideranças                         [ Novo registro ]      │
├──────────────────────────────────────────────────────────────────────────┤
│ Nome | Tipo | Território | Responsável | Status | Ações                 │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Cadastrar associações, grupos, referências institucionais e atores territoriais.

---

# WEB-CAD-04 — Territórios
**Perfis:** Chefe de Gabinete, Administrativo

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Territórios                                                             │
├──────────────────────────────────────────────────────────────────────────┤
│ Região [ lista ]                                                        │
│  └─ Bairro                                                              │
│      └─ Microárea                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Nova região ] [ Novo bairro ] [ Nova microárea ]                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Manter a hierarquia territorial do gabinete.

---

# 8. ATENDIMENTO

# WEB-ATD-01 — Fila de Demandas
**Perfis:** Assessor Nível I, Supervisor, Chefe, Jurídico/Admin conforme filtro

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Fila de Demandas                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ Busca [____] Status [▼] Categoria [▼] Prioridade [▼] SLA [▼] [Filtrar] │
├──────────────────────────────────────────────────────────────────────────┤
│ Título | Cidadão | Território | Responsável | SLA | Status | Ações      │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: resumo da fila / IA sugere priorização                  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Controlar toda a fila operacional de atendimento.

---

# WEB-ATD-02 — Detalhe da Demanda
**Perfis:** Assessor Nível I, Chefe, Supervisor, Jurídico/Admin quando atribuídos

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Demanda: Título da demanda                                              │
│ Status [ EM_ATENDIMENTO ▼ ] Prioridade [ ALTA ▼ ]                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Aba Resumo | Histórico | Encaminhamentos | Anexos | Agenda vinculada    │
├──────────────────────────────────────────────────────────────────────────┤
│ Cidadão / território / categoria / descrição / prazo / responsável      │
├──────────────────────────────────────────────────────────────────────────┤
│ Ações: [ Assumir ] [ Encaminhar ] [ Atualizar ] [ Concluir ] [ Reabrir ]│
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: IA resume histórico e sugere próxima etapa              │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Ser a tela central do ciclo de vida da demanda.

---

# WEB-ATD-03 — Triagem / Distribuição
**Perfis:** Supervisor, Chefe de Gabinete

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Triagem e Distribuição                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│ Demandas sem responsável                                                │
│ Título | Categoria | Território | Prioridade sugerida | Atribuir        │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Responsáveis disponíveis                                                 │
│ Nome | Carga atual | Área | Status                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Atribuir ] [ Repriorizar ] [ Encaminhar ao jurídico ]                 │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Distribuir a carga de trabalho com controle.

---

# WEB-ATD-04 — Encaminhamentos
**Perfis:** Assessor Nível I, Jurídico, Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Encaminhamentos                                                         │
├──────────────────────────────────────────────────────────────────────────┤
│ Tipo [ interno / jurídico / administrativo ] [ Novo encaminhamento ]    │
├──────────────────────────────────────────────────────────────────────────┤
│ Demanda | Destino | Responsável | Data | Status | Ações                 │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ATD-05 — Histórico de Atendimento
**Perfis:** Assessor Nível I, Chefe, Jurídico/Admin quando aplicável

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Histórico de Atendimento                                                │
├──────────────────────────────────────────────────────────────────────────┤
│ Linha do tempo                                                          │
│ - Demanda aberta                                                        │
│ - Atribuída a assessor X                                                │
│ - Encaminhada ao jurídico                                               │
│ - Documento anexado                                                     │
│ - Concluída                                                             │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Oferecer rastreabilidade completa da demanda.

---

# 9. AGENDA

# WEB-AGD-01 — Calendário Geral
**Perfis:** Assessor Nível I, Administrativo, Chefe, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Calendário Geral                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Dia ] [ Semana ] [ Mês ] Tipo [▼] Responsável [▼] Território [▼]     │
├──────────────────────────────────────────────────────────────────────────┤
│ Calendário central                                                      │
│ Eventos coloridos por tipo/status                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel lateral: próximos eventos / conflitos / lembretes                │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Centralizar a agenda do gabinete e do vereador.

---

# WEB-AGD-02 — Novo Compromisso / Evento
**Perfis:** Assessor Nível I, Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Novo Compromisso                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ Título*                                                                 │
│ [____________________________________________________________]          │
│ Tipo* [ institucional ▼ ] Status [ planejado ▼ ]                        │
│ Data/Hora início [____] fim [____]                                      │
│ Local / território                                                      │
│ Participantes                                                           │
│ [ adicionar participante ]                                              │
│ Observações                                                             │
│ [____________________________________________________________]          │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Salvar ] [ Salvar e notificar ]                                       │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-AGD-03 — Agenda do Vereador
**Perfis:** Vereador, Chefe, Administrativo

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Agenda do Vereador                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ Compromissos do dia / semana / mês                                      │
│ Cards com horário, tipo, local, participantes, contexto                 │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: briefing resumido por compromisso                       │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Dar uma visão limpa e priorizada da agenda estratégica.

---

# WEB-AGD-04 — Visitas de Campo
**Perfis:** Supervisor, Assessor Nível I, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Visitas de Campo                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ Período [▼] Equipe [▼] Território [▼] Resultado [▼] [Filtrar]          │
├──────────────────────────────────────────────────────────────────────────┤
│ Colaborador | Data | Território | Tipo | Resultado | Ações             │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 10. JURÍDICO

# WEB-JUR-01 — Dashboard Jurídico
**Perfis:** Assessor Jurídico, Chefe, Vereador em leitura resumida

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Jurídico                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ Pareceres em elaboração | Em revisão | Protocolados | Prazos críticos   │
├──────────────────────────────────────────────────────────────────────────┤
│ Lista de pendências                                                     │
│ - Parecer demanda X                                                     │
│ - Requerimento Y em revisão                                             │
│ - Ofício Z aguardando protocolo                                         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-JUR-02 — Lista de Documentos Jurídicos
**Perfis:** Assessor Jurídico, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Documentos Jurídicos                                 [ Novo documento ] │
├──────────────────────────────────────────────────────────────────────────┤
│ Tipo [ parecer / ofício / requerimento ▼ ] Status [▼] [Filtrar]        │
├──────────────────────────────────────────────────────────────────────────┤
│ Título | Tipo | Demanda vinculada | Versão | Status | Autor | Ações     │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-JUR-03 — Editor de Parecer
**Perfis:** Assessor Jurídico, Chefe em revisão

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Editor de Parecer                                                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Título*                                                                 │
│ Demanda vinculada [▼]                                                   │
│ Status [ EM_ELABORACAO ▼ ]                                              │
├──────────────────────────────────────────────────────────────────────────┤
│ Editor textual                                                          │
│ [ conteúdo do parecer ______________________________________________ ]  │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: histórico de versões / IA resume anexos                 │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Salvar rascunho ] [ Nova versão ] [ Enviar revisão ]                  │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Produzir parecer jurídico versionável.

---

# WEB-JUR-04 — Requerimentos
**Perfis:** Assessor Jurídico, Assessor Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Requerimentos                                      [ Novo requerimento ]│
├──────────────────────────────────────────────────────────────────────────┤
│ Número | Tema | Status | Responsável | Protocolo | Ações                │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-JUR-05 — Ofícios
**Perfis:** Assessor Jurídico, Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Ofícios                                                  [ Novo ofício ]│
├──────────────────────────────────────────────────────────────────────────┤
│ Destinatário | Tema | Status | Data | Protocolo | Ações                │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-JUR-06 — Arquivo Jurídico / Versões
**Perfis:** Jurídico, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Arquivo Jurídico                                                        │
├──────────────────────────────────────────────────────────────────────────┤
│ Busca [_____________] Tipo [▼] Status [▼] Período [▼] [Filtrar]        │
├──────────────────────────────────────────────────────────────────────────┤
│ Documento | Tipo | Versão atual | Situação | Relacionado a | Ações      │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: histórico de versões / anexos / protocolo               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 11. ADMINISTRATIVO

# WEB-ADM-01 — Protocolos
**Perfis:** Assessor Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Protocolos                                             [ Novo protocolo ]│
├──────────────────────────────────────────────────────────────────────────┤
│ Número | Tipo | Responsável | Prazo | Status | Relacionado a | Ações    │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ADM-02 — Detalhe do Protocolo
**Perfis:** Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Protocolo #2026-001                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Aba Resumo | Rito | Prazos | Checklist | Despachos | Anexos             │
├──────────────────────────────────────────────────────────────────────────┤
│ Tipo / origem / responsável / data / vínculo documental                 │
├──────────────────────────────────────────────────────────────────────────┤
│ Ações: [ Atualizar status ] [ Adicionar despacho ] [ Concluir ]         │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ADM-03 — Tarefas e Checklists
**Perfis:** Administrativo, Assessor Nível I, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Tarefas e Checklists                                 [ Nova tarefa ]    │
├──────────────────────────────────────────────────────────────────────────┤
│ Responsável [▼] Status [▼] Prazo [▼] Tipo [▼] [Filtrar]                │
├──────────────────────────────────────────────────────────────────────────┤
│ Tarefa | Responsável | Prazo | Prioridade | Status | Ações             │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Checklist lateral do item selecionado                                   │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ADM-04 — Ritos e Prazos
**Perfis:** Administrativo, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Ritos e Prazos                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Tipo de rito | Etapa atual | Prazo limite | Alerta | Situação           │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 12. PROJETOS

# WEB-PRO-01 — Lista de Projetos
**Perfis:** Chefe, Assessor Nível I, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Projetos do Mandato                                  [ Novo projeto ]   │
├──────────────────────────────────────────────────────────────────────────┤
│ Projeto | Dono | Fase | Início | Fim previsto | Risco | Status | Ações │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-PRO-02 — Detalhe do Projeto
**Perfis:** Chefe, Assessor Nível I, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Projeto: Nome do projeto                                                │
├──────────────────────────────────────────────────────────────────────────┤
│ Aba Resumo | Etapas | Entregáveis | Indicadores | Riscos | Equipe       │
├──────────────────────────────────────────────────────────────────────────┤
│ Descrição / dono / território / status / datas                          │
├──────────────────────────────────────────────────────────────────────────┤
│ Ações: [ Editar ] [ Nova etapa ] [ Novo entregável ] [ Registrar risco ]│
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-PRO-03 — Board de Etapas
**Perfis:** Chefe, Assessor Nível I

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Board de Etapas                                                         │
├──────────────────────────────────────────────────────────────────────────┤
│ Planejado | Em andamento | Bloqueado | Concluído                        │
│ [ cartão etapa ] [ cartão etapa ] [ cartão etapa ]                      │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-PRO-04 — Indicadores de Projeto
**Perfis:** Chefe, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Indicadores do Projeto                                                  │
├──────────────────────────────────────────────────────────────────────────┤
│ Meta | Realizado | Tendência | Próximo marco                            │
│ Gráficos e cards                                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 13. TERRITORIAL

# WEB-TER-01 — Dashboard Territorial
**Perfis:** Chefe, Supervisor, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Dashboard Territorial                                                   │
│ Período [▼] Região [▼] Bairro [▼] [Aplicar]                            │
├──────────────────────────────────────────────────────────────────────────┤
│ Demandas | Visitas | Cobertura de equipe | Temas recorrentes            │
├──────────────────────────────────────────────────────────────────────────┤
│ [Mapa agregado]                                                         │
├──────────────────────────────────────────────────────────────────────────┤
│ [Gráfico temas por território] [Evolução temporal]                      │
└──────────────────────────────────────────────────────────────────────────┘
```

## Objetivo
Consolidar visão geográfica agregada da atuação do gabinete.

---

# WEB-TER-02 — Cobertura de Equipes
**Perfis:** Supervisor, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Cobertura de Equipes                                                    │
├──────────────────────────────────────────────────────────────────────────┤
│ Equipe [▼] Período [▼] Território [▼]                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Colaborador | Visitas | Registros | Demandas abertas | Área coberta     │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-TER-03 — Eventos Territoriais
**Perfis:** Supervisor, Assessor Nível I, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Eventos Territoriais                                [ Novo evento ]     │
├──────────────────────────────────────────────────────────────────────────┤
│ Tipo | Território | Data | Equipe | Público estimado | Ações            │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-TER-04 — Tendências Agregadas
**Perfis:** Chefe, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Tendências Agregadas                                                    │
├──────────────────────────────────────────────────────────────────────────┤
│ Tema | Territórios recorrentes | Evolução | Volume | Observação         │
│ ...                                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Painel direito: IA resume padrões agregados                             │
└──────────────────────────────────────────────────────────────────────────┘
```

## Observação ética
A leitura é agregada por território e tema, sem perfilamento individual sensível.

---

# 14. RELATÓRIOS

# WEB-REL-01 — Central de Relatórios
**Perfis:** todos os perfis autorizados, com catálogo filtrado por permissão

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Central de Relatórios                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Categoria [ operacional ▼ ] Perfil [ auto ] Período [▼] [Filtrar]      │
├──────────────────────────────────────────────────────────────────────────┤
│ Relatórios disponíveis                                                  │
│ - Demandas por status                                                   │
│ - Agenda consolidada                                                    │
│ - Pareceres por período                                                 │
│ - Protocolos vencidos                                                   │
│ - Cobertura territorial                                                 │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Gerar ] [ Exportar PDF ] [ Exportar Excel ]                           │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-REL-02 — Relatório Operacional
**Perfis:** Assessor Nível I, Supervisor, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Relatório Operacional                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Filtros: período / responsável / território / categoria                 │
├──────────────────────────────────────────────────────────────────────────┤
│ Cards + tabela + gráfico                                                │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-REL-03 — Relatório Jurídico
**Perfis:** Jurídico, Chefe

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Relatório Jurídico                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ Filtros: tipo documento / período / status / autor                      │
├──────────────────────────────────────────────────────────────────────────┤
│ Tabela + resumo por status                                              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-REL-04 — Relatório Territorial
**Perfis:** Supervisor, Chefe, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Relatório Territorial                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Filtros: período / região / bairro / tema                               │
├──────────────────────────────────────────────────────────────────────────┤
│ Mapa agregado + gráfico + tabela                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-REL-05 — Relatório Executivo
**Perfis:** Chefe, Vereador

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Relatório Executivo                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Filtros: período / eixos / prioridade estratégica                       │
├──────────────────────────────────────────────────────────────────────────┤
│ Cards executivos + tendências + projetos críticos + agenda              │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 15. ADMINISTRAÇÃO

# WEB-ADMN-01 — Usuários
**Perfis:** Chefe de Gabinete

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Usuários                                              [ Novo usuário ]  │
├──────────────────────────────────────────────────────────────────────────┤
│ Nome | Perfil | Escopo | Status | Último acesso | Ações                │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ADMN-02 — Novo Usuário / Edição
**Perfis:** Chefe de Gabinete

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Cadastro de Usuário                                                     │
├──────────────────────────────────────────────────────────────────────────┤
│ Nome*                                                                   │
│ E-mail login*                                                           │
│ Perfil* [▼]                                                             │
│ Escopo territorial [▼]                                                  │
│ Escopo de equipe [▼]                                                    │
│ Ativo [toggle]                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Salvar ] [ Redefinir senha ]                                          │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ADMN-03 — Parâmetros do Sistema
**Perfis:** Chefe de Gabinete

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Parâmetros do Sistema                                                   │
├──────────────────────────────────────────────────────────────────────────┤
│ Abas: categorias | prioridades | tipos de agenda | tipos de documento   │
│ territórios | SLA | notificações                                        │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# WEB-ADMN-04 — Auditoria
**Perfis:** Chefe de Gabinete

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Auditoria                                                               │
├──────────────────────────────────────────────────────────────────────────┤
│ Período [▼] Usuário [▼] Entidade [▼] Ação [▼] [Filtrar]                │
├──────────────────────────────────────────────────────────────────────────┤
│ Data | Usuário | Entidade | Ação | Registro | Detalhes                  │
│ ...                                                                     │
└──────────────────────────────────────────────────────────────────────────┘
```

---

# 16. IA ASSISTIVA

## 16.1 Posição no produto
A IA não precisa ser um menu principal isolado no MVP. Ela pode existir como:
- painel lateral contextual
- central de insights
- sugestões dentro de demanda, agenda, jurídico e relatórios

# WEB-IA-01 — Painel IA Assistiva
**Perfis:** Assessor Nível I, Jurídico, Administrativo, Chefe, Vereador com escopo executivo

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ IA Assistiva                                                            │
├──────────────────────────────────────────────────────────────────────────┤
│ Sugestões do contexto atual                                             │
│ - Resumo automático                                                     │
│ - Próxima etapa sugerida                                                │
│ - Alertas de prazo                                                      │
│ - Temas correlatos                                                      │
├──────────────────────────────────────────────────────────────────────────┤
│ [ Aplicar manualmente ] [ Copiar ] [ Ignorar ]                          │
└──────────────────────────────────────────────────────────────────────────┘
```

## Casos de uso visuais
- em uma demanda: resumir histórico
- em um parecer: sugerir minuta base
- em um relatório: resumir pontos críticos
- em projetos: destacar risco de atraso
- no territorial: resumir temas agregados

---

# 17. Wireframes por perfil

# 17.1 Colaborador Externo
## Enxerga no mobile
- Login
- Home de Campo
- Novo Contato
- Consentimento
- Nova Demanda
- Nova Visita
- Agenda do Dia
- Meus Registros
- Sincronização

## Não enxerga
- dashboards estratégicos
- jurídico
- administração
- relatórios executivos

---

# 17.2 Supervisor de Equipe
## Enxerga no mobile
- tudo do colaborador externo
- visão resumida da equipe

## Enxerga no web
- Atendimento
- Agenda
- Territorial (cobertura)
- Relatórios operacionais da equipe

---

# 17.3 Assessor Nível I
## Enxerga no web
- Cadastros
- Atendimento
- Agenda
- Projetos
- Relatórios operacionais

## Não enxerga por padrão
- administração de usuários
- auditoria geral

---

# 17.4 Assessor Jurídico
## Enxerga no web
- Jurídico
- Atendimento em itens atribuídos
- Relatórios jurídicos
- consulta a cadastros quando necessário

---

# 17.5 Assessor Administrativo
## Enxerga no web
- Agenda
- Administrativo
- Protocolos
- Relatórios administrativos
- leitura de atendimento correlato

---

# 17.6 Chefe de Gabinete
## Enxerga no web
- todos os módulos
- dashboards executivos
- administração
- auditoria
- parâmetros
- territorial agregado
- projetos completos

---

# 17.7 Vereador
## Enxerga no web
- Executivo
- Agenda consolidada
- Projetos prioritários
- Territorial agregado
- Relatórios executivos
- insights assistivos

## Não enxerga por padrão
- manutenção operacional completa
- edição massiva de registros
- administração de usuários
- auditoria detalhada

---

# 18. Componentes transversais recomendados

## Busca global
Permite procurar:
- cidadão
- demanda
- projeto
- ofício
- parecer
- protocolo
- evento de agenda

## Centro de notificações
Tipos:
- prazo vencendo
- demanda crítica
- documento em revisão
- evento próximo
- tarefa bloqueada

## Painel lateral contextual
Usos:
- histórico
- resumo IA
- anexos rápidos
- tarefas relacionadas
- participantes

## Breadcrumb
Importante para módulos profundos como Jurídico e Administrativo.

---

# 19. Fluxo visual recomendado de MVP

## Ordem de construção sugerida do ponto de vista de UX
1. Mobile Login + Home + Novo Contato + Nova Demanda + Sync
2. Web Cadastros + Fila de Demandas + Detalhe da Demanda
3. Agenda Geral + Agenda do Vereador
4. Usuários + Perfis + Parâmetros
5. Territorial agregado
6. Jurídico
7. Administrativo
8. Projetos
9. Relatórios
10. IA assistiva contextual

---

# 20. Observações finais de UX

## Simplicidade operacional
O risco deste sistema é ficar “pesado” demais. Por isso:
- perfis de campo devem ver pouco e agir rápido
- vereador deve ver pouco e decidir rápido
- chefe deve ter profundidade sem perder visão macro
- jurídico e administrativo devem ter organização por fila e documento

## Separação clara entre perfis
As telas não devem tentar servir a todos ao mesmo tempo.
O sistema precisa mudar de profundidade conforme perfil.

## Uso de IA
IA deve aparecer como **assistente**, não como protagonista da decisão.
Ela sugere, resume e alerta. O humano decide.

---

# 21. Próximo passo natural

A continuação ideal deste material é transformar cada tela em **backlog técnico por tela**, separado em:
- frontend
- backend
- banco
- validações
- testes de aceite

Isso já permitirá quebrar o projeto em épicos e sprints de implementação.

