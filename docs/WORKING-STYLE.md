# Working Style — Cómo trabajamos en Astro-Nex

> **Este documento define LA forma de trabajar del proyecto.** Es vinculante para
> cualquier sesión (humana o asistida por IA). Su objetivo: desarrollos robustos,
> pero simples y fáciles de mantener, pensando en ti (desarrollador futuro) y en
> los usuarios humanos de la comunidad.
>
> Creado: 2026-06-27. Mantenido vivo.

## Filosofía

**Robusto, pero simple y fácil de mantener.** Cada decisión prioriza:

1. **Correctitud verificable** — el código hace lo que debe, y lo podemos probar.
2. **Simplicidad** — la solución más simple que funcione. Sin sobre-ingeniería.
3. **Mantenibilidad** — código que tú (o un nuevo colaborador) entenderá en 6 meses
   sin dolores de cabeza. Nombres claros, archivos enfocados, sin sorpresas.
4. **Fidelidad al original** — cuando porteamos, respetamos el comportamiento del
   Astro-Nex original (Python 2). Solo cambiamos lo que Py3/GTK3 exige.
5. **Empatía con el usuario** — la comunidad usará esto. Mensajes claros, sin
   crashes silenciosos, documentación honesta.

## El ciclo de trabajo (obligatorio)

Todo trabajo de features/ports sigue este ciclo, en orden. **No se saltan pasos.**

```
   ┌─────────────────────────────────────────────────────────┐
   │  1. BRAINSTORMING                                       │
   │     Usar el skill $brainstorming ANTES de implementar.  │
   │     Explorar intención, requisitos, diseño, enfoques.   │
   │     Presentar diseño → aprobación del humano.           │
   │     (Solo para tareas creativas/no triviales; no para  │
   │      un fix de una línea obvio.)                       │
   └───────────────────────┬─────────────────────────────────┘
                           ▼
   ┌─────────────────────────────────────────────────────────┐
   │  2. PLAN + WORKTREE AISLADO                             │
   │     Spec a docs/superpowers/specs/. Plan a plans/.      │
   │     git worktree add .worktrees/<milestone> -b ...      │
   │     Nunca trabajar directo en main.                     │
   └───────────────────────┬─────────────────────────────────┘
                           ▼
   ┌─────────────────────────────────────────────────────────┐
   │  3. IMPLEMENTACIÓN CON TDD                              │
   │     RED: escribir test que falle primero.               │
   │     GREEN: mínimo código para pasar.                    │
   │     REFACTOR: limpiar manteniendo verde.                │
   │     Verificar contra el original (Docker/golden data).  │
   │     Sin código de producción sin test que falle antes.  │
   └───────────────────────┬─────────────────────────────────┘
                           ▼
   ┌─────────────────────────────────────────────────────────┐
   │  4. QA / VERIFICACIÓN                                   │
   │     Suite completa pasa (evidencia fresca, no "creo").  │
   │     Smoke test de integración del milestone.            │
   │     No-regresión: lo que ya funcionaba sigue funcionando.│
   │     Si algo no pasa → NO cerrar. Ciclar al paso 3 o 1.  │
   └───────────────────────┬─────────────────────────────────┘
                           ▼
   ┌─────────────────────────────────────────────────────────┐
   │  5. CIERRE LIMPIO                                       │
   │     Commits con mensaje claro (feat/fix/docs/chore).    │
   │     Merge --no-ff a main. Push.                         │
   │     Cerrar issues afectados (con comentario de cómo).   │
   │     Cerrar milestone si todos sus issues están done.    │
   │     Borrar rama del worktree (git branch -d).           │
   │     Actualizar HANDOFF.md + ROADMAP + CHANGELOG.        │
   └─────────────────────────────────────────────────────────┘
```

### ¿Qué pasa cuando algo no funciona?

