# Python Tkinter Tetris

A classic desktop-native Tetris clone written from scratch using Python's **Tkinter** engine, featuring a pure single-threaded asynchronous architecture.

## 🚀 Key Architectural & Python Developer Concepts

* **Asynchronous Event-Driven Loop (`.after()`):** Uses recursive `.after(ms, callback)` scheduling for a thread-safe main loop and instant frame canceling via `master.after_cancel()`.
* **Mathematical Vector Rotations:** Maps states to coordinate tuples via a declarative dictionary (`self.rotations`) with built-in collision checks.
* **State Management & Grid Coordination:** Tracks the playing field using a 2D layout array and handles row sweeping via precise offset calculations.

## 🎮 How to Run & Controls

```bash
python tetris.py
```
* <kbd>←</kbd> / <kbd>→</kbd> : Move Left/Right | <kbd>↑</kbd> : Rotate | <kbd>↓</kbd> : Soft Drop | <kbd>P</kbd> : Pause