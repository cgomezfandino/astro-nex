# Astro-Nex — macOS `.app` Bundling

**Date:** 2026-06-27
**Status:** Approved (pending implementation)
**Scope:** Phase 2 — Packaging (subset). Aditivo; no modifica código fuente.

## Objetivo

Entregar una aplicación macOS **autocontenida** `Astro-Nex.app` que se instala y
abre con **doble clic** (icono en Dock), sin requerir que el usuario instale nada.
Se añade macOS como *target* de distribución **sin romper** el soporte multiplataforma
existente (Windows, Linux y macOS-por-terminal siguen funcionando igual).

## Contexto

La Fase 1 (port a Python 3 + GTK 3) está cerrada y verificada:
52 tests pasan, la GUI importa y arranca, y el pipeline de cálculo → render →
export PNG/PDF funciona end-to-end en macOS Apple Silicon (Python 3.14 arm64).

Hoy la app solo se lanza por terminal (`astronex` / `python -m astronex`) y depende de
un venv + las librerías de Homebrew (gtk+3, cairo, glib, pango, gdk-pixbuf, harfbuzz,
libepoxy, gobject-introspection). El binario original `_pysw.so` (ELF x86-64 de Linux)
fue sustituido por la wheel nativa `pyswisseph`.

Lo que falta para "ejecutable en macOS" = **empaquetar** todo eso en un `.app`.

## Requisitos

### Funcionales
- **R1** Doble clic en `Astro-Nex.app` abre la ventana (sin terminal, sin instalar deps).
- **R2** App **autocontenida**: GTK, cairo, pyswisseph, etc. embebidos; sin dependencias
  externas en tiempo de ejecución.
- **R3** Icono propio en Dock, Finder y `Cmd-Tab`.
- **R4** **Relocatable**: se puede mover a `/Applications` (u otra ruta) sin romperse.
- **R5** Diagnóstico en fallos: si el arranque falla, mostrar un diálogo con el error y
  dejar log en `~/Library/Logs/Astro-Nex/app.log` (no crash silencioso).
- **R6** Firma **ad-hoc** local (`codesign -s -`) para ejecución sin fricción en la
  máquina de build. Firma Developer ID / notarización **fuera de alcance** (ver issue
  de seguimiento).

### No funcionales
- **N1** **Aditivo y no intrusivo**: el build vive en `tools/` y **nunca** modifica
  `src/`, `tests/` ni `pyproject.toml`. El flujo Windows/Linux/macOS-terminal no cambia.
- **N2** **Idempotente y reproducible**: borrar `dist/` y re-correr el build da el mismo
  resultado. Fallo a mitad → limpieza y repo intacto.
- **N3** **Opt-in**: solo quien quiere el `.app` corre el build. Los demás siguen con
  `pip install -e .` + `astronex`.
- **N4** Build **auto-verificado**: lanza la app en background y comprueba que arranca;
  solo declara éxito si queda corriendo.
- **N5** Tras el build, la suite de tests debe seguir pasando (verificación de
  no-regresión multiplataforma).

### Fuera de alcance (este hito)
- Firma Developer ID y notarización (issue de seguimiento).
- Empaquetado `.dmg` instalable (issue de seguimiento).
- Funcionalidad de la Fase 2 (age point Huber, paridad visual, diálogos, DB).

## Arquitectura del bundle

