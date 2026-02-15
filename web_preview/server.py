"""
remotionBinario Studio — Full Dashboard Server.

Integrates: Python animation engine + Node.js SVG importer.
Usage: python main.py --serve
"""

import os
import io
import json
import glob
import base64
import tempfile
import subprocess
import traceback
from concurrent.futures import ThreadPoolExecutor

from flask import (
    Flask, render_template, jsonify, request, send_file, abort
)

# Import the engine
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from oled_animator.dsl import parse_scene, DSLError
from oled_animator.exporters.c_array import export_c_array
from oled_animator.exporters.delta import export_delta
from oled_animator.exporters.gif_preview import save_gif

# Paths
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
EXAMPLES_DIR = os.path.join(BASE_DIR, "examples")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")
SVG_IMPORTER = os.path.join(BASE_DIR, "tools", "svg_importer", "svg2sprite.js")

# Ensure directories exist
os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Thread pool for non-blocking renders
executor = ThreadPoolExecutor(max_workers=2)


def create_app():
    """Create Flask app for the Studio Dashboard."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16MB max upload

    # ───────────────────────────────────
    # Dashboard
    # ───────────────────────────────────
    @app.route("/")
    def index():
        return render_template("dashboard.html")

    # ───────────────────────────────────
    # Scene Management
    # ───────────────────────────────────
    @app.route("/api/scenes")
    def list_scenes():
        """List all YAML scene files recursively."""
        scenes = []
        for root, dirs, files in os.walk(EXAMPLES_DIR):
            for f in sorted(files):
                if f.endswith((".yaml", ".yml")):
                    full = os.path.join(root, f)
                    rel = os.path.relpath(full, EXAMPLES_DIR)
                    scenes.append({
                        "name": rel,
                        "path": full,
                        "size": os.path.getsize(full),
                    })
        return jsonify(scenes)

    @app.route("/api/scenes/<path:name>", methods=["GET"])
    def get_scene(name):
        """Read a YAML scene file."""
        fpath = os.path.join(EXAMPLES_DIR, name)
        if not os.path.isfile(fpath):
            abort(404)
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        return jsonify({"name": name, "content": content})

    @app.route("/api/scenes/<path:name>", methods=["PUT"])
    def save_scene(name):
        """Save/update a YAML scene file."""
        fpath = os.path.join(EXAMPLES_DIR, name)
        data = request.get_json()
        content = data.get("content", "")
        os.makedirs(os.path.dirname(fpath), exist_ok=True)
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(content)
        return jsonify({"status": "ok", "name": name})

    # ───────────────────────────────────
    # Render Engine
    # ───────────────────────────────────
    @app.route("/api/render", methods=["POST"])
    def render_scene():
        """Render YAML content and return base64 frames."""
        data = request.get_json()
        yaml_content = data.get("yaml", "")
        scale = data.get("scale", 4)

        if not yaml_content.strip():
            return jsonify({"error": "Empty YAML"}), 400

        try:
            # Write to temp file for the DSL parser
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False, dir=EXAMPLES_DIR
            ) as tmp:
                tmp.write(yaml_content)
                tmp_path = tmp.name

            scene = parse_scene(tmp_path)
            anim = scene["animation"]
            frames_canvas = anim.render_all()

            # Convert to base64
            frame_data = []
            for canvas in frames_canvas:
                img = canvas.get_image().convert("L")
                scaled = img.resize(
                    (anim.width * scale, anim.height * scale), 0
                )
                buf = io.BytesIO()
                scaled.save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                frame_data.append(b64)

            # Calculate memory stats
            frame_bytes = (anim.width * anim.height) // 8
            total_bytes = frame_bytes * anim.total_frames
            esp32_flash = 4 * 1024 * 1024  # 4MB

            result = {
                "fps": anim.fps,
                "width": anim.width,
                "height": anim.height,
                "scaled_width": anim.width * scale,
                "scaled_height": anim.height * scale,
                "frame_count": len(frame_data),
                "frames": frame_data,
                "memory": {
                    "frame_bytes": frame_bytes,
                    "total_bytes": total_bytes,
                    "total_kb": round(total_bytes / 1024, 2),
                    "flash_pct": round((total_bytes / esp32_flash) * 100, 2),
                },
            }
            return jsonify(result)

        except DSLError as e:
            return jsonify({"error": f"DSL Error: {str(e)}"}), 400
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    # ───────────────────────────────────
    # SVG Import (calls Node.js)
    # ───────────────────────────────────
    @app.route("/api/svg-import", methods=["POST"])
    def svg_import():
        """Import an SVG file via svg2sprite.js."""
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename.lower().endswith(".svg"):
            return jsonify({"error": "Only SVG files accepted"}), 400

        # Save uploaded SVG to assets
        svg_path = os.path.join(ASSETS_DIR, file.filename)
        file.save(svg_path)

        # Options from form
        width = request.form.get("width", "64")
        dither = request.form.get("dither", "false") == "true"
        invert = request.form.get("invert", "false") == "true"

        # Build command
        cmd = ["node", SVG_IMPORTER, svg_path, "--width", width, "--c-header"]
        if dither:
            cmd.append("--dither")
        if invert:
            cmd.append("--invert")

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=30
            )
            output = result.stdout + result.stderr

            # Find generated files
            basename = os.path.splitext(file.filename)[0]
            generated = {
                "svg": svg_path,
                "preview": None,
                "header": None,
                "output": output,
            }

            preview_path = os.path.join(ASSETS_DIR, f"{basename}_preview.png")
            header_path = os.path.join(ASSETS_DIR, f"{basename}.h")

            if os.path.exists(preview_path):
                generated["preview"] = f"/api/assets/{basename}_preview.png"
            if os.path.exists(header_path):
                generated["header"] = f"/api/assets/{basename}.h"

            # Generate YAML snippet
            generated["yaml_snippet"] = (
                f"  - type: sprite\n"
                f"    id: {basename}\n"
                f"    props:\n"
                f"      x: 0\n"
                f"      y: 0\n"
                f"      src: \"assets/{basename}_preview.png\"\n"
            )

            return jsonify(generated)

        except subprocess.TimeoutExpired:
            return jsonify({"error": "SVG processing timed out"}), 500
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    # ───────────────────────────────────
    # Assets Library
    # ───────────────────────────────────
    @app.route("/api/assets")
    def list_assets():
        """List all assets (sprites, PNGs, headers)."""
        assets = []
        if os.path.isdir(ASSETS_DIR):
            for f in sorted(os.listdir(ASSETS_DIR)):
                fpath = os.path.join(ASSETS_DIR, f)
                if os.path.isfile(fpath):
                    ext = os.path.splitext(f)[1].lower()
                    assets.append({
                        "name": f,
                        "type": ext,
                        "size": os.path.getsize(fpath),
                        "url": f"/api/assets/{f}",
                    })
        return jsonify(assets)

    @app.route("/api/assets/<path:name>")
    def get_asset(name):
        """Serve an asset file."""
        fpath = os.path.join(ASSETS_DIR, name)
        if not os.path.isfile(fpath):
            abort(404)
        return send_file(fpath)

    # ───────────────────────────────────
    # Export
    # ───────────────────────────────────
    @app.route("/api/export", methods=["POST"])
    def export_scene():
        """Export current YAML to C-array, GIF, or Delta."""
        data = request.get_json()
        yaml_content = data.get("yaml", "")
        fmt = data.get("format", "horizontal")
        export_type = data.get("type", "c_array")  # c_array, gif, delta

        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".yaml", delete=False, dir=EXAMPLES_DIR
            ) as tmp:
                tmp.write(yaml_content)
                tmp_path = tmp.name

            scene = parse_scene(tmp_path)
            anim = scene["animation"]
            frames = anim.render_all()

            if export_type == "c_array":
                out_path = os.path.join(OUTPUT_DIR, "animation.h")
                result = export_c_array(
                    frames, out_path, anim.width, anim.height, anim.fps, fmt=fmt
                )
                return send_file(
                    out_path,
                    as_attachment=True,
                    download_name="animation.h",
                    mimetype="text/plain",
                )

            elif export_type == "delta":
                out_path = os.path.join(OUTPUT_DIR, "animation_delta.h")
                result = export_delta(
                    frames, out_path, anim.width, anim.height, anim.fps
                )
                return send_file(
                    out_path,
                    as_attachment=True,
                    download_name="animation_delta.h",
                    mimetype="text/plain",
                )

            elif export_type == "gif":
                out_path = os.path.join(OUTPUT_DIR, "preview.gif")
                result = save_gif(frames, out_path, anim.fps, scale=4)
                return send_file(
                    out_path,
                    as_attachment=True,
                    download_name="preview.gif",
                    mimetype="image/gif",
                )

            else:
                return jsonify({"error": f"Unknown export type: {export_type}"}), 400

        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500
        finally:
            try:
                os.unlink(tmp_path)
            except:
                pass

    # ───────────────────────────────────
    # Image2CPP Features
    # ───────────────────────────────────
    @app.route("/api/image2cpp/convert", methods=["POST"])
    def image2cpp_convert():
        """Convert uploaded image(s) or ZIP to 1-bit Canvas & C-array."""
        if "file" not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files["file"]
        if not file.filename:
            return jsonify({"error": "No filename"}), 400

        # Settings
        settings = {
            "width": int(request.form.get("width", 128)),
            "height": int(request.form.get("height", 64)),
            "background": request.form.get("background", "black"),
            "scale_mode": request.form.get("scale_mode", "fit"),
            "dither": request.form.get("dither", "floyd-steinberg"),
            "threshold": int(request.form.get("threshold", 128)),
            "invert": request.form.get("invert", "false") == "true",
            "rotate": int(request.form.get("rotate", 0)),
        }

        try:
            results = []
            filename = file.filename.lower()

            if filename.endswith(".zip"):
                from oled_animator.image_converter import process_zip
                # Read zip into memory
                file_bytes = io.BytesIO(file.read())
                processed_list = process_zip(file_bytes, settings)
                
                for item in processed_list:
                    # Render to C-array
                    c_data = item["canvas"].to_bytes("horizontal") # Default preview format
                    
                    # Convert preview to base64
                    buf = io.BytesIO()
                    item["preview_image"].save(buf, format="PNG")
                    b64 = base64.b64encode(buf.getvalue()).decode("ascii")
                    
                    results.append({
                        "name": item["name"],
                        "preview": b64,
                        "c_array": list(c_data), # Send as list of ints for frontend to format
                        "width": item["width"],
                        "height": item["height"]
                    })
            
            else:
                from oled_animator.image_converter import process_image
                # Process single image
                file_bytes = io.BytesIO(file.read())
                item = process_image(file_bytes, file.filename, settings)
                
                if "error" in item:
                    return jsonify({"error": item["error"]}), 400

                c_data = item["canvas"].to_bytes("horizontal")
                buf = io.BytesIO()
                item["preview_image"].save(buf, format="PNG")
                b64 = base64.b64encode(buf.getvalue()).decode("ascii")

                results.append({
                    "name": item["name"],
                    "preview": b64,
                    "c_array": list(c_data),
                    "width": item["width"],
                    "height": item["height"]
                })

            return jsonify({"results": results})

        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500

    @app.route("/api/image2cpp/reverse", methods=["POST"])
    def image2cpp_reverse():
        """Convert C-array hex string back to image preview."""
        data = request.get_json()
        hex_string = data.get("hex", "")
        width = int(data.get("width", 128))
        height = int(data.get("height", 64))
        mode = data.get("mode", "horizontal")

        try:
            from oled_animator.image_converter import bytes_to_image
            img = bytes_to_image(hex_string, width, height, mode)
            
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            b64 = base64.b64encode(buf.getvalue()).decode("ascii")
            
            return jsonify({"preview": b64})
            
        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": str(e)}), 500


    return app


def start_server(port: int = 5050):
    """Start the Studio Dashboard server."""
    app = create_app()
    print(f"\n🚀 remotionBinario Studio")
    print(f"   http://localhost:{port}")
    print(f"   Scenes: {EXAMPLES_DIR}")
    print(f"   Assets: {ASSETS_DIR}")
    print(f"   Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=port, debug=False)
