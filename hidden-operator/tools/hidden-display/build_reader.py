#!/usr/bin/env python3
"""Build the committed reader with JDK 21 / Android SDK 36 / D8 36.0.0.

--check rebuilds in a temporary directory and requires identical dex bytes.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import tempfile


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    here = Path(__file__).resolve().parent
    sdk = Path(os.environ.get("ANDROID_HOME") or os.environ.get("ANDROID_SDK_ROOT") or "")
    android = sdk / "platforms/android-36/android.jar"
    d8 = sdk / "build-tools/36.0.0/lib/d8.jar"
    java_home = os.environ.get("JAVA_HOME")
    suffix = ".exe" if os.name == "nt" else ""
    javac = str(Path(java_home) / ("bin/javac" + suffix)) if java_home else shutil.which("javac")
    java = str(Path(java_home) / ("bin/java" + suffix)) if java_home else shutil.which("java")
    if not android.is_file() or not d8.is_file() or not java or not javac:
        raise SystemExit("Need JAVA_HOME (JDK 21) and ANDROID_HOME with platforms;android-36 and build-tools;36.0.0")
    compiler = subprocess.check_output([javac, "-version"], text=True, stderr=subprocess.STDOUT).strip()
    if not compiler.startswith("javac 21."):
        raise SystemExit("Reproducible reader build requires JDK 21; found " + compiler)
    with tempfile.TemporaryDirectory(prefix="agent-bridge-reader-") as temp:
        classes, dex = Path(temp) / "classes", Path(temp) / "dex"
        classes.mkdir(); dex.mkdir()
        subprocess.run([javac, "--release", "8", "-g:none", "-cp", str(android), "-d", str(classes), str(here / "UD.java")], check=True)
        subprocess.run([java, "-cp", str(d8), "com.android.tools.r8.D8", "--min-api", "34", "--lib", str(android),
                        "--output", str(dex), *map(str, sorted(classes.glob("*.class")))], check=True)
        built = (dex / "classes.dex").read_bytes()
        if args.check:
            if built != (here / "ud.dex").read_bytes():
                raise SystemExit("ud.dex does not match the checked-in Java source; rebuild with the pinned toolchain")
        else:
            (here / "ud.dex").write_bytes(built)
        print("Reader dex verified:" if args.check else "Reader dex built:", hashlib.sha256(built).hexdigest())


if __name__ == "__main__":
    main()
