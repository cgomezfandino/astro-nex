#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Assemble a macOS ``Astro-Nex.app`` bundle (HYBRID approach).

The .app embeds the astronex package + launcher + icon + Info.plist and
references the system/Homebrew Python + GTK stack at runtime via env vars in
the launcher. This is robust (no fragile dylib-path rewriting or framework-
Python bundling) at the cost of requiring Homebrew + the GTK stack on the
target Mac. A fully self-contained "embedded" bundle is the spec's longer-term
goal, deferred pending a standalone-Python resolution.

Implements docs/superpowers/specs/2026-06-27-macos-app-bundling-design.md
(hybrid variant). Aditivo y no intrusivo: vive en tools/, never modifies src/,
tests/, or pyproject.toml. The .app is relocatable (works from /Applications
or anywhere) and self-diagnoses on launch failure.

Usage:
    python3 tools/build_macos_app.py               # build + self-verify
    python3 tools/build_macos_app.py --no-verify   # build only

Requirements (auto-checked): Homebrew gtk+3 stack, macOS 11+.
Native tooling: codesign, sips, iconutil (ship with macOS / Xcode CLI).
"""
import os
import shutil
import subprocess
import sys
import sysconfig
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
APP = DIST / "Astro-Nex.app"
CONTENTS = APP / "Contents"
MACOS_DIR = CONTENTS / "MacOS"
RESOURCES = CONTENTS / "Resources"
TMPL = ROOT / "tools" / "macos"

VERSION = "2.0.0.dev0"
BUNDLE_ID = "net.astronex.App"

BREW_PACKAGES = ["gtk+3", "cairo", "glib", "pango", "gdk-pixbuf", "harfbuzz",
                 "libepoxy", "gobject-introspection"]


def run(cmd, **kw):
    r = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if r.returncode != 0:
        raise RuntimeError("command failed: %s\n%s" % (" ".join(map(str, cmd)),
                                                       r.stderr))
    return r


def info(msg):
    print("•", msg)


def warn(msg):
    print("!", msg, file=sys.stderr)


def preflight():
    info("preflight: checking toolchain and Homebrew packages")
    for tool in ("codesign", "sips", "iconutil"):
        if not shutil.which(tool):
            raise RuntimeError("missing native tool: %s (install Xcode CLI)" % tool)
    for pkg in BREW_PACKAGES:
        r = run(["brew", "--prefix", pkg])
        if not r.stdout.strip() or not Path(r.stdout.strip()).exists():
            raise RuntimeError("Homebrew package not found: %s" % pkg)
    # Resolve the Homebrew python3 to invoke at runtime.
    brew = "/opt/homebrew" if Path("/opt/homebrew/bin/python3").exists() else "/usr/local"
    py3 = Path(brew) / "bin" / "python3"
    if not py3.exists():
        raise RuntimeError("Homebrew python3 not found at %s" % py3)
    return str(py3)


def skeleton():
    info("clean dist/ and create bundle skeleton")
    if APP.exists():
        shutil.rmtree(APP)
    for d in (MACOS_DIR, RESOURCES):
        d.mkdir(parents=True, exist_ok=True)


def copy_astronex():
    info("copying astronex package into Resources/")
    dst = RESOURCES / "astronex"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(ROOT / "src" / "astronex", dst,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))


def build_icon():
    info("building Astro-Nex.icns from iconex-48.png")
    src = TMPL / "iconex-48.png"
    iconset = DIST / "Astro-Nex.iconset"
    if iconset.exists():
        shutil.rmtree(iconset)
    iconset.mkdir()
    for s in [16, 32, 64, 128, 256, 512]:
        run(["sips", "-z", str(s), str(s), str(src),
             "--out", str(iconset / ("icon_%dx%d.png" % (s, s)))])
        run(["sips", "-z", str(s * 2), str(s * 2), str(src),
             "--out", str(iconset / ("icon_%dx%d@2x.png" % (s, s)))])
    icns = RESOURCES / "Astro-Nex.icns"
    run(["iconutil", "-c", "icns", str(iconset), "-o", str(icns)])
    shutil.rmtree(iconset)


def write_plist():
    info("writing Info.plist from template")
    tmpl = (TMPL / "Info.plist.tmpl").read_text()
    text = (tmpl.replace("{{BUNDLE_ID}}", BUNDLE_ID)
                .replace("{{VERSION}}", VERSION))
    (CONTENTS / "Info.plist").write_text(text)


def write_launcher(py3):
    info("writing launcher (MacOS/Astro-Nex)")
    tmpl = (TMPL / "launcher.sh.tmpl").read_text()
    text = (tmpl.replace("{{PY_BIN}}", py3)
                .replace("{{ASTRONEX_DIR}}", "$CONTENTS/Resources/astronex")
                .replace("{{VERSION}}", VERSION))
    launcher = MACOS_DIR / "Astro-Nex"
    launcher.write_text(text)
    launcher.chmod(0o755)


def codesign():
    info("ad-hoc signing (codesign -s -)")
    run(["codesign", "-s", "-", "--force", str(APP)])


def self_verify():
    info("self-verification: launching the .app and checking it stays alive")
    subprocess.Popen(["open", "-n", "-a", str(APP)],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    import time
    time.sleep(6)
    r = subprocess.run(["pgrep", "-f", "astronex"], capture_output=True)
    subprocess.run(["pkill", "-f", "astronex"], capture_output=True)
    if r.returncode != 0:
        log = Path.home() / "Library/Logs/Astro-Nex/app.log"
        tail = ""
        if log.exists():
            tail = "\n".join(log.read_text(errors="replace").splitlines()[-20:])
        raise RuntimeError("app did not stay alive. Log tail:\n%s" % tail)
    info("app launched and stayed alive ✓")


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-verify", action="store_true")
    args = ap.parse_args()
    try:
        py3 = preflight()
        skeleton()
        copy_astronex()
        build_icon()
        write_plist()
        write_launcher(py3)
        codesign()
        if not args.no_verify:
            self_verify()
        info("DONE: %s" % APP)
    except Exception as exc:
        warn("BUILD FAILED: %s" % exc)
        if APP.exists():
            shutil.rmtree(APP)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