```
dist/Astro-Nex.app/
└── Contents/
    ├── Info.plist                          # metadata, bundle id, icono, high-res
    ├── Resources/
    │   ├── Astro-Nex.icns                  # icono (generado de iconex-48.png)
    │   └── astro-nex-launcher.sh           # wrapper que fija entorno GTK antes de python
    └── MacOS/
        ├── Astro-Nex                       # ejecutable = copia del launcher (chmod +x)
        └── Astro-Nex.bin/                  # árbol privado, todo @executable_path
            ├── python3.14                  # intérprete standalone (del venv)
            ├── lib/python3.14/             # stdlib + site-packages
            │   └── site-packages/          # astronex (copiado), pyswisseph, pycairo, PyGObject…
            └── lib/                        # dylibs GTK relocatizadas
                ├── libgtk-3.0.dylib, libcairo-2.dylib, libglib-2.0.dylib,
                │   libpango-1.0.dylib, libgdk_pixbuf-2.0.dylib, libepoxy.dylib, harfbuzz…
                ├── girepository-1.0/       # typelibs GI (Gtk-3.0.typelib, …)
                ├── gdk-pixbuf-2.0/         # cargadores de imagen (loaders + loaders.cache)
                └── schemas/                # glib schemas compilados (gschemas_compiled)
```

**Principio de aislamiento:** todo lo que el proceso necesita vive bajo
`Contents/MacOS/`. Ninguna ruta externa (ni `/opt/homebrew`) se referencia en
tiempo de ejecución.

## Componentes

### 1. `tools/build_macos_app.py` (NUEVO)
Script Python idempotente que ensambla el bundle. Pasos:

1. **Prechequeos**: detecta prefijos Homebrew (`brew --prefix <pkg>` para gtk+3, cairo,
   glib, pango, gdk-pixbuf, harfbuzz, libepoxy, gobject-introspection, pygobject3).
   Falla con mensaje accionable si falta algo. Confirma arquitectura (arm64/intel) y
   versión de Python.
2. **Limpieza + esqueleto**: borra `dist/`, crea `Contents/{MacOS,Resources}`.
3. **Copia intérprete**: copia el Python del venv + stdlib + `site-packages`. Convierte
   la instalación *editable* de `astronex` a copia real (resuelve el `.pth`/`__edit__`).
4. **Copia árbol GTK** de Homebrew:
   - `.dylib` del runtime (gtk, cairo, glib, pango, gdk-pixbuf, harfbuzz, epoxy, …).
   - typelibs GI (`Gtk-3.0.typelib` y dependencias).
   - cargadores gdk-pixbuf + `loaders.cache`.
   - schemas glib compilados.
   - recurso `src/astronex/data/Astro-Nex.ttf` → `Resources/`.
5. **Reescritura de dylib paths** con `install_name_tool` (la parte delicada):
   - `-id @executable_path/Astro-Nex.bin/lib/<name>` para cada dylib/so del bundle.
   - `-change /opt/homebrew/... @rpath/<name>` por cada dependencia referenciada.
   - Fija `LC_RPATH` del intérprete a `@executable_path/Astro-Nex.bin/lib`.
6. **Icono**: genera `Astro-Nex.icns` desde `iconex-48.png` con `sips` + `iconutil`
   (nativos de macOS, sin dependencias nuevas).
7. **Info.plist**: desde plantilla (bundle id `net.astronex.App`, versión, `LSMinimumSystemVersion`,
   `NSHighResolutionCapable`, `CFBundleIconFile`).
8. **Launcher**: escribe `astro-nex-launcher.sh` desde plantilla y lo copia como
   `MacOS/Astro-Nex` (chmod 0755).
9. **Firma ad-hoc**: `codesign -s - --force --deep dist/Astro-Nex.app`.
10. **Validación automática**: lanza el `.app` en background con timeout corto y comprueba
    que el proceso queda vivo (no crash inmediato). Aborta con log si falla.

### 2. `tools/macos/Info.plist.tmpl` (NUEVO)
Plantilla del plist. Variables sustituidas por el script: `{{VERSION}}`,
`{{BUNDLE_ID}}`, `{{ICON}}`.

### 3. `tools/macos/launcher.sh.tmpl` (NUEVO)
Plantilla del wrapper bash. Fija entorno y lanza python. Variables: `{{PY_BIN}}`,
`{{LIB_DIR}}`, `{{GI_TYPELIB_PATH}}`, etc.

