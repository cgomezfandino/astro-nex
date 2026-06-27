# Port de `directions.py` — Revolución Solar + Progresión Secundaria (issue #16)

- **Fecha:** 2026-06-27
- **Milestone:** Phase 2B — Motor de cálculo (primer issue)
- **Estado:** Diseño aprobado (pendiente de revisión final del usuario)
- **Issue:** GitHub #16

## Contexto

`directions.py` (legacy, 134 líneas, Python 2) implementa dos técnicas direccionales
del método API/Huber: **revolución solar** (`solar_rev`) y **progresión secundaria**
(`sec_prog`). Ambas están acopladas al objeto monolítico `boss` (estado global + GUI):
leen de `boss.state` y mutan estado + llaman directamente a `boss.da.panel.set_date_only`
(GUI). El port a Python 3 / GTK 3 exige desacoplar: el **cálculo vive en `core/` puro**
(sin GUI, sin mutar el singleton `Current`), y la integración con estado/GUI queda para
Phase 2D (cuando el `Current` completo y los diálogos existan).

Dependencias ya portadas y reutilizables:
- `strdate_to_date` → `core/utils.py` (parses ISO date string → datetime UTC).
- `ephemeris.julday`/`calc`/`revjul` → `core/ephemeris.py` (wrapper pyswisseph).

Dependencia a portar en este issue:
- `NeXDate.getnewdt` → falta en `core/nexdate.py` (necesaria para que `solar_rev`
  devuelva una fecha local legible, como hace el legacy).

## Objetivo

Portar el **cálculo** de revolución solar y progresión secundaria a `core/directions.py`,
como funciones puras (entradas explícitas → salidas de datos), verificadas contra datos
golden generados ejecutando el código legacy original en Docker (máxima fidelidad).

**Fuera de alcance (YAGNI para este issue):**
- Mutación de `Current` (state.calcdt.setdt, setprogchart) → Phase 2D.
- Llamadas GUI (`da.panel.set_date_only`) → Phase 2D.
- Portar el resto de `NeXDate` (setdt, set_now, set_delta, dateforstore) → cae más
  adelante en 2B con otros tipos de carta.
- Integración con el motor de dibujo (2C) y la GUI (2D).

## Principio rector

**El contrato es la salida, no el algoritmo.** El golden captura el JD resultante
(solar_rev) y el datetime progresado (sec_prog). Mientras el output coincida con el
golden dentro de tolerancia, el algoritmo interno puede mejorarse (refactor, bisección,
mejores nombres) sin riesgo. Esto permite modernizar código viejo/legacy priorizando
simplicidad, robustez y tiempos de ejecución, sin impactar los cálculos.

## Arquitectura

```
tests/golden/directions.json   (generado una vez vía Docker, source of truth)
        ▲
        │ verifica (≤ tolerancia)
        │
src/astronex/core/directions.py
    solar_rev(natal_sun_lon, target_year, birth_month, birth_day, epheflag)  → jd
    sec_prog(natal_dt, target_year, sec_alltimes, now_dt)                    → prog_dt

src/astronex/core/nexdate.py
    NeXDate.getnewdt(dateset)  → local datetime   (añadido)
```

Capa GUI/state (2D, futuro) consume estas funciones; aquí no mutamos nada.

## API propuesta

### `solar_rev`

```python
def solar_rev(natal_sun_lon, target_year, birth_month, birth_day, epheflag=4):
    """Julian Day (UT) en que el Sol vuelve a natal_sun_lon durante target_year.

    Partiendo del mes/día de nacimiento en el año objetivo, busca por convergencia
    el JD cuya posición solar iguala la natal.
    """
    return jd   # float
```

Mapeo de entradas (lo que el legacy sacaba de `boss.state`):
- `natal_sun_lon` ← `curr_chart.planets[0]`
- `target_year` ← `date.dt.year`
- `birth_month`, `birth_day` ← parseados de `curr_chart.date`
- `epheflag` ← `state.epheflag`

Salida: `jd` (float). La conversión a fecha local (vía `revjul` + `getnewdt`) la hace el
consumidor; el test la verifica para cubrir ambas piezas.

### `sec_prog`

