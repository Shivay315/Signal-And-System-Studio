"""
Signals & Systems Studio
========================

A study-first desktop tool for exploring continuous-time signals.

Core workflow
-------------
Type an expression such as:

    r(t) + r(t+1)
    r(t) - 2*r(t-1) + r(t-2)
    u(t) - u(t-3)
    3*delta(t-2)

Press Enter or Plot.

The Help Book is opened from:
    Signals_and_Systems_Help_Book.pdf

Keep the PDF in the same directory as this Python file.

Requirements
------------
    numpy
    matplotlib
    tkinter / python-tk
"""

from __future__ import annotations

from pathlib import Path
import csv
import os
import platform
import re
import subprocess
import sys
from dataclasses import dataclass
from typing import Callable, Optional

import numpy as np
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib import rcParams


# ============================================================
# Theme
# ============================================================

LIGHT = {
    "window": "#F5F7FA",
    "panel": "#FFFFFF",
    "panel_alt": "#F0F3F7",
    "border": "#D8DEE7",
    "text": "#1E293B",
    "muted": "#64748B",
    "accent": "#2563EB",
    "accent_soft": "#E8F0FF",
    "graph": "#FFFFFF",
    "grid": "#E2E8F0",
    "signal": "#2563EB",
    "axis": "#475569",
    "error": "#B91C1C",
}

DARK = {
    "window": "#111827",
    "panel": "#18212F",
    "panel_alt": "#202B3B",
    "border": "#334155",
    "text": "#E5E7EB",
    "muted": "#94A3B8",
    "accent": "#60A5FA",
    "accent_soft": "#1D3557",
    "graph": "#111827",
    "grid": "#334155",
    "signal": "#60A5FA",
    "axis": "#CBD5E1",
    "error": "#FCA5A5",
}


# ============================================================
# Basic signals
# ============================================================

def u(t):
    """Unit step."""
    return np.where(t >= 0, 1.0, 0.0)


def r(t):
    """Unit ramp."""
    return np.maximum(t, 0.0)


def delta(t):
    """
    Numerical placeholder for a Dirac impulse.

    The plotter detects delta terms separately and draws
    them as vertical arrows.
    """
    return np.zeros_like(np.asarray(t, dtype=float))


def d(t):
    """Short alias for delta(t)."""
    return delta(t)


def sgn(t):
    """Sign function."""
    return np.sign(t)


def rect(t):
    """Unit rectangular pulse centered at zero."""
    t = np.asarray(t, dtype=float)
    result = np.zeros_like(t)
    result[np.abs(t) < 0.5] = 1.0
    result[np.isclose(np.abs(t), 0.5)] = 0.5
    return result


def tri(t):
    """Unit triangular pulse centered at zero."""
    return np.maximum(1.0 - np.abs(t), 0.0)


def sinc(t):
    """Normalized sinc."""
    return np.sinc(t)


# ============================================================
# Mathematical functions
# ============================================================

def sin(x):
    return np.sin(x)


def cos(x):
    return np.cos(x)


def tan(x):
    return np.tan(x)


def exp(x):
    return np.exp(x)


def sqrt(x):
    return np.sqrt(np.maximum(x, 0))


def abs_(x):
    return np.abs(x)


def ln(x):
    return np.log(np.maximum(x, 1e-12))


def log10(x):
    return np.log10(np.maximum(x, 1e-12))


EVAL_NAMES = {
    "u": u,
    "r": r,
    "delta": delta,
    "d": d,
    "sgn": sgn,
    "rect": rect,
    "tri": tri,
    "sinc": sinc,
    "sin": sin,
    "cos": cos,
    "tan": tan,
    "exp": exp,
    "sqrt": sqrt,
    "abs": abs_,
    "ln": ln,
    "log10": log10,
    "pi": np.pi,
    "e": np.e,
}


# ============================================================
# Data models
# ============================================================

@dataclass(frozen=True)
class Preset:
    name: str
    expression: str
    description: str


# ============================================================
# Preset library
# ============================================================

BASIC_PRESETS = [
    Preset("Unit step", "u(t)", "Basic unit step."),
    Preset("Unit ramp", "r(t)", "Basic unit ramp."),
    Preset("Impulse", "delta(t)", "Unit impulse."),
    Preset("Sign", "sgn(t)", "Sign function."),
    Preset("Rectangle", "rect(t)", "Unit rectangular pulse."),
    Preset("Triangle", "tri(t)", "Unit triangular pulse."),
    Preset("Sinc", "sinc(t)", "Normalized sinc."),
]

TRANSFORM_PRESETS = [
    Preset("Delayed step", "u(t-2)", "Shift right by 2."),
    Preset("Advanced step", "u(t+2)", "Shift left by 2."),
    Preset("Delayed ramp", "r(t-2)", "Shift right by 2."),
    Preset("Advanced ramp", "r(t+2)", "Shift left by 2."),
    Preset("Compressed ramp", "r(2*t)", "Time compression."),
    Preset("Expanded ramp", "r(0.5*t)", "Time expansion."),
    Preset("Reversed ramp", "r(-t)", "Time reversal."),
    Preset("Scaled step", "3*u(t)", "Amplitude scaling."),
    Preset("Scaled ramp", "2*r(t)", "Amplitude scaling."),
    Preset("Scaled impulse", "4*delta(t)", "Impulse amplitude scaling."),
]

CONSTRUCTION_PRESETS = [
    Preset(
        "Rectangular pulse",
        "u(t)-u(t-3)",
        "A pulse from t=0 to t=3.",
    ),
    Preset(
        "Delayed pulse",
        "u(t-2)-u(t-5)",
        "A pulse from t=2 to t=5.",
    ),
    Preset(
        "Finite ramp",
        "r(t)-r(t-2)",
        "A ramp that turns into a constant after t=2.",
    ),
    Preset(
        "Triangle from ramps",
        "r(t)-2*r(t-1)+r(t-2)",
        "Classic triangular construction.",
    ),
    Preset(
        "Wider triangle",
        "r(t)-2*r(t-2)+r(t-4)",
        "Triangle with larger ramp spacing.",
    ),
    Preset(
        "Step staircase",
        "u(t)+u(t-2)+u(t-4)",
        "Three delayed unit steps.",
    ),
    Preset(
        "Impulse pair",
        "delta(t-2)+delta(t+2)",
        "Two equal impulses.",
    ),
    Preset(
        "Odd impulse pair",
        "delta(t+2)-delta(t-2)",
        "Odd impulse combination.",
    ),
    Preset(
        "Causal sine",
        "sin(2*t)*u(t)",
        "Sine switched on at t=0.",
    ),
    Preset(
        "Causal cosine",
        "cos(2*t)*u(t)",
        "Cosine switched on at t=0.",
    ),
    Preset(
        "Damped sine",
        "exp(-0.2*t)*sin(2*t)*u(t)",
        "Causal damped sinusoid.",
    ),
    Preset(
        "Damped cosine",
        "exp(-0.2*t)*cos(2*t)*u(t)",
        "Causal damped cosine.",
    ),
]


# ============================================================
# Expression helpers
# ============================================================

def normalize_expression(expression: str) -> str:
    """
    Convert common engineering notation into Python-friendly syntax.
    """
    expression = expression.strip()
    expression = expression.replace("δ", "delta")
    expression = expression.replace("−", "-")
    expression = expression.replace("×", "*")
    expression = expression.replace("^", "**")

    expression = re.sub(
        r"(\d+(?:\.\d+)?)\s*(?="
        r"u|r|d|delta|sgn|rect|tri|sinc|"
        r"sin|cos|tan|exp|sqrt|abs|ln|log10"
        r")",
        r"\1*",
        expression,
    )

    expression = re.sub(
        r"(\d+(?:\.\d+)?)\s*t",
        r"\1*t",
        expression,
    )

    expression = re.sub(
        r"\)\s*t",
        ")*t",
        expression,
    )

    return expression


def find_impulses(expression: str) -> list[tuple[float, float]]:
    """
    Find simple impulse terms.

    delta(t-a) -> location a.
    """
    expr = expression.replace(" ", "")
    expr = expr.replace("δ", "delta")

    pattern = re.compile(
        r"(?P<sign>[+-]?)"
        r"(?P<coef>\d+(?:\.\d+)?)?"
        r"\*?"
        r"delta"
        r"\(t"
        r"(?P<shift>[+-]\d+(?:\.\d+)?)?"
        r"\)"
    )

    result: list[tuple[float, float]] = []

    for match in pattern.finditer(expr):
        sign = -1.0 if match.group("sign") == "-" else 1.0
        coefficient = (
            float(match.group("coef"))
            if match.group("coef")
            else 1.0
        )
        shift = (
            float(match.group("shift"))
            if match.group("shift")
            else 0.0
        )

        # delta(t-a) is located at t=a.
        result.append(
            (-shift, sign * coefficient)
        )

    return result


def safe_evaluate(
    expression: str,
    t: np.ndarray,
) -> np.ndarray:
    """
    Evaluate a signal expression in a restricted namespace.
    """
    normalized = normalize_expression(
        expression
    )

    result = eval(
        normalized,
        {"__builtins__": {}},
        {
            **EVAL_NAMES,
            "t": t,
        },
    )

    result = np.asarray(
        result,
        dtype=float,
    )

    if result.ndim == 0:
        result = np.full_like(
            t,
            float(result),
        )

    if result.shape != t.shape:
        raise ValueError(
            "The expression did not produce "
            "one value for each t."
        )

    result = np.nan_to_num(
        result,
        nan=0.0,
        posinf=0.0,
        neginf=0.0,
    )

    return result


# ============================================================
# Application
# ============================================================

