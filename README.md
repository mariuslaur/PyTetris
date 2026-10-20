
Python Tkinter Tetris

A classic, fully functional desktop-native Tetris clone written from scratch using Python's native Tkinter for graphics and native threading for concurrent game loops.
The engine showcases grid tracking, geometry rotation translations, and clean separation between individual shape behavior and global game logic.

🚀 Key Architectural & Python Developer Concepts

This codebase serves as an excellent case study for traditional event-driven desktop architectures in Python. Here are the core developer takeaways categorized by discipline:

1. Concurrency Model & Event Loop Integration

• Multithreaded Execution: The project decouples the graphics rendering frame from the game engine tick. The GUI runs on the main thread via master.mainloop(), while the core game loop runs inside a separate background threading.Thread(daemon=True).
• Thread Safety Caution: Game ticks directly manipulate UI assets via self.master.update() from the background thread. For a senior developer, this highlights a classic race condition landscape—Tkinter is inherently not thread-safe.

2. Mathematical Vector Rotations

• Pre-Computed Translation Offsets: Rather than using intensive dynamic matrix multiplication at runtime, shapes use a declarative lookup table (self.rotations) to map indexed states (0-3) to coordinate translations.
• State Boundaries & Collision Detection: Rotation permissions (okToRotate) utilize strict boundary assertions derived from screen size limits (mox, moy) preventing pieces from clipping outside visible matrix memory boundaries.

3. State Management & Grid Coordination

• Sparse Matrix Tracking: The grid state is stored in a multi-dimensional array mapping canvas element references (self.lines).
• Row Sweeping Engine: Line clearance utilizes an index shift array algorithm (adjustLines). Instead of recreating array buffers, it mutates current indices downward based on the calculated multi-line drop factor (deltaY).

🛠️ Codebase Deep-Dive for Seniors

Production Strengths

• Polymorphic Design: Clean inheritance model where individual blocks (e.g., AShape, BShape) inherit universal bounds checking and translation logic from a single generic Shape base class.
• Deterministic Configuration: Constant global variables control canvas scaling (GridUnit), frame delays, and point increments uniformly.
• Responsive Control Mappings: Standard input hooks bind keyboard event signatures safely via canvas.bind_all().

🎮 How to Run

Because the project leverages zero external dependencies outside Python's core toolkit, you can launch the game straight out of the box.
bash
# Clone this repository or copy the code file
python tetris.py

Key Controls

• ← / → : Move Piece Left or Right
• ↑ : Rotate Piece Clockwise
• ↓ : Soft Drop / Accelerated Fall
• P : Pause / Unpause Game