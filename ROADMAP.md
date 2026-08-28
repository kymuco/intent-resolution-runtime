# Intent Resolution Runtime Roadmap

## M0 execution decision

For implementation history, **M0.1 through M0.10 are ten separate pull requests**. The later four-PR packaging suggestion preserved in the original planning record below is superseded by this decision. The substantive M0 plan itself is preserved verbatim, except for ChatGPT-internal citation markers that have no meaning in GitHub.

---

Да. Сейчас репозиторий в идеальном стартовом состоянии: в `main` только **Apache-2.0 LICENSE**, никакой случайной ранней архитектуры ещё нет. Лицензия действительно Apache License 2.0.

Я бы сделал **M0 полностью charter-first и без runtime-кода**. Его задача — не «описать красивую концепцию», а закрыть те решения, изменение которых после M1–M4 будет дорогим.

# M0 — Runtime Charter & Boundary Freeze

Главная формулировка:

> **IRR resolves human or companion intent into bounded, attributable operational work representations. It does not grant authority and does not perform effects.**

И более короткая внутренняя формула:

```text
Intent ≠ Permission ≠ Effect
```

IRR находится именно между первым и вторым.

---

## M0.1 — Product Charter & Vocabulary

Первый PR должен ответить на вопрос: **что такое IRR и чем он не является**.

Будущий документ:

```text
docs/m0_runtime_charter.md
```

Плюс короткий `README.md`.

Замораживаем:

```text
Repository: intent-resolution-runtime
Distribution: intent-resolution-runtime
Python namespace later: intent_resolution_runtime
Short name: IRR
```

И роли:

```text
Principal
    тот, чьи цели/полномочия рассматриваются

Origin
    кто фактически породил IntentRequest:
    human / companion / worker / system

Host
    система, использующая IRR

Cognitive Provider
    LLM / Organism / другой resolver,
    предлагающий interpretation

IRR
    validates and resolves intent

Governance
    решает, что разрешено

Executor
    выполняет capabilities

Worker
    выполняет делегированную сложную работу
    (например Codexia)
```

Очень важно сразу разделить:

```text
origin ≠ principal
origin ≠ authority
context ≠ authority
intention ≠ approval
```

Например Kaguya может предложить:

> «Стоит открыть последние experiment reports».

Но это остаётся:

```text
origin = companion
```

а не подделывается под:

```text
origin = human
```

### Явные non-goals M0

IRR не является:

- shell-command generator;
- desktop automation engine;
- policy engine;
- permission system;
- companion/personality;
- memory system;
- general chat assistant;
- Runplane replacement;
- Codexia replacement;
- HDE-specific subsystem;
- Organism runtime.

Это должно быть буквально записано.

---

# M0.2 — Trust, Context & Resolution Semantics

Это, пожалуй, самый важный PR M0.

Здесь замораживаем **как IRR имеет право понимать намерение**.

Базовая цепочка:

```text
IntentRequest
      ↓
explicit bounded context
      ↓
interpretation
      ↓
ambiguity analysis
      ↓
resolution
```

### Никакого ambient context

IRR не имеет права самостоятельно:

```text
scan home directory
scan project
read HDE memory
inspect browser
search files
query GitHub
```

только потому, что это помогло бы понять запрос.

Контекст должен быть:

```text
caller-supplied
explicit
bounded
attributable
```

Если нужны новые данные — IRR формирует **потребность в observation**, но сам не идёт их добывать.

---

## Material ambiguity

Нам нужна очень строгая граница между допустимым предположением и вопросом пользователю.

Я бы определил:

> **Material ambiguity — неоднозначность, которая может изменить ресурс, получателя, scope, disclosure, mutation, executable target, стоимость или внешний effect.**

Например:

> «Отправь Ивану файл».

Если известных Иванов два — нельзя угадывать.

> «Запусти его».

Если в контексте нет одного точного referent — нельзя угадывать.

> «Удали старый backup».

Если критерий `old` не определён — нельзя произвольно выбрать файл.

IRR должен вернуть:

```text
clarification_required
```

или оставить точку **late binding**.

При этом несущественные предположения могут быть допустимы, но должны быть видимыми:

```text
assumption:
    presentation ordering = newest first
```

Никаких скрытых assumptions.

---

# M0.3 — Intent → Work Boundary

Здесь фиксируем самое фундаментальное: **что именно IRR производит**.

Не shell:

```text
Expand-Archive ...
Start-Process ...
```

а semantic operations:

```text
filesystem.search
artifact.select
archive.inspect
archive.extract
workspace.inspect
process.launch
```

При этом IRR не должен иметь захардкоженный список Windows-команд или Linux utilities.

Будущая conceptual pipeline:

```text
IntentRequest
     ↓
ResolvedIntent
     ↓
WorkPlan
     ↓
WorkStep[]
```

Но точные Python schemas появятся только в M1.

### WorkPlan — не scripting language

Я бы уже сейчас заморозил это решение.

Не строим мини-Python внутри IRR.

