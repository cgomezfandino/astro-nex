# Astro-Nex — Modernización a Python 3 + GTK 3 (Fase 1: port mínimo vertical)

- **Fecha:** 2026-06-26
- **Estado:** Diseño aprobado (pendiente de revisión final del usuario antes del plan de implementación)
- **Autor original del proyecto:** José Antonio Rodríguez (jar@eideia.net) — Astro-Nex 1.2.3, GPLv3
- **Método astrológico:** API = *Astrologisch-Psychologisches Institut* (método de Bruno y Louise Huber)

> ⚠️ Aclaración de terminología: "API" en este proyecto es el **método astrológico Huber**, NO una interfaz de programación. El proyecto original es una app de escritorio, no un servicio web.

## Contexto

El repositorio actual (`Astro-Nex-1.2.3`) es una aplicación de escritorio escrita en **Python 2 + PyGTK 2 + GTK 2 + Cairo**, que calcula y dibuja cartas astrológicas con el método Huber. Usa **Swiss Ephemeris** (vía un wrapper SWIG `_pysw.so` + `pysw.py`), `pytz` para zonas horarias y datos geoespaciales para localidades. Exporta a PNG y PDF.

Problemas para macOS y mantenibilidad:
1. **Python 2** está descontinuado (EOL 2020).
2. **PyGTK 2 / GTK 2** nunca se portaron a Python 3 y están muertos en macOS moderno.
3. El binario `_pysw.so` incluido es **ELF de Linux x86-64** → no carga en macOS (Mach-O). Lo mismo `libswe.a`.

Entorno de desarrollo confirmado: macOS 26.5.1, **Apple Silicon (arm64)**, Python 3.14 (Homebrew), Homebrew y git instalados. La carpeta actual **no** está bajo control de git todavía.

## Decisiones tomadas (brainstorming)

1. **Estrategia:** Modernizar a **Python 3 + GTK 3** (PyGObject), recompilando/usando Swiss Ephemeris moderno (no el `.so` de Linux). Corre nativo en mac/win/linux y queda mantenible.
2. **Primer hito:** **Port mínimo vertical** — flujo central end-to-end, no paridad total de funciones.
3. **Verificación:** levantar el original **una vez** en Docker/VM Linux para generar cartas "golden" de referencia.
4. **Enfoque de estructura:** **B — núcleo limpio sin GUI + shell GTK3 fino**, reutilizando la lógica probada (portar, no reescribir).

## Objetivo del hito (Fase 1)

En macOS Apple Silicon nativo, lograr el flujo completo:

> introducir datos de nacimiento → calcular carta Huber → dibujar la rueda en pantalla (GTK 3) → exportar **PNG y PDF**

…con salidas **verificadas idénticas** al original (golden charts), sin romper Windows/Linux.

## Arquitectura y layout del repositorio nuevo

```
astro-nex/                       (repo nuevo, GPLv3)
├── pyproject.toml               # packaging + dependencias modernas
├── LICENSE (GPLv3)
├── NOTICE                       # crédito al autor original
├── README.md
├── src/astronex/
│   ├── core/        # SIN GTK ni cairo — testeable y reutilizable (Fase 3)
│   │   ├── ephemeris.py   # re-implementa la interfaz de pysw.py sobre pyswisseph
│   │   ├── nexdate.py     # fechas, UT, Julian Day (portado)
│   │   ├── timezones.py   # zona horaria (zoneinfo + tzdata)
│   │   ├── chart.py       # modelo de carta Huber (portado, desacoplado de drawing)
│   │   ├── zodiac.py      # datos zodiacales puros (sin cairo)
│   │   └── directions.py  # age point / direcciones
│   ├── render/      # dibujo cairo puro: recibe un cairo.Context, agnóstico del destino
│   │   ├── wheel.py       # rueda Huber (de roundedcharts/coredraw)
│   │   ├── aspects.py
│   │   └── glyphs.py      # fuente Astro-Nex.ttf
│   ├── surfaces/    # backends de salida: screen (GTK3 DrawingArea), png, pdf
│   ├── gui/         # app GTK3 mínima (PyGObject)
│   │   ├── app.py
│   │   ├── chart_entry.py  # diálogo de datos de nacimiento
│   │   └── chart_view.py   # DrawingArea que pinta con render/
│   ├── data/        # local.db, countries, Astro-Nex.ttf, ephe
│   └── __main__.py  # `python -m astronex`
├── tests/
│   ├── golden/             # cartas de referencia generadas desde el original
│   ├── test_core.py        # compara posiciones/casas/aspectos/age point contra golden
│   └── conftest.py
├── tools/
│   └── original-docker/    # Dockerfile para correr el original (Py2/GTK2) y generar golden
└── docs/
```

### Decisión central de bajo acoplamiento