```python
def sec_prog(natal_dt, target_year, sec_alltimes=False, now_dt=None):
    """Datetime progresado (UTC) por la regla 1 año de vida = 1 día tras el nacimiento.

    - sec_alltimes=False: progdate = natal_dt + timedelta(days=years_from_birth).
    - sec_alltimes=True: interpola linealmente entre los 'cumpleaños sintéticos'
      del año en curso (reparte el día progresado a lo largo del año). Requiere now_dt.
    """
    return prog_dt   # datetime, tz-aware UTC
```

Mapeo de entradas:
- `natal_dt` ← `strdate_to_date(chart.date)`
- `target_year` ← `date.dt.year`
- `sec_alltimes` ← `boss.da.sec_alltimes`
- `now_dt` ← `boss.state.date.dt` (solo rama interpolada)

Salida: `prog_dt` (datetime UTC aware).

### `NeXDate.getnewdt` (añadido)

```python
def getnewdt(self, dateset):
    """(y, m, d, h_float) en UT → datetime local (aware), regla del legacy."""
    ...
    return local_dt
```

Portado fiel de `nexdate.py:60-68`; Py2→3 (`timezone('utc')` → `UTC`).

## Golden vía boss-stub en Docker

Las funciones legacy exigen un `boss` como argumento. Se construye un **stub de `boss`**
(`tools/original-docker/boss_stub.py`) que implementa solo la superficie tocada por
`solar_rev`/`sec_prog`, de modo que el código legacy se ejecuta **sin modificar** y
captura sus mutaciones de estado. Corre bajo Python 2 dentro del contenedor.

### Superficie tocada (auditoría del legacy)

**`solar_rev`** lee: `curr_chart.date`, `curr_chart.planets[0]`, `state.date.dt.year`,
`state.epheflag`, `curr_chart.zone`. Escribe/llama: `state.date.getnewdt(sol)` ← **dato
capturado**, `da.panel.set_date_only(dt)` ← GUI (stub descarta).

**`sec_prog`** lee: `curr_chart.date`, `state.date.dt.year`, `state.now`, `state.date.dt`,
`da.sec_alltimes`. Escribe: `state.calcdt.setdt(dt)` ← capturado, `state.setprogchart`,
`da.panel.set_date_only`.

### Stub (bosquejo)

```python
# boss_stub.py — corre en Py2 dentro del contenedor
class _Panel:        # absorbe set_date_only sin tocar GUI
    def set_date_only(self, dt): self.captured = dt
class _DA:
    def __init__(self): self.panel = _Panel(); self.sec_alltimes = False
class _Date:         # intercepta getnewdt / setdt
    def getnewdt(self, ds): ...; self.captured_getnewdt = loc; return loc
    def setdt(self, dt): self.captured_setdt = dt
class Boss:
    def __init__(self, ds, epheflag): self.da = _DA(); self.state = _State(ds, epheflag)
```

El stub de `getnewdt`/`setdt` es un espejo del `NeXDate` legacy (idéntico), para que el
golden refleje el comportamiento real. La versión Py3 que portemos a `core/nexdate.py`
se verifica por separado contra el output del stub.

### Flujo del generador

`gen_golden.py` se extiende para, además del ephemeris.json existente, emitir
`directions.json`:

```python
from boss_stub import Boss
import directions as legacy_dir

def dump_directions(datasets):
    out = []
    for c in datasets:
        boss = Boss(c, epheflag=4)
        legacy_dir.solar_rev(boss)
        jd_solrev = boss.solar_jd            # capturado por el stub
        dt_solrev = boss.da.panel.captured
        legacy_dir.sec_prog(boss)
        progdt = boss.state.calcdt.captured_setdt
        out.append({...})
    return out
```

### Datasets fijos (reutilizan los del ephemeris golden + target_year)

`target_year` = año en que se proyectan las direcciones (el "ahora" del usuario).
`now_dt` = fecha/hora concreta dentro de `target_year` usada por la rama
interpolada de `sec_prog` (`sec_alltimes=True`); se fija al 1 de julio del
`target_year` a las 12:00 UTC para todos los casos (determinista).

```json
[
  {"name":"ref1","y":1970,"m":1,"d":1,"h":12.0,"lat":40.4168,"lon":-3.7038,"target_year":2025},
  {"name":"ref2","y":1985,"m":6,"d":15,"h":8.5,"lat":51.5074,"lon":-0.1278,"target_year":2025},
  {"name":"ref3","y":2000,"m":12,"d":31,"h":23.25,"lat":-34.6037,"lon":-58.3816,"target_year":2025},
  {"name":"ref4","y":1969,"m":7,"d":20,"h":20.2833,"lat":48.8566,"lon":2.3522,"target_year":2025}
]
```