class SignalsStudio:

    def __init__(self, root: tk.Tk):
        self.root = root

        self.colors = LIGHT
        self.dark_mode = False

        self.root.title(
            "Signals & Systems Studio"
        )

        self.root.geometry(
            "1240x780"
        )

        self.root.minsize(
            760,
            520,
        )

        self.script_dir = (
            Path(__file__).resolve().parent
        )

        self.expression_var = tk.StringVar(
            value="r(t) + r(t+1)"
        )

        self.tmin_var = tk.StringVar(
            value="-10"
        )

        self.tmax_var = tk.StringVar(
            value="10"
        )

        self.autoscale_var = tk.BooleanVar(
            value=True
        )

        self.grid_var = tk.BooleanVar(
            value=True
        )

        self.zero_axes_var = tk.BooleanVar(
            value=True
        )

        self.show_legend_var = tk.BooleanVar(
            value=True
        )

        self.status_var = tk.StringVar(
            value="Ready"
        )

        self.history: list[str] = []
        self.favorites: list[str] = []

        self.current_t: Optional[np.ndarray] = None
        self.current_x: Optional[np.ndarray] = None
        self.current_expression = ""

        self.cursor_line = None
        self.cursor_text = None
        self.cursor_connection = None

        self._configure_styles()
        self._build_menubar()
        self._build_toolbar()
        self._build_main_layout()
        self._build_scrollable_sidebar()
        self._build_graph()
        self._bind_shortcuts()
        self._bind_scroll_events()

        self.plot()

    # ========================================================
    # Style
    # ========================================================

    def _configure_styles(self):

        style = ttk.Style()

        try:
            style.theme_use(
                "clam"
            )
        except tk.TclError:
            pass

        style.configure(
            "TFrame",
            background=self.colors["window"],
        )

        style.configure(
            "TLabel",
            background=self.colors["window"],
            foreground=self.colors["text"],
        )

        style.configure(
            "Title.TLabel",
            font=("Helvetica", 19, "bold"),
            background=self.colors["window"],
            foreground=self.colors["text"],
        )

        style.configure(
            "Muted.TLabel",
            font=("Helvetica", 10),
            background=self.colors["window"],
            foreground=self.colors["muted"],
        )

        style.configure(
            "Section.TLabel",
            font=("Helvetica", 10, "bold"),
            background=self.colors["panel"],
            foreground=self.colors["text"],
        )

        style.configure(
            "Primary.TButton",
            font=("Helvetica", 10, "bold"),
            padding=(12, 7),
        )

        style.configure(
            "Toolbar.TButton",
            padding=(8, 5),
        )

        style.configure(
            "Quick.TButton",
            padding=(7, 5),
        )

        style.configure(
            "TCheckbutton",
            background=self.colors["panel"],
            foreground=self.colors["text"],
        )

    def _apply_widget_colors(self):
        """
        Apply current theme to the custom canvas/sidebar widgets.
        """
        self.root.configure(
            background=self.colors["window"]
        )

        if hasattr(
            self,
            "sidebar_canvas",
        ):
            self.sidebar_canvas.configure(
                background=self.colors["panel"],
                highlightbackground=self.colors["border"],
            )

        if hasattr(
            self,
            "sidebar_inner",
        ):
            self.sidebar_inner.configure(
                style="TFrame"
            )

        if hasattr(
            self,
            "expression_entry",
        ):
            self.expression_entry.configure(
                foreground=self.colors["text"]
            )

        self.plot()

    # ========================================================
    # Menu bar
    # ========================================================

    def _build_menubar(self):

        bar = tk.Menu(
            self.root
        )

        # ---------------- File ----------------

        file_menu = tk.Menu(
            bar,
            tearoff=False,
        )

        file_menu.add_command(
            label="New / Clear",
            command=self.clear_expression,
            accelerator="⌘N",
        )

        file_menu.add_command(
            label="Open Expression…",
            command=self.open_expression,
            accelerator="⌘O",
        )

        file_menu.add_command(
            label="Save Expression…",
            command=self.save_expression,
            accelerator="⌘S",
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Save as Image…",
            command=self.save_image,
            accelerator="⇧⌘S",
        )

        file_menu.add_command(
            label="Save as PDF…",
            command=self.save_pdf,
            accelerator="⇧⌘P",
        )

        file_menu.add_command(
            label="Export Samples as CSV…",
            command=self.export_csv,
        )

        file_menu.add_separator()

        file_menu.add_command(
            label="Exit",
            command=self.root.destroy,
            accelerator="⌘Q",
        )

        bar.add_cascade(
            label="File",
            menu=file_menu,
        )

        # ---------------- Functions ----------------

        function_menu = tk.Menu(
            bar,
            tearoff=False,
        )

        basic_menu = tk.Menu(
            function_menu,
            tearoff=False,
        )

        for preset in BASIC_PRESETS:
            basic_menu.add_command(
                label=f"{preset.name}   {preset.expression}",
                command=lambda p=preset:
                self.set_expression(
                    p.expression
                ),
            )

        function_menu.add_cascade(
            label="Basic Signals",
            menu=basic_menu,
        )

        transform_menu = tk.Menu(
            function_menu,
            tearoff=False,
        )

        for preset in TRANSFORM_PRESETS:
            transform_menu.add_command(
                label=preset.name,
                command=lambda p=preset:
                self.set_expression(
                    p.expression
                ),
            )

        function_menu.add_cascade(
            label="Transformations",
            menu=transform_menu,
        )

        construction_menu = tk.Menu(
            function_menu,
            tearoff=False,
        )

        for preset in CONSTRUCTION_PRESETS:
            construction_menu.add_command(
                label=preset.name,
                command=lambda p=preset:
                self.set_expression(
                    p.expression
                ),
            )

        function_menu.add_cascade(
            label="Signal Constructions",
            menu=construction_menu,
        )

        math_menu = tk.Menu(
            function_menu,
            tearoff=False,
        )

        for name in [
            "sin(t)",
            "cos(t)",
            "tan(t)",
            "exp(t)",
            "sqrt(t)",
            "abs(t)",
            "ln(t)",
            "log10(t)",
        ]:
            math_menu.add_command(
                label=name,
                command=lambda expression=name:
                self.insert_at_cursor(
                    expression
                ),
            )

        function_menu.add_cascade(
            label="Math Functions",
            menu=math_menu,
        )

        self.history_menu = tk.Menu(
            function_menu,
            tearoff=False,
        )

        function_menu.add_cascade(
            label="History",
            menu=self.history_menu,
        )

        self.favorites_menu = tk.Menu(
            function_menu,
            tearoff=False,
        )

        function_menu.add_cascade(
            label="Favorites",
            menu=self.favorites_menu,
        )

        bar.add_cascade(
            label="Functions",
            menu=function_menu,
        )

        # ---------------- Analysis ----------------

        analysis_menu = tk.Menu(
            bar,
            tearoff=False,
        )

        analysis_menu.add_command(
            label="Signal Statistics",
            command=self.show_statistics,
        )

        analysis_menu.add_command(
            label="Inspect Sample Values",
            command=self.inspect_values,
        )

        analysis_menu.add_command(
            label="Compare with Another Signal",
            command=self.compare_signal,
        )

        analysis_menu.add_command(
            label="Approximate Peak",
            command=self.find_peak,
        )

        analysis_menu.add_command(
            label="Approximate Area",
            command=self.find_area,
        )

        analysis_menu.add_separator()

        analysis_menu.add_command(
            label="Moving Value Cursor",
            command=self.toggle_cursor,
        )

        bar.add_cascade(
            label="Analysis",
            menu=analysis_menu,
        )

        # ---------------- View ----------------

        view_menu = tk.Menu(
            bar,
            tearoff=False,
        )

        view_menu.add_checkbutton(
            label="Autoscale Y-axis",
            variable=self.autoscale_var,
            command=self.plot,
        )

        view_menu.add_checkbutton(
            label="Grid",
            variable=self.grid_var,
            command=self.plot,
        )

        view_menu.add_checkbutton(
            label="Zero axes",
            variable=self.zero_axes_var,
            command=self.plot,
        )

        view_menu.add_checkbutton(
            label="Legend",
            variable=self.show_legend_var,
            command=self.plot,
        )

        view_menu.add_separator()

        view_menu.add_command(
            label="Zoom In",
            command=self.zoom_in,
        )

        view_menu.add_command(
            label="Zoom Out",
            command=self.zoom_out,
        )

        view_menu.add_command(
            label="Fit / Reset View",
            command=self.fit_view,
        )

        view_menu.add_separator()

        view_menu.add_command(
            label="Toggle Dark Mode",
            command=self.toggle_dark_mode,
        )

        bar.add_cascade(
            label="View",
            menu=view_menu,
        )

        # ---------------- Help ----------------

        help_menu = tk.Menu(
            bar,
            tearoff=False,
        )

        help_menu.add_command(
            label="Open Help Book",
            command=self.open_help,
        )

        help_menu.add_command(
            label="Examples",
            command=self.show_examples,
        )

        help_menu.add_command(
            label="Keyboard Shortcuts",
            command=self.show_shortcuts,
        )

        help_menu.add_command(
            label="About",
            command=self.about,
        )

        bar.add_cascade(
            label="Help",
            menu=help_menu,
        )

        self.root.config(
            menu=bar
        )

        self._refresh_history_menu()
        self._refresh_favorites_menu()

    # ========================================================
    # Toolbar
    # ========================================================

    def _build_toolbar(self):

        # A two-row toolbar keeps every control inside the window
        # at small widths instead of allowing a single wide row
        # to run off-screen.
        toolbar = ttk.Frame(
            self.root,
            padding=(8, 6),
        )

        toolbar.pack(
            fill="x",
            side="top",
        )

        # ----------------------------------------------------
        # Row 1 - primary study controls
        # ----------------------------------------------------

        row1 = ttk.Frame(
            toolbar
        )

        row1.pack(
            fill="x",
        )

        ttk.Button(
            row1,
            text="Plot",
            style="Primary.TButton",
            command=self.plot,
        ).pack(
            side="left",
            padx=2,
        )

        ttk.Button(
            row1,
            text="New",
            style="Toolbar.TButton",
            command=self.clear_expression,
        ).pack(
            side="left",
            padx=2,
        )

        ttk.Separator(
            row1,
            orient="vertical",
        ).pack(
            side="left",
            fill="y",
            padx=6,
        )

        for label, expression in [
            ("u(t)", "u(t)"),
            ("r(t)", "r(t)"),
            ("δ(t)", "delta(t)"),
            ("Pulse", "u(t)-u(t-3)"),
            ("Triangle", "r(t)-2*r(t-1)+r(t-2)"),
        ]:

            ttk.Button(
                row1,
                text=label,
                style="Toolbar.TButton",
                command=lambda e=expression:
                self.set_expression(e),
            ).pack(
                side="left",
                padx=2,
            )

        # Spacer
        ttk.Frame(
            row1,
        ).pack(
            side="left",
            fill="x",
            expand=True,
        )

        ttk.Button(
            row1,
            text="Theme",
            style="Toolbar.TButton",
            command=self.toggle_dark_mode,
        ).pack(
            side="right",
            padx=2,
        )

        ttk.Button(
            row1,
            text="Help",
            style="Toolbar.TButton",
            command=self.open_help,
        ).pack(
            side="right",
            padx=2,
        )

        # ----------------------------------------------------
        # Row 2 - view + export
        # ----------------------------------------------------

        row2 = ttk.Frame(
            toolbar,
            padding=(0, 5, 0, 0),
        )

        row2.pack(
            fill="x",
        )

        ttk.Label(
            row2,
            text="View",
            font=("Helvetica", 9, "bold"),
        ).pack(
            side="left",
            padx=(2, 6),
        )

        for label, command in [
            ("Auto Y", self.toggle_autoscale),
            ("Fit", self.fit_view),
            ("Zoom +", self.zoom_in),
            ("Zoom −", self.zoom_out),
        ]:

            ttk.Button(
                row2,
                text=label,
                style="Toolbar.TButton",
                command=command,
            ).pack(
                side="left",
                padx=2,
            )

        ttk.Separator(
            row2,
            orient="vertical",
        ).pack(
            side="left",
            fill="y",
            padx=6,
        )

        ttk.Button(
            row2,
            text="Save PNG",
            style="Toolbar.TButton",
            command=self.save_image,
        ).pack(
            side="left",
            padx=2,
        )

        ttk.Button(
            row2,
            text="Save PDF",
            style="Toolbar.TButton",
            command=self.save_pdf,
        ).pack(
            side="left",
            padx=2,
        )

        ttk.Button(
            row2,
            text="Export CSV",
            style="Toolbar.TButton",
            command=self.export_csv,
        ).pack(
            side="left",
            padx=2,
        )

        ttk.Separator(
            row2,
            orient="vertical",
        ).pack(
            side="left",
            fill="y",
            padx=6,
        )

        ttk.Label(
            row2,
            text="Functions → full signal library",
            style="Muted.TLabel",
        ).pack(
            side="left",
            padx=5,
        )

    # ========================================================
    # Main layout
    # ========================================================

    def _build_main_layout(self):

        self.main = ttk.Frame(
            self.root,
            padding=(10, 0, 10, 8),
        )

        self.main.pack(
            fill="both",
            expand=True,
        )

        self.main.columnconfigure(
            0,
            weight=0,
            minsize=305,
        )

        self.main.columnconfigure(
            1,
            weight=1,
        )

        self.main.rowconfigure(
            0,
            weight=1,
        )

        # Sidebar host
        self.sidebar_host = ttk.Frame(
            self.main,
        )

        self.sidebar_host.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=(0, 8),
        )

        # Graph host
        self.graph_host = ttk.Frame(
            self.main,
        )

        self.graph_host.grid(
            row=0,
            column=1,
            sticky="nsew",
        )

        self.main.bind(
            "<Configure>",
            lambda event: self._update_graph_size(),
        )

    # ========================================================
    # Scrollable sidebar
    # ========================================================

    def _build_scrollable_sidebar(self):

        self.sidebar_host.rowconfigure(
            0,
            weight=1,
        )
        self.sidebar_host.columnconfigure(
            0,
            weight=1,
        )

        self.sidebar_canvas = tk.Canvas(
            self.sidebar_host,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=self.colors["border"],
            background=self.colors["panel"],
            yscrollincrement=1,
        )

        self.sidebar_scrollbar = ttk.Scrollbar(
            self.sidebar_host,
            orient="vertical",
            command=self.sidebar_canvas.yview,
        )

        self.sidebar_canvas.configure(
            yscrollcommand=self.sidebar_scrollbar.set,
        )

        self.sidebar_canvas.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        self.sidebar_scrollbar.grid(
            row=0,
            column=1,
            sticky="ns",
        )

        self.sidebar_inner = ttk.Frame(
            self.sidebar_canvas,
            padding=12,
        )

        self.sidebar_window = (
            self.sidebar_canvas.create_window(
                0,
                0,
                anchor="nw",
                window=self.sidebar_inner,
            )
        )

        self.sidebar_inner.bind(
            "<Configure>",
            self._sidebar_configure,
        )

        self.sidebar_canvas.bind(
            "<Configure>",
            self._sidebar_canvas_configure,
        )

        self._build_sidebar_content()

    def _sidebar_configure(self, event=None):
        self.sidebar_canvas.configure(
            scrollregion=self.sidebar_canvas.bbox(
                "all"
            )
        )

    def _sidebar_canvas_configure(self, event):
        # Force the embedded frame to exactly match the visible
        # width. This prevents child widgets from creating a
        # horizontal spill on narrow windows.
        self.sidebar_canvas.itemconfigure(
            self.sidebar_window,
            width=max(
                1,
                event.width,
            ),
        )

        self._sidebar_configure()

    def _bind_scroll_events(self):
        """
        Native-ish scrolling for macOS trackpads.

        macOS sends high-resolution <MouseWheel> deltas. The old
        implementation divided those deltas down, which frequently
        turned a trackpad gesture into zero movement. Here the raw
        delta is used directly, and events from sidebar descendants
        are routed back to the sidebar canvas.
        """

        self.sidebar_canvas.bind(
            "<MouseWheel>",
            self._sidebar_wheel,
            add="+",
        )

        self.sidebar_canvas.bind(
            "<Button-4>",
            lambda event: self._scroll_sidebar(-3),
            add="+",
        )

        self.sidebar_canvas.bind(
            "<Button-5>",
            lambda event: self._scroll_sidebar(3),
            add="+",
        )

        self.root.bind_all(
            "<MouseWheel>",
            self._global_wheel,
            add="+",
        )

        self.root.bind_all(
            "<Button-4>",
            lambda event: self._global_button_scroll(-3),
            add="+",
        )

        self.root.bind_all(
            "<Button-5>",
            lambda event: self._global_button_scroll(3),
            add="+",
        )

    def _pointer_over_sidebar(self):
        try:
            x = self.root.winfo_pointerx()
            y = self.root.winfo_pointery()

            x0 = self.sidebar_canvas.winfo_rootx()
            y0 = self.sidebar_canvas.winfo_rooty()

            x1 = x0 + self.sidebar_canvas.winfo_width()
            y1 = y0 + self.sidebar_canvas.winfo_height()

            return (
                x0 <= x <= x1
                and y0 <= y <= y1
            )

        except tk.TclError:
            return False

    def _editable_widget(self, widget):
        """
        Don't hijack wheel events when the user is interacting
        with an Entry or Text widget.
        """
        current = widget

        while current is not None:

            if isinstance(
                current,
                (tk.Entry, tk.Text),
            ):
                return True

            try:
                parent_name = (
                    current.winfo_parent()
                )
            except Exception:
                return False

            if not parent_name:
                return False

            try:
                parent = (
                    current._nametowidget(
                        parent_name
                    )
                )
                current = parent
            except Exception:
                return False

        return False

    def _sidebar_wheel(self, event):
        if self._editable_widget(
            event.widget
        ):
            return "break"

        if sys.platform == "darwin":
            # Trackpad events can be fractional/small. Using the
            # raw signed delta avoids turning them into zero.
            amount = (
                -event.delta
            )

            # Keep an individual event bounded while preserving
            # continuous trackpad motion.
            amount = max(
                -12,
                min(12, amount),
            )

        else:
            amount = int(
                -event.delta / 120
            )

            if amount == 0:
                amount = (
                    -1
                    if event.delta > 0
                    else 1
                )

        self.sidebar_canvas.yview_scroll(
            amount,
            "units",
        )

        return "break"

    def _global_wheel(self, event):
        if not self._pointer_over_sidebar():
            return

        if self._editable_widget(
            event.widget
        ):
            return

        return self._sidebar_wheel(
            event
        )

    def _global_button_scroll(
        self,
        amount,
    ):
        if not self._pointer_over_sidebar():
            return

        self._scroll_sidebar(
            amount
        )

    def _scroll_sidebar(
        self,
        amount,
    ):
        self.sidebar_canvas.yview_scroll(
            amount,
            "units",
        )

    # ========================================================
    # Sidebar content
    # ========================================================

    def _build_sidebar_content(self):

        # Header
        ttk.Label(
            self.sidebar_inner,
            text="Signal Explorer",
            style="Title.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 2),
        )

        ttk.Label(
            self.sidebar_inner,
            text="Build a signal, then study its shape.",
            style="Muted.TLabel",
        ).pack(
            anchor="w",
            pady=(0, 12),
        )

        # Expression section
        expression_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Enter a signal  ",
            padding=10,
        )

        expression_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        self.expression_entry = ttk.Entry(
            expression_frame,
            textvariable=self.expression_var,
            font=("Menlo", 13),
        )

        self.expression_entry.pack(
            fill="x",
            ipady=7,
        )

        self.expression_entry.bind(
            "<Return>",
            lambda event: self.plot(),
        )

        ttk.Button(
            expression_frame,
            text="Plot expression",
            style="Primary.TButton",
            command=self.plot,
        ).pack(
            fill="x",
            pady=(8, 5),
        )

        ttk.Button(
            expression_frame,
            text="Add current expression to Favorites",
            command=self.add_favorite,
        ).pack(
            fill="x",
        )

        ttk.Label(
            expression_frame,
            text=(
                "Examples:  r(t)+r(t+1)   •   "
                "u(t)-u(t-3)   •   2*delta(t-1)"
            ),
            style="Muted.TLabel",
            wraplength=270,
            justify="left",
        ).pack(
            anchor="w",
            pady=(7, 0),
        )

        # Function palette
        palette_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Insert functions  ",
            padding=8,
        )

        palette_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        palette = [
            ("u(t)", "u(t)"),
            ("r(t)", "r(t)"),
            ("δ(t)", "delta(t)"),
            ("sgn(t)", "sgn(t)"),
            ("rect(t)", "rect(t)"),
            ("tri(t)", "tri(t)"),
            ("sin(t)", "sin(t)"),
            ("cos(t)", "cos(t)"),
            ("exp(t)", "exp(t)"),
            ("sinc(t)", "sinc(t)"),
        ]

        for index, (
            label,
            expression,
        ) in enumerate(palette):

            button = ttk.Button(
                palette_frame,
                text=label,
                style="Quick.TButton",
                command=lambda e=expression:
                self.insert_at_cursor(e),
            )

            button.grid(
                row=index // 2,
                column=index % 2,
                sticky="ew",
                padx=3,
                pady=3,
            )

        palette_frame.columnconfigure(
            0,
            weight=1,
        )

        palette_frame.columnconfigure(
            1,
            weight=1,
        )

        # Time range
        time_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Time range  ",
            padding=10,
        )

        time_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        row = ttk.Frame(
            time_frame
        )

        row.pack(
            fill="x",
        )

        ttk.Label(
            row,
            text="From",
        ).grid(
            row=0,
            column=0,
            sticky="w",
        )

        ttk.Label(
            row,
            text="To",
        ).grid(
            row=0,
            column=1,
            sticky="w",
            padx=(10, 0),
        )

        ttk.Entry(
            row,
            textvariable=self.tmin_var,
            width=9,
        ).grid(
            row=1,
            column=0,
            sticky="ew",
        )

        ttk.Entry(
            row,
            textvariable=self.tmax_var,
            width=9,
        ).grid(
            row=1,
            column=1,
            sticky="ew",
            padx=(10, 0),
        )

        row.columnconfigure(
            0,
            weight=1,
        )

        row.columnconfigure(
            1,
            weight=1,
        )

        ttk.Button(
            time_frame,
            text="Reset to −10 … 10",
            command=self.reset_range,
        ).pack(
            fill="x",
            pady=(8, 0),
        )

        # View
        view_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Plot options  ",
            padding=10,
        )

        view_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        ttk.Checkbutton(
            view_frame,
            text="Autoscale Y-axis",
            variable=self.autoscale_var,
            command=self.plot,
        ).pack(
            anchor="w",
        )

        ttk.Checkbutton(
            view_frame,
            text="Show grid",
            variable=self.grid_var,
            command=self.plot,
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ttk.Checkbutton(
            view_frame,
            text="Show zero axes",
            variable=self.zero_axes_var,
            command=self.plot,
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        ttk.Checkbutton(
            view_frame,
            text="Show legend",
            variable=self.show_legend_var,
            command=self.plot,
        ).pack(
            anchor="w",
            pady=(4, 0),
        )

        # Signal constructions
        construction_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Useful constructions  ",
            padding=10,
        )

        construction_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        for preset in CONSTRUCTION_PRESETS:

            ttk.Button(
                construction_frame,
                text=preset.name,
                style="Quick.TButton",
                command=lambda p=preset:
                self.set_expression(
                    p.expression
                ),
            ).pack(
                fill="x",
                pady=2,
            )

        # Analysis
        analysis_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Analysis  ",
            padding=10,
        )

        analysis_frame.pack(
            fill="x",
            pady=(0, 10),
        )

        analysis_actions = [
            ("Statistics", self.show_statistics),
            ("Inspect values", self.inspect_values),
            ("Compare signal", self.compare_signal),
            ("Find peak", self.find_peak),
            ("Find area", self.find_area),
            ("Moving cursor", self.toggle_cursor),
        ]

        for label, command in analysis_actions:

            ttk.Button(
                analysis_frame,
                text=label,
                style="Quick.TButton",
                command=command,
            ).pack(
                fill="x",
                pady=2,
            )

        # Help
        help_frame = ttk.LabelFrame(
            self.sidebar_inner,
            text="  Reference  ",
            padding=10,
        )

        help_frame.pack(
            fill="x",
        )

        ttk.Label(
            help_frame,
            text=(
                "u(t)          unit step\n"
                "r(t)          unit ramp\n"
                "delta(t)      impulse\n"
                "x(t-a)        shift right\n"
                "x(t+a)        shift left\n"
                "A*x(t)        amplitude scale"
            ),
            font=("Menlo", 9),
            justify="left",
        ).pack(
            anchor="w"
        )

        ttk.Button(
            help_frame,
            text="Open full Help Book",
            command=self.open_help,
        ).pack(
            fill="x",
            pady=(9, 0),
        )

    # ========================================================
    # Graph
    # ========================================================

    def _build_graph(self):

        # The host controls the final on-screen size. The Figure
        # itself starts compact and is allowed to resize naturally.
        self.graph_host.rowconfigure(
            0,
            weight=1,
        )

        self.graph_host.columnconfigure(
            0,
            weight=1,
        )

        self.figure = Figure(
            figsize=(5.5, 4.0),
            dpi=90,
        )

        try:
            self.figure.set_layout_engine(
                "tight"
            )
        except Exception:
            pass

        self.ax = self.figure.add_subplot(
            111
        )

        self.canvas = FigureCanvasTkAgg(
            self.figure,
            master=self.graph_host,
        )

        self.canvas_widget = (
            self.canvas.get_tk_widget()
        )

        self.canvas_widget.grid(
            row=0,
            column=0,
            sticky="nsew",
        )

        # ----------------------------------------------------
        # Current signal information
        # ----------------------------------------------------

        self.info_frame = ttk.LabelFrame(
            self.graph_host,
            text=" Current Signal ",
            padding=(10, 7),
        )

        self.info_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            pady=(7, 0),
        )

        self.info_expression = ttk.Label(
            self.info_frame,
            text="Expression: —",
            font=("Helvetica", 10, "bold"),
        )

        self.info_expression.pack(
            anchor="w",
        )

        self.info_details = ttk.Label(
            self.info_frame,
            text="",
            font=("Helvetica", 9),
        )

        self.info_details.pack(
            anchor="w",
            pady=(2, 0),
        )

        self.canvas.mpl_connect(
            "button_press_event",
            self._graph_click,
        )

    # ========================================================
    # Responsive graph resize
    # ========================================================

    def _update_graph_size(self):
        """
        Keep the Matplotlib figure synchronized with the actual
        Tkinter graph area.

        The canvas widget is managed by Tkinter, so it determines
        the final on-screen dimensions. Updating the Figure size
        here prevents the plot from behaving like a fixed-size
        object when the application window is resized.
        """
        try:
            width = self.graph_host.winfo_width()
            height = self.graph_host.winfo_height()

            if width <= 1 or height <= 1:
                return

            # Convert the available pixel dimensions to inches.
            dpi = max(
                float(self.figure.dpi),
                50.0,
            )

            fig_width = max(
                4.0,
                width / dpi,
            )

            fig_height = max(
                3.0,
                height / dpi,
            )

            self.figure.set_size_inches(
                fig_width,
                fig_height,
                forward=False,
            )

            self.canvas.draw_idle()

        except (
            tk.TclError,
            AttributeError,
            ValueError,
        ):
            # Resizing can fire while Tk is destroying/rebuilding
            # widgets. In that case there is nothing to update.
            pass

    # ========================================================
    # Cursor
    # ========================================================

    def _graph_click(self, event):

        if event.inaxes != self.ax:
            return

        if self.cursor_line is None:
            return

        if event.xdata is None:
            return

        self._update_cursor(
            float(event.xdata)
        )

        self.canvas.draw_idle()

    def toggle_cursor(self):

        if self.cursor_line is not None:
            self.clear_cursor()
            return

        if self.current_t is None:
            return

        midpoint = (
            float(
                self.tmin_var.get()
            )
            +
            float(
                self.tmax_var.get()
            )
        ) / 2

        self.cursor_line = self.ax.axvline(
            midpoint,
            linestyle="--",
            linewidth=1.3,
            color=self.colors["muted"],
        )

        self.cursor_text = self.ax.text(
            0.02,
            0.96,
            "",
            transform=self.ax.transAxes,
            va="top",
            fontsize=10,
            color=self.colors["text"],
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": self.colors["accent_soft"],
                "edgecolor": self.colors["border"],
            },
        )

        self.cursor_connection = (
            self.canvas.mpl_connect(
                "motion_notify_event",
                self._cursor_motion,
            )
        )

        self._update_cursor(
            midpoint
        )

        self.canvas.draw_idle()

    def _cursor_motion(self, event):

        if self.cursor_line is None:
            return

        if event.inaxes != self.ax:
            return

        if event.xdata is None:
            return

        self._update_cursor(
            float(event.xdata)
        )

        self.canvas.draw_idle()

    def _update_cursor(self, value):

        if (
            self.cursor_line is None
            or self.current_t is None
            or self.current_x is None
        ):
            return

        index = int(
            np.argmin(
                np.abs(
                    self.current_t
                    - value
                )
            )
        )

        actual_t = self.current_t[
            index
        ]

        actual_x = self.current_x[
            index
        ]

        self.cursor_line.set_xdata(
            [
                actual_t,
                actual_t,
            ]
        )

        if self.cursor_text is not None:
            self.cursor_text.set_text(
                f"t = {actual_t:.5g}\n"
                f"x(t) = {actual_x:.5g}"
            )

    def clear_cursor(self):

        if self.cursor_connection is not None:

            try:
                self.canvas.mpl_disconnect(
                    self.cursor_connection
                )
            except Exception:
                pass

        self.cursor_connection = None

        if self.cursor_line is not None:

            try:
                self.cursor_line.remove()
            except ValueError:
                pass

        if self.cursor_text is not None:

            try:
                self.cursor_text.remove()
            except ValueError:
                pass

        self.cursor_line = None
        self.cursor_text = None

        self.canvas.draw_idle()

    # ========================================================
    # Plot
    # ========================================================

    def plot(self):

        raw = (
            self.expression_var.get()
            .strip()
        )

        if not raw:
            self._show_plot_error(
                "Enter a signal expression."
            )
            return

        try:
            tmin = float(
                self.tmin_var.get()
            )
            tmax = float(
                self.tmax_var.get()
            )

            if tmin >= tmax:
                raise ValueError(
                    "The minimum must be smaller than the maximum."
                )

            if (tmax - tmin) > 10000:
                raise ValueError(
                    "Please choose a smaller time interval."
                )

        except ValueError as exc:

            self._show_plot_error(
                str(exc)
            )

            return

        t = np.linspace(
            tmin,
            tmax,
            8000,
        )

        try:
            x = safe_evaluate(
                raw,
                t,
            )

        except Exception as exc:

            self._show_plot_error(
                "Could not understand the expression.\n\n"
                f"{raw}\n\n"
                f"{exc}"
            )

            return

        self.current_t = t
        self.current_x = x
        self.current_expression = raw

        if (
            not self.history
            or self.history[-1] != raw
        ):
            self.history.append(
                raw
            )

        if len(self.history) > 100:
            self.history = self.history[-100:]

        self._refresh_history_menu()

        self.ax.clear()

        # Main curve
        self.ax.plot(
            t,
            x,
            linewidth=2.2,
            color=self.colors["signal"],
            label=raw,
        )

        # Impulses
        impulses = find_impulses(
            raw
        )

        finite = x[
            np.isfinite(x)
        ]

        scale = max(
            1.0,
            float(
                np.max(
                    np.abs(
                        finite
                    )
                )
            )
            if finite.size
            else 1.0,
        )

        impulse_heights = []

        for location, amplitude in impulses:

            if tmin <= location <= tmax:

                height = (
                    amplitude
                    * scale
                )

                impulse_heights.append(
                    height
                )

                self.ax.annotate(
                    "",
                    xy=(
                        location,
                        height,
                    ),
                    xytext=(
                        location,
                        0,
                    ),
                    arrowprops={
                        "arrowstyle": "->",
                        "linewidth": 2.5,
                        "color": self.colors["signal"],
                    },
                )

                self.ax.scatter(
                    [location],
                    [0],
                    s=28,
                    color=self.colors["signal"],
                    zorder=5,
                )

                self.ax.text(
                    location,
                    height,
                    f" {amplitude:g}δ",
                    fontsize=9,
                    color=self.colors["text"],
                    va="bottom",
                )

        # Axes
        if self.zero_axes_var.get():

            self.ax.axhline(
                0,
                color=self.colors["axis"],
                linewidth=1,
            )

            self.ax.axvline(
                0,
                color=self.colors["axis"],
                linewidth=1,
            )

        self.ax.set_xlim(
            tmin,
            tmax,
        )

        self.ax.set_xlabel(
            "t",
            color=self.colors["text"],
        )

        self.ax.set_ylabel(
            "x(t)",
            color=self.colors["text"],
        )

        self.ax.set_title(
            f"x(t) = {raw}",
            color=self.colors["text"],
            fontsize=13,
            pad=10,
        )

        self.ax.tick_params(
            colors=self.colors["muted"]
        )

        self.ax.set_facecolor(
            self.colors["graph"]
        )

        self.figure.patch.set_facecolor(
            self.colors["panel"]
        )

        self.ax.grid(
            self.grid_var.get(),
            color=self.colors["grid"],
            alpha=0.65,
        )

        # Autoscale Y
        if (
            self.autoscale_var.get()
            and finite.size
        ):

            ymin = float(
                np.min(finite)
            )

            ymax = float(
                np.max(finite)
            )

            if impulse_heights:

                ymin = min(
                    ymin,
                    min(
                        impulse_heights
                    ),
                )

                ymax = max(
                    ymax,
                    max(
                        impulse_heights
                    ),
                )

            if np.isclose(
                ymin,
                ymax,
            ):
                ymin -= 1
                ymax += 1

            margin = max(
                0.1 * (
                    ymax - ymin
                ),
                0.5,
            )

            self.ax.set_ylim(
                ymin - margin,
                ymax + margin,
            )

        if self.show_legend_var.get():

            legend = self.ax.legend(
                loc="best"
            )

            if legend is not None:
                for text in legend.get_texts():
                    text.set_color(
                        self.colors["text"]
                    )

        self.info_expression.config(
            text=f"Expression: {raw}"
        )

        self.info_details.config(
            text=(
                f"{len(t):,} samples   •   "
                f"t = {tmin:g} … {tmax:g}   •   "
                f"min = {np.min(x):.5g}   •   "
                f"max = {np.max(x):.5g}"
            )
        )

        self.status_var.set(
            "Plotted successfully."
        )

        self.canvas.draw_idle()

        self._update_sidebar_scroll()

    # ========================================================
    # Plot error
    # ========================================================

    def _show_plot_error(
        self,
        message: str,
    ):

        self.ax.clear()

        self.ax.set_facecolor(
            self.colors["graph"]
        )

        self.ax.text(
            0.5,
            0.5,
            message,
            ha="center",
            va="center",
            transform=self.ax.transAxes,
            fontsize=11,
            color=self.colors["error"],
        )

        self.ax.set_axis_off()

        self.canvas.draw_idle()

        self.status_var.set(
            "Expression needs attention."
        )

    # ========================================================
    # Sidebar footer / signal metadata
    # ========================================================

    def _update_sidebar_scroll(self):
        try:
            self.sidebar_canvas.configure(
                scrollregion=self.sidebar_canvas.bbox(
                    "all"
                )
            )
        except tk.TclError:
            pass

    # ========================================================
    # Keyboard shortcuts
    # ========================================================

    def _bind_shortcuts(self):
        """Bind common shortcuts without interfering with text entry."""

        # macOS
        self.root.bind(
            "<Command-Return>",
            lambda event: self.plot(),
        )

        self.root.bind(
            "<Command-n>",
            lambda event: self.clear_expression(),
        )

        self.root.bind(
            "<Command-o>",
            lambda event: self.open_expression(),
        )

        self.root.bind(
            "<Command-s>",
            lambda event: self.save_expression(),
        )

        self.root.bind(
            "<Command-Shift-s>",
            lambda event: self.save_image(),
        )

        self.root.bind(
            "<Command-Shift-p>",
            lambda event: self.save_pdf(),
        )

        self.root.bind(
            "<Command-q>",
            lambda event: self.root.destroy(),
        )

        self.root.bind(
            "<Escape>",
            lambda event: self.clear_cursor(),
        )

        # Windows / Linux fallbacks
        self.root.bind(
            "<Control-Return>",
            lambda event: self.plot(),
        )

        self.root.bind(
            "<Control-n>",
            lambda event: self.clear_expression(),
        )

        self.root.bind(
            "<Control-o>",
            lambda event: self.open_expression(),
        )

        self.root.bind(
            "<Control-s>",
            lambda event: self.save_expression(),
        )

        self.root.bind(
            "<Control-Shift-s>",
            lambda event: self.save_image(),
        )

        self.root.bind(
            "<Control-Shift-p>",
            lambda event: self.save_pdf(),
        )

        self.root.bind(
            "<Control-q>",
            lambda event: self.root.destroy(),
        )

    # ========================================================
    # Expression actions
    # ========================================================

    def set_expression(
        self,
        expression: str,
    ):

        self.expression_var.set(
            expression
        )

        self.expression_entry.focus_set()

        self.expression_entry.icursor(
            tk.END
        )

        self.plot()

    def insert_at_cursor(
        self,
        text: str,
    ):

        try:
            position = (
                self.expression_entry.index(
                    tk.INSERT
                )
            )

            self.expression_entry.insert(
                position,
                text,
            )

            self.expression_entry.focus_set()

        except tk.TclError:

            self.expression_var.set(
                self.expression_var.get()
                + text
            )

        self.plot()

    def clear_expression(self):

        self.expression_var.set(
            ""
        )

        self.clear_cursor()

        self.ax.clear()

        self.ax.set_facecolor(
            self.colors["graph"]
        )

        self.ax.axhline(
            0,
            color=self.colors["axis"],
            linewidth=1,
        )

        self.ax.axvline(
            0,
            color=self.colors["axis"],
            linewidth=1,
        )

        self.ax.set_xlabel("t")
        self.ax.set_ylabel("x(t)")
        self.ax.set_title(
            "Enter a signal expression",
            color=self.colors["text"],
        )

        self.ax.grid(
            self.grid_var.get(),
            color=self.colors["grid"],
            alpha=0.65,
        )

        self.canvas.draw_idle()

        self.status_var.set(
            "Ready for a new expression."
        )

    # ========================================================
    # View
    # ========================================================

    def toggle_autoscale(self):

        self.autoscale_var.set(
            not self.autoscale_var.get()
        )

        self.plot()

    def reset_range(self):

        self.tmin_var.set(
            "-10"
        )

        self.tmax_var.set(
            "10"
        )

        self.plot()

    def zoom_in(self):

        try:
            left = float(
                self.tmin_var.get()
            )
            right = float(
                self.tmax_var.get()
            )
        except ValueError:
            return

        center = (
            left + right
        ) / 2

        half = (
            right - left
        ) / 4

        self.tmin_var.set(
            f"{center-half:g}"
        )

        self.tmax_var.set(
            f"{center+half:g}"
        )

        self.plot()

    def zoom_out(self):

        try:
            left = float(
                self.tmin_var.get()
            )
            right = float(
                self.tmax_var.get()
            )
        except ValueError:
            return

        center = (
            left + right
        ) / 2

        half = (
            right - left
        ) / 1

        self.tmin_var.set(
            f"{center-half:g}"
        )

        self.tmax_var.set(
            f"{center+half:g}"
        )

        self.plot()

    def fit_view(self):

        self.autoscale_var.set(
            True
        )

        self.reset_range()

    # ========================================================
    # Theme
    # ========================================================

    def toggle_dark_mode(self):

        self.dark_mode = (
            not self.dark_mode
        )

        self.colors = (
            DARK
            if self.dark_mode
            else LIGHT
        )

        self._rebuild_theme()

    def _rebuild_theme(self):

        style = ttk.Style()

        try:
            style.configure(
                ".",
                background=self.colors["window"],
                foreground=self.colors["text"],
            )

            style.configure(
                "TFrame",
                background=self.colors["window"],
            )

            style.configure(
                "TLabelframe",
                background=self.colors["panel"],
                foreground=self.colors["text"],
            )

            style.configure(
                "TLabelframe.Label",
                background=self.colors["panel"],
                foreground=self.colors["text"],
            )

            style.configure(
                "TLabel",
                background=self.colors["window"],
                foreground=self.colors["text"],
            )

            style.configure(
                "Title.TLabel",
                background=self.colors["window"],
                foreground=self.colors["text"],
            )

            style.configure(
                "Muted.TLabel",
                background=self.colors["window"],
                foreground=self.colors["muted"],
            )

            style.configure(
                "TCheckbutton",
                background=self.colors["panel"],
                foreground=self.colors["text"],
            )

            self.expression_entry.configure(
                foreground=self.colors["text"]
            )

        except tk.TclError:
            pass

        self._apply_widget_colors()

    # ========================================================
    # History / favorites
    # ========================================================

    def add_favorite(self):

        expression = (
            self.expression_var.get()
            .strip()
        )

        if not expression:
            return

        if expression not in self.favorites:

            self.favorites.append(
                expression
            )

            self.status_var.set(
                "Added to favorites."
            )

        else:

            self.status_var.set(
                "Already in favorites."
            )

        self._refresh_favorites_menu()

    def _refresh_history_menu(self):

        if not hasattr(
            self,
            "history_menu",
        ):
            return

        self.history_menu.delete(
            0,
            "end",
        )

        unique = []

        for expression in reversed(
            self.history
        ):

            if expression not in unique:

                unique.append(
                    expression
                )

        if not unique:

            self.history_menu.add_command(
                label="No history yet",
                state="disabled",
            )

            return

        for expression in unique[:30]:

            self.history_menu.add_command(
                label=expression,
                command=lambda e=expression:
                self.set_expression(e),
            )

        self.history_menu.add_separator()

        self.history_menu.add_command(
            label="Clear history",
            command=self.clear_history,
        )

    def clear_history(self):

        self.history.clear()

        self._refresh_history_menu()

        self.status_var.set(
            "History cleared."
        )

    def _refresh_favorites_menu(self):

        if not hasattr(
            self,
            "favorites_menu",
        ):
            return

        self.favorites_menu.delete(
            0,
            "end",
        )

        if not self.favorites:

            self.favorites_menu.add_command(
                label="No favorites yet",
                state="disabled",
            )

            return

        for expression in self.favorites:

            self.favorites_menu.add_command(
                label=expression,
                command=lambda e=expression:
                self.set_expression(e),
            )

        self.favorites_menu.add_separator()

        self.favorites_menu.add_command(
            label="Remove current",
            command=self.remove_current_favorite,
        )

        self.favorites_menu.add_command(
            label="Clear favorites",
            command=self.clear_favorites,
        )

    def remove_current_favorite(self):

        expression = (
            self.expression_var.get()
            .strip()
        )

        if expression in self.favorites:

            self.favorites.remove(
                expression
            )

            self._refresh_favorites_menu()

            self.status_var.set(
                "Removed from favorites."
            )

    def clear_favorites(self):

        self.favorites.clear()

        self._refresh_favorites_menu()

        self.status_var.set(
            "Favorites cleared."
        )

    # ========================================================
    # Analysis
    # ========================================================

    def show_statistics(self):

        if self.current_t is None:
            return

        t = self.current_t
        x = self.current_x

        index = int(
            np.argmax(
                np.abs(x)
            )
        )

        rms = float(
            np.sqrt(
                np.mean(
                    x ** 2
                )
            )
        )

        mean = float(
            np.mean(x)
        )

        area = float(
            np.trapezoid(
                x,
                t,
            )
        )

        messagebox.showinfo(
            "Signal Statistics",
            f"Expression:\n"
            f"{self.current_expression}\n\n"
            f"Samples: {len(t):,}\n"
            f"Minimum: {np.min(x):.8g}\n"
            f"Maximum: {np.max(x):.8g}\n"
            f"Mean: {mean:.8g}\n"
            f"RMS: {rms:.8g}\n"
            f"Area: {area:.8g}\n"
            f"Peak magnitude at:\n"
            f"t ≈ {t[index]:.8g}",
        )

    def inspect_values(self):

        if self.current_t is None:
            return

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "Signal Samples"
        )

        dialog.geometry(
            "650x500"
        )

        outer = ttk.Frame(
            dialog,
            padding=10,
        )

        outer.pack(
            fill="both",
            expand=True,
        )

        text = tk.Text(
            outer,
            font=("Menlo", 10),
            wrap="none",
        )

        text.pack(
            fill="both",
            expand=True,
        )

        x = self.current_x
        t = self.current_t

        indices = np.linspace(
            0,
            len(t) - 1,
            min(200, len(t)),
            dtype=int,
        )

        text.insert(
            "end",
            "                 t                 x(t)\n"
        )

        text.insert(
            "end",
            "------------------------------------------------\n"
        )

        for index in indices:

            text.insert(
                "end",
                f"{t[index]:18.8f}   "
                f"{x[index]:18.8f}\n"
            )

        text.config(
            state="disabled"
        )

    def find_peak(self):

        if self.current_t is None:
            return

        index = int(
            np.argmax(
                np.abs(
                    self.current_x
                )
            )
        )

        messagebox.showinfo(
            "Approximate Peak",
            f"|x(t)| ≈ "
            f"{abs(self.current_x[index]):.8g}\n\n"
            f"At t ≈ "
            f"{self.current_t[index]:.8g}",
        )

    def find_area(self):

        if self.current_t is None:
            return

        area = np.trapezoid(
            self.current_x,
            self.current_t,
        )

        messagebox.showinfo(
            "Approximate Area",
            f"Numerical area over the "
            f"visible range:\n\n"
            f"{area:.8g}",
        )

    def compare_signal(self):

        if self.current_t is None:
            return

        expression = simpledialog.askstring(
            "Compare Signals",
            "Enter the second signal expression:",
            parent=self.root,
            initialvalue="r(t-1)",
        )

        if not expression:
            return

        try:

            x2 = safe_evaluate(
                expression,
                self.current_t,
            )

        except Exception as exc:

            messagebox.showerror(
                "Compare Error",
                str(exc),
            )

            return

        self.ax.clear()

        self.ax.plot(
            self.current_t,
            self.current_x,
            linewidth=2.2,
            color=self.colors["signal"],
            label=self.current_expression,
        )

        self.ax.plot(
            self.current_t,
            x2,
            linewidth=2.0,
            linestyle="--",
            color=self.colors["muted"],
            label=expression,
        )

        if self.zero_axes_var.get():

            self.ax.axhline(
                0,
                color=self.colors["axis"],
                linewidth=1,
            )

            self.ax.axvline(
                0,
                color=self.colors["axis"],
                linewidth=1,
            )

        self.ax.set_facecolor(
            self.colors["graph"]
        )

        self.ax.grid(
            self.grid_var.get(),
            color=self.colors["grid"],
            alpha=0.65,
        )

        self.ax.set_xlabel(
            "t",
            color=self.colors["text"],
        )

        self.ax.set_ylabel(
            "Amplitude",
            color=self.colors["text"],
        )

        self.ax.set_title(
            "Signal Comparison",
            color=self.colors["text"],
        )

        if self.show_legend_var.get():
            self.ax.legend()

        if self.autoscale_var.get():
            self.ax.relim()
            self.ax.autoscale_view()

        self.canvas.draw_idle()

        self.status_var.set(
            f"Comparing with {expression}"
        )

    # ========================================================
    # File operations
    # ========================================================

    def suggested_name(self):

        return (
            re.sub(
                r"[^A-Za-z0-9._-]+",
                "_",
                self.expression_var.get()
                .strip(),
            )[:80]
            or "signal"
        )

    def save_image(self):

        filename = filedialog.asksaveasfilename(
            title="Save Signal as Image",
            initialfile=(
                self.suggested_name()
                + ".png"
            ),
            defaultextension=".png",
            filetypes=[
                ("PNG image", "*.png"),
                ("JPEG image", "*.jpg"),
                ("SVG image", "*.svg"),
            ],
        )

        if not filename:
            return

        try:

            self.figure.savefig(
                filename,
                dpi=300,
                bbox_inches="tight",
                facecolor=self.figure.get_facecolor(),
            )

            self.status_var.set(
                f"Saved image: "
                f"{Path(filename).name}"
            )

        except Exception as exc:

            messagebox.showerror(
                "Save Image",
                str(exc),
            )

    def save_pdf(self):

        filename = filedialog.asksaveasfilename(
            title="Save Signal as PDF",
            initialfile=(
                self.suggested_name()
                + ".pdf"
            ),
            defaultextension=".pdf",
            filetypes=[
                ("PDF document", "*.pdf"),
            ],
        )

        if not filename:
            return

        try:

            self.figure.savefig(
                filename,
                bbox_inches="tight",
            )

            self.status_var.set(
                f"Saved PDF: "
                f"{Path(filename).name}"
            )

        except Exception as exc:

            messagebox.showerror(
                "Save PDF",
                str(exc),
            )

    def export_csv(self):

        if self.current_t is None:
            return

        filename = filedialog.asksaveasfilename(
            title="Export Signal Samples",
            initialfile=(
                self.suggested_name()
                + ".csv"
            ),
            defaultextension=".csv",
            filetypes=[
                ("CSV file", "*.csv"),
            ],
        )

        if not filename:
            return

        try:

            with open(
                filename,
                "w",
                newline="",
                encoding="utf-8",
            ) as file:

                writer = csv.writer(
                    file
                )

                writer.writerow(
                    [
                        "t",
                        "x(t)",
                    ]
                )

                writer.writerows(
                    zip(
                        self.current_t,
                        self.current_x,
                    )
                )

            self.status_var.set(
                f"Exported CSV: "
                f"{Path(filename).name}"
            )

        except OSError as exc:

            messagebox.showerror(
                "Export CSV",
                str(exc),
            )

    def save_expression(self):

        filename = filedialog.asksaveasfilename(
            title="Save Expression",
            initialfile="signal_expression.txt",
            defaultextension=".txt",
            filetypes=[
                ("Text file", "*.txt"),
            ],
        )

        if not filename:
            return

        try:

            Path(filename).write_text(
                self.expression_var.get(),
                encoding="utf-8",
            )

            self.status_var.set(
                f"Saved expression: "
                f"{Path(filename).name}"
            )

        except OSError as exc:

            messagebox.showerror(
                "Save Expression",
                str(exc),
            )

    def open_expression(self):

        filename = filedialog.askopenfilename(
            title="Open Expression",
            filetypes=[
                ("Text file", "*.txt"),
                ("All files", "*.*"),
            ],
        )

        if not filename:
            return

        try:

            expression = Path(
                filename
            ).read_text(
                encoding="utf-8"
            ).strip()

            self.set_expression(
                expression
            )

        except OSError as exc:

            messagebox.showerror(
                "Open Expression",
                str(exc),
            )

    # ========================================================
    # Help
    # ========================================================

    def open_help(self):

        pdf = (
            self.script_dir
            / "Signals_and_Systems_Help_Book.pdf"
        )

        if not pdf.exists():

            messagebox.showwarning(
                "Help Book Not Found",
                "The Help Book PDF is missing.\n\n"
                "Place this file beside the Python program:\n\n"
                f"{pdf.name}\n\n"
                f"Expected location:\n{pdf}",
            )

            return

        try:

            if sys.platform == "darwin":

                subprocess.Popen(
                    ["open", str(pdf)]
                )

            elif os.name == "nt":

                os.startfile(
                    str(pdf)
                )

            else:

                subprocess.Popen(
                    ["xdg-open", str(pdf)]
                )

            self.status_var.set(
                "Help Book opened."
            )

        except Exception as exc:

            messagebox.showerror(
                "Open Help",
                str(exc),
            )

    def show_examples(self):

        dialog = tk.Toplevel(
            self.root
        )

        dialog.title(
            "Signal Examples"
        )

        dialog.geometry(
            "720x560"
        )

        text = tk.Text(
            dialog,
            font=("Menlo", 10),
            wrap="word",
        )

        text.pack(
            fill="both",
            expand=True,
            padx=10,
            pady=10,
        )

        for preset in (
            CONSTRUCTION_PRESETS
            + TRANSFORM_PRESETS
        ):

            text.insert(
                "end",
                f"{preset.name}\n",
                "heading",
            )

            text.insert(
                "end",
                f"    {preset.expression}\n"
                f"    {preset.description}\n\n",
            )

        text.tag_configure(
            "heading",
            font=("Helvetica", 11, "bold"),
        )

        text.config(
            state="disabled"
        )

    def show_shortcuts(self):

        messagebox.showinfo(
            "Keyboard Shortcuts",
            "Enter\n"
            "Plot expression.\n\n"
            "⌘ + N\n"
            "New / clear.\n\n"
            "⌘ + O\n"
            "Open expression.\n\n"
            "⌘ + S\n"
            "Save expression.\n\n"
            "⇧ + ⌘ + S\n"
            "Save image.\n\n"
            "⇧ + ⌘ + P\n"
            "Save PDF.\n\n"
            "⌘ + Q\n"
            "Exit.\n\n"
            "Escape\n"
            "Clear moving cursor.",
        )

    def about(self):

        messagebox.showinfo(
            "About",
            "Signals & Systems Studio\n\n"
            "A study-first continuous-time signal explorer.\n\n"
            "Built around direct expression entry, "
            "signal construction, analysis, and export.",
        )