V1 WorkPlan:

```text
steps
dependencies
symbolic inputs/outputs
bounded ordering
explicit continuation points
```

Но:

```text
no arbitrary loops
no hidden retries
no arbitrary embedded code
no shell fragments
```

Если требуется новое решение после observation:

```text
execution result
      ↓
IRR continuation
      ↓
successor WorkPlan
```

а не скрытый автономный цикл внутри plan.

Это сильно упростит безопасность.

---

# M0.4 — Late Binding & Observation Boundary

Это нужно выделить отдельно, потому что без этого наши реальные сценарии не работают.

Например:

> Найди последний organism_lab backup, распакуй и запусти.

На момент первоначального запроса IRR **не знает**, какой файл является backup.

Поэтому:

```text
Step 1:
filesystem.search

output:
backup_candidates
```

дальше:

```text
Step 2:
artifact.select

input:
$step1.backup_candidates
```

потом:

```text
Step 3:
archive.inspect

input:
$step2.selected_artifact
```

И т.д.

То есть WorkPlan должен поддерживать **symbolic dataflow**.

Но есть ещё более сложный случай.

После `archive.inspect` выясняется:

```text
two launchers found
```

IRR не должен автоматически выбирать случайный.

Получаем:

```text
execution observation
        ↓
IRR continuation
        ↓
clarification_required
```

или новый resolution.

Это позволит assistant быть действительно разумным, а не просто строить одноразовые цепочки.

---

# M0.5 — Capability Boundary

Следующее решение:

> IRR не должен придумывать capabilities.

Host/execution environment предоставляет **Capability Catalog**.

Концептуально:

```text
CapabilityDescriptor
├─ capability_id
├─ purpose
├─ input contract
├─ output contract
├─ effect metadata
├─ scope requirements
└─ executor/provider identity
```

Например:

```text
filesystem.search
archive.extract
process.launch
telegram.send_file
```

IRR планирует только из известных capabilities.

Если нужной нет:

```text
missing_capability
```

А не:

> «Ну тогда попробую через PowerShell».

Это очень важная fail-closed граница.

### И ещё одна тонкость

IRR может видеть:

```text
effect_class = external_disclosure
```

но не решает:

```text
allowed = true
```

Это принадлежит Governance.

То есть:

```text
IRR:
"This operation sends file X externally."

Governance:
"May this happen?"
```

---

# M0.6 — Governance & Authority Boundary

Здесь фиксируем:

```text
IRR
 ↓
WorkProposal
 ↓
Governance
 ↓
Authorization
 ↓
Executor
```

IRR не должен выдавать поля вроде:

```text
approved = true
safe = true
permission_granted = true
```

Он может утверждать только:

```text
requested_scope
requested_effect
affected_resources
data_flow
uncertainty
```

Policy может:

```text
approve
deny
constrain
require_review
```

Но если Governance меняет план:

```text
"разрешено только читать, не извлекать"
```

старый WorkPlan не редактируется молча.

Создаётся:

```text
successor resolution / successor plan
```

с lineage.

---

# M0.7 — Cognitive Provider Boundary

Вот здесь заранее готовим место для organism_lab.

Архитектура:

```text
              IRR
               │
       CognitiveProvider
          /          \
        LLM        Organism
```

Provider выдаёт:

```text
CandidateResolution
```

Он **не владеет окончательным IRR state**.

IRR:

```text
validate
normalize
reject malformed output
check refs
check capabilities
check ambiguity
```

То есть:

> **Cognitive provider proposes. IRR accepts valid semantics.**

Это позволит позже сделать:

```text
LLMResolver
OrganismResolver
HybridResolver
DeterministicResolver
```

без изменения внешнего API.

И я бы прямо записал в M0:

> Organism integration is intentionally deferred. IRR must expose a stable cognitive seam without depending on organism_lab internals.

Это особенно важно пока organism_lab продолжает быстро эволюционировать.

---

# M0.8 — Worker Delegation Boundary

Codexia лучше тоже учесть сейчас, но не интегрировать.

Есть принципиальная разница между:

```text
filesystem.search
```

и:

```text
"исследуй 40 PR и предложи следующий эксперимент"
```

Поэтому я бы не прятал Codexia за обычным capability вроде:

```text
codexia.do_work
```

Лучше две разновидности downstream handoff:

```text
CapabilityHandoff
```

для bounded operations,

и:

```text
DelegatedWorkHandoff
```

для worker'ов.

Например:

```text
DelegatedWork
├─ objective
├─ scope
├─ context
├─ allowed capabilities
├─ forbidden effects
├─ expected deliverables
└─ completion contract
```

IRR остаётся владельцем **исходного intent lifecycle**.

Codexia владеет только жизненным циклом своей delegated subtask.

```text
User intent
    ↓
IRR
    ↓
Codexia subtask
    ↓
WorkerResult
    ↓
IRR
    ↓
intent completed / continuation required
```

---

# M0.9 — Failure, Retry & Unknown Outcome Principles

