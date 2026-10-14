#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create a GIF of the Danny Opera Solver pipeline running in real-time.
Captures console output as a GIF, similar to Autobolge's assets/autobolge.gif
"""

import sys
import os
import subprocess
import threading
import time
import tempfile
from pathlib import Path

sys.path.insert(0, r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver")

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("PIL not available - install with: pip install pillow")


class ConsoleRecorder:
    """Records console output as a GIF by capturing frames."""

    def __init__(self, width=1200, height=800, font_size=14, fps=5):
        self.width = width
        self.height = height
        self.font_size = font_size
        self.fps = fps
        self.frames = []
        self.buffer = []
        self.lock = threading.Lock()
        self.running = False

        # Try to load a monospace font
        try:
            self.font = ImageFont.truetype("consola.ttf", font_size)
        except:
            try:
                self.font = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", font_size)
            except:
                try:
                    self.font = ImageFont.truetype("DejaVuSansMono.ttf", font_size)
                except:
                    self.font = ImageFont.load_default()

        # Calculate char dimensions
        test_img = Image.new('RGB', (10, 10))
        draw = ImageDraw.Draw(test_img)
        bbox = draw.textbbox((0, 0), "M", font=self.font)
        self.char_width = bbox[2] - bbox[0]
        self.char_height = bbox[3] - bbox[1]
        self.cols = width // self.char_width
        self.rows = height // self.char_height

    def add_line(self, line):
        """Add a line to the buffer."""
        with self.lock:
            self.buffer.append(line)
            # Keep only last N lines (terminal height)
            max_lines = self.rows
            if len(self.buffer) > max_lines:
                self.buffer = self.buffer[-max_lines:]

    def capture_frame(self):
        """Capture current buffer as a frame."""
        with self.lock:
            lines = self.buffer[-self.rows:] if len(self.buffer) > self.rows else self.buffer[:]

        # Create image
        img = Image.new('RGB', (self.width, self.height), color='black')
        draw = ImageDraw.Draw(img)

        for i, line in enumerate(lines):
            y = i * self.char_height
            draw.text((0, y), line[:self.cols], font=self.font, fill='white')

        self.frames.append(img)

    def save_gif(self, output_path, duration=100):
        """Save frames as GIF."""
        if not self.frames:
            print("No frames to save")
            return
        self.frames[0].save(
            output_path,
            save_all=True,
            append_images=self.frames[1:],
            duration=1000 // self.fps,
            loop=0
        )
        print(f"Saved GIF to {output_path} ({len(self.frames)} frames)")


def record_pipeline():
    """Run the Danny Opera Solver pipeline and record as GIF."""
    print("Starting Danny Opera Solver GIF recording...")
    print("This will run the pipeline and capture console output as a GIF.")
    print("Press Ctrl+C to stop early.")
    print()

    # Setup recorder
    recorder = ConsoleRecorder(width=1200, height=800, font_size=14, fps=5)

    # Command to run - use the test_pipeline_final.py which works
    cmd = [
        sys.executable, "-u",  # -u for unbuffered output
        "C:/Development/ISyCo Git/malbolge-lisp-forensics/danny-opera-solver/test_pipeline_final.py"
    ]

    # Start process
    proc = subprocess.Popen(
        [sys.executable, "-u", "C:/Development/ISyCo Git/malbolge-lisp-forensics/danny-opera-solver/test_pipeline_final.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        universal_newlines=True,
        cwd=r"C:\Development\ISyCo Git\malbolge-lisp-forensics\danny-opera-solver"
    )

    recorder = ConsoleRecorder(width=1200, height=800, font_size=14, fps=5)
    recorder.running = True

    # Thread to read output
    def read_output():
        for line in iter(proc.stdout.readline, ''):
            if not recorder.running:
                break
            line = line.rstrip('\n\r')
            recorder.add_line(line)
            recorder.capture_frame()
            time.sleep(0.1)  # Small delay between frames

        # Capture final frames
        for _ in range(5):
            recorder.capture_frame()
            time.sleep(0.2)
        recorder.running = False

    reader_thread = threading.Thread(target=read_output)
    reader_thread.start()

    # Wait for process to complete
    proc.wait()
    recorder.running = False
    reader_thread.join()

    # Add a few final frames
    for _ in range(10):
        recorder.capture_frame()
        time.sleep(0.1)

    # Save GIF
    output_path = Path.cwd() / "danny_opera_solver.gif"
    recorder.save_gif(str(Path.cwd() / "danny_opera_solver.gif"), duration=200)
    print(f"\nGIF saved to {output_path}")


if __name__ == "__main__":
    import sys
    import subprocess
    import threading
    import time
    from pathlib import Path
    import threading

    # Check PIL
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("Installing Pillow...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"])
        from PIL import Image, ImageDraw, ImageFont

    # Run
    print("Starting Danny Opera Solver GIF recording...")
    print("This will run the pipeline and capture console output as a GIF.")
    print("Press Ctrl+C to stop early.")
    print()

    # Run the pipeline once
    record_pipeline()
    print("Done!")