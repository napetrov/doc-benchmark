# oneTBB Doc Quality — Анализ слабых мест

**Дата:** 2026-03-04  
**Датасет:** `results/onetbb_final` (80 вопросов)  
**Судья:** claude-sonnet-4-6

---

## Общая статистика

| Режим | Min | Avg | Max |
|-------|-----|-----|-----|
| Без документации (`without_docs`) | 42 | 84.4 | 100 |
| С документацией (`with_docs`) | 24 | 84.3 | 100 |

- **docs_helped:** 50 вопросов (62.5%) — документация улучшила ответ
- **knowledge_sufficient:** 30 вопросов (37.5%) — модель знала без документации

---

## 1. Вопросы с наименьшим рейтингом БЕЗ документации

_Это области, где LLM плохо отвечает из встроенных знаний — документация может значительно помочь._

| # | Score (no→with) | Delta | Question ID | Тема |
|---|----------------|-------|-------------|------|
| 1 | 42 → 54 | +12 | q_026 | Preprocessor макросы / CMake для отключения dynamic memory allocation и кастомного аллокатора |
| 2 | 51 → 67 | +16 | onetbb-Q005 | Reader-writer mutex: разница spin_rw_mutex и speculative_spin_rw_mutex при read-mostly доступе |
| 3 | 55 → **94** | **+39** | q_008 | Производительность `tbb::feeder` vs `parallel_for` с lazy evaluation |
| 4 | 56 → 63 | +7 | q_018 | CMake-конфигурация arena observers + `tbb::feeder` для отладки scheduling |
| 5 | 61 → **92** | **+31** | onetbb-Q001 | Гонки данных при инкременте member counter в `parallel_for` body |
| 6 | 64 → **93** | **+29** | q_016 | Task stealing: `tbb::task` vs кастомный work queue с explicit task affinity |
| 7 | 67 → 76 | +9 | onetbb-Q013 | Безопасность итерации по `concurrent_vector` во время параллельной записи |
| 8 | 73 → 87 | +14 | q_036 | `std::move` с concurrent контейнерами — moved-from объекты |
| 9 | 73 → 88 | +15 | onetbb-Q021 | NUMA/hybrid CPU: locality через task_arena + `constraints` |
| 10 | 76 → 87 | +11 | q_013 | `task_group` vs `task_arena` — разница в контроле thread participation |

### Ключевые слабости (без документации):

| Проблема | Вопросы |
|----------|---------|
| **Неправильный код** (`code_quality` < 50) | q_026, q_008, onetbb-Q001, q_016 |
| **Неверное correctness** (< 50) | q_026, onetbb-Q005, q_008, q_018, onetbb-Q013 |
| **Не даёт actionable steps** (actionability < 30) | onetbb-Q005 |

### Что нужно улучшить/добавить в документацию:

1. **CMake custom allocator** — раздел про `TBBmalloc_proxy` и `TBBMALLOC_SCALABLE_PROXY` недостаточно детален
2. **spin_rw_mutex vs speculative_spin_rw_mutex** — нет примеров с write-heavy vs read-heavy сравнением производительности
3. **tbb::feeder performance** — нет benchmark-сравнения с `parallel_for`
4. **Arena observers** — отсутствует пример CMake + observer API вместе
5. **Data races в parallel_for body** — нужен explicit anti-pattern раздел с примерами race-free счётчиков
6. **NUMA task_arena constraints** — примеры есть, но разбросаны; нужен единый how-to guide

---

## 2. Вопросы с наименьшим рейтингом С документацией

_Это области, где документация активно мешает или вводит в заблуждение — критично для исправления._

| # | Score (no→with) | Delta | Question ID | Тема |
|---|----------------|-------|-------------|------|
| 1 | **94 → 24** | **-70** | q_044 | Инвалидация итераторов/ссылок при расширении `concurrent_vector` |
| 2 | **77 → 38** | **-39** | q_019 | CMake: установка только компонентов flow graph без полного task scheduler |
| 3 | **81 → 55** | **-26** | q_020 | Thread pinning для flow graph nodes (inference latency) |
| 4 | **84 → 57** | **-27** | q_032 | `tbb::flow` dynamic allocation для нод — compile-time alternatives |
| 5 | **86 → 63** | **-23** | q_035 | CMake linking + `std::move` с `concurrent_vector` без data races |
| 6 | **86 → 63** | **-23** | q_052 | Blocking внутри `parallel_for` на `std::cout` — thread utilization |
| 7 | **87 → 67** | **-20** | q_049 | `parallel_do_feeder` non-blocking push — cache coherence impl |
| 8 | **100 → 73** | **-27** | onetbb-Q011 | Exception handling внутри parallel алгоритмов |

### Конкретные ошибки в документации (требуют fix):

#### 🔴 Критические (документация вводит в заблуждение):

**q_044 — `concurrent_vector` iterator invalidation (-70)**
> Документация содержит **неверное утверждение**: ссылки на элементы `concurrent_vector` якобы могут стать невалидными при расширении. На самом деле `concurrent_vector` гарантирует стабильность ссылок. Документ должен быть исправлен.

**q_019 — CMake компонентная установка (-39)**
> Документация описывает флаги которых нет или они не работают. Пользователь следует инструкциям и не находит нужного компонента. Нужен актуальный пример `find_package(TBB COMPONENTS tbb)`.

**q_032 — flow graph node allocation (-27)**
> Код в документации имеет **семантическую ошибку**: создаёт узлы в стеке, хотя `graph` берёт ownership и ожидает heap allocation. Пример компилируется но приводит к UB.

#### 🟡 Значительные (документация неполная/вводящая):

**q_020 — Thread pinning (-26)**
> Документация предлагает ручной OS-level pinning (`pthread_setaffinity`), но не упоминает `task_arena::constraints` — наиболее правильный TBB-native способ.

**onetbb-Q005 — Reader-writer mutex (-16 для with_docs)**
> Документация содержит **ошибку по умолчанию**: `scoped_lock(mutex, bool write=?)` — указан неверный default. Нужно проверить и исправить.

---

## 3. Сводная таблица приоритетов по исправлениям

| Приоритет | Тема | Тип исправления |
|-----------|------|----------------|
| 🔴 P0 | `concurrent_vector` iterator validity | Исправить ошибочное утверждение |
| 🔴 P0 | `tbb::flow` node allocation pattern | Исправить код с UB |
| 🔴 P0 | `scoped_lock` default write flag | Исправить неверный default |
| 🔴 P1 | CMake component install (flow graph) | Обновить примеры |
| 🟡 P1 | `task_arena::constraints` для thread pinning | Добавить как primary approach |
| 🟡 P2 | CMake custom allocator / `TBBmalloc_proxy` | Расширить раздел |
| 🟡 P2 | NUMA + constraints how-to guide | Консолидировать scattered примеры |
| 🟢 P3 | Data races anti-patterns в parallel_for | Добавить anti-pattern раздел |
| 🟢 P3 | `tbb::feeder` vs `parallel_for` performance | Добавить benchmark comparison |