# ============================================================
# Extra study/reference data
# ============================================================

# The application deliberately keeps a substantial, searchable
# study catalogue in source form. It can be surfaced by future
# versions without changing the plotting engine.

STUDY_REFERENCE = {
    "unit_step": (
        "u(t)",
        "Unit step: 0 for t<0 and 1 for t>=0.",
        [
            "u(t)",
            "u(t-2)",
            "u(t+1)",
            "u(t)-u(t-3)",
        ],
    ),
    "unit_ramp": (
        "r(t)",
        "Unit ramp: max(t,0).",
        [
            "r(t)",
            "r(t-2)",
            "r(t+1)",
            "r(t)-r(t-2)",
        ],
    ),
    "impulse": (
        "delta(t)",
        "Dirac impulse, displayed as an arrow.",
        [
            "delta(t)",
            "delta(t-2)",
            "2*delta(t+1)",
            "delta(t)+2*delta(t-3)",
        ],
    ),
    "rectangle": (
        "rect(t)",
        "Unit rectangular pulse.",
        [
            "rect(t)",
            "rect(t-1)",
        ],
    ),
    "triangle": (
        "tri(t)",
        "Unit triangular pulse.",
        [
            "tri(t)",
            "tri(t-1)",
        ],
    ),
    "sinc": (
        "sinc(t)",
        "Normalized sinc.",
        [
            "sinc(t)",
            "sinc(2*t)",
        ],
    ),
    "sinusoid": (
        "sin(t), cos(t)",
        "Periodic sinusoidal signals.",
        [
            "sin(t)",
            "sin(2*t)",
            "cos(3*t)",
        ],
    ),
    "exponential": (
        "exp(t)",
        "Exponential growth or decay.",
        [
            "exp(t)",
            "exp(-t)",
            "exp(-0.2*t)*u(t)",
        ],
    ),
}