### 4. `tools/macos/Astro-Nex.icns` (NUEVO)
Icono multi-resolución generado de `iconex-48.png`.

## El launcher — robustez de arranque

Responsabilidades, en orden:

1. **Entorno aislado** — fija las variables **solo** a rutas dentro del bundle:
   - `DYLD_LIBRARY_PATH`, `DYLD_FALLBACK_LIBRARY_PATH` → dylibs del bundle.
   - `GI_TYPELIB_PATH` → typelibs embebidos.
   - `GTK_PATH`, `GDK_PIXBUF_MODULE_FILE`, `GTK_IM_MODULE_FILE` → cargadores del bundle.
   - `XDG_DATA_DIRS` → schemas y recursos compartidos del bundle.
   - `LANG`/`LC_*` → locales del sistema (legado de i18n del original).
2. **Diagnóstico en fallos** — si la import de GTK o el arranque fallan, captura stderr,
   escribe `~/Library/Logs/Astro-Nex/app.log` y muestra un diálogo nativo de macOS
   (`osascript -e 'display dialog …'`) con el error. Nunca crash silencioso.
3. **Instancia única** — lockfile simple (`/tmp/astro-nex.lock`) para evitar ventanas
   duplicadas en doble-clic repetido.

## Verificación

- **Build auto-verificado (R1/R2/R4)**: tras ensamblar, el script lanza el `.app` en
  background con timeout y comprueba que el proceso queda vivo. Solo éxito si arranca.
- **No-regresión multiplataforma (N5)**: tras el build, correr `pytest` desde el venv
  normal (sin tocar el bundle) → los 52 tests deben seguir pasando, confirmando que
  `src/` está intacto.
- **Relocatable (R4)**: mover `dist/Astro-Nex.app` a `/Applications` y abrir con doble
  clic → debe arrancar.
- **Diagnóstico (R5)**: probar el camino de error inyectando un dylib roto y verificar
  que aparece el diálogo + log.

## Riesgos y mitigaciones

| Riesgo | Mitigación |
|---|------| 
| Reescribir dylib paths es delicado; error → app no carga | `otool -L` por cada binario para detectar dependencias referenciadas; iterar hasta cierre transitivo. Build aborta con diagnóstico si `DYLD` resuelve algo fuera del bundle. |
| PyGObject en arm64 puede tener typelibs faltantes | Copiar el set completo de typelibs de `Gtk-3.0.typelib` + dependencias; validación de arranque lo detecta. |
| El intérprete embebido puede buscar stdlib en ruta absoluta | Fijar `PYTHONHOME`/`PYTHONPATH` en el launcher a rutas del bundle; validar. |
| `iconutil`/`sips` asumen PNG con alpha correcto | Verificar formato de `iconex-48.png` (ya es RGBA 48×48); generar iconset multi-resolución. |
| Firma ad-hoc no abre en otra Mac (Gatekeeper) | Documentado: firma Developer ID/notarización es el issue de seguimiento. En la Mac de build funciona sin fricción. |

## Entregables

| Entregable | Descripción |
|---|---|
| `tools/build_macos_app.py` | Script de build idempotente y auto-verificado |
| `tools/macos/Info.plist.tmpl` | Plantilla del plist |
| `tools/macos/launcher.sh.tmpl` | Plantilla del wrapper con robustez |
| `tools/macos/Astro-Nex.icns` | Icono multi-resolución |
| `dist/Astro-Nex.app` | App autocontenida (generada, no versionada) |
| `.gitignore` (entrada `dist/`) | Evitar commitear el bundle |
| Issue de seguimiento | `.dmg` + firma/notarización (milestone Phase 2) |
| Tests de no-regresión | `pytest` pasa tras el build |

## Seguimiento (fuera de este hito)

Issue en milestone **Phase 2 — Feature parity & community release** para:
- Empaquetado `.dmg` instalable.
- Firma Developer ID + notarización (requiere cuenta Apple Developer, ~99 USD/año).