Хотя execution появится позже, эту границу надо заморозить сейчас.

Особенно:

```text
unknown outcome ≠ failed
```

Если executor говорит:

> «Я отправил запрос Telegram, но соединение оборвалось до подтверждения».

IRR не имеет права автоматически:

```text
send again
```

Иначе получаем две отправки.

Поэтому:

```text
succeeded
failed
blocked
interrupted
unknown_outcome
```

должны быть концептуально разными.

И:

> Effectful unknown outcome never implies automatic retry.

Это пригодится в M5, но правило надо установить уже в charter.

---

# M0.10 — Reference Scenarios

M0 должен закончиться не только текстом, но и набором **architecture fixtures**.

Я бы взял восемь сценариев.

### Scenario A — Restore backup

```text
"Найди последний backup organism_lab,
распакуй в W:\organism_lab и запусти."
```

Проверяет:

```text
search
selection
late binding
archive
filesystem mutation
process execution
```

### Scenario B — Telegram

```text
"Отправь мне последний Voice Engine report в Telegram."
```

Проверяет:

```text
artifact discovery
recipient binding
external disclosure
network effect
```

### Scenario C — Codexia

```text
"Изучи результаты CG2.42 и предложи следующий experiment."
```

Проверяет worker delegation.

### Scenario D — Ambiguous referent

```text
"Запусти его."
```

Должен закончиться clarification.

### Scenario E — Companion initiative

Kaguya предлагает:

```text
"Стоит проверить последние логи."
```

Проверяет:

```text
origin=companion
principal=user
origin ≠ authority
```

### Scenario F — Missing capability

```text
"Отправь файл через Signal."
```

при отсутствии Signal provider.

Результат:

```text
missing_capability
```

а не произвольный workaround.

### Scenario G — No operational intent

```text
"Как ты думаешь, этот эксперимент хороший?"
```

IRR должен суметь сказать:

```text
no_operational_work
```

а не превращать любое предложение в действия.

### Scenario H — Observation changes plan

После поиска backup обнаружено два равноценных кандидата.

Проверяем:

```text
continuation
clarification
no silent choice
```

Если архитектура красиво объясняет все восемь — M0 почти наверняка достаточно хорош.

---

# Как я бы разбил реальную реализацию M0 на PR

Чтобы не растянуть charter на месяц:

```text
PR0.1 — Runtime Charter & Vocabulary
README
runtime charter
actors
scope/non-goals

PR0.2 — Trust, Context & Resolution Semantics
origin/principal distinction
bounded context
ambiguity rules
provenance
authority separation

PR0.3 — Work, Capability & Handoff Boundaries
semantic work graph
late binding
capability catalog
governance seam
delegation seam
unknown outcome

PR0.4 — Reference Scenarios & M0 Closure
8 architecture fixtures
boundary matrix
M1 handoff
M0 closure statement
```

Я бы **не делал больше четырёх PR для M0**. Иначе мы начнём проектировать документацию вместо runtime.

---

# Предлагаемая структура репозитория после M0

Без implementation code:

```text
intent-resolution-runtime/
├── LICENSE
├── README.md
├── ROADMAP.md
└── docs/
    ├── m0_runtime_charter.md
    ├── terminology.md
    ├── trust_and_authority.md
    ├── resolution_semantics.md
    ├── work_and_handoff_boundary.md
    ├── cognitive_provider_boundary.md
    ├── reference_scenarios.md
    └── m0_closure.md
```

`src/` я бы **вообще не создавал в M0**.

Первый `src/intent_resolution_runtime/` появляется в **M1**, когда мы действительно замораживаем Intent IR.

---

# Definition of Done M0

M0 закрыт, если мы можем ответить однозначно на следующие вопросы:

```text
1. Что IRR получает?
2. Кто является origin и кто principal?
3. Какой context разрешён?
4. Когда IRR обязан спросить clarification?
5. Что считается ResolvedIntent?
6. Как intent становится semantic work?
7. Как представляется неизвестный будущий результат?
8. Откуда берутся capabilities?
9. Что происходит при отсутствующей capability?
10. Где заканчивается IRR и начинается governance?
11. Где заканчивается governance и начинается execution?
12. Чем worker delegation отличается от capability execution?
13. Где подключается LLM?
14. Где в будущем подключается Organism?
15. Что происходит при unknown outcome?
16. Почему IRR не может выполнить действие самостоятельно?
```

И главное архитектурное доказательство:

```text
Character_OS
Organism
HDE
Codexia
Runplane
```

должны быть **заменяемыми внешними соседями**, а не зависимостями ядра IRR.

---

Если всё это зафиксировать, то M1 становится очень механическим:

```text
charter semantics
      ↓
Python immutable contracts
      ↓
validation
      ↓
canonical serialization
      ↓
digests / identity
      ↓
tests
```

То есть M0 действительно выполняет свою задачу: **после него мы перестаём обсуждать, “что такое IRR”, и начинаем просто строить его**.
