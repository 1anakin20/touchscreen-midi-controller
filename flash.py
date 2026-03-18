#!/usr/bin/env python3
"""
flash.py — Generate firmware from a layout JSON and flash it to an Arduino.

Usage:
    python flash.py --config my_layout.json
    python flash.py --config my_layout.json --port COM3
    python flash.py --config my_layout.json --port /dev/cu.usbmodem14101
    python flash.py --config my_layout.json --generate-only
    python flash.py --list-ports

Requirements:
    - Python 3.7+
    - arduino-cli  installed and on your PATH
      Download: https://arduino.github.io/arduino-cli/latest/installation/

arduino-cli first-time setup (run once, not part of this script):
    arduino-cli core update-index
    arduino-cli core install arduino:avr
    arduino-cli lib install "MCUFRIEND_kbv" "Adafruit GFX Library" "TouchScreen"
"""

import argparse
import subprocess
import sys
import os
import tempfile
import shutil
import json
import re
from pathlib import Path


BOARD_FQBN = "arduino:avr:uno"   # Arduino Uno — change for other boards


# ── Port detection ────────────────────────────────────────────────────────────

def list_ports() -> list[dict]:
    """Ask arduino-cli for connected boards."""
    try:
        result = subprocess.run(
            ["arduino-cli", "board", "list", "--format", "json"],
            capture_output=True, text=True, check=True
        )
        data = json.loads(result.stdout)
        # arduino-cli ≥0.35 nests under "detected_ports"
        ports = data.get("detected_ports", data) if isinstance(data, dict) else data
        return ports if isinstance(ports, list) else []
    except (subprocess.CalledProcessError, json.JSONDecodeError, FileNotFoundError):
        return []

def find_arduino_port() -> str | None:
    """Return the first port that looks like an Arduino Uno."""
    ports = list_ports()
    for entry in ports:
        # Handle nested structure across different arduino-cli versions
        port_info = entry.get("port", entry)
        address   = port_info.get("address", "")
        boards    = entry.get("matching_boards", [])
        for b in boards:
            if "uno" in b.get("name", "").lower() or "uno" in b.get("fqbn", "").lower():
                return address
        # Fallback: any port with a known Arduino VID
        protocol_label = port_info.get("protocol_label", "")
        if "Arduino" in protocol_label or "usb" in port_info.get("protocol", "").lower():
            if address:
                return address
    return None

def print_ports():
    ports = list_ports()
    if not ports:
        print("No boards detected. Is the Arduino connected?")
        print("(arduino-cli must be installed and on PATH)")
        return
    print(f"{'PORT':<30}  {'BOARD':<30}  {'FQBN'}")
    print("-" * 80)
    for entry in ports:
        port_info = entry.get("port", entry)
        address   = port_info.get("address", "?")
        boards    = entry.get("matching_boards", [])
        if boards:
            for b in boards:
                print(f"{address:<30}  {b.get('name','?'):<30}  {b.get('fqbn','?')}")
        else:
            print(f"{address:<30}  {'(unknown)':<30}")


# ── Compile & upload ──────────────────────────────────────────────────────────

def check_arduino_cli():
    if shutil.which("arduino-cli") is None:
        print("Error: arduino-cli not found on PATH.")
        print("")
        print("Install it from: https://arduino.github.io/arduino-cli/latest/installation/")
        print("")
        print("Then run once:")
        print("  arduino-cli core update-index")
        print("  arduino-cli core install arduino:avr")
        print('  arduino-cli lib install "MCUFRIEND_kbv" "Adafruit GFX Library" "TouchScreen"')
        sys.exit(1)

def compile_and_upload(sketch_path: str, port: str, verbose: bool = False):
    """Compile the sketch and upload to the Arduino."""
    sketch_dir = str(Path(sketch_path).parent)

    print(f"Compiling {sketch_path} ...")
    compile_cmd = [
        "arduino-cli", "compile",
        "--fqbn", BOARD_FQBN,
        sketch_dir
    ]
    if verbose:
        compile_cmd.append("--verbose")

    result = subprocess.run(compile_cmd, capture_output=not verbose, text=True)
    if result.returncode != 0:
        print("Compilation failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print("✓  Compiled successfully")

    print(f"Uploading to {port} ...")
    upload_cmd = [
        "arduino-cli", "upload",
        "--fqbn", BOARD_FQBN,
        "--port", port,
        sketch_dir
    ]
    if verbose:
        upload_cmd.append("--verbose")

    result = subprocess.run(upload_cmd, capture_output=not verbose, text=True)
    if result.returncode != 0:
        print("Upload failed:")
        print(result.stdout)
        print(result.stderr)
        sys.exit(1)
    print("✓  Upload complete — your controller is ready!")


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate and flash Arduino MIDI controller firmware from a layout JSON.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python flash.py --config my_layout.json
  python flash.py --config my_layout.json --port COM3
  python flash.py --config my_layout.json --generate-only
  python flash.py --list-ports
        """
    )
    parser.add_argument("--config",        "-c", help="Path to layout JSON file")
    parser.add_argument("--port",          "-p", help="Arduino serial port (e.g. COM3 or /dev/cu.usbmodem...)")
    parser.add_argument("--output",        "-o", help="Override output .ino path")
    parser.add_argument("--generate-only", "-g", action="store_true",
                        help="Only generate the .ino, do not compile or flash")
    parser.add_argument("--list-ports",    "-l", action="store_true",
                        help="List connected Arduino boards and exit")
    parser.add_argument("--verbose",       "-v", action="store_true",
                        help="Show full arduino-cli output")
    parser.add_argument("--board",         "-b", default=BOARD_FQBN,
                        help=f"Board FQBN (default: {BOARD_FQBN})")
    args = parser.parse_args()

    # ── List ports mode ──────────────────────────────────────────
    if args.list_ports:
        check_arduino_cli()
        print_ports()
        return

    # ── Need a config for everything else ────────────────────────
    if not args.config:
        parser.print_help()
        sys.exit(1)

    if not os.path.exists(args.config):
        print(f"Error: config file not found: {args.config}")
        sys.exit(1)

    # ── Step 1: Generate firmware ────────────────────────────────
    # Import generate module from same directory as flash.py
    script_dir = Path(__file__).parent
    sys.path.insert(0, str(script_dir))
    from generate import generate

    config_stem = Path(args.config).stem
    output_path = args.output or f"firmware/{config_stem}/{config_stem}.ino"

    print(f"Reading config: {args.config}")
    generate(args.config, output_path)

    if args.generate_only:
        print(f"\nSketch written to: {output_path}")
        print("To compile and upload manually:")
        print(f"  arduino-cli compile --fqbn {args.board} {Path(output_path).parent}")
        print(f"  arduino-cli upload  --fqbn {args.board} --port <PORT> {Path(output_path).parent}")
        return

    # ── Step 2: Check arduino-cli ────────────────────────────────
    check_arduino_cli()

    # ── Step 3: Resolve port ─────────────────────────────────────
    port = args.port
    if not port:
        print("No port specified — auto-detecting Arduino...")
        port = find_arduino_port()
        if port:
            print(f"Found Arduino at: {port}")
        else:
            print("Could not auto-detect Arduino port.")
            print("")
            print("Run:  python flash.py --list-ports")
            print("Then: python flash.py --config my_layout.json --port <PORT>")
            sys.exit(1)

    # ── Step 4: Compile & upload ─────────────────────────────────
    compile_and_upload(output_path, port, verbose=args.verbose)


if __name__ == "__main__":
    main()
