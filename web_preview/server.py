"""
Web Preview Server — Flask-based browser preview for animations.

Usage: python main.py scene.yaml --serve --port 5050
"""

import os
import io
import json
import base64
from flask import Flask, render_template, jsonify


def create_app(frames: list, fps: int, width: int, height: int, scale: int = 4):
    """Create Flask app for previewing animations in the browser."""
    template_dir = os.path.join(os.path.dirname(__file__), "templates")
    app = Flask(__name__, template_folder=template_dir)

    frame_data = []
    for canvas in frames:
        img = canvas.get_image().convert("L")
        scaled = img.resize(
            (width * scale, height * scale),
            0,  # NEAREST
        )
        buf = io.BytesIO()
        scaled.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode("ascii")
        frame_data.append(b64)

    @app.route("/")
    def index():
        return render_template(
            "preview.html",
            width=width * scale,
            height=height * scale,
            fps=fps,
            frame_count=len(frames),
        )

    @app.route("/api/frames")
    def api_frames():
        return jsonify({
            "fps": fps,
            "width": width * scale,
            "height": height * scale,
            "original_width": width,
            "original_height": height,
            "frame_count": len(frame_data),
            "frames": frame_data,
        })

    return app


def start_server(frames: list, fps: int, width: int, height: int,
                 port: int = 5050, scale: int = 4):
    """Start the Flask dev server."""
    app = create_app(frames, fps, width, height, scale)
    print(f"\n🌐 remotionBinario Web Preview")
    print(f"   http://localhost:{port}")
    print(f"   {len(frames)} frames @ {fps} FPS | {width}x{height} (scaled {scale}x)")
    print(f"   Press Ctrl+C to stop\n")
    app.run(host="0.0.0.0", port=port, debug=False)
