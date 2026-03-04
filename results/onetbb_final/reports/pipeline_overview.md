# Doc-Benchmark Pipeline: Описание и схема

**Репозиторий:** https://github.com/napetrov/doc-benchmark  
**Дата:** 2026-03-04

---

## Схема пайплайна

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        DOC-BENCHMARK PIPELINE                           │
└─────────────────────────────────────────────────────────────────────────┘

  GitHub Repo
  (uxlfoundation/oneTBB)
       │
       ▼
┌─────────────────┐
│   1. PERSONAS   │  LLM анализирует репо и создаёт профили пользователей
│                 │  кто пишет код, кто оптимизирует, кто интегрирует
│ Output:         │
│ personas/       │  Пример персоны:
│ oneTBB.json     │  • HPC Engineer — advanced, заботится о NUMA/throughput
└────────┬────────┘  • ML Framework Dev — intermediate, flow graph & latency
         │           • Systems Integrator — beginner, CMake/build config
         │
         ▼
┌─────────────────┐
│  2. QUESTIONS   │  Для каждой персоны × seed topics → вопросы
│                 │
│  Внутри:        │  a) Context7 → извлекает seed topics из документации
│  • LLM генерит  │  б) LLM генерит вопросы (по сложности: basic/advanced)
│  • Валидация    │  в) LLM-валидатор отсеивает слабые (threshold 60)
│  • Дедупликация │  г) Embedding similarity → дедупликация (>0.85)
│                 │  д) Merge personas для дублей
│ Output:         │
│ questions/      │  Типы вопросов: how-to, scenario, explain, compare
│ oneTBB.json     │  Difficulty: basic / intermediate / advanced
└────────┬────────┘  Всего: 30-80 уникальных вопросов
         │
         ├────────────────────────────────────┐
         ▼                                    ▼
┌─────────────────┐                ┌─────────────────┐
│  3a. ANSWERS    │                │  3b. ANSWERS    │
│  WITH DOCS      │                │  WITHOUT DOCS   │
│                 │                │                 │
│ Context7 →      │                │ LLM отвечает    │
│ достаёт         │                │ только из       │
│ релевантные     │                │ встроенных      │
│ фрагменты docs  │                │ знаний          │
│ → LLM с         │                │ (baseline)      │
│ контекстом      │                │                 │
└────────┬────────┘                └────────┬────────┘
         │                                  │
         └──────────────┬───────────────────┘
                        │
                        ▼
              ┌─────────────────┐
              │ answers/        │
              │ oneTBB.json     │  Каждая запись:
              └────────┬────────┘  { with_docs: {answer, retrieved_docs},
                       │             without_docs: {answer} }
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 4. EVALUATION                        │
│              (LLM-as-Judge)                         │
│                                                     │
│  Судья: отдельная модель (claude-sonnet-4-6)        │
│  Отвечает НЕ та же модель что генерировала ответы   │
│                                                     │
│  Оценивает каждый ответ по 5 измерениям (0-100):    │
│                                                     │
│  ┌─────────────────┬────────────────────────────┐   │
│  │ Dimension       │ Что проверяет               │   │
│  ├─────────────────┼────────────────────────────┤   │
│  │ Correctness     │ Фактическая точность        │   │
│  │ Completeness    │ Полнота охвата темы         │   │
│  │ Specificity     │ Привязка к конкретной lib   │   │
│  │ Code Quality    │ Корректность кода / примеров│   │
│  │ Actionability   │ Можно ли применить сразу   │   │
│  └─────────────────┴────────────────────────────┘   │
│                                                     │
│  Aggregate = avg(5 dims)                            │
│  Delta = with_docs.aggregate - without_docs.agg     │
│                                                     │
│  Diagnosis:                                         │
│  • docs_helped (delta > 0)                          │
│  • knowledge_sufficient (delta ≤ 0)                 │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
              ┌─────────────────┐
              │ eval/           │
              │ oneTBB.json     │
              └────────┬────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────┐
│                 5. REPORT                            │
│                                                     │
│  • Агрегированные метрики                           │
│  • Топ/боттом вопросы                               │
│  • Анализ delta (где docs помогли/помешали)         │
│  • Рекомендации по улучшению документации           │
└─────────────────────────────────────────────────────┘
                       │
                       ▼
              reports/oneTBB.md
              reports/oneTBB_low_scores_analysis.md
```

---

## Модели в пайплайне

| Шаг | Роль | Модель (текущий прогон) |
|-----|------|------------------------|
| Personas | Генератор | gpt-4o |
| Questions | Генератор + валидатор | gpt-4o |
| Answers with_docs | Отвечает с контекстом | gpt-4o |
| Answers without_docs | Baseline answerer | gpt-4o |
| Evaluation | Судья (Judge) | claude-sonnet-4-6 |
| Embeddings (dedup) | Similarity | text-embedding-3-small |

> **Ключевой принцип:** Judge ≠ Answerer. Разные модели на генерацию и оценку — избегаем self-serving bias.

---

## Context7 — роль в пайплайне

Context7 — сервис, который умеет:
1. **Topic discovery** — извлекает ключевые темы из документации библиотеки (по repo slug)
2. **Retrieval (RAG)** — для каждого вопроса возвращает релевантные фрагменты docs

```
Вопрос → Context7.resolve_library("oneTBB")
       → Context7.search(question_text, max_tokens=8000)
       → retrieved_docs (список сниппетов)
       → LLM(question + retrieved_docs) → answer_with_docs
```

---

## Структура файлов

```
results/onetbb_final/
├── personas/
│   └── oneTBB.json          # 5-8 персон с профилями
├── questions/
│   └── oneTBB.json          # 80 вопросов с метаданными
├── answers/
│   └── oneTBB.json          # Ответы with_docs + without_docs
├── eval/
│   └── oneTBB.json          # Оценки по 5 dim + delta + diagnosis
└── reports/
    ├── oneTBB.md                        # Основной отчёт
    └── oneTBB_low_scores_analysis.md    # Анализ слабых мест (этот файл)
```

---

## Запуск пайплайна (CLI)

```bash
# 1. Персоны
python cli.py personas discover --product oneTBB --repo uxlfoundation/oneTBB --count 5

# 2. Вопросы
python cli.py questions generate --product oneTBB --personas personas/oneTBB.json --count 2

# 3. Ответы
python cli.py answers generate --product oneTBB --questions questions/oneTBB.json --model gpt-4o

# 4. Эвалюация
python cli.py eval score --product oneTBB --answers answers/oneTBB.json \
  --judge-model claude-sonnet-4 --judge-provider anthropic

# 5. Отчёт
python cli.py report generate --product oneTBB --eval eval/oneTBB.json
```
