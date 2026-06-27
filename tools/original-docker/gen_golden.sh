#!/usr/bin/env bash
# Regenerate the golden reference data from the ORIGINAL legacy engine.
#
# This runs the unmodified Python 2 legacy code (pysw + directions + utils)
# inside the Docker container and emits JSON the Python 3 port is verified
# against. Deterministic: Moshier ephemeris (EPHEFLAG=4), fixed inputs.
#
# Usage:
#   ./gen_golden.sh                # regenerate ALL golden files
#   ./gen_golden.sh ephemeris      # only tests/golden/ephemeris.json
#   ./gen_golden.sh directions     # only tests/golden/directions.json
#   ./gen_golden.sh chart_types    # only tests/golden/chart_types.json
set -euo pipefail

DIR="$(cd "$(dirname "$0")" && pwd)"
ROOT="$(cd "$DIR/../.." && pwd)"   # repo root (astro-nex)
LEGACY="$ROOT/../Astro-Nex-1.2.3/astronex"
MODE="${1:-all}"

# Stage the legacy source into the build context (gitignored at runtime).
cp "$LEGACY/utils.py"       "$DIR/legacy/"
cp "$LEGACY/directions.py"  "$DIR/legacy/"
cp "$LEGACY/nexdate.py"     "$DIR/legacy/"
cp "$LEGACY/tz_sup.py"      "$DIR/legacy/"
cp "$LEGACY/chart.py"       "$DIR/legacy/"
# chart.py imports drawing (GUI/cairo, unavailable headless); that import is
# unused by the Tier-A pure methods we exercise, so strip it for the container.
python3 -c "
p='$DIR/legacy/chart.py'
lines=[l for l in open(p).read().splitlines() if 'roundedcharts' not in l]
open(p,'w').write('\n'.join(lines)+'\n')
"

docker build --platform linux/amd64 -t astronex-golden "$DIR"

run() {  # run <mode> <out-subpath>
  local mode="$1" out="$2"
  mkdir -p "$DIR/out"
  docker run --rm --platform linux/amd64 --entrypoint python2.7 \
    -v "$DIR/out:/out" astronex-golden \
    gen_golden.py datasets.json "/out/$out" "$mode"
  cp "$DIR/out/$out" "$ROOT/tests/golden/$out"
  echo "wrote tests/golden/$out"
}

case "$MODE" in
  all)        run ephemeris   ephemeris.json
              run directions  directions.json
              run chart_types chart_types.json ;;
  ephemeris)  run ephemeris   ephemeris.json ;;
  directions) run directions  directions.json ;;
  chart_types) run chart_types chart_types.json ;;
  *) echo "unknown mode: $MODE (use all|ephemeris|directions|chart_types)"; exit 1 ;;
esac