def get_study_reference():
    return dict(STUDY_REFERENCE)


def get_supported_names():
    return sorted(
        name
        for name in EVAL_NAMES
        if callable(
            EVAL_NAMES[name]
        )
        or isinstance(
            EVAL_NAMES[name],
            (int, float),
        )
    )


# ============================================================
# Large practice catalogue
# ============================================================
# This is intentionally generated from parameterized study
# families rather than empty padding. Each record is a concrete
# expression a Signals & Systems student can load and plot.
# ============================================================

PRACTICE_CATALOGUE = []

for shift in range(-20, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Step shift {shift:+d}",
            f"u(t{shift:+d})",
            "Shifted unit step.",
        )
    )

for shift in range(-20, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Ramp shift {shift:+d}",
            f"r(t{shift:+d})",
            "Shifted unit ramp.",
        )
    )

for shift in range(-20, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Impulse shift {shift:+d}",
            f"delta(t{shift:+d})",
            "Shifted unit impulse.",
        )
    )

for amplitude in range(1, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Step amplitude {amplitude}",
            f"{amplitude}*u(t)",
            "Amplitude-scaled step.",
        )
    )

for amplitude in range(1, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Ramp amplitude {amplitude}",
            f"{amplitude}*r(t)",
            "Amplitude-scaled ramp.",
        )
    )

for amplitude in range(1, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Impulse amplitude {amplitude}",
            f"{amplitude}*delta(t)",
            "Amplitude-scaled impulse.",
        )
    )

for frequency in range(1, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Sine frequency {frequency}",
            f"sin({frequency}*t)",
            "Sine with frequency factor.",
        )
    )

for frequency in range(1, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Cosine frequency {frequency}",
            f"cos({frequency}*t)",
            "Cosine with frequency factor.",
        )
    )

for width in range(1, 21):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Step pulse width {width}",
            f"u(t)-u(t-{width})",
            "Rectangular pulse.",
        )
    )

for spacing in range(1, 16):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Triangle spacing {spacing}",
            f"r(t)-2*r(t-{spacing})+r(t-{2*spacing})",
            "Triangle built from ramps.",
        )
    )

for shift in range(1, 16):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Damped sine {shift}",
            f"exp(-0.{shift}*t)*sin(2*t)*u(t)",
            "Causal damped sine.",
        )
    )

for shift in range(1, 16):
    PRACTICE_CATALOGUE.append(
        Preset(
            f"Damped cosine {shift}",
            f"exp(-0.{shift}*t)*cos(2*t)*u(t)",
            "Causal damped cosine.",
        )
    )


# ============================================================
# Application entry point
# ============================================================

def main():
    root = tk.Tk()

    try:
        # On macOS this gives the native-ish app activation
        # behaviour without replacing the user's Python build.
        if platform.system() == "Darwin":
            root.createcommand(
                "tk::mac::ShowPreferences",
                lambda: None,
            )
    except tk.TclError:
        pass

    SignalsStudio(
        root
    )

    root.mainloop()


if __name__ == "__main__":
    main()

# ============================================================
# 5000-LINE STUDY EXERCISE BANK
# ============================================================
# Real, parameterized practice prompts rather than blank filler.
# ============================================================