**Nos devolvemos o pensamos qué hacer mejor/distinto.** No se fuerza una solución
mediocre. Si en QA algo falla:
- Bug en el código → vuelta al paso 3 (TDD: escribir test que reproduzca el bug).
- Enfoque equivocado → vuelta al paso 1 (brainstorming: replantear).
- Algo del original no entendemos → investigar con Docker antes de seguir.

## Reglas de oro (no negociables)

1. **Nada de código sin test que falle primero.** (TDD estricto.)
2. **Evidencia antes de afirmar.** Nunca "creo que pasa" — correr el comando, leer
   la salida, entonces afirmar. (Skill: verification-before-completion.)
3. **main siempre verde y deployable.** Nunca se rompe; el trabajo va en worktrees.
4. **Fidelidad verificable.** Al portar, comparar contra el original (golden data
   ≤1e-4°, o comparación visual con Docker). No inventar comportamiento.
5. **Commits pequeños y atómicos.** Un commit = una idea. Mensaje explica el "qué"
   y el "por qué". Referencian el issue (`Refs: #NN`).
6. **Puntos de control frecuentes.** Commitear + pushear a menudo. El HANDOFF.md
   captura el estado al cerrar cada sesión.
7. **Simplicidad sobre brillantez.** Si una solución es elegante pero incomprensible,
   no sirve. El código se lee muchas más veces de lo que se escribe.
8. **Empatía con el usuario humano.** Errores con mensajes accionables (no crashes
   silenciosos). Documentación honesta (no prometer lo que no hay).

## Estructura del repositorio

```
astro-nex/
├── src/astronex/         # código fuente (multiplataforma: Win/Linux/macOS)
│   ├── core/             # sin GTK, sin cairo: cálculo, datos, estado
│   ├── render/           # cairo: rueda, glifos
│   ├── surfaces/         # export PNG/PDF
│   ├── gui/              # GTK 3: ventana, diálogos
│   └── data/             # recursos empaquetados (local.db, .ttf, cfg.ini)
├── tests/                # pytest, incluye golden/ (datos de referencia)
├── tools/
│   ├── original-docker/  # harness para correr el original Py2 como referencia
│   └── build_macos_app.py# (futuro, 2E) empaquetado .app
├── docs/
│   ├── HANDOFF.md        # ESTADO ACTUAL — leer al iniciar cada sesión
│   ├── WORKING-STYLE.md  # este documento
│   ├── ROADMAP.md        # fases y sub-milestones
│   └── superpowers/{specs,plans}/  # specs y planes de cada trabajo
├── CHANGELOG.md
├── pyproject.toml
└── .worktrees/           # worktrees aislados (gitignored)
```

## Convenciones de Git

- **Rama principal**: `main` (siempre verde).
- **Ramas de feature**: `milestone-2X-<tema>` (ej: `milestone-2A-data-foundations`).
- **Commits**: prefijo convencional (`feat`, `fix`, `docs`, `chore`, `test`, `refactor`).
- **Merge**: `--no-ff` con mensaje que referencia los issues cerrados.
- **Nunca** se commitea en `main` directamente durante desarrollo.

## Cómo iniciar una nueva sesión

1. `cd /Users/cgomezfandino/repos/astro-nex && git pull`
2. **Leer `docs/HANDOFF.md`** — dice dónde estamos y qué toca.
3. Verificar baseline: crear venv, instalar, correr `pytest -q` → debe pasar.
4. Identificar el siguiente hito (HANDOFF lo indica) y su milestone en GitHub.
5. Empezar por el paso 1 del ciclo (brainstorming) o 2 si ya hay spec.

## Cómo cerrar una sesión

1. Asegurar todo commiteado y test verde (con evidencia).
2. Push a `main` (si hubo merge) o a la rama del worktree.
3. Actualizar `docs/HANDOFF.md` con el nuevo estado.
4. Si se cerró un milestone: cerrar issues, cerrar milestone en GitHub, actualizar
   ROADMAP + CHANGELOG, borrar worktree/rama.
5. Dejar el repo limpio (sin working tree sucio, sin worktrees colgados).