El `pysw.py` original ya expone una capa Python limpia (`julday`, `revjul`, `calc`, `calc_ut`, `calc_ut_with_speed`, `houses`, `local_houses`, `planets`, `fixstar`, `delta`…). Se **re-implementa esa misma firma** en `core/ephemeris.py` pero sobre `pyswisseph`, de modo que el resto del código portado (sobre todo `chart.py`, 1346 líneas) cambie lo mínimo en sus llamadas.

Acoplamientos a cortar durante el port:
- `chart.py → drawing.roundedcharts` (el cálculo no debe depender del dibujo).
- `zodiac.py → cairo` y `config.py → gtk`.
- Bindings viejos `pango`/`pangocairo` (GTK2) → `gi.repository.Pango` / `PangoCairo` (GTK3) en la capa `render/`.

## Flujo de datos (slice vertical)

1. `gui/chart_entry`: fecha, hora, lugar (lat/long/zona).
2. `core.nexdate` + `core.timezones` → Julian Day en UT.
3. `core.ephemeris` (pyswisseph) → posiciones planetarias + casas.
4. `core.chart.Chart` → modelo Huber (planetas, casas, aspectos, age point).
5. `render/wheel` pinta el modelo en un `cairo.Context`.
6. Un **mismo render** sirve a `surfaces/screen` (pantalla GTK3), `surfaces/png` y `surfaces/pdf`.

## Dependencias

- **`pyswisseph`** (PyPI) — binding mantenido de Swiss Ephemeris con ruedas arm64; reemplaza el `.so` de Linux y `pysw.py`.
- **PyGObject + GTK 3** vía Homebrew (`gtk+3`, `pygobject3`) — GUI.
- **`pycairo`** — dibujo.
- **`zoneinfo`** (stdlib Py3.9+) + **`tzdata`** — zonas horarias (sustituye `pytz`; si el código portado asume API `pytz`, se mantiene `pytz` para minimizar cambios).
- Fuente **`Astro-Nex.ttf`** empaquetada en `data/`.
- Efemérides: por defecto modo **Moshier** (sin archivos `.se1`, vía epheflag); evaluar bundlear un set reducido de `.se1` si se requiere precisión máxima. **Decisión por defecto v1: Moshier** (sin bundlear `.se1`), revisable si la verificación golden muestra desviaciones inaceptables.

## Verificación (golden charts)

- `tools/original-docker/`: Dockerfile basado en una imagen Debian antigua con Python 2.7 + el `_pysw.so` x86-64 existente. Corre el original una sola vez (modo consola `nex.py -c` o script batch) y, para un set fijo de fechas/lugares conocidos, vuelca a JSON: posiciones planetarias, cúspides de casas, aspectos y age point.
- Esos dumps se guardan en `tests/golden/`.
- Los tests comparan la salida del `core` nuevo contra los golden con tolerancia mínima (objetivo ≤ 0.0001°).
- Una vez generados los golden, el desarrollo diario **no** necesita la VM/Docker.

## Testing

- **`pytest`**: unit tests del `core` (efemérides, nexdate/zona horaria, modelo de carta) contra los golden.
- Test de `render`: genera PNG sin crashear; comparación de imagen de referencia opcional.
- CI con GitHub Actions (mac + Linux) — se añade en la Fase 2.

## Licencia

- **Se mantiene GPLv3** (obligatorio porque Swiss Ephemeris / pyswisseph son GPL/AGPL). `LICENSE` en raíz, cabeceras de copyright conservadas, crédito al autor original en `NOTICE`/README.
- **Nota para Fase 3 (startup como servicio):** exponer el software como servicio en red puede activar obligaciones **AGPL** de las versiones modernas de Swiss Ephemeris → habría que liberar el servicio bajo (A)GPL o adquirir la **licencia comercial de Astrodienst**. Se documenta ahora; **no bloquea la Fase 1**.

## Fuera de alcance de este hito (YAGNI)

- Diálogos avanzados: parejas, ciclos, tránsitos completos, lote PDF, plagram, importación, búsqueda, base de datos de cartas guardadas.
- API web / integración con la startup (Fase 3).
- Instaladores `.app` / `.dmg` / empaquetado de distribución (puede añadirse en Fase 2).

## Roadmap general (contexto, fuera de esta spec)

- **Fase 1 (esta spec):** modernizar y correr el slice vertical en macOS.
- **Fase 2:** publicar en GitHub abierto bajo GPLv3 (CI, README, NOTICE, releases) + portar diálogos restantes hacia paridad.
- **Fase 3:** integrar con la startup *Astro Soul Center* (envolver `core/` en CLI/API/servicio; revisar implicaciones AGPL).

## Riesgos y puntos abiertos

- **Diferencias de API entre `pysw` (SWIG) y `pyswisseph`**: se mitiga re-implementando la interfaz exacta en `core/ephemeris.py`.
- **Precisión Moshier vs `.se1`**: la verificación golden lo dirá; plan B = bundlear `.se1`.
- **Render GTK2→GTK3 (pango/pangocairo)**: la parte menos mecánica; se aísla en `render/`.
- **Nombre del repo nuevo**: se asume `astro-nex` (confirmable).