Cada caso guarda entradas (lon sol natal, mes/día nacimiento, año objetivo,
`now_dt` fijo) + salidas esperadas (jd_solrev, dt_solrev, progdt,
progdt_alltimes).

### Captura de salidas en el stub (coherencia de nombres)

El stub expone los resultados capturados en atributos fijos que el generador
lee sin ambigüedad:

- `boss.solar_jd` — JD resultante de la convergencia de `solar_rev` (capturado
  vía `revjul` inverso o directamente del último `julday` iterado antes de
  salir; ver implementación).
- `boss.da.panel.captured` — datetime local entregado a `set_date_only`.
- `boss.state.calcdt.captured_setdt` — datetime progresado entregado a `setdt`.

## Verificación (Py3)

```python
GOLDEN = json.load(...golden/directions.json)
def test_solar_rev(c):
    jd = solar_rev(c["natal_sun_lon"], c["target_year"], c["m"], c["d"], epheflag=4)
    assert abs(jd - c["jd_solrev"]) < 1e-5      # ~1 seg
def test_sec_prog(c):
    dt = sec_prog(c["natal_dt_utc"], c["target_year"], sec_alltimes=False)
    assert abs((dt - c["progdt"]).total_seconds()) < 60  # minuto
def test_sec_prog_alltimes(c):
    dt = sec_prog(c["natal_dt_utc"], c["target_year"], sec_alltimes=True, now_dt=c["now_dt"])
    assert abs((dt - c["progdt_alltimes"]).total_seconds()) < 60
def test_getnewdt(...):
    assert abs((nd.getnewdt(ds) - golden).total_seconds()) < 1
```

Tolerancias: solar_rev `1e-5` día (~1 s), sec_prog 60 s (trabaja a minuto).

## Mejoras de robustez/simplicidad (en el paso REFACTOR, golden como árbitro)

| Pieza | Legacy (Py2) | Mejora propuesta | Por qué es segura |
|---|---|---|---|
| `solar_rev` convergencia | Bucle de 6 pasos anidados (0.1→1e-6), offset manual | Portar **verbatim primero**, luego **bisección** (~20 iters) o Newton con velocidad solar | Converge a la misma raíz → mismo JD → pasa golden |
| `sec_prog` rama interpolada | Aritmética manual con nombres crípticos | Misma matemática, `timedelta` nombrado, nombres claros | Output idéntico |
| `print dt, self.tz` en `setdt` | Print de depuración | Eliminar | No afecta cálculo |
| `boss` global | Arg monolítico | **API pura** (args explícitos) | Mejora central del issue |

**Disciplina:** el refactor de bisección se aplica **después** del green verbatim, y solo
se acepta si el golden sigue pasando. Si diverge, se descarta y se queda el verbatim.

## Testing

- `tests/test_directions.py`: parametrizado contra `golden/directions.json` (solar_rev,
  sec_prog ambas ramas, getnewdt).
- `tests/test_nexdate.py`: caso nuevo para `getnewdt`.
- Smoke test de integración: solar_rev → revjul → getnewdt → Chart.calc → export PNG
  (verifica el pipeline entero, no solo la unidad).
- No-regresión: la suite completa (125+ tests) debe seguir verde.

## Plan de tareas (preview)

1. Boss-stub en Docker + extender `gen_golden.py` → `tests/golden/directions.json`.
2. `NeXDate.getnewdt` (TDD contra stub).
3. `core/directions.solar_rev` (TDD verbatim → refactor bisección si pasa golden).
4. `core/directions.sec_prog` (TDD, ambas ramas).
5. Smoke test + QA completa + cerrar issue #16.

## Riesgos

- **Diferencias Py2↔Py3 en aritmética de datetime/timedelta:** mitigado por golden
  generado del original; tolerancias reflejan la granularidad real de la operación.
- **`tz_sup`/historical-DST:** el legacy `setdt`/`getnewdt` rutean por `bisect_right`
  sobre `_utc_transition_times` para nacimientos pre-hora-estándar. El `getnewdt` que
  portamos NO necesita esa rama (convierte UT→local directo); el `setdt` histórico es
  issue #5, no este. Se documenta para no confundir.
- **Bisección que no converge:** fallback al verbatim; el verbatim siempre queda como
  referencia fiel.