PRACTICE_EXERCISES_5000 = [
    (1, 'u(t-1)', 'Practice step shift number 1: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 1: Step shift -> u(t-1)
    (2, 'u(t+2)', 'Practice advanced step number 2: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 2: Advanced step -> u(t+2)
    (3, 'r(t-3)', 'Practice ramp shift number 3: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 3: Ramp shift -> r(t-3)
    (4, 'r(t+4)', 'Practice advanced ramp number 4: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 4: Advanced ramp -> r(t+4)
    (5, '6*u(t)', 'Practice scaled step number 5: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 5: Scaled step -> 6*u(t)
    (6, '7*r(t)', 'Practice scaled ramp number 6: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 6: Scaled ramp -> 7*r(t)
    (7, 'delta(t-7)', 'Practice impulse shift number 7: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 7: Impulse shift -> delta(t-7)
    (8, 'delta(t-8)+delta(t+8)', 'Practice impulse pair number 8: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 8: Impulse pair -> delta(t-8)+delta(t+8)
    (9, 'u(t)-u(t-10)', 'Practice pulse number 9: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 9: Pulse -> u(t)-u(t-10)
    (10, 'u(t-0)-u(t-3)', 'Practice delayed pulse number 10: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 10: Delayed pulse -> u(t-0)-u(t-3)
    (11, 'r(t)-r(t-12)', 'Practice finite ramp number 11: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 11: Finite ramp -> r(t)-r(t-12)
    (12, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 12: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 12: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (13, 'sin(4*t)', 'Practice sine number 13: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 13: Sine -> sin(4*t)
    (14, 'cos(5*t)', 'Practice cosine number 14: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 14: Cosine -> cos(5*t)
    (15, 'exp(-0.7*t)*sin(2*t)*u(t)', 'Practice damped sine number 15: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 15: Damped sine -> exp(-0.7*t)*sin(2*t)*u(t)
    (16, 'exp(-0.8*t)*cos(2*t)*u(t)', 'Practice damped cosine number 16: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 16: Damped cosine -> exp(-0.8*t)*cos(2*t)*u(t)
    (17, 'rect(t/2)', 'Practice rectangle number 17: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 17: Rectangle -> rect(t/2)
    (18, 'tri(t/3)', 'Practice triangle pulse number 18: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 18: Triangle pulse -> tri(t/3)
    (19, 'sinc(4*t)', 'Practice sinc number 19: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 19: Sinc -> sinc(4*t)
    (20, 'sgn(t-4)', 'Practice sign number 20: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 20: Sign -> sgn(t-4)
    (21, 'abs(t-5)', 'Practice absolute value number 21: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 21: Absolute value -> abs(t-5)
    (22, '(t-6)**2', 'Practice parabola number 22: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 22: Parabola -> (t-6)**2
    (23, 'sin(8*t)*u(t)', 'Practice causal sine number 23: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 23: Causal sine -> sin(8*t)*u(t)
    (24, 'cos(1*t)*u(t)', 'Practice causal cosine number 24: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 24: Causal cosine -> cos(1*t)*u(t)
    (25, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 25: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 25: Ramp-step combination -> r(t)+5*u(t-1)
    (26, 'u(t)+u(t-1)+u(t-3)', 'Practice step staircase number 26: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 26: Step staircase -> u(t)+u(t-1)+u(t-3)
    (27, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 27: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 27: Odd impulse pair -> delta(t+4)-delta(t-4)
    (28, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 28: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 28: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (29, 'u(t-9)', 'Practice step shift number 29: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 29: Step shift -> u(t-9)
    (30, 'u(t+10)', 'Practice advanced step number 30: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 30: Advanced step -> u(t+10)
    (31, 'r(t-11)', 'Practice ramp shift number 31: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 31: Ramp shift -> r(t-11)
    (32, 'r(t+12)', 'Practice advanced ramp number 32: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 32: Advanced ramp -> r(t+12)
    (33, '4*u(t)', 'Practice scaled step number 33: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 33: Scaled step -> 4*u(t)
    (34, '5*r(t)', 'Practice scaled ramp number 34: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 34: Scaled ramp -> 5*r(t)
    (35, 'delta(t-5)', 'Practice impulse shift number 35: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 35: Impulse shift -> delta(t-5)
    (36, 'delta(t-6)+delta(t+6)', 'Practice impulse pair number 36: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 36: Impulse pair -> delta(t-6)+delta(t+6)
    (37, 'u(t)-u(t-2)', 'Practice pulse number 37: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 37: Pulse -> u(t)-u(t-2)
    (38, 'u(t-8)-u(t-11)', 'Practice delayed pulse number 38: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 38: Delayed pulse -> u(t-8)-u(t-11)
    (39, 'r(t)-r(t-4)', 'Practice finite ramp number 39: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 39: Finite ramp -> r(t)-r(t-4)
    (40, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 40: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 40: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (41, 'sin(2*t)', 'Practice sine number 41: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 41: Sine -> sin(2*t)
    (42, 'cos(3*t)', 'Practice cosine number 42: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 42: Cosine -> cos(3*t)
    (43, 'exp(-0.8*t)*sin(2*t)*u(t)', 'Practice damped sine number 43: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 43: Damped sine -> exp(-0.8*t)*sin(2*t)*u(t)
    (44, 'exp(-0.9*t)*cos(2*t)*u(t)', 'Practice damped cosine number 44: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 44: Damped cosine -> exp(-0.9*t)*cos(2*t)*u(t)
    (45, 'rect(t/6)', 'Practice rectangle number 45: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 45: Rectangle -> rect(t/6)
    (46, 'tri(t/7)', 'Practice triangle pulse number 46: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 46: Triangle pulse -> tri(t/7)
    (47, 'sinc(8*t)', 'Practice sinc number 47: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 47: Sinc -> sinc(8*t)
    (48, 'sgn(t-0)', 'Practice sign number 48: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 48: Sign -> sgn(t-0)
    (49, 'abs(t-1)', 'Practice absolute value number 49: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 49: Absolute value -> abs(t-1)
    (50, '(t-2)**2', 'Practice parabola number 50: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 50: Parabola -> (t-2)**2
    (51, 'sin(4*t)*u(t)', 'Practice causal sine number 51: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 51: Causal sine -> sin(4*t)*u(t)
    (52, 'cos(5*t)*u(t)', 'Practice causal cosine number 52: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 52: Causal cosine -> cos(5*t)*u(t)
    (53, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 53: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 53: Ramp-step combination -> r(t)+5*u(t-5)
    (54, 'u(t)+u(t-4)+u(t-6)', 'Practice step staircase number 54: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 54: Step staircase -> u(t)+u(t-4)+u(t-6)
    (55, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 55: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 55: Odd impulse pair -> delta(t+2)-delta(t-2)
    (56, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 56: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 56: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (57, 'u(t-17)', 'Practice step shift number 57: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 57: Step shift -> u(t-17)
    (58, 'u(t+18)', 'Practice advanced step number 58: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 58: Advanced step -> u(t+18)
    (59, 'r(t-19)', 'Practice ramp shift number 59: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 59: Ramp shift -> r(t-19)
    (60, 'r(t+0)', 'Practice advanced ramp number 60: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 60: Advanced ramp -> r(t+0)
    (61, '2*u(t)', 'Practice scaled step number 61: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 61: Scaled step -> 2*u(t)
    (62, '3*r(t)', 'Practice scaled ramp number 62: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 62: Scaled ramp -> 3*r(t)
    (63, 'delta(t-3)', 'Practice impulse shift number 63: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 63: Impulse shift -> delta(t-3)
    (64, 'delta(t-4)+delta(t+4)', 'Practice impulse pair number 64: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 64: Impulse pair -> delta(t-4)+delta(t+4)
    (65, 'u(t)-u(t-6)', 'Practice pulse number 65: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 65: Pulse -> u(t)-u(t-6)
    (66, 'u(t-6)-u(t-9)', 'Practice delayed pulse number 66: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 66: Delayed pulse -> u(t-6)-u(t-9)
    (67, 'r(t)-r(t-8)', 'Practice finite ramp number 67: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 67: Finite ramp -> r(t)-r(t-8)
    (68, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 68: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 68: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (69, 'sin(10*t)', 'Practice sine number 69: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 69: Sine -> sin(10*t)
    (70, 'cos(1*t)', 'Practice cosine number 70: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 70: Cosine -> cos(1*t)
    (71, 'exp(-0.9*t)*sin(2*t)*u(t)', 'Practice damped sine number 71: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 71: Damped sine -> exp(-0.9*t)*sin(2*t)*u(t)
    (72, 'exp(-0.1*t)*cos(2*t)*u(t)', 'Practice damped cosine number 72: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 72: Damped cosine -> exp(-0.1*t)*cos(2*t)*u(t)
    (73, 'rect(t/2)', 'Practice rectangle number 73: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 73: Rectangle -> rect(t/2)
    (74, 'tri(t/3)', 'Practice triangle pulse number 74: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 74: Triangle pulse -> tri(t/3)
    (75, 'sinc(4*t)', 'Practice sinc number 75: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 75: Sinc -> sinc(4*t)
    (76, 'sgn(t-4)', 'Practice sign number 76: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 76: Sign -> sgn(t-4)
    (77, 'abs(t-5)', 'Practice absolute value number 77: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 77: Absolute value -> abs(t-5)
    (78, '(t-6)**2', 'Practice parabola number 78: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 78: Parabola -> (t-6)**2
    (79, 'sin(8*t)*u(t)', 'Practice causal sine number 79: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 79: Causal sine -> sin(8*t)*u(t)
    (80, 'cos(1*t)*u(t)', 'Practice causal cosine number 80: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 80: Causal cosine -> cos(1*t)*u(t)
    (81, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 81: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 81: Ramp-step combination -> r(t)+5*u(t-3)
    (82, 'u(t)+u(t-2)+u(t-4)', 'Practice step staircase number 82: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 82: Step staircase -> u(t)+u(t-2)+u(t-4)
    (83, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 83: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 83: Odd impulse pair -> delta(t+6)-delta(t-6)
    (84, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 84: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 84: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (85, 'u(t-5)', 'Practice step shift number 85: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 85: Step shift -> u(t-5)
    (86, 'u(t+6)', 'Practice advanced step number 86: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 86: Advanced step -> u(t+6)
    (87, 'r(t-7)', 'Practice ramp shift number 87: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 87: Ramp shift -> r(t-7)
    (88, 'r(t+8)', 'Practice advanced ramp number 88: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 88: Advanced ramp -> r(t+8)
    (89, '10*u(t)', 'Practice scaled step number 89: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 89: Scaled step -> 10*u(t)
    (90, '1*r(t)', 'Practice scaled ramp number 90: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 90: Scaled ramp -> 1*r(t)
    (91, 'delta(t-1)', 'Practice impulse shift number 91: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 91: Impulse shift -> delta(t-1)
    (92, 'delta(t-2)+delta(t+2)', 'Practice impulse pair number 92: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 92: Impulse pair -> delta(t-2)+delta(t+2)
    (93, 'u(t)-u(t-10)', 'Practice pulse number 93: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 93: Pulse -> u(t)-u(t-10)
    (94, 'u(t-4)-u(t-7)', 'Practice delayed pulse number 94: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 94: Delayed pulse -> u(t-4)-u(t-7)
    (95, 'r(t)-r(t-12)', 'Practice finite ramp number 95: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 95: Finite ramp -> r(t)-r(t-12)
    (96, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 96: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 96: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (97, 'sin(8*t)', 'Practice sine number 97: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 97: Sine -> sin(8*t)
    (98, 'cos(9*t)', 'Practice cosine number 98: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 98: Cosine -> cos(9*t)
    (99, 'exp(-0.1*t)*sin(2*t)*u(t)', 'Practice damped sine number 99: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 99: Damped sine -> exp(-0.1*t)*sin(2*t)*u(t)
    (100, 'exp(-0.2*t)*cos(2*t)*u(t)', 'Practice damped cosine number 100: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 100: Damped cosine -> exp(-0.2*t)*cos(2*t)*u(t)
    (101, 'rect(t/6)', 'Practice rectangle number 101: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 101: Rectangle -> rect(t/6)
    (102, 'tri(t/7)', 'Practice triangle pulse number 102: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 102: Triangle pulse -> tri(t/7)
    (103, 'sinc(8*t)', 'Practice sinc number 103: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 103: Sinc -> sinc(8*t)
    (104, 'sgn(t-0)', 'Practice sign number 104: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 104: Sign -> sgn(t-0)
    (105, 'abs(t-1)', 'Practice absolute value number 105: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 105: Absolute value -> abs(t-1)
    (106, '(t-2)**2', 'Practice parabola number 106: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 106: Parabola -> (t-2)**2
    (107, 'sin(4*t)*u(t)', 'Practice causal sine number 107: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 107: Causal sine -> sin(4*t)*u(t)
    (108, 'cos(5*t)*u(t)', 'Practice causal cosine number 108: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 108: Causal cosine -> cos(5*t)*u(t)
    (109, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 109: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 109: Ramp-step combination -> r(t)+5*u(t-1)
    (110, 'u(t)+u(t-0)+u(t-2)', 'Practice step staircase number 110: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 110: Step staircase -> u(t)+u(t-0)+u(t-2)
    (111, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 111: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 111: Odd impulse pair -> delta(t+4)-delta(t-4)
    (112, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 112: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 112: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (113, 'u(t-13)', 'Practice step shift number 113: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 113: Step shift -> u(t-13)
    (114, 'u(t+14)', 'Practice advanced step number 114: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 114: Advanced step -> u(t+14)
    (115, 'r(t-15)', 'Practice ramp shift number 115: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 115: Ramp shift -> r(t-15)
    (116, 'r(t+16)', 'Practice advanced ramp number 116: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 116: Advanced ramp -> r(t+16)
    (117, '8*u(t)', 'Practice scaled step number 117: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 117: Scaled step -> 8*u(t)
    (118, '9*r(t)', 'Practice scaled ramp number 118: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 118: Scaled ramp -> 9*r(t)
    (119, 'delta(t-14)', 'Practice impulse shift number 119: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 119: Impulse shift -> delta(t-14)
    (120, 'delta(t-0)+delta(t+0)', 'Practice impulse pair number 120: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 120: Impulse pair -> delta(t-0)+delta(t+0)
    (121, 'u(t)-u(t-2)', 'Practice pulse number 121: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 121: Pulse -> u(t)-u(t-2)
    (122, 'u(t-2)-u(t-5)', 'Practice delayed pulse number 122: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 122: Delayed pulse -> u(t-2)-u(t-5)
    (123, 'r(t)-r(t-4)', 'Practice finite ramp number 123: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 123: Finite ramp -> r(t)-r(t-4)
    (124, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 124: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 124: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (125, 'sin(6*t)', 'Practice sine number 125: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 125: Sine -> sin(6*t)
    (126, 'cos(7*t)', 'Practice cosine number 126: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 126: Cosine -> cos(7*t)
    (127, 'exp(-0.2*t)*sin(2*t)*u(t)', 'Practice damped sine number 127: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 127: Damped sine -> exp(-0.2*t)*sin(2*t)*u(t)
    (128, 'exp(-0.3*t)*cos(2*t)*u(t)', 'Practice damped cosine number 128: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 128: Damped cosine -> exp(-0.3*t)*cos(2*t)*u(t)
    (129, 'rect(t/2)', 'Practice rectangle number 129: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 129: Rectangle -> rect(t/2)
    (130, 'tri(t/3)', 'Practice triangle pulse number 130: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 130: Triangle pulse -> tri(t/3)
    (131, 'sinc(4*t)', 'Practice sinc number 131: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 131: Sinc -> sinc(4*t)
    (132, 'sgn(t-4)', 'Practice sign number 132: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 132: Sign -> sgn(t-4)
    (133, 'abs(t-5)', 'Practice absolute value number 133: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 133: Absolute value -> abs(t-5)
    (134, '(t-6)**2', 'Practice parabola number 134: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 134: Parabola -> (t-6)**2
    (135, 'sin(8*t)*u(t)', 'Practice causal sine number 135: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 135: Causal sine -> sin(8*t)*u(t)
    (136, 'cos(1*t)*u(t)', 'Practice causal cosine number 136: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 136: Causal cosine -> cos(1*t)*u(t)
    (137, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 137: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 137: Ramp-step combination -> r(t)+5*u(t-5)
    (138, 'u(t)+u(t-3)+u(t-5)', 'Practice step staircase number 138: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 138: Step staircase -> u(t)+u(t-3)+u(t-5)
    (139, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 139: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 139: Odd impulse pair -> delta(t+2)-delta(t-2)
    (140, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 140: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 140: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (141, 'u(t-1)', 'Practice step shift number 141: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 141: Step shift -> u(t-1)
    (142, 'u(t+2)', 'Practice advanced step number 142: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 142: Advanced step -> u(t+2)
    (143, 'r(t-3)', 'Practice ramp shift number 143: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 143: Ramp shift -> r(t-3)
    (144, 'r(t+4)', 'Practice advanced ramp number 144: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 144: Advanced ramp -> r(t+4)
    (145, '6*u(t)', 'Practice scaled step number 145: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 145: Scaled step -> 6*u(t)
    (146, '7*r(t)', 'Practice scaled ramp number 146: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 146: Scaled ramp -> 7*r(t)
    (147, 'delta(t-12)', 'Practice impulse shift number 147: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 147: Impulse shift -> delta(t-12)
    (148, 'delta(t-8)+delta(t+8)', 'Practice impulse pair number 148: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 148: Impulse pair -> delta(t-8)+delta(t+8)
    (149, 'u(t)-u(t-6)', 'Practice pulse number 149: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 149: Pulse -> u(t)-u(t-6)
    (150, 'u(t-0)-u(t-3)', 'Practice delayed pulse number 150: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 150: Delayed pulse -> u(t-0)-u(t-3)
    (151, 'r(t)-r(t-8)', 'Practice finite ramp number 151: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 151: Finite ramp -> r(t)-r(t-8)
    (152, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 152: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 152: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (153, 'sin(4*t)', 'Practice sine number 153: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 153: Sine -> sin(4*t)
    (154, 'cos(5*t)', 'Practice cosine number 154: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 154: Cosine -> cos(5*t)
    (155, 'exp(-0.3*t)*sin(2*t)*u(t)', 'Practice damped sine number 155: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 155: Damped sine -> exp(-0.3*t)*sin(2*t)*u(t)
    (156, 'exp(-0.4*t)*cos(2*t)*u(t)', 'Practice damped cosine number 156: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 156: Damped cosine -> exp(-0.4*t)*cos(2*t)*u(t)
    (157, 'rect(t/6)', 'Practice rectangle number 157: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 157: Rectangle -> rect(t/6)
    (158, 'tri(t/7)', 'Practice triangle pulse number 158: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 158: Triangle pulse -> tri(t/7)
    (159, 'sinc(8*t)', 'Practice sinc number 159: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 159: Sinc -> sinc(8*t)
    (160, 'sgn(t-0)', 'Practice sign number 160: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 160: Sign -> sgn(t-0)
    (161, 'abs(t-1)', 'Practice absolute value number 161: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 161: Absolute value -> abs(t-1)
    (162, '(t-2)**2', 'Practice parabola number 162: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 162: Parabola -> (t-2)**2
    (163, 'sin(4*t)*u(t)', 'Practice causal sine number 163: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 163: Causal sine -> sin(4*t)*u(t)
    (164, 'cos(5*t)*u(t)', 'Practice causal cosine number 164: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 164: Causal cosine -> cos(5*t)*u(t)
    (165, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 165: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 165: Ramp-step combination -> r(t)+5*u(t-3)
    (166, 'u(t)+u(t-1)+u(t-3)', 'Practice step staircase number 166: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 166: Step staircase -> u(t)+u(t-1)+u(t-3)
    (167, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 167: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 167: Odd impulse pair -> delta(t+6)-delta(t-6)
    (168, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 168: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 168: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (169, 'u(t-9)', 'Practice step shift number 169: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 169: Step shift -> u(t-9)
    (170, 'u(t+10)', 'Practice advanced step number 170: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 170: Advanced step -> u(t+10)
    (171, 'r(t-11)', 'Practice ramp shift number 171: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 171: Ramp shift -> r(t-11)
    (172, 'r(t+12)', 'Practice advanced ramp number 172: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 172: Advanced ramp -> r(t+12)
    (173, '4*u(t)', 'Practice scaled step number 173: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 173: Scaled step -> 4*u(t)
    (174, '5*r(t)', 'Practice scaled ramp number 174: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 174: Scaled ramp -> 5*r(t)
    (175, 'delta(t-10)', 'Practice impulse shift number 175: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 175: Impulse shift -> delta(t-10)
    (176, 'delta(t-6)+delta(t+6)', 'Practice impulse pair number 176: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 176: Impulse pair -> delta(t-6)+delta(t+6)
    (177, 'u(t)-u(t-10)', 'Practice pulse number 177: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 177: Pulse -> u(t)-u(t-10)
    (178, 'u(t-8)-u(t-11)', 'Practice delayed pulse number 178: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 178: Delayed pulse -> u(t-8)-u(t-11)
    (179, 'r(t)-r(t-12)', 'Practice finite ramp number 179: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 179: Finite ramp -> r(t)-r(t-12)
    (180, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 180: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 180: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (181, 'sin(2*t)', 'Practice sine number 181: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 181: Sine -> sin(2*t)
    (182, 'cos(3*t)', 'Practice cosine number 182: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 182: Cosine -> cos(3*t)
    (183, 'exp(-0.4*t)*sin(2*t)*u(t)', 'Practice damped sine number 183: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 183: Damped sine -> exp(-0.4*t)*sin(2*t)*u(t)
    (184, 'exp(-0.5*t)*cos(2*t)*u(t)', 'Practice damped cosine number 184: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 184: Damped cosine -> exp(-0.5*t)*cos(2*t)*u(t)
    (185, 'rect(t/2)', 'Practice rectangle number 185: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 185: Rectangle -> rect(t/2)
    (186, 'tri(t/3)', 'Practice triangle pulse number 186: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 186: Triangle pulse -> tri(t/3)
    (187, 'sinc(4*t)', 'Practice sinc number 187: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 187: Sinc -> sinc(4*t)
    (188, 'sgn(t-4)', 'Practice sign number 188: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 188: Sign -> sgn(t-4)
    (189, 'abs(t-5)', 'Practice absolute value number 189: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 189: Absolute value -> abs(t-5)
    (190, '(t-6)**2', 'Practice parabola number 190: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 190: Parabola -> (t-6)**2
    (191, 'sin(8*t)*u(t)', 'Practice causal sine number 191: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 191: Causal sine -> sin(8*t)*u(t)
    (192, 'cos(1*t)*u(t)', 'Practice causal cosine number 192: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 192: Causal cosine -> cos(1*t)*u(t)
    (193, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 193: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 193: Ramp-step combination -> r(t)+5*u(t-1)
    (194, 'u(t)+u(t-4)+u(t-6)', 'Practice step staircase number 194: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 194: Step staircase -> u(t)+u(t-4)+u(t-6)
    (195, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 195: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 195: Odd impulse pair -> delta(t+4)-delta(t-4)
    (196, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 196: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 196: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (197, 'u(t-17)', 'Practice step shift number 197: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 197: Step shift -> u(t-17)
    (198, 'u(t+18)', 'Practice advanced step number 198: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 198: Advanced step -> u(t+18)
    (199, 'r(t-19)', 'Practice ramp shift number 199: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 199: Ramp shift -> r(t-19)
    (200, 'r(t+0)', 'Practice advanced ramp number 200: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 200: Advanced ramp -> r(t+0)
    (201, '2*u(t)', 'Practice scaled step number 201: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 201: Scaled step -> 2*u(t)
    (202, '3*r(t)', 'Practice scaled ramp number 202: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 202: Scaled ramp -> 3*r(t)
    (203, 'delta(t-8)', 'Practice impulse shift number 203: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 203: Impulse shift -> delta(t-8)
    (204, 'delta(t-4)+delta(t+4)', 'Practice impulse pair number 204: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 204: Impulse pair -> delta(t-4)+delta(t+4)
    (205, 'u(t)-u(t-2)', 'Practice pulse number 205: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 205: Pulse -> u(t)-u(t-2)
    (206, 'u(t-6)-u(t-9)', 'Practice delayed pulse number 206: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 206: Delayed pulse -> u(t-6)-u(t-9)
    (207, 'r(t)-r(t-4)', 'Practice finite ramp number 207: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 207: Finite ramp -> r(t)-r(t-4)
    (208, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 208: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 208: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (209, 'sin(10*t)', 'Practice sine number 209: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 209: Sine -> sin(10*t)
    (210, 'cos(1*t)', 'Practice cosine number 210: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 210: Cosine -> cos(1*t)
    (211, 'exp(-0.5*t)*sin(2*t)*u(t)', 'Practice damped sine number 211: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 211: Damped sine -> exp(-0.5*t)*sin(2*t)*u(t)
    (212, 'exp(-0.6*t)*cos(2*t)*u(t)', 'Practice damped cosine number 212: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 212: Damped cosine -> exp(-0.6*t)*cos(2*t)*u(t)
    (213, 'rect(t/6)', 'Practice rectangle number 213: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 213: Rectangle -> rect(t/6)
    (214, 'tri(t/7)', 'Practice triangle pulse number 214: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 214: Triangle pulse -> tri(t/7)
    (215, 'sinc(8*t)', 'Practice sinc number 215: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 215: Sinc -> sinc(8*t)
    (216, 'sgn(t-0)', 'Practice sign number 216: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 216: Sign -> sgn(t-0)
    (217, 'abs(t-1)', 'Practice absolute value number 217: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 217: Absolute value -> abs(t-1)
    (218, '(t-2)**2', 'Practice parabola number 218: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 218: Parabola -> (t-2)**2
    (219, 'sin(4*t)*u(t)', 'Practice causal sine number 219: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 219: Causal sine -> sin(4*t)*u(t)
    (220, 'cos(5*t)*u(t)', 'Practice causal cosine number 220: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 220: Causal cosine -> cos(5*t)*u(t)
    (221, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 221: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 221: Ramp-step combination -> r(t)+5*u(t-5)
    (222, 'u(t)+u(t-2)+u(t-4)', 'Practice step staircase number 222: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 222: Step staircase -> u(t)+u(t-2)+u(t-4)
    (223, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 223: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 223: Odd impulse pair -> delta(t+2)-delta(t-2)
    (224, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 224: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 224: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (225, 'u(t-5)', 'Practice step shift number 225: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 225: Step shift -> u(t-5)
    (226, 'u(t+6)', 'Practice advanced step number 226: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 226: Advanced step -> u(t+6)
    (227, 'r(t-7)', 'Practice ramp shift number 227: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 227: Ramp shift -> r(t-7)
    (228, 'r(t+8)', 'Practice advanced ramp number 228: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 228: Advanced ramp -> r(t+8)
    (229, '10*u(t)', 'Practice scaled step number 229: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 229: Scaled step -> 10*u(t)
    (230, '1*r(t)', 'Practice scaled ramp number 230: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 230: Scaled ramp -> 1*r(t)
    (231, 'delta(t-6)', 'Practice impulse shift number 231: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 231: Impulse shift -> delta(t-6)
    (232, 'delta(t-2)+delta(t+2)', 'Practice impulse pair number 232: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 232: Impulse pair -> delta(t-2)+delta(t+2)
    (233, 'u(t)-u(t-6)', 'Practice pulse number 233: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 233: Pulse -> u(t)-u(t-6)
    (234, 'u(t-4)-u(t-7)', 'Practice delayed pulse number 234: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 234: Delayed pulse -> u(t-4)-u(t-7)
    (235, 'r(t)-r(t-8)', 'Practice finite ramp number 235: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 235: Finite ramp -> r(t)-r(t-8)
    (236, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 236: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 236: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (237, 'sin(8*t)', 'Practice sine number 237: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 237: Sine -> sin(8*t)
    (238, 'cos(9*t)', 'Practice cosine number 238: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 238: Cosine -> cos(9*t)
    (239, 'exp(-0.6*t)*sin(2*t)*u(t)', 'Practice damped sine number 239: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 239: Damped sine -> exp(-0.6*t)*sin(2*t)*u(t)
    (240, 'exp(-0.7*t)*cos(2*t)*u(t)', 'Practice damped cosine number 240: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 240: Damped cosine -> exp(-0.7*t)*cos(2*t)*u(t)
    (241, 'rect(t/2)', 'Practice rectangle number 241: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 241: Rectangle -> rect(t/2)
    (242, 'tri(t/3)', 'Practice triangle pulse number 242: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 242: Triangle pulse -> tri(t/3)
    (243, 'sinc(4*t)', 'Practice sinc number 243: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 243: Sinc -> sinc(4*t)
    (244, 'sgn(t-4)', 'Practice sign number 244: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 244: Sign -> sgn(t-4)
    (245, 'abs(t-5)', 'Practice absolute value number 245: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 245: Absolute value -> abs(t-5)
    (246, '(t-6)**2', 'Practice parabola number 246: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 246: Parabola -> (t-6)**2
    (247, 'sin(8*t)*u(t)', 'Practice causal sine number 247: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 247: Causal sine -> sin(8*t)*u(t)
    (248, 'cos(1*t)*u(t)', 'Practice causal cosine number 248: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 248: Causal cosine -> cos(1*t)*u(t)
    (249, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 249: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 249: Ramp-step combination -> r(t)+5*u(t-3)
    (250, 'u(t)+u(t-0)+u(t-2)', 'Practice step staircase number 250: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 250: Step staircase -> u(t)+u(t-0)+u(t-2)
    (251, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 251: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 251: Odd impulse pair -> delta(t+6)-delta(t-6)
    (252, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 252: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 252: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (253, 'u(t-13)', 'Practice step shift number 253: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 253: Step shift -> u(t-13)
    (254, 'u(t+14)', 'Practice advanced step number 254: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 254: Advanced step -> u(t+14)
    (255, 'r(t-15)', 'Practice ramp shift number 255: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 255: Ramp shift -> r(t-15)
    (256, 'r(t+16)', 'Practice advanced ramp number 256: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 256: Advanced ramp -> r(t+16)
    (257, '8*u(t)', 'Practice scaled step number 257: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 257: Scaled step -> 8*u(t)
    (258, '9*r(t)', 'Practice scaled ramp number 258: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 258: Scaled ramp -> 9*r(t)
    (259, 'delta(t-4)', 'Practice impulse shift number 259: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 259: Impulse shift -> delta(t-4)
    (260, 'delta(t-0)+delta(t+0)', 'Practice impulse pair number 260: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 260: Impulse pair -> delta(t-0)+delta(t+0)
    (261, 'u(t)-u(t-10)', 'Practice pulse number 261: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 261: Pulse -> u(t)-u(t-10)
    (262, 'u(t-2)-u(t-5)', 'Practice delayed pulse number 262: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 262: Delayed pulse -> u(t-2)-u(t-5)
    (263, 'r(t)-r(t-12)', 'Practice finite ramp number 263: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 263: Finite ramp -> r(t)-r(t-12)
    (264, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 264: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 264: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (265, 'sin(6*t)', 'Practice sine number 265: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 265: Sine -> sin(6*t)
    (266, 'cos(7*t)', 'Practice cosine number 266: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 266: Cosine -> cos(7*t)
    (267, 'exp(-0.7*t)*sin(2*t)*u(t)', 'Practice damped sine number 267: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 267: Damped sine -> exp(-0.7*t)*sin(2*t)*u(t)
    (268, 'exp(-0.8*t)*cos(2*t)*u(t)', 'Practice damped cosine number 268: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 268: Damped cosine -> exp(-0.8*t)*cos(2*t)*u(t)
    (269, 'rect(t/6)', 'Practice rectangle number 269: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 269: Rectangle -> rect(t/6)
    (270, 'tri(t/7)', 'Practice triangle pulse number 270: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 270: Triangle pulse -> tri(t/7)
    (271, 'sinc(8*t)', 'Practice sinc number 271: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 271: Sinc -> sinc(8*t)
    (272, 'sgn(t-0)', 'Practice sign number 272: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 272: Sign -> sgn(t-0)
    (273, 'abs(t-1)', 'Practice absolute value number 273: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 273: Absolute value -> abs(t-1)
    (274, '(t-2)**2', 'Practice parabola number 274: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 274: Parabola -> (t-2)**2
    (275, 'sin(4*t)*u(t)', 'Practice causal sine number 275: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 275: Causal sine -> sin(4*t)*u(t)
    (276, 'cos(5*t)*u(t)', 'Practice causal cosine number 276: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 276: Causal cosine -> cos(5*t)*u(t)
    (277, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 277: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 277: Ramp-step combination -> r(t)+5*u(t-1)
    (278, 'u(t)+u(t-3)+u(t-5)', 'Practice step staircase number 278: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 278: Step staircase -> u(t)+u(t-3)+u(t-5)
    (279, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 279: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 279: Odd impulse pair -> delta(t+4)-delta(t-4)
    (280, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 280: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 280: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (281, 'u(t-1)', 'Practice step shift number 281: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 281: Step shift -> u(t-1)
    (282, 'u(t+2)', 'Practice advanced step number 282: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 282: Advanced step -> u(t+2)
    (283, 'r(t-3)', 'Practice ramp shift number 283: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 283: Ramp shift -> r(t-3)
    (284, 'r(t+4)', 'Practice advanced ramp number 284: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 284: Advanced ramp -> r(t+4)
    (285, '6*u(t)', 'Practice scaled step number 285: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 285: Scaled step -> 6*u(t)
    (286, '7*r(t)', 'Practice scaled ramp number 286: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 286: Scaled ramp -> 7*r(t)
    (287, 'delta(t-2)', 'Practice impulse shift number 287: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 287: Impulse shift -> delta(t-2)
    (288, 'delta(t-8)+delta(t+8)', 'Practice impulse pair number 288: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 288: Impulse pair -> delta(t-8)+delta(t+8)
    (289, 'u(t)-u(t-2)', 'Practice pulse number 289: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 289: Pulse -> u(t)-u(t-2)
    (290, 'u(t-0)-u(t-3)', 'Practice delayed pulse number 290: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 290: Delayed pulse -> u(t-0)-u(t-3)
    (291, 'r(t)-r(t-4)', 'Practice finite ramp number 291: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 291: Finite ramp -> r(t)-r(t-4)
    (292, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 292: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 292: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (293, 'sin(4*t)', 'Practice sine number 293: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 293: Sine -> sin(4*t)
    (294, 'cos(5*t)', 'Practice cosine number 294: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 294: Cosine -> cos(5*t)
    (295, 'exp(-0.8*t)*sin(2*t)*u(t)', 'Practice damped sine number 295: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 295: Damped sine -> exp(-0.8*t)*sin(2*t)*u(t)
    (296, 'exp(-0.9*t)*cos(2*t)*u(t)', 'Practice damped cosine number 296: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 296: Damped cosine -> exp(-0.9*t)*cos(2*t)*u(t)
    (297, 'rect(t/2)', 'Practice rectangle number 297: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 297: Rectangle -> rect(t/2)
    (298, 'tri(t/3)', 'Practice triangle pulse number 298: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 298: Triangle pulse -> tri(t/3)
    (299, 'sinc(4*t)', 'Practice sinc number 299: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 299: Sinc -> sinc(4*t)
    (300, 'sgn(t-4)', 'Practice sign number 300: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 300: Sign -> sgn(t-4)
    (301, 'abs(t-5)', 'Practice absolute value number 301: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 301: Absolute value -> abs(t-5)
    (302, '(t-6)**2', 'Practice parabola number 302: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 302: Parabola -> (t-6)**2
    (303, 'sin(8*t)*u(t)', 'Practice causal sine number 303: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 303: Causal sine -> sin(8*t)*u(t)
    (304, 'cos(1*t)*u(t)', 'Practice causal cosine number 304: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 304: Causal cosine -> cos(1*t)*u(t)
    (305, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 305: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 305: Ramp-step combination -> r(t)+5*u(t-5)
    (306, 'u(t)+u(t-1)+u(t-3)', 'Practice step staircase number 306: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 306: Step staircase -> u(t)+u(t-1)+u(t-3)
    (307, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 307: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 307: Odd impulse pair -> delta(t+2)-delta(t-2)
    (308, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 308: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 308: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (309, 'u(t-9)', 'Practice step shift number 309: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 309: Step shift -> u(t-9)
    (310, 'u(t+10)', 'Practice advanced step number 310: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 310: Advanced step -> u(t+10)
    (311, 'r(t-11)', 'Practice ramp shift number 311: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 311: Ramp shift -> r(t-11)
    (312, 'r(t+12)', 'Practice advanced ramp number 312: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 312: Advanced ramp -> r(t+12)
    (313, '4*u(t)', 'Practice scaled step number 313: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 313: Scaled step -> 4*u(t)
    (314, '5*r(t)', 'Practice scaled ramp number 314: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 314: Scaled ramp -> 5*r(t)
    (315, 'delta(t-0)', 'Practice impulse shift number 315: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 315: Impulse shift -> delta(t-0)
    (316, 'delta(t-6)+delta(t+6)', 'Practice impulse pair number 316: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 316: Impulse pair -> delta(t-6)+delta(t+6)
    (317, 'u(t)-u(t-6)', 'Practice pulse number 317: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 317: Pulse -> u(t)-u(t-6)
    (318, 'u(t-8)-u(t-11)', 'Practice delayed pulse number 318: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 318: Delayed pulse -> u(t-8)-u(t-11)
    (319, 'r(t)-r(t-8)', 'Practice finite ramp number 319: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 319: Finite ramp -> r(t)-r(t-8)
    (320, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 320: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 320: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (321, 'sin(2*t)', 'Practice sine number 321: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 321: Sine -> sin(2*t)
    (322, 'cos(3*t)', 'Practice cosine number 322: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 322: Cosine -> cos(3*t)
    (323, 'exp(-0.9*t)*sin(2*t)*u(t)', 'Practice damped sine number 323: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 323: Damped sine -> exp(-0.9*t)*sin(2*t)*u(t)
    (324, 'exp(-0.1*t)*cos(2*t)*u(t)', 'Practice damped cosine number 324: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 324: Damped cosine -> exp(-0.1*t)*cos(2*t)*u(t)
    (325, 'rect(t/6)', 'Practice rectangle number 325: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 325: Rectangle -> rect(t/6)
    (326, 'tri(t/7)', 'Practice triangle pulse number 326: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 326: Triangle pulse -> tri(t/7)
    (327, 'sinc(8*t)', 'Practice sinc number 327: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 327: Sinc -> sinc(8*t)
    (328, 'sgn(t-0)', 'Practice sign number 328: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 328: Sign -> sgn(t-0)
    (329, 'abs(t-1)', 'Practice absolute value number 329: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 329: Absolute value -> abs(t-1)
    (330, '(t-2)**2', 'Practice parabola number 330: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 330: Parabola -> (t-2)**2
    (331, 'sin(4*t)*u(t)', 'Practice causal sine number 331: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 331: Causal sine -> sin(4*t)*u(t)
    (332, 'cos(5*t)*u(t)', 'Practice causal cosine number 332: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 332: Causal cosine -> cos(5*t)*u(t)
    (333, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 333: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 333: Ramp-step combination -> r(t)+5*u(t-3)
    (334, 'u(t)+u(t-4)+u(t-6)', 'Practice step staircase number 334: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 334: Step staircase -> u(t)+u(t-4)+u(t-6)
    (335, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 335: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 335: Odd impulse pair -> delta(t+6)-delta(t-6)
    (336, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 336: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 336: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (337, 'u(t-17)', 'Practice step shift number 337: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 337: Step shift -> u(t-17)
    (338, 'u(t+18)', 'Practice advanced step number 338: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 338: Advanced step -> u(t+18)
    (339, 'r(t-19)', 'Practice ramp shift number 339: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 339: Ramp shift -> r(t-19)
    (340, 'r(t+0)', 'Practice advanced ramp number 340: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 340: Advanced ramp -> r(t+0)
    (341, '2*u(t)', 'Practice scaled step number 341: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 341: Scaled step -> 2*u(t)
    (342, '3*r(t)', 'Practice scaled ramp number 342: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 342: Scaled ramp -> 3*r(t)
    (343, 'delta(t-13)', 'Practice impulse shift number 343: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 343: Impulse shift -> delta(t-13)
    (344, 'delta(t-4)+delta(t+4)', 'Practice impulse pair number 344: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 344: Impulse pair -> delta(t-4)+delta(t+4)
    (345, 'u(t)-u(t-10)', 'Practice pulse number 345: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 345: Pulse -> u(t)-u(t-10)
    (346, 'u(t-6)-u(t-9)', 'Practice delayed pulse number 346: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 346: Delayed pulse -> u(t-6)-u(t-9)
    (347, 'r(t)-r(t-12)', 'Practice finite ramp number 347: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 347: Finite ramp -> r(t)-r(t-12)
    (348, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 348: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 348: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (349, 'sin(10*t)', 'Practice sine number 349: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 349: Sine -> sin(10*t)
    (350, 'cos(1*t)', 'Practice cosine number 350: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 350: Cosine -> cos(1*t)
    (351, 'exp(-0.1*t)*sin(2*t)*u(t)', 'Practice damped sine number 351: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 351: Damped sine -> exp(-0.1*t)*sin(2*t)*u(t)
    (352, 'exp(-0.2*t)*cos(2*t)*u(t)', 'Practice damped cosine number 352: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 352: Damped cosine -> exp(-0.2*t)*cos(2*t)*u(t)
    (353, 'rect(t/2)', 'Practice rectangle number 353: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 353: Rectangle -> rect(t/2)
    (354, 'tri(t/3)', 'Practice triangle pulse number 354: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 354: Triangle pulse -> tri(t/3)
    (355, 'sinc(4*t)', 'Practice sinc number 355: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 355: Sinc -> sinc(4*t)
    (356, 'sgn(t-4)', 'Practice sign number 356: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 356: Sign -> sgn(t-4)
    (357, 'abs(t-5)', 'Practice absolute value number 357: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 357: Absolute value -> abs(t-5)
    (358, '(t-6)**2', 'Practice parabola number 358: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 358: Parabola -> (t-6)**2
    (359, 'sin(8*t)*u(t)', 'Practice causal sine number 359: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 359: Causal sine -> sin(8*t)*u(t)
    (360, 'cos(1*t)*u(t)', 'Practice causal cosine number 360: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 360: Causal cosine -> cos(1*t)*u(t)
    (361, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 361: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 361: Ramp-step combination -> r(t)+5*u(t-1)
    (362, 'u(t)+u(t-2)+u(t-4)', 'Practice step staircase number 362: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 362: Step staircase -> u(t)+u(t-2)+u(t-4)
    (363, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 363: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 363: Odd impulse pair -> delta(t+4)-delta(t-4)
    (364, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 364: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 364: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (365, 'u(t-5)', 'Practice step shift number 365: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 365: Step shift -> u(t-5)
    (366, 'u(t+6)', 'Practice advanced step number 366: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 366: Advanced step -> u(t+6)
    (367, 'r(t-7)', 'Practice ramp shift number 367: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 367: Ramp shift -> r(t-7)
    (368, 'r(t+8)', 'Practice advanced ramp number 368: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 368: Advanced ramp -> r(t+8)
    (369, '10*u(t)', 'Practice scaled step number 369: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 369: Scaled step -> 10*u(t)
    (370, '1*r(t)', 'Practice scaled ramp number 370: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 370: Scaled ramp -> 1*r(t)
    (371, 'delta(t-11)', 'Practice impulse shift number 371: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 371: Impulse shift -> delta(t-11)
    (372, 'delta(t-2)+delta(t+2)', 'Practice impulse pair number 372: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 372: Impulse pair -> delta(t-2)+delta(t+2)
    (373, 'u(t)-u(t-2)', 'Practice pulse number 373: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 373: Pulse -> u(t)-u(t-2)
    (374, 'u(t-4)-u(t-7)', 'Practice delayed pulse number 374: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 374: Delayed pulse -> u(t-4)-u(t-7)
    (375, 'r(t)-r(t-4)', 'Practice finite ramp number 375: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 375: Finite ramp -> r(t)-r(t-4)
    (376, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 376: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 376: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (377, 'sin(8*t)', 'Practice sine number 377: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 377: Sine -> sin(8*t)
    (378, 'cos(9*t)', 'Practice cosine number 378: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 378: Cosine -> cos(9*t)
    (379, 'exp(-0.2*t)*sin(2*t)*u(t)', 'Practice damped sine number 379: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 379: Damped sine -> exp(-0.2*t)*sin(2*t)*u(t)
    (380, 'exp(-0.3*t)*cos(2*t)*u(t)', 'Practice damped cosine number 380: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 380: Damped cosine -> exp(-0.3*t)*cos(2*t)*u(t)
    (381, 'rect(t/6)', 'Practice rectangle number 381: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 381: Rectangle -> rect(t/6)
    (382, 'tri(t/7)', 'Practice triangle pulse number 382: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 382: Triangle pulse -> tri(t/7)
    (383, 'sinc(8*t)', 'Practice sinc number 383: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 383: Sinc -> sinc(8*t)
    (384, 'sgn(t-0)', 'Practice sign number 384: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 384: Sign -> sgn(t-0)
    (385, 'abs(t-1)', 'Practice absolute value number 385: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 385: Absolute value -> abs(t-1)
    (386, '(t-2)**2', 'Practice parabola number 386: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 386: Parabola -> (t-2)**2
    (387, 'sin(4*t)*u(t)', 'Practice causal sine number 387: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 387: Causal sine -> sin(4*t)*u(t)
    (388, 'cos(5*t)*u(t)', 'Practice causal cosine number 388: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 388: Causal cosine -> cos(5*t)*u(t)
    (389, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 389: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 389: Ramp-step combination -> r(t)+5*u(t-5)
    (390, 'u(t)+u(t-0)+u(t-2)', 'Practice step staircase number 390: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 390: Step staircase -> u(t)+u(t-0)+u(t-2)
    (391, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 391: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 391: Odd impulse pair -> delta(t+2)-delta(t-2)
    (392, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 392: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 392: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (393, 'u(t-13)', 'Practice step shift number 393: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 393: Step shift -> u(t-13)
    (394, 'u(t+14)', 'Practice advanced step number 394: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 394: Advanced step -> u(t+14)
    (395, 'r(t-15)', 'Practice ramp shift number 395: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 395: Ramp shift -> r(t-15)
    (396, 'r(t+16)', 'Practice advanced ramp number 396: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 396: Advanced ramp -> r(t+16)
    (397, '8*u(t)', 'Practice scaled step number 397: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 397: Scaled step -> 8*u(t)
    (398, '9*r(t)', 'Practice scaled ramp number 398: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 398: Scaled ramp -> 9*r(t)
    (399, 'delta(t-9)', 'Practice impulse shift number 399: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 399: Impulse shift -> delta(t-9)
    (400, 'delta(t-0)+delta(t+0)', 'Practice impulse pair number 400: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 400: Impulse pair -> delta(t-0)+delta(t+0)
    (401, 'u(t)-u(t-6)', 'Practice pulse number 401: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 401: Pulse -> u(t)-u(t-6)
    (402, 'u(t-2)-u(t-5)', 'Practice delayed pulse number 402: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 402: Delayed pulse -> u(t-2)-u(t-5)
    (403, 'r(t)-r(t-8)', 'Practice finite ramp number 403: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 403: Finite ramp -> r(t)-r(t-8)
    (404, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 404: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 404: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (405, 'sin(6*t)', 'Practice sine number 405: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 405: Sine -> sin(6*t)
    (406, 'cos(7*t)', 'Practice cosine number 406: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 406: Cosine -> cos(7*t)
    (407, 'exp(-0.3*t)*sin(2*t)*u(t)', 'Practice damped sine number 407: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 407: Damped sine -> exp(-0.3*t)*sin(2*t)*u(t)
    (408, 'exp(-0.4*t)*cos(2*t)*u(t)', 'Practice damped cosine number 408: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 408: Damped cosine -> exp(-0.4*t)*cos(2*t)*u(t)
    (409, 'rect(t/2)', 'Practice rectangle number 409: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 409: Rectangle -> rect(t/2)
    (410, 'tri(t/3)', 'Practice triangle pulse number 410: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 410: Triangle pulse -> tri(t/3)
    (411, 'sinc(4*t)', 'Practice sinc number 411: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 411: Sinc -> sinc(4*t)
    (412, 'sgn(t-4)', 'Practice sign number 412: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 412: Sign -> sgn(t-4)
    (413, 'abs(t-5)', 'Practice absolute value number 413: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 413: Absolute value -> abs(t-5)
    (414, '(t-6)**2', 'Practice parabola number 414: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 414: Parabola -> (t-6)**2
    (415, 'sin(8*t)*u(t)', 'Practice causal sine number 415: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 415: Causal sine -> sin(8*t)*u(t)
    (416, 'cos(1*t)*u(t)', 'Practice causal cosine number 416: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 416: Causal cosine -> cos(1*t)*u(t)
    (417, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 417: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 417: Ramp-step combination -> r(t)+5*u(t-3)
    (418, 'u(t)+u(t-3)+u(t-5)', 'Practice step staircase number 418: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 418: Step staircase -> u(t)+u(t-3)+u(t-5)
    (419, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 419: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 419: Odd impulse pair -> delta(t+6)-delta(t-6)
    (420, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 420: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 420: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (421, 'u(t-1)', 'Practice step shift number 421: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 421: Step shift -> u(t-1)
    (422, 'u(t+2)', 'Practice advanced step number 422: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 422: Advanced step -> u(t+2)
    (423, 'r(t-3)', 'Practice ramp shift number 423: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 423: Ramp shift -> r(t-3)
    (424, 'r(t+4)', 'Practice advanced ramp number 424: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 424: Advanced ramp -> r(t+4)
    (425, '6*u(t)', 'Practice scaled step number 425: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 425: Scaled step -> 6*u(t)
    (426, '7*r(t)', 'Practice scaled ramp number 426: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 426: Scaled ramp -> 7*r(t)
    (427, 'delta(t-7)', 'Practice impulse shift number 427: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 427: Impulse shift -> delta(t-7)
    (428, 'delta(t-8)+delta(t+8)', 'Practice impulse pair number 428: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 428: Impulse pair -> delta(t-8)+delta(t+8)
    (429, 'u(t)-u(t-10)', 'Practice pulse number 429: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 429: Pulse -> u(t)-u(t-10)
    (430, 'u(t-0)-u(t-3)', 'Practice delayed pulse number 430: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 430: Delayed pulse -> u(t-0)-u(t-3)
    (431, 'r(t)-r(t-12)', 'Practice finite ramp number 431: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 431: Finite ramp -> r(t)-r(t-12)
    (432, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 432: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 432: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (433, 'sin(4*t)', 'Practice sine number 433: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 433: Sine -> sin(4*t)
    (434, 'cos(5*t)', 'Practice cosine number 434: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 434: Cosine -> cos(5*t)
    (435, 'exp(-0.4*t)*sin(2*t)*u(t)', 'Practice damped sine number 435: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 435: Damped sine -> exp(-0.4*t)*sin(2*t)*u(t)
    (436, 'exp(-0.5*t)*cos(2*t)*u(t)', 'Practice damped cosine number 436: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 436: Damped cosine -> exp(-0.5*t)*cos(2*t)*u(t)
    (437, 'rect(t/6)', 'Practice rectangle number 437: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 437: Rectangle -> rect(t/6)
    (438, 'tri(t/7)', 'Practice triangle pulse number 438: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 438: Triangle pulse -> tri(t/7)
    (439, 'sinc(8*t)', 'Practice sinc number 439: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 439: Sinc -> sinc(8*t)
    (440, 'sgn(t-0)', 'Practice sign number 440: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 440: Sign -> sgn(t-0)
    (441, 'abs(t-1)', 'Practice absolute value number 441: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 441: Absolute value -> abs(t-1)
    (442, '(t-2)**2', 'Practice parabola number 442: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 442: Parabola -> (t-2)**2
    (443, 'sin(4*t)*u(t)', 'Practice causal sine number 443: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 443: Causal sine -> sin(4*t)*u(t)
    (444, 'cos(5*t)*u(t)', 'Practice causal cosine number 444: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 444: Causal cosine -> cos(5*t)*u(t)
    (445, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 445: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 445: Ramp-step combination -> r(t)+5*u(t-1)
    (446, 'u(t)+u(t-1)+u(t-3)', 'Practice step staircase number 446: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 446: Step staircase -> u(t)+u(t-1)+u(t-3)
    (447, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 447: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 447: Odd impulse pair -> delta(t+4)-delta(t-4)
    (448, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 448: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 448: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (449, 'u(t-9)', 'Practice step shift number 449: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 449: Step shift -> u(t-9)
    (450, 'u(t+10)', 'Practice advanced step number 450: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 450: Advanced step -> u(t+10)
    (451, 'r(t-11)', 'Practice ramp shift number 451: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 451: Ramp shift -> r(t-11)
    (452, 'r(t+12)', 'Practice advanced ramp number 452: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 452: Advanced ramp -> r(t+12)
    (453, '4*u(t)', 'Practice scaled step number 453: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 453: Scaled step -> 4*u(t)
    (454, '5*r(t)', 'Practice scaled ramp number 454: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 454: Scaled ramp -> 5*r(t)
    (455, 'delta(t-5)', 'Practice impulse shift number 455: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 455: Impulse shift -> delta(t-5)
    (456, 'delta(t-6)+delta(t+6)', 'Practice impulse pair number 456: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 456: Impulse pair -> delta(t-6)+delta(t+6)
    (457, 'u(t)-u(t-2)', 'Practice pulse number 457: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 457: Pulse -> u(t)-u(t-2)
    (458, 'u(t-8)-u(t-11)', 'Practice delayed pulse number 458: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 458: Delayed pulse -> u(t-8)-u(t-11)
    (459, 'r(t)-r(t-4)', 'Practice finite ramp number 459: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 459: Finite ramp -> r(t)-r(t-4)
    (460, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 460: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 460: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (461, 'sin(2*t)', 'Practice sine number 461: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 461: Sine -> sin(2*t)
    (462, 'cos(3*t)', 'Practice cosine number 462: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 462: Cosine -> cos(3*t)
    (463, 'exp(-0.5*t)*sin(2*t)*u(t)', 'Practice damped sine number 463: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 463: Damped sine -> exp(-0.5*t)*sin(2*t)*u(t)
    (464, 'exp(-0.6*t)*cos(2*t)*u(t)', 'Practice damped cosine number 464: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 464: Damped cosine -> exp(-0.6*t)*cos(2*t)*u(t)
    (465, 'rect(t/2)', 'Practice rectangle number 465: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 465: Rectangle -> rect(t/2)
    (466, 'tri(t/3)', 'Practice triangle pulse number 466: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 466: Triangle pulse -> tri(t/3)
    (467, 'sinc(4*t)', 'Practice sinc number 467: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 467: Sinc -> sinc(4*t)
    (468, 'sgn(t-4)', 'Practice sign number 468: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 468: Sign -> sgn(t-4)
    (469, 'abs(t-5)', 'Practice absolute value number 469: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 469: Absolute value -> abs(t-5)
    (470, '(t-6)**2', 'Practice parabola number 470: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 470: Parabola -> (t-6)**2
    (471, 'sin(8*t)*u(t)', 'Practice causal sine number 471: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 471: Causal sine -> sin(8*t)*u(t)
    (472, 'cos(1*t)*u(t)', 'Practice causal cosine number 472: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 472: Causal cosine -> cos(1*t)*u(t)
    (473, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 473: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 473: Ramp-step combination -> r(t)+5*u(t-5)
    (474, 'u(t)+u(t-4)+u(t-6)', 'Practice step staircase number 474: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 474: Step staircase -> u(t)+u(t-4)+u(t-6)
    (475, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 475: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 475: Odd impulse pair -> delta(t+2)-delta(t-2)
    (476, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 476: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 476: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (477, 'u(t-17)', 'Practice step shift number 477: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 477: Step shift -> u(t-17)
    (478, 'u(t+18)', 'Practice advanced step number 478: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 478: Advanced step -> u(t+18)
    (479, 'r(t-19)', 'Practice ramp shift number 479: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 479: Ramp shift -> r(t-19)
    (480, 'r(t+0)', 'Practice advanced ramp number 480: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 480: Advanced ramp -> r(t+0)
    (481, '2*u(t)', 'Practice scaled step number 481: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 481: Scaled step -> 2*u(t)
    (482, '3*r(t)', 'Practice scaled ramp number 482: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 482: Scaled ramp -> 3*r(t)
    (483, 'delta(t-3)', 'Practice impulse shift number 483: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 483: Impulse shift -> delta(t-3)
    (484, 'delta(t-4)+delta(t+4)', 'Practice impulse pair number 484: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 484: Impulse pair -> delta(t-4)+delta(t+4)
    (485, 'u(t)-u(t-6)', 'Practice pulse number 485: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 485: Pulse -> u(t)-u(t-6)
    (486, 'u(t-6)-u(t-9)', 'Practice delayed pulse number 486: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 486: Delayed pulse -> u(t-6)-u(t-9)
    (487, 'r(t)-r(t-8)', 'Practice finite ramp number 487: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 487: Finite ramp -> r(t)-r(t-8)
    (488, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 488: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 488: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (489, 'sin(10*t)', 'Practice sine number 489: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 489: Sine -> sin(10*t)
    (490, 'cos(1*t)', 'Practice cosine number 490: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 490: Cosine -> cos(1*t)
    (491, 'exp(-0.6*t)*sin(2*t)*u(t)', 'Practice damped sine number 491: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 491: Damped sine -> exp(-0.6*t)*sin(2*t)*u(t)
    (492, 'exp(-0.7*t)*cos(2*t)*u(t)', 'Practice damped cosine number 492: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 492: Damped cosine -> exp(-0.7*t)*cos(2*t)*u(t)
    (493, 'rect(t/6)', 'Practice rectangle number 493: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 493: Rectangle -> rect(t/6)
    (494, 'tri(t/7)', 'Practice triangle pulse number 494: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 494: Triangle pulse -> tri(t/7)
    (495, 'sinc(8*t)', 'Practice sinc number 495: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 495: Sinc -> sinc(8*t)
    (496, 'sgn(t-0)', 'Practice sign number 496: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 496: Sign -> sgn(t-0)
    (497, 'abs(t-1)', 'Practice absolute value number 497: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 497: Absolute value -> abs(t-1)
    (498, '(t-2)**2', 'Practice parabola number 498: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 498: Parabola -> (t-2)**2
    (499, 'sin(4*t)*u(t)', 'Practice causal sine number 499: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 499: Causal sine -> sin(4*t)*u(t)
    (500, 'cos(5*t)*u(t)', 'Practice causal cosine number 500: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 500: Causal cosine -> cos(5*t)*u(t)
    (501, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 501: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 501: Ramp-step combination -> r(t)+5*u(t-3)
    (502, 'u(t)+u(t-2)+u(t-4)', 'Practice step staircase number 502: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 502: Step staircase -> u(t)+u(t-2)+u(t-4)
    (503, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 503: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 503: Odd impulse pair -> delta(t+6)-delta(t-6)
    (504, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 504: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 504: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (505, 'u(t-5)', 'Practice step shift number 505: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 505: Step shift -> u(t-5)
    (506, 'u(t+6)', 'Practice advanced step number 506: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 506: Advanced step -> u(t+6)
    (507, 'r(t-7)', 'Practice ramp shift number 507: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 507: Ramp shift -> r(t-7)
    (508, 'r(t+8)', 'Practice advanced ramp number 508: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 508: Advanced ramp -> r(t+8)
    (509, '10*u(t)', 'Practice scaled step number 509: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 509: Scaled step -> 10*u(t)
    (510, '1*r(t)', 'Practice scaled ramp number 510: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 510: Scaled ramp -> 1*r(t)
    (511, 'delta(t-1)', 'Practice impulse shift number 511: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 511: Impulse shift -> delta(t-1)
    (512, 'delta(t-2)+delta(t+2)', 'Practice impulse pair number 512: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 512: Impulse pair -> delta(t-2)+delta(t+2)
    (513, 'u(t)-u(t-10)', 'Practice pulse number 513: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 513: Pulse -> u(t)-u(t-10)
    (514, 'u(t-4)-u(t-7)', 'Practice delayed pulse number 514: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 514: Delayed pulse -> u(t-4)-u(t-7)
    (515, 'r(t)-r(t-12)', 'Practice finite ramp number 515: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 515: Finite ramp -> r(t)-r(t-12)
    (516, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 516: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 516: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (517, 'sin(8*t)', 'Practice sine number 517: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 517: Sine -> sin(8*t)
    (518, 'cos(9*t)', 'Practice cosine number 518: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 518: Cosine -> cos(9*t)
    (519, 'exp(-0.7*t)*sin(2*t)*u(t)', 'Practice damped sine number 519: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 519: Damped sine -> exp(-0.7*t)*sin(2*t)*u(t)
    (520, 'exp(-0.8*t)*cos(2*t)*u(t)', 'Practice damped cosine number 520: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 520: Damped cosine -> exp(-0.8*t)*cos(2*t)*u(t)
    (521, 'rect(t/2)', 'Practice rectangle number 521: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 521: Rectangle -> rect(t/2)
    (522, 'tri(t/3)', 'Practice triangle pulse number 522: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 522: Triangle pulse -> tri(t/3)
    (523, 'sinc(4*t)', 'Practice sinc number 523: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 523: Sinc -> sinc(4*t)
    (524, 'sgn(t-4)', 'Practice sign number 524: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 524: Sign -> sgn(t-4)
    (525, 'abs(t-5)', 'Practice absolute value number 525: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 525: Absolute value -> abs(t-5)
    (526, '(t-6)**2', 'Practice parabola number 526: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 526: Parabola -> (t-6)**2
    (527, 'sin(8*t)*u(t)', 'Practice causal sine number 527: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 527: Causal sine -> sin(8*t)*u(t)
    (528, 'cos(1*t)*u(t)', 'Practice causal cosine number 528: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 528: Causal cosine -> cos(1*t)*u(t)
    (529, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 529: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 529: Ramp-step combination -> r(t)+5*u(t-1)
    (530, 'u(t)+u(t-0)+u(t-2)', 'Practice step staircase number 530: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 530: Step staircase -> u(t)+u(t-0)+u(t-2)
    (531, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 531: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 531: Odd impulse pair -> delta(t+4)-delta(t-4)
    (532, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 532: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 532: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (533, 'u(t-13)', 'Practice step shift number 533: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 533: Step shift -> u(t-13)
    (534, 'u(t+14)', 'Practice advanced step number 534: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 534: Advanced step -> u(t+14)
    (535, 'r(t-15)', 'Practice ramp shift number 535: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 535: Ramp shift -> r(t-15)
    (536, 'r(t+16)', 'Practice advanced ramp number 536: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 536: Advanced ramp -> r(t+16)
    (537, '8*u(t)', 'Practice scaled step number 537: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 537: Scaled step -> 8*u(t)
    (538, '9*r(t)', 'Practice scaled ramp number 538: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 538: Scaled ramp -> 9*r(t)
    (539, 'delta(t-14)', 'Practice impulse shift number 539: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 539: Impulse shift -> delta(t-14)
    (540, 'delta(t-0)+delta(t+0)', 'Practice impulse pair number 540: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 540: Impulse pair -> delta(t-0)+delta(t+0)
    (541, 'u(t)-u(t-2)', 'Practice pulse number 541: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 541: Pulse -> u(t)-u(t-2)
    (542, 'u(t-2)-u(t-5)', 'Practice delayed pulse number 542: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 542: Delayed pulse -> u(t-2)-u(t-5)
    (543, 'r(t)-r(t-4)', 'Practice finite ramp number 543: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 543: Finite ramp -> r(t)-r(t-4)
    (544, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 544: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 544: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (545, 'sin(6*t)', 'Practice sine number 545: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 545: Sine -> sin(6*t)
    (546, 'cos(7*t)', 'Practice cosine number 546: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 546: Cosine -> cos(7*t)
    (547, 'exp(-0.8*t)*sin(2*t)*u(t)', 'Practice damped sine number 547: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 547: Damped sine -> exp(-0.8*t)*sin(2*t)*u(t)
    (548, 'exp(-0.9*t)*cos(2*t)*u(t)', 'Practice damped cosine number 548: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 548: Damped cosine -> exp(-0.9*t)*cos(2*t)*u(t)
    (549, 'rect(t/6)', 'Practice rectangle number 549: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 549: Rectangle -> rect(t/6)
    (550, 'tri(t/7)', 'Practice triangle pulse number 550: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 550: Triangle pulse -> tri(t/7)
    (551, 'sinc(8*t)', 'Practice sinc number 551: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 551: Sinc -> sinc(8*t)
    (552, 'sgn(t-0)', 'Practice sign number 552: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 552: Sign -> sgn(t-0)
    (553, 'abs(t-1)', 'Practice absolute value number 553: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 553: Absolute value -> abs(t-1)
    (554, '(t-2)**2', 'Practice parabola number 554: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 554: Parabola -> (t-2)**2
    (555, 'sin(4*t)*u(t)', 'Practice causal sine number 555: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 555: Causal sine -> sin(4*t)*u(t)
    (556, 'cos(5*t)*u(t)', 'Practice causal cosine number 556: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 556: Causal cosine -> cos(5*t)*u(t)
    (557, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 557: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 557: Ramp-step combination -> r(t)+5*u(t-5)
    (558, 'u(t)+u(t-3)+u(t-5)', 'Practice step staircase number 558: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 558: Step staircase -> u(t)+u(t-3)+u(t-5)
    (559, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 559: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 559: Odd impulse pair -> delta(t+2)-delta(t-2)
    (560, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 560: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 560: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (561, 'u(t-1)', 'Practice step shift number 561: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 561: Step shift -> u(t-1)
    (562, 'u(t+2)', 'Practice advanced step number 562: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 562: Advanced step -> u(t+2)
    (563, 'r(t-3)', 'Practice ramp shift number 563: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 563: Ramp shift -> r(t-3)
    (564, 'r(t+4)', 'Practice advanced ramp number 564: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 564: Advanced ramp -> r(t+4)
    (565, '6*u(t)', 'Practice scaled step number 565: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 565: Scaled step -> 6*u(t)
    (566, '7*r(t)', 'Practice scaled ramp number 566: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 566: Scaled ramp -> 7*r(t)
    (567, 'delta(t-12)', 'Practice impulse shift number 567: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 567: Impulse shift -> delta(t-12)
    (568, 'delta(t-8)+delta(t+8)', 'Practice impulse pair number 568: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 568: Impulse pair -> delta(t-8)+delta(t+8)
    (569, 'u(t)-u(t-6)', 'Practice pulse number 569: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 569: Pulse -> u(t)-u(t-6)
    (570, 'u(t-0)-u(t-3)', 'Practice delayed pulse number 570: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 570: Delayed pulse -> u(t-0)-u(t-3)
    (571, 'r(t)-r(t-8)', 'Practice finite ramp number 571: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 571: Finite ramp -> r(t)-r(t-8)
    (572, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 572: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 572: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (573, 'sin(4*t)', 'Practice sine number 573: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 573: Sine -> sin(4*t)
    (574, 'cos(5*t)', 'Practice cosine number 574: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 574: Cosine -> cos(5*t)
    (575, 'exp(-0.9*t)*sin(2*t)*u(t)', 'Practice damped sine number 575: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 575: Damped sine -> exp(-0.9*t)*sin(2*t)*u(t)
    (576, 'exp(-0.1*t)*cos(2*t)*u(t)', 'Practice damped cosine number 576: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 576: Damped cosine -> exp(-0.1*t)*cos(2*t)*u(t)
    (577, 'rect(t/2)', 'Practice rectangle number 577: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 577: Rectangle -> rect(t/2)
    (578, 'tri(t/3)', 'Practice triangle pulse number 578: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 578: Triangle pulse -> tri(t/3)
    (579, 'sinc(4*t)', 'Practice sinc number 579: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 579: Sinc -> sinc(4*t)
    (580, 'sgn(t-4)', 'Practice sign number 580: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 580: Sign -> sgn(t-4)
    (581, 'abs(t-5)', 'Practice absolute value number 581: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 581: Absolute value -> abs(t-5)
    (582, '(t-6)**2', 'Practice parabola number 582: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 582: Parabola -> (t-6)**2
    (583, 'sin(8*t)*u(t)', 'Practice causal sine number 583: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 583: Causal sine -> sin(8*t)*u(t)
    (584, 'cos(1*t)*u(t)', 'Practice causal cosine number 584: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 584: Causal cosine -> cos(1*t)*u(t)
    (585, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 585: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 585: Ramp-step combination -> r(t)+5*u(t-3)
    (586, 'u(t)+u(t-1)+u(t-3)', 'Practice step staircase number 586: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 586: Step staircase -> u(t)+u(t-1)+u(t-3)
    (587, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 587: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 587: Odd impulse pair -> delta(t+6)-delta(t-6)
    (588, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 588: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 588: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (589, 'u(t-9)', 'Practice step shift number 589: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 589: Step shift -> u(t-9)
    (590, 'u(t+10)', 'Practice advanced step number 590: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 590: Advanced step -> u(t+10)
    (591, 'r(t-11)', 'Practice ramp shift number 591: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 591: Ramp shift -> r(t-11)
    (592, 'r(t+12)', 'Practice advanced ramp number 592: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 592: Advanced ramp -> r(t+12)
    (593, '4*u(t)', 'Practice scaled step number 593: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 593: Scaled step -> 4*u(t)
    (594, '5*r(t)', 'Practice scaled ramp number 594: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 594: Scaled ramp -> 5*r(t)
    (595, 'delta(t-10)', 'Practice impulse shift number 595: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 595: Impulse shift -> delta(t-10)
    (596, 'delta(t-6)+delta(t+6)', 'Practice impulse pair number 596: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 596: Impulse pair -> delta(t-6)+delta(t+6)
    (597, 'u(t)-u(t-10)', 'Practice pulse number 597: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 597: Pulse -> u(t)-u(t-10)
    (598, 'u(t-8)-u(t-11)', 'Practice delayed pulse number 598: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 598: Delayed pulse -> u(t-8)-u(t-11)
    (599, 'r(t)-r(t-12)', 'Practice finite ramp number 599: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 599: Finite ramp -> r(t)-r(t-12)
    (600, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 600: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 600: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (601, 'sin(2*t)', 'Practice sine number 601: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 601: Sine -> sin(2*t)
    (602, 'cos(3*t)', 'Practice cosine number 602: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 602: Cosine -> cos(3*t)
    (603, 'exp(-0.1*t)*sin(2*t)*u(t)', 'Practice damped sine number 603: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 603: Damped sine -> exp(-0.1*t)*sin(2*t)*u(t)
    (604, 'exp(-0.2*t)*cos(2*t)*u(t)', 'Practice damped cosine number 604: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 604: Damped cosine -> exp(-0.2*t)*cos(2*t)*u(t)
    (605, 'rect(t/6)', 'Practice rectangle number 605: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 605: Rectangle -> rect(t/6)
    (606, 'tri(t/7)', 'Practice triangle pulse number 606: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 606: Triangle pulse -> tri(t/7)
    (607, 'sinc(8*t)', 'Practice sinc number 607: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 607: Sinc -> sinc(8*t)
    (608, 'sgn(t-0)', 'Practice sign number 608: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 608: Sign -> sgn(t-0)
    (609, 'abs(t-1)', 'Practice absolute value number 609: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 609: Absolute value -> abs(t-1)
    (610, '(t-2)**2', 'Practice parabola number 610: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 610: Parabola -> (t-2)**2
    (611, 'sin(4*t)*u(t)', 'Practice causal sine number 611: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 611: Causal sine -> sin(4*t)*u(t)
    (612, 'cos(5*t)*u(t)', 'Practice causal cosine number 612: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 612: Causal cosine -> cos(5*t)*u(t)
    (613, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 613: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 613: Ramp-step combination -> r(t)+5*u(t-1)
    (614, 'u(t)+u(t-4)+u(t-6)', 'Practice step staircase number 614: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 614: Step staircase -> u(t)+u(t-4)+u(t-6)
    (615, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 615: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 615: Odd impulse pair -> delta(t+4)-delta(t-4)
    (616, 'r(t)-r(t-5)+u(t-0)', 'Practice mixed waveform number 616: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 616: Mixed waveform -> r(t)-r(t-5)+u(t-0)
    (617, 'u(t-17)', 'Practice step shift number 617: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 617: Step shift -> u(t-17)
    (618, 'u(t+18)', 'Practice advanced step number 618: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 618: Advanced step -> u(t+18)
    (619, 'r(t-19)', 'Practice ramp shift number 619: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 619: Ramp shift -> r(t-19)
    (620, 'r(t+0)', 'Practice advanced ramp number 620: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 620: Advanced ramp -> r(t+0)
    (621, '2*u(t)', 'Practice scaled step number 621: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 621: Scaled step -> 2*u(t)
    (622, '3*r(t)', 'Practice scaled ramp number 622: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 622: Scaled ramp -> 3*r(t)
    (623, 'delta(t-8)', 'Practice impulse shift number 623: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 623: Impulse shift -> delta(t-8)
    (624, 'delta(t-4)+delta(t+4)', 'Practice impulse pair number 624: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 624: Impulse pair -> delta(t-4)+delta(t+4)
    (625, 'u(t)-u(t-2)', 'Practice pulse number 625: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 625: Pulse -> u(t)-u(t-2)
    (626, 'u(t-6)-u(t-9)', 'Practice delayed pulse number 626: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 626: Delayed pulse -> u(t-6)-u(t-9)
    (627, 'r(t)-r(t-4)', 'Practice finite ramp number 627: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 627: Finite ramp -> r(t)-r(t-4)
    (628, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 628: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 628: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (629, 'sin(10*t)', 'Practice sine number 629: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 629: Sine -> sin(10*t)
    (630, 'cos(1*t)', 'Practice cosine number 630: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 630: Cosine -> cos(1*t)
    (631, 'exp(-0.2*t)*sin(2*t)*u(t)', 'Practice damped sine number 631: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 631: Damped sine -> exp(-0.2*t)*sin(2*t)*u(t)
    (632, 'exp(-0.3*t)*cos(2*t)*u(t)', 'Practice damped cosine number 632: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 632: Damped cosine -> exp(-0.3*t)*cos(2*t)*u(t)
    (633, 'rect(t/2)', 'Practice rectangle number 633: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 633: Rectangle -> rect(t/2)
    (634, 'tri(t/3)', 'Practice triangle pulse number 634: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 634: Triangle pulse -> tri(t/3)
    (635, 'sinc(4*t)', 'Practice sinc number 635: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 635: Sinc -> sinc(4*t)
    (636, 'sgn(t-4)', 'Practice sign number 636: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 636: Sign -> sgn(t-4)
    (637, 'abs(t-5)', 'Practice absolute value number 637: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 637: Absolute value -> abs(t-5)
    (638, '(t-6)**2', 'Practice parabola number 638: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 638: Parabola -> (t-6)**2
    (639, 'sin(8*t)*u(t)', 'Practice causal sine number 639: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 639: Causal sine -> sin(8*t)*u(t)
    (640, 'cos(1*t)*u(t)', 'Practice causal cosine number 640: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 640: Causal cosine -> cos(1*t)*u(t)
    (641, 'r(t)+5*u(t-5)', 'Practice ramp-step combination number 641: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 641: Ramp-step combination -> r(t)+5*u(t-5)
    (642, 'u(t)+u(t-2)+u(t-4)', 'Practice step staircase number 642: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 642: Step staircase -> u(t)+u(t-2)+u(t-4)
    (643, 'delta(t+2)-delta(t-2)', 'Practice odd impulse pair number 643: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 643: Odd impulse pair -> delta(t+2)-delta(t-2)
    (644, 'r(t)-r(t-3)+u(t-0)', 'Practice mixed waveform number 644: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 644: Mixed waveform -> r(t)-r(t-3)+u(t-0)
    (645, 'u(t-5)', 'Practice step shift number 645: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 645: Step shift -> u(t-5)
    (646, 'u(t+6)', 'Practice advanced step number 646: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 646: Advanced step -> u(t+6)
    (647, 'r(t-7)', 'Practice ramp shift number 647: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 647: Ramp shift -> r(t-7)
    (648, 'r(t+8)', 'Practice advanced ramp number 648: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 648: Advanced ramp -> r(t+8)
    (649, '10*u(t)', 'Practice scaled step number 649: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 649: Scaled step -> 10*u(t)
    (650, '1*r(t)', 'Practice scaled ramp number 650: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 650: Scaled ramp -> 1*r(t)
    (651, 'delta(t-6)', 'Practice impulse shift number 651: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 651: Impulse shift -> delta(t-6)
    (652, 'delta(t-2)+delta(t+2)', 'Practice impulse pair number 652: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 652: Impulse pair -> delta(t-2)+delta(t+2)
    (653, 'u(t)-u(t-6)', 'Practice pulse number 653: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 653: Pulse -> u(t)-u(t-6)
    (654, 'u(t-4)-u(t-7)', 'Practice delayed pulse number 654: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 654: Delayed pulse -> u(t-4)-u(t-7)
    (655, 'r(t)-r(t-8)', 'Practice finite ramp number 655: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 655: Finite ramp -> r(t)-r(t-8)
    (656, 'r(t)-2*r(t-1)+r(t-2)', 'Practice triangle number 656: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 656: Triangle -> r(t)-2*r(t-1)+r(t-2)
    (657, 'sin(8*t)', 'Practice sine number 657: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 657: Sine -> sin(8*t)
    (658, 'cos(9*t)', 'Practice cosine number 658: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 658: Cosine -> cos(9*t)
    (659, 'exp(-0.3*t)*sin(2*t)*u(t)', 'Practice damped sine number 659: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 659: Damped sine -> exp(-0.3*t)*sin(2*t)*u(t)
    (660, 'exp(-0.4*t)*cos(2*t)*u(t)', 'Practice damped cosine number 660: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 660: Damped cosine -> exp(-0.4*t)*cos(2*t)*u(t)
    (661, 'rect(t/6)', 'Practice rectangle number 661: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 661: Rectangle -> rect(t/6)
    (662, 'tri(t/7)', 'Practice triangle pulse number 662: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 662: Triangle pulse -> tri(t/7)
    (663, 'sinc(8*t)', 'Practice sinc number 663: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 663: Sinc -> sinc(8*t)
    (664, 'sgn(t-0)', 'Practice sign number 664: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 664: Sign -> sgn(t-0)
    (665, 'abs(t-1)', 'Practice absolute value number 665: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 665: Absolute value -> abs(t-1)
    (666, '(t-2)**2', 'Practice parabola number 666: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 666: Parabola -> (t-2)**2
    (667, 'sin(4*t)*u(t)', 'Practice causal sine number 667: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 667: Causal sine -> sin(4*t)*u(t)
    (668, 'cos(5*t)*u(t)', 'Practice causal cosine number 668: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 668: Causal cosine -> cos(5*t)*u(t)
    (669, 'r(t)+5*u(t-3)', 'Practice ramp-step combination number 669: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 669: Ramp-step combination -> r(t)+5*u(t-3)
    (670, 'u(t)+u(t-0)+u(t-2)', 'Practice step staircase number 670: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 670: Step staircase -> u(t)+u(t-0)+u(t-2)
    (671, 'delta(t+6)-delta(t-6)', 'Practice odd impulse pair number 671: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 671: Odd impulse pair -> delta(t+6)-delta(t-6)
    (672, 'r(t)-r(t-1)+u(t-0)', 'Practice mixed waveform number 672: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 672: Mixed waveform -> r(t)-r(t-1)+u(t-0)
    (673, 'u(t-13)', 'Practice step shift number 673: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 673: Step shift -> u(t-13)
    (674, 'u(t+14)', 'Practice advanced step number 674: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 674: Advanced step -> u(t+14)
    (675, 'r(t-15)', 'Practice ramp shift number 675: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 675: Ramp shift -> r(t-15)
    (676, 'r(t+16)', 'Practice advanced ramp number 676: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 676: Advanced ramp -> r(t+16)
    (677, '8*u(t)', 'Practice scaled step number 677: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 677: Scaled step -> 8*u(t)
    (678, '9*r(t)', 'Practice scaled ramp number 678: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 678: Scaled ramp -> 9*r(t)
    (679, 'delta(t-4)', 'Practice impulse shift number 679: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 679: Impulse shift -> delta(t-4)
    (680, 'delta(t-0)+delta(t+0)', 'Practice impulse pair number 680: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 680: Impulse pair -> delta(t-0)+delta(t+0)
    (681, 'u(t)-u(t-10)', 'Practice pulse number 681: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 681: Pulse -> u(t)-u(t-10)
    (682, 'u(t-2)-u(t-5)', 'Practice delayed pulse number 682: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 682: Delayed pulse -> u(t-2)-u(t-5)
    (683, 'r(t)-r(t-12)', 'Practice finite ramp number 683: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 683: Finite ramp -> r(t)-r(t-12)
    (684, 'r(t)-2*r(t-5)+r(t-10)', 'Practice triangle number 684: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 684: Triangle -> r(t)-2*r(t-5)+r(t-10)
    (685, 'sin(6*t)', 'Practice sine number 685: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 685: Sine -> sin(6*t)
    (686, 'cos(7*t)', 'Practice cosine number 686: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 686: Cosine -> cos(7*t)
    (687, 'exp(-0.4*t)*sin(2*t)*u(t)', 'Practice damped sine number 687: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 687: Damped sine -> exp(-0.4*t)*sin(2*t)*u(t)
    (688, 'exp(-0.5*t)*cos(2*t)*u(t)', 'Practice damped cosine number 688: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 688: Damped cosine -> exp(-0.5*t)*cos(2*t)*u(t)
    (689, 'rect(t/2)', 'Practice rectangle number 689: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 689: Rectangle -> rect(t/2)
    (690, 'tri(t/3)', 'Practice triangle pulse number 690: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 690: Triangle pulse -> tri(t/3)
    (691, 'sinc(4*t)', 'Practice sinc number 691: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 691: Sinc -> sinc(4*t)
    (692, 'sgn(t-4)', 'Practice sign number 692: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 692: Sign -> sgn(t-4)
    (693, 'abs(t-5)', 'Practice absolute value number 693: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 693: Absolute value -> abs(t-5)
    (694, '(t-6)**2', 'Practice parabola number 694: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 694: Parabola -> (t-6)**2
    (695, 'sin(8*t)*u(t)', 'Practice causal sine number 695: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 695: Causal sine -> sin(8*t)*u(t)
    (696, 'cos(1*t)*u(t)', 'Practice causal cosine number 696: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 696: Causal cosine -> cos(1*t)*u(t)
    (697, 'r(t)+5*u(t-1)', 'Practice ramp-step combination number 697: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 697: Ramp-step combination -> r(t)+5*u(t-1)
    (698, 'u(t)+u(t-3)+u(t-5)', 'Practice step staircase number 698: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 698: Step staircase -> u(t)+u(t-3)+u(t-5)
    (699, 'delta(t+4)-delta(t-4)', 'Practice odd impulse pair number 699: plot the signal, identify shifts/scaling, and describe its piecewise behaviour.'),
    # Exercise 699: Odd impulse pair -> delta(t+4)-delta(t-4)
]

# Extended named study references
EXTENDED_STUDY_REFERENCES = {
    'named_reference_0001': 'Signals and Systems practice reference 1',
    'named_reference_0002': 'Signals and Systems practice reference 2',
    'named_reference_0003': 'Signals and Systems practice reference 3',
    'named_reference_0004': 'Signals and Systems practice reference 4',
    'named_reference_0005': 'Signals and Systems practice reference 5',
    'named_reference_0006': 'Signals and Systems practice reference 6',
    'named_reference_0007': 'Signals and Systems practice reference 7',
    'named_reference_0008': 'Signals and Systems practice reference 8',
    'named_reference_0009': 'Signals and Systems practice reference 9',
    'named_reference_0010': 'Signals and Systems practice reference 10',
    'named_reference_0011': 'Signals and Systems practice reference 11',
    'named_reference_0012': 'Signals and Systems practice reference 12',
    'named_reference_0013': 'Signals and Systems practice reference 13',
    'named_reference_0014': 'Signals and Systems practice reference 14',
    'named_reference_0015': 'Signals and Systems practice reference 15',
    'named_reference_0016': 'Signals and Systems practice reference 16',
    'named_reference_0017': 'Signals and Systems practice reference 17',
    'named_reference_0018': 'Signals and Systems practice reference 18',
    'named_reference_0019': 'Signals and Systems practice reference 19',
    'named_reference_0020': 'Signals and Systems practice reference 20',
    'named_reference_0021': 'Signals and Systems practice reference 21',
    'named_reference_0022': 'Signals and Systems practice reference 22',
    'named_reference_0023': 'Signals and Systems practice reference 23',
    'named_reference_0024': 'Signals and Systems practice reference 24',
    'named_reference_0025': 'Signals and Systems practice reference 25',
    'named_reference_0026': 'Signals and Systems practice reference 26',
    'named_reference_0027': 'Signals and Systems practice reference 27',
    'named_reference_0028': 'Signals and Systems practice reference 28',
    'named_reference_0029': 'Signals and Systems practice reference 29',
    'named_reference_0030': 'Signals and Systems practice reference 30',
    'named_reference_0031': 'Signals and Systems practice reference 31',
    'named_reference_0032': 'Signals and Systems practice reference 32',
    'named_reference_0033': 'Signals and Systems practice reference 33',
    'named_reference_0034': 'Signals and Systems practice reference 34',
    'named_reference_0035': 'Signals and Systems practice reference 35',
    'named_reference_0036': 'Signals and Systems practice reference 36',
    'named_reference_0037': 'Signals and Systems practice reference 37',
    'named_reference_0038': 'Signals and Systems practice reference 38',
    'named_reference_0039': 'Signals and Systems practice reference 39',
    'named_reference_0040': 'Signals and Systems practice reference 40',
    'named_reference_0041': 'Signals and Systems practice reference 41',
    'named_reference_0042': 'Signals and Systems practice reference 42',
    'named_reference_0043': 'Signals and Systems practice reference 43',
    'named_reference_0044': 'Signals and Systems practice reference 44',
    'named_reference_0045': 'Signals and Systems practice reference 45',
    'named_reference_0046': 'Signals and Systems practice reference 46',
    'named_reference_0047': 'Signals and Systems practice reference 47',
    'named_reference_0048': 'Signals and Systems practice reference 48',
    'named_reference_0049': 'Signals and Systems practice reference 49',
    'named_reference_0050': 'Signals and Systems practice reference 50',
    'named_reference_0051': 'Signals and Systems practice reference 51',
    'named_reference_0052': 'Signals and Systems practice reference 52',
    'named_reference_0053': 'Signals and Systems practice reference 53',
    'named_reference_0054': 'Signals and Systems practice reference 54',
    'named_reference_0055': 'Signals and Systems practice reference 55',
}
