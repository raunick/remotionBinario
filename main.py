#!/usr/bin/env python3
"""
remotionBinario — OLED Animation Engine CLI.

Usage:
  python main.py scene.yaml
  python main.py scene.yaml --format page
  python main.py scene.yaml --delta
  python main.py scene.yaml --serve --port 5050
  python main.py scene.yaml --no-ascii --no-gif
"""

import argparse
import os
import sys
import time

from oled_animator.dsl import parse_scene, DSLError
from oled_animator.exporters.c_array import export_c_array
from oled_animator.exporters.delta import export_delta
from oled_animator.exporters.gif_preview import save_gif
from oled_animator.exporters.ascii_preview import print_animation


BANNER = r"""
    ╔═══════════════════════════════════════════╗
    ║   remotionBinario  v1.0                   ║
    ║   OLED Animation Engine for MCUs          ║
    ╚═══════════════════════════════════════════╝
"""


def main():
    parser = argparse.ArgumentParser(
        description="remotionBinario — OLED Animation Engine for Microcontrollers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=BANNER,
    )
    parser.add_argument("scene", help="Path to YAML scene file")
    parser.add_argument("--output-dir", "-o", default="output", help="Output directory (default: output)")
    parser.add_argument("--format", "-f", default=None, help="Byte format: horizontal, vertical, page")
    parser.add_argument("--delta", action="store_true", help="Enable delta compression export")
    parser.add_argument("--no-gif", action="store_true", help="Skip GIF generation")
    parser.add_argument("--no-ascii", action="store_true", help="Skip ASCII terminal preview")
    parser.add_argument("--scale", type=int, default=4, help="GIF/Web scale factor (default: 4)")
    parser.add_argument("--dithering", action="store_true", help="Force dithering on all sprites")
    parser.add_argument("--serve", action="store_true", help="Start web preview server")
    parser.add_argument("--port", type=int, default=5050, help="Web preview port (default: 5050)")

    args = parser.parse_args()

    print(BANNER)

    # Parse scene
    print(f"📄 Loading scene: {args.scene}")
    try:
        scene = parse_scene(args.scene)
    except DSLError as e:
        print(f"\n❌ DSL Error: {e}")
        sys.exit(1)
    except FileNotFoundError:
        print(f"\n❌ File not found: {args.scene}")
        sys.exit(1)

    anim = scene["animation"]
    output_opts = scene["output"]

    fmt = args.format or output_opts.get("format", "horizontal")
    do_gif = not args.no_gif and output_opts.get("gif", True)
    do_ascii = not args.no_ascii and output_opts.get("ascii_preview", True)
    do_c_array = output_opts.get("c_array", True)
    do_delta = args.delta or output_opts.get("delta_compression", False)

    # Render
    print(f"🎨 Rendering {anim.total_frames} frames ({anim.width}x{anim.height} @ {anim.fps} FPS)...")
    t0 = time.time()
    frames = anim.render_all()
    elapsed = time.time() - t0
    print(f"   Done in {elapsed:.2f}s ({elapsed / anim.total_frames * 1000:.1f}ms/frame)")

    output_dir = args.output_dir
    os.makedirs(output_dir, exist_ok=True)

    # Web preview (blocks)
    if args.serve:
        from web_preview.server import start_server
        start_server(frames, anim.fps, anim.width, anim.height,
                     port=args.port, scale=args.scale)
        return

    # C-Array export
    if do_c_array:
        h_path = os.path.join(output_dir, "animation.h")
        result = export_c_array(
            frames, h_path, anim.width, anim.height, anim.fps, fmt=fmt,
        )
        print(f"\n📦 C-Array exported: {result['path']}")
        print(f"   Format: {fmt}")
        print(f"   {result['frame_count']} frames × {result['frame_size']} bytes = {result['total_kb']:.2f} KB")

    # Delta export
    if do_delta:
        delta_path = os.path.join(output_dir, "animation_delta.h")
        result = export_delta(
            frames, delta_path, anim.width, anim.height, anim.fps,
        )
        print(f"\n📦 Delta exported: {result['path']}")
        print(f"   Delta: {result['total_bytes']} bytes ({result['total_bytes'] / 1024:.2f} KB)")
        print(f"   Full would be: {result['full_bytes']} bytes ({result['full_bytes'] / 1024:.2f} KB)")
        print(f"   💾 Savings: {result['savings_pct']:.1f}%")

    # GIF
    if do_gif:
        gif_path = os.path.join(output_dir, "preview.gif")
        result = save_gif(frames, gif_path, anim.fps, scale=args.scale)
        if result:
            print(f"\n🎬 GIF saved: {result['path']}")
            print(f"   {result['resolution']} | {result['frame_count']} frames | {result['duration_ms']}ms/frame")

    # ASCII preview
    if do_ascii:
        print(f"\n🖥️  ASCII Preview ({anim.fps} FPS):\n")
        print_animation(frames, anim.fps, loops=1)

    print(f"\n✅ All done! Output in: {os.path.abspath(output_dir)}/")


if __name__ == "__main__":
    main()
