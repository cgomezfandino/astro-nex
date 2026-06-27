# Astro-Nex — Handoff (punto de control)

> **Lee esto al iniciar cada sesión.** Captura el estado y el siguiente paso.
> Metodología detallada en `docs/WORKING-STYLE.md`.
>
> Última actualización: 2026-06-27 (tras cerrar Phase 2A, QA verde).

## Estado actual (verificado con evidencia)

| Hito | Estado | Ref |
|---|---|---|
| Phase 1 (slice Py3/GTK3) | ✅ DONE | v0.1.0 |
| **Phase 2A — Cimientos de datos** | ✅ **DONE, mergeado, QA verde, milestone cerrado** | commit `9b72fee`, milestone #4 closed |
| Phase 2B — Motor de cálculo | ⏳ **SIGUIENTE** | milestone #5 (abierto) |
| Phase 2C–2E | ⏳ Pendientes | milestones #6, #7, #2 |

- **`main`**: sincronizada con `origin/main`, working tree limpio, sin ramas colgadas.
- **Tests**: 125 pasando (venv limpio). Baseline sólida.
- **Issues**: 2A (#11–#15) cerrados. 20 abiertos repartidos en 2B–2E.

## Qué es el proyecto

Modernización de **Astro-Nex 1.2.3** (método API/Huber, GPLv3, autor José Antonio
Rodríguez 1960–2022, mantenido en su honor). Objetivo: app macOS `.app` ejecutable
con doble clic + soporte multiplataforma (Win/Linux/macOS). Repo del port:
`/Users/cgomezfandino/repos/astro-nex` · GitHub: `cgomezfandino/astro-nex`.

**Decisión clave**: port completo a Py3/GTK3 primero → empaquetado `.app` al final.
El slice actual es ~4% del código (1084/28639 LOC); falta portar la funcionalidad
para igualar el screenshot de referencia.

## ━━ SIGUIENTE PASITO: Phase 2B ━━

El siguiente hito es **2B · Motor de cálculo completo** (milestone #5). Sus issues:

| Issue | Qué | Notas |
|---|---|---|
| #16 | Port `directions.py` | solar_rev, sec_prog. Consolidar con `strdate_to_date` ya portado. |
| **#17** | **Age Point Huber (Lebensuhr)** | **La pieza distintiva del método API/Huber.** Núcleo. |
| #18 | Tipos de carta (Nodal, House, Local, Soul, Dharma, Prof, Transits, UR-Nodal) | Extiende `core/chart.py` (solo radix hoy). |
| #5  | Historical-DST timezones (`tz_sup`) | Nacimientos pre-hora-estándar. |

### Cómo empezaremos 2B (plan de arranque)

1. **`git pull`** → verificar baseline (125 tests pasan).
2. **Brainstorming** (skill `$brainstorming`) para el primer issue. Orden sugerido:
   - Empezar por **#16 directions** (más autocontenido, desbloquea otros cálculos).
   - Luego **completar `NeXDate`** (set_now, dateforstore) — necesario para `Current`
     y para los tipos de carta. Cae naturalmente en 2B.
   - Luego **#18 tipos de carta** (radix ya está; añadir el resto).
   - Por último **#17 Age Point** (lo más distintivo y complejo; mejor con base sólida).
   - **#5 tz_sup** puede ir en paralelo cuando tengamos fechas históricas que probar.
3. **Worktree aislado**: `git worktree add .worktrees/2B-calc -b milestone-2B-calc`.
4. **TDD por cada issue**: test contra golden data del original → portar → QA.
5. Al cerrar 2B: smoke test integración → cerrar issues → merge → push → cerrar milestone.

### Dependencias a recordar
- `Current` (state.py) quedó con métodos pendientes de `NeXDate.set_now`/`dateforstore`.
  Completar `NeXDate` en 2B cierra ese ciclo.
- Los tipos de carta (#18) alimentan el motor de dibujo (2C) y la GUI (2D).

## Documentación importante

- `docs/WORKING-STYLE.md` — **cómo trabajamos** (brainstorm→TDD→QA→ciclar). Leer.
- `docs/ROADMAP.md` — fases y sub-milestones.
- `CHANGELOG.md` — historial de cambios.
- `docs/superpowers/specs/2026-06-27-macos-app-bundling-design.md` — spec del `.app`.
- `tools/original-docker/` — harness para comparar contra el original (referencia).

## Snapshot técnico de 2A (para contexto)

Portados con TDD: `config.py` (#13), `state.py` (#12), `zodiac.py` (#14),
`countries.py` (#15), `database.py` (#11). Bug real cazado: `store_chart` (named
vs positional placeholders). `local.db` (279 tablas SQLite) empaquetada en
`src/astronex/data/`. Smoke test integración OK (lookup Girona, Zodiac 12 glifos,
chart store round-trip).
