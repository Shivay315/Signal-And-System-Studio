# Signals & Systems Studio

> A desktop study tool for building, visualizing, and analyzing continuous-time signals with simple mathematical expressions.

Signals & Systems Studio is a Python/Tkinter application designed for students studying **Signals and Systems**. Instead of drawing every signal manually, you can type expressions such as `r(t) + r(t+1)`, `u(t)-u(t-3)`, or `2*delta(t-1)` and immediately see the resulting waveform.

The application combines:

- direct mathematical signal entry
- common continuous-time signals
- time shifting, reversal, scaling, and signal construction
- numerical impulse visualization
- graph controls and zooming
- signal analysis tools
- expression history and favorites
- PNG, PDF, and CSV export
- a built-in Help Book
- a scrollable study sidebar
- light/dark themes

---

## Table of Contents

1. [What the project does](#what-the-project-does)
2. [Main idea](#main-idea)
3. [Features](#features)
4. [Project structure](#project-structure)
5. [Requirements](#requirements)
6. [Installation on macOS](#installation-on-macos)
7. [Running the application](#running-the-application)
8. [Interface overview](#interface-overview)
9. [Entering a signal](#entering-a-signal)
10. [Supported basic signals](#supported-basic-signals)
11. [Mathematical functions](#mathematical-functions)
12. [Time transformations](#time-transformations)
13. [Signal constructions](#signal-constructions)
14. [Time range controls](#time-range-controls)
15. [Toolbar](#toolbar)
16. [Menus](#menus)
17. [Analysis tools](#analysis-tools)
18. [History and favorites](#history-and-favorites)
19. [View controls](#view-controls)
20. [Exporting results](#exporting-results)
21. [Help Book](#help-book)
22. [Keyboard shortcuts](#keyboard-shortcuts)
23. [Examples](#examples)
24. [Screenshot guide](#screenshot-guide)
25. [Troubleshooting](#troubleshooting)
26. [How the program works](#how-the-program-works)
27. [Limitations](#limitations)
28. [Future improvements](#future-improvements)
29. [License](#license)

---

## What the project does

Signals & Systems Studio turns a typed signal expression into a plotted waveform.

For example:

```text
r(t) + r(t+1)
```

can be interpreted as a sum of two ramp signals and plotted over the selected time interval.

A second example:

```text
u(t) - u(t-3)
```

creates a rectangular pulse extending from approximately `t = 0` to `t = 3`.

Another example:

```text
r(t) - 2*r(t-1) + r(t-2)
```

constructs a triangular waveform from shifted ramps.

The goal is to make the relationship between **signal notation, mathematical operations, and waveform shape** easy to explore interactively.

---

## Main idea

The central workflow is intentionally simple:

```text
Type expression
      ↓
Choose time range
      ↓
Press Plot / Enter
      ↓
Waveform appears
      ↓
Analyze / transform / export
```

The application is therefore useful both for:

- learning signal transformations visually
- checking handwritten solutions
- experimenting with signal combinations
- generating plots for notes and assignments

---

# Features

## 1. Expression-based plotting

The most important feature is the expression box. You can write signal equations directly instead of assembling them only through buttons.

Examples:

```text
u(t)
```

```text
r(t)
```

```text
r(t)+r(t+1)
```

```text
u(t)-u(t-3)
```

```text
3*delta(t-2)
```

```text
r(t)-2*r(t-1)+r(t-2)
```

Press **Enter** in the expression field or press **Plot expression**.

### Screenshot to add here
**Filename:** <img width="1470" height="926" alt="image" src="https://github.com/user-attachments/assets/877a9c60-fc1f-46df-ae8b-2fdf0c39fe36" />


Capture the complete application window while the expression box contains a non-trivial example such as:

```text
r(t)-2*r(t-1)+r(t-2)
```

The screenshot should clearly show:

- the expression field
- the Plot button
- the function palette
- the time range
- the resulting graph

This should be the **first screenshot in the README**, immediately after the feature introduction.

---

## 2. Built-in signal palette

The sidebar contains quick buttons for frequently used functions.

Available quick-entry signals include:

- `u(t)` — unit step
- `r(t)` — unit ramp
- `delta(t)` — impulse
- `sgn(t)` — sign function
- `rect(t)` — rectangular pulse
- `tri(t)` — triangular pulse
- `sin(t)` — sine
- `cos(t)` — cosine
- `exp(t)` — exponential
- `sinc(t)` — normalized sinc

Clicking one of these buttons inserts the function into the expression field.

### Screenshot to add here
**Filename:** <img width="370" height="211" alt="image" src="https://github.com/user-attachments/assets/ad61e9d9-8c40-4602-ba59-52a01e4c683d" />


Capture the left sidebar with the **Insert functions** section fully visible. Make sure the graph is also visible on the right so readers can understand that the buttons are connected to the plotter.

Place this image in this section directly after the function list.

---

## 3. Scrollable study sidebar

The left side of the application contains more controls than can fit on a short screen, so the sidebar is vertically scrollable.

The sidebar is designed to work with normal mouse-wheel input and macOS trackpad scrolling.

The embedded sidebar width is constrained to the visible panel so that controls do not intentionally create a horizontal overflow.

### Screenshot to add here
**Filename:** <img width="407" height="841" alt="image" src="https://github.com/user-attachments/assets/8ed778f4-5b5d-4f60-988e-545437059e36" />


Capture the application at a smaller vertical size where the lower sidebar sections are partially hidden. Then scroll the sidebar down and capture a second image.

Recommended pair:

```text
03a-sidebar-top.png
03b-sidebar-bottom.png
```

Use the first image near this section and the second one later near **Analysis tools**.

---

# Requirements

The application uses:

- Python 3
- NumPy
- Matplotlib
- Tkinter
- `python-tk` on Homebrew Python installations where Tkinter is packaged separately

The tested development environment for this project uses modern Python/NumPy/Matplotlib on macOS.

---

# Project structure

A recommended project folder looks like this:

```text
SNS Studio/
│
├── just_trying_to_study.py
├── Signals_and_Systems_Help_Book.pdf
└── README.md
```

You may also keep screenshots in a dedicated folder:

```text
SNS Studio/
├── just_trying_to_study.py
├── Signals_and_Systems_Help_Book.pdf
├── README.md
└── screenshots/
    ├── 01-main-expression.png
    ├── 02-function-palette.png
    ├── 03-scrollable-sidebar.png
    ├── 04-time-range.png
    ├── 05-toolbar.png
    ├── 06-file-menu.png
    ├── 07-functions-menu.png
    ├── 08-analysis-menu.png
    ├── 09-view-menu.png
    ├── 10-help-menu.png
    ├── 11-statistics.png
    ├── 12-inspect-values.png
    ├── 13-compare.png
    ├── 14-cursor.png
    ├── 15-export-dialog.png
    ├── 16-dark-mode.png
    └── 17-help-book.png
```

---

# Installation on macOS

## Step 1 — Open Terminal

Go to the project directory.

Example:

```bash
cd ~/Documents/College\ Work/DTU/Semester\ 7/Signals\ and\ System
```

If the application is inside `SNS Studio`:

```bash
cd SNS\ Studio
```

---

## Step 2 — Create a virtual environment

From the parent project directory:

```bash
python3 -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

You should then see something similar to:

```text
(.venv) shivay@MacBook ... %
```

---

## Step 3 — Install Python packages

```bash
python -m pip install numpy matplotlib
```

---

## Step 4 — Make sure Tkinter is available

On Homebrew Python, Tkinter may need the matching Tk package.

Install the required packages with Homebrew if necessary:

```bash
brew install tcl-tk
brew install python-tk@3.14
```

The exact `python-tk` version should match the Python version installed on your system.

Test Tkinter with:

```bash
python -m tkinter
```

A small Tk window should appear if the installation is working.

---

# Running the application

From inside the `SNS Studio` folder:

```bash
python just_trying_to_study.py
```

The program should open as a desktop application.

The application automatically plots the default expression when it starts.

### Screenshot to add here
**Filename:** <img width="1470" height="952" alt="image" src="https://github.com/user-attachments/assets/3da0baa7-1e74-4e4e-ad9a-9608745acd8e" />


Capture the complete application immediately after launching it. Use this as the main **Getting Started** visual immediately after the run command.

---

# Interface overview

The interface has five major regions:

```text
┌─────────────────────────────────────────────────────────────┐
│ Menu Bar                                                    │
├─────────────────────────────────────────────────────────────┤
│ Toolbar                                                     │
├───────────────────┬─────────────────────────────────────────┤
│                   │                                         │
│ Scrollable        │                                         │
│ Study Sidebar     │            Signal Graph                 │
│                   │                                         │
│                   │                                         │
└───────────────────┴─────────────────────────────────────────┘
```

### Menu bar

Contains File, Functions, Analysis, View, and Help controls.

### Toolbar

Provides the most frequently used plotting, signal, view, export, theme, and help actions.

### Sidebar

Contains:

- expression entry
- function buttons
- time range
- construction presets
- analysis buttons
- quick reference

### Graph area

The Matplotlib graph displays the currently evaluated signal.

### Status area

The application provides status messages for actions such as exporting files, changing expressions, and opening the Help Book.

---

# Entering a signal

## Basic syntax

Signals are written using normal mathematical expression syntax.

Use:

```text
+
-
*
/
**
(
)
```

The program also normalizes several common notations automatically.

For example:

```text
2r(t)
```

can be normalized to multiplication form, while:

```text
r(t)^2
```

is converted to Python-style exponentiation.

The application also understands the Unicode symbols:

- `δ` for impulse
- `−` for minus
- `×` for multiplication

### Examples

```text
u(t-2)
```

Shift the step to the right by 2.

```text
u(t+2)
```

Shift the step to the left by 2.

```text
2*r(t)
```

Scale a ramp in amplitude by 2.

```text
r(2*t)
```

Compress the signal in time.

```text
r(0.5*t)
```

Expand the signal in time.

---

# Supported basic signals

## Unit step

```text
u(t)
```

Implemented as a numerical unit-step function.

```text
u(t-2)
```

represents a delayed step.

---

## Unit ramp

```text
r(t)
```

The ramp is defined numerically as:

```text
max(t, 0)
```

Examples:

```text
r(t-2)
```

```text
r(-t)
```

```text
2*r(t)
```

---

## Impulse

Use:

```text
delta(t)
```

or:

```text
d(t)
```

The application treats the impulse specially for plotting. It extracts simple `delta(...)` terms and displays them as vertical impulse arrows rather than trying to represent an ideal Dirac delta with an ordinary sampled function.

Examples:

```text
delta(t)
```

```text
delta(t-2)
```

```text
2*delta(t+1)
```

### Screenshot to add here
**Filename:** <img width="1470" height="956" alt="image" src="https://github.com/user-attachments/assets/dec1c010-72f5-45cf-8f43-99040465e05c" />


Plot:

```text
2*delta(t-2)
```

Make sure the impulse arrow and its location are clearly visible. This is an important screenshot because it demonstrates that the application handles impulses differently from ordinary continuous curves.

---

## Sign function

```text
sgn(t)
```

Returns the numerical sign of each sampled time value.

---

## Rectangular pulse

```text
rect(t)
```

The built-in function is centered around zero.

---

## Triangular pulse

```text
tri(t)
```

A triangular shape centered at zero.

---

## Sinc

```text
sinc(t)
```

Uses NumPy's normalized sinc definition.

---

# Mathematical functions

The expression engine supports these mathematical functions:

| Function | Example |
|---|---|
| `sin` | `sin(t)` |
| `cos` | `cos(t)` |
| `tan` | `tan(t)` |
| `exp` | `exp(-0.2*t)` |
| `sqrt` | `sqrt(abs(t))` |
| `abs` | `abs(t)` |
| `ln` | `ln(t)` |
| `log10` | `log10(t)` |
| `pi` | `sin(pi*t)` |
| `e` | `e**t` |

The sidebar and **Functions → Math Functions** menu provide quick insertion for common functions.

---

# Time transformations

Signals and Systems students frequently work with transformations of the form:

```text
x(t-a)
x(t+a)
x(-t)
Ax(t)
x(at)
```

The application makes these easy to test.

## Time delay

```text
u(t-2)
```

A positive subtraction shifts the waveform right.

## Time advance

```text
u(t+2)
```

A positive addition inside the argument shifts the waveform left.

## Time compression

```text
r(2*t)
```

## Time expansion

```text
r(0.5*t)
```

## Time reversal

```text
r(-t)
```

## Amplitude scaling

```text
3*u(t)
```

```text
2*r(t)
```

### Screenshot to add here
**Filename:** `screenshots/06-transformations.png`

Use one expression that demonstrates at least two transformations, for example:

```text
2*r(2*(t-1))
```

Capture the graph plus the expression field. The purpose of this image is to visually connect the notation to the transformation.

---

# Signal constructions

The project includes built-in examples of how common waveforms can be constructed from basic building blocks.

## Rectangular pulse from steps

```text
u(t)-u(t-3)
```

This creates a finite pulse.

## Delayed pulse

```text
u(t-2)-u(t-5)
```

## Finite ramp construction

```text
r(t)-r(t-2)
```

## Triangle from ramps

```text
r(t)-2*r(t-1)+r(t-2)
```

This is especially useful for learning how a triangular waveform can be assembled from ramps.

### Screenshot to add here
**Filename:** `screenshots/07-triangle-from-ramps.png`

Plot:

```text
r(t)-2*r(t-1)+r(t-2)
```

This should be one of the most prominent images in the README because it demonstrates the educational purpose of the tool.

Suggested caption:

> A triangular waveform constructed using shifted unit ramps.

---

# Time range controls

The sidebar allows the visible time interval to be changed.

The default range is:

```text
From: -10
To:    10
```

The plot is sampled over the selected interval using 8000 time samples.

The program checks that:

- the lower bound is smaller than the upper bound
- the interval is not excessively large

### Screenshot to add here
**Filename:** `screenshots/08-time-range.png`

Show the time-range controls with a changed interval such as:

```text
From: -5
To: 5
```

Also show the resulting graph.

---

# Toolbar

The toolbar has two rows so that controls remain visible on smaller windows.

## Row 1

### Plot

Plots the current expression.

### New

Clears the current expression.

### u(t)

Quickly selects the unit step.

### r(t)

Quickly selects the unit ramp.

### δ(t)

Quickly selects the impulse.

### Pulse

Loads:

```text
u(t)-u(t-3)
```

### Triangle

Loads:

```text
r(t)-2*r(t-1)+r(t-2)
```

### Theme

Switches the application theme.

### Help

Opens the Help Book.

## Row 2

### Auto Y

Toggles automatic Y-axis scaling.

### Fit

Resets the view.

### Zoom + / Zoom −

Changes the visible plot scale.

### Save PNG

Exports the current graph as an image.

### Save PDF

Exports the current graph as a PDF.

### Export CSV

Exports the sampled time and amplitude values.

### Screenshot to add here
**Filename:** `screenshots/09-toolbar.png`

Capture only the upper portion of the application, with the complete two-row toolbar visible. Make sure labels are readable.

---

# Menus

## File menu

The File menu provides:

- New / Clear
- Open Expression
- Save Expression
- Save as Image
- Save as PDF
- Export Samples as CSV
- Exit

### Screenshot to add here
**Filename:** `screenshots/10-file-menu.png`

Open the File menu and capture the complete dropdown.

Place it directly below this section.

---

## Functions menu

The Functions menu contains:

- Basic Signals
- Transformations
- Signal Constructions
- Math Functions
- History
- Favorites

### Screenshot to add here
**Filename:** `screenshots/11-functions-menu.png`

Open the **Functions** menu so that the top-level categories are visible. Do not worry about opening every submenu in one screenshot; one screenshot can show the structure, while additional screenshots can show important submenus if desired.

### Optional extra screenshots

```text
screenshots/11a-basic-signals-menu.png
screenshots/11b-transformations-menu.png
screenshots/11c-constructions-menu.png
screenshots/11d-math-menu.png
```

These are optional because the README already documents the individual functions.

---

## Analysis menu

The Analysis menu provides:

- Signal Statistics
- Inspect Sample Values
- Compare with Another Signal
- Approximate Peak
- Approximate Area
- Moving Value Cursor

### Screenshot to add here
**Filename:** `screenshots/12-analysis-menu.png`

Open the Analysis menu and capture the complete dropdown.

---

## View menu

The View menu controls:

- Autoscale Y-axis
- Grid
- Zero axes
- Legend
- Zoom In
- Zoom Out
- Fit / Reset View
- Toggle Dark Mode

### Screenshot to add here
**Filename:** `screenshots/13-view-menu.png`

Open the View menu and capture it over the graph.

---

## Help menu

The Help menu contains:

- Open Help Book
- Examples
- Keyboard Shortcuts
- About

### Screenshot to add here
**Filename:** `screenshots/14-help-menu.png`

Open the Help menu and capture the complete dropdown.

---

# Analysis tools

The application includes several tools for studying the plotted signal rather than only looking at its shape.

## Signal Statistics

The statistics dialog reports:

- expression
- number of samples
- minimum
- maximum
- mean
- RMS
- numerical area
- approximate location of the largest magnitude sample

The area is calculated numerically with NumPy's trapezoidal integration function.

### Screenshot to add here
**Filename:** `screenshots/15-statistics.png`

Plot a simple but non-trivial signal, then open **Analysis → Signal Statistics**. Capture the statistics dialog with the graph visible behind it when possible.

---

## Inspect Sample Values

This tool opens a table-like text window containing sampled values:

```text
t                 x(t)
--------------------------------
...
```

Up to 200 evenly distributed sample locations are shown.

### Screenshot to add here
**Filename:** `screenshots/16-inspect-values.png`

Open **Inspect Sample Values** and capture the resulting window.

---

## Compare with Another Signal

You can compare the current signal with a second typed expression.

For example, start with:

```text
r(t)
```

and compare it with:

```text
r(t-1)
```

The graph then shows both waveforms using separate line styles/legend entries.

### Screenshot to add here
**Filename:** `screenshots/17-compare.png`

Use a clearly shifted pair such as:

```text
r(t)
```

and:

```text
r(t-2)
```

Capture the comparison graph and its legend.

---

## Approximate Peak

The peak tool finds the largest absolute sampled amplitude and reports its approximate value and location.

### Screenshot recommendation
A screenshot is optional here. If you include one:

```text
screenshots/18-peak-dialog.png
```

Capture the peak dialog.

---

## Approximate Area

The area tool numerically integrates the plotted signal over the visible time range.

This is an approximation based on the sampled waveform.

### Screenshot recommendation
Optional:

```text
screenshots/19-area-dialog.png
```

---

## Moving Value Cursor

The moving cursor creates a vertical line on the graph and reports the nearest sampled values of:

```text
t
x(t)
```

As the pointer moves over the graph, the reported values update.

### Screenshot to add here
**Filename:** `screenshots/20-moving-cursor.png`

Move the cursor over a point where the signal has an easy-to-understand value. Capture the graph with the vertical cursor line and the small value label visible.

---

# History and favorites

## History

Each plotted expression can be added to the application's expression history.

History is available under:

```text
Functions → History
```

The application keeps recent entries and limits the history list to the latest 100 expressions.

---

## Favorites

You can save a useful expression as a favorite so it can be reused later.

Use the **Add current expression to Favorites** button in the sidebar or access favorites through:

```text
Functions → Favorites
```

Favorites can be:

- selected again
- removed individually
- cleared completely

### Screenshot to add here
**Filename:** `screenshots/21-history-favorites.png`

Create a few expressions, add at least one favorite, then open **Functions → Favorites** or **Functions → History** and capture the resulting menu.

---

# View controls

## Autoscale Y-axis

When enabled, the graph automatically adjusts its Y-axis to the current signal.

## Grid

Displays or hides graph grid lines.

## Zero axes

Displays the horizontal and vertical zero axes.

## Legend

Shows or hides the graph legend when applicable.

## Zoom

Use **Zoom +** and **Zoom −** to change the visible plot scale.

## Fit / Reset View

Returns the graph to a fitted view.

---

# Exporting results

The application can export the current signal in three useful forms.

## PNG / JPEG / SVG image

Use:

```text
File → Save as Image…
```

The toolbar also provides **Save PNG**.

The image is exported at high resolution.

---

## PDF

Use:

```text
File → Save as PDF…
```

The plotted graph is saved as a PDF document.

---

## CSV

Use:

```text
File → Export Samples as CSV…
```

The exported file contains two columns:

```text
t,x(t)
```

This is useful for further processing in:

- Excel
- MATLAB
- Python
- spreadsheets
- other numerical tools

### Screenshot to add here
**Filename:** `screenshots/22-export.png`

Open one of the Save/Export dialogs and capture the filename/type selection. Do not include private directory names in the screenshot.

---

# Saving and opening expressions

## Save Expression

The expression itself can be stored as a `.txt` file.

Example contents:

```text
r(t)-2*r(t-1)+r(t-2)
```

## Open Expression

A previously saved `.txt` expression can be reopened, and the application loads it into the expression field.

This makes it easy to build a small personal library of signals.

---

# Help Book

The application expects a PDF named:

```text
Signals_and_Systems_Help_Book.pdf
```

The Help Book must be in the **same directory as `just_trying_to_study.py`**.

When **Help** or **Open Help Book** is selected, the application asks the operating system to open the PDF using the default PDF viewer.

If the file is missing, the application displays a warning explaining the expected filename and location.

### Screenshot to add here
**Filename:** `screenshots/23-help-book.png`

Capture the first page of the Help Book PDF open on your screen.

For the README, use this screenshot after the Help Book explanation rather than putting a huge PDF page image near the top of the document.

---

# Keyboard shortcuts

The main shortcuts shown by the application are:

| Action | Shortcut |
|---|---|
| New / Clear | `⌘N` |
| Open Expression | `⌘O` |
| Save Expression | `⌘S` |
| Save as Image | `⇧⌘S` |
| Save as PDF | `⇧⌘P` |
| Exit | `⌘Q` |
| Plot | `Enter` while focused in the expression field |

The Help menu also provides a **Keyboard Shortcuts** dialog.

### Screenshot recommendation
Optional:

```text
screenshots/24-shortcuts.png
```

Capture the shortcuts dialog.

---

# Examples

## Example 1 — Unit step

Expression:

```text
u(t)
```

Expected behavior: the signal changes from approximately `0` to `1` at the origin.

---

## Example 2 — Shifted step

Expression:

```text
u(t-2)
```

Expected behavior: the transition occurs at approximately `t = 2`.

---

## Example 3 — Ramp

Expression:

```text
r(t)
```

Expected behavior: zero for negative time and linearly increasing for positive time.

---

## Example 4 — Shifted ramp

Expression:

```text
r(t-2)
```

The ramp starts increasing after its shift point.

---

## Example 5 — Rectangular pulse

Expression:

```text
u(t)-u(t-3)
```

This demonstrates how two step functions can form a finite-duration pulse.

### Suggested screenshot
Use:

```text
screenshots/25-rectangular-pulse.png
```

---

## Example 6 — Triangle from ramps

Expression:

```text
r(t)-2*r(t-1)+r(t-2)
```

This is the recommended demonstration example for the project because it shows how a piecewise triangular waveform can be constructed from shifted ramps.

---

## Example 7 — Damped sinusoid

Expression:

```text
exp(-0.2*t)*sin(2*t)*u(t)
```

This creates a causal damped sinusoid.

---

## Example 8 — Impulse pair

Expression:

```text
delta(t-2)-delta(t+2)
```

This is useful for studying shifted impulses and sign/amplitude changes.

---

# Screenshot guide

This section is the recommended image plan for the GitHub README.

Do **not** take screenshots of Terminal unless the README section specifically discusses installation. For the main project presentation, use clean screenshots containing only the application and relevant dialogs.

## Recommended screenshot set

| # | Filename | What to capture | Where to place it |
|---|---|---|---|
| 1 | `01-main-expression.png` | Full app with a non-trivial expression and graph | Near the top after project introduction |
| 2 | `02-function-palette.png` | Sidebar function buttons | Basic function section |
| 3 | `03-scrollable-sidebar.png` | Scrollable sidebar | Sidebar/interface section |
| 4 | `04-first-launch.png` | Fresh application launch | Running the application |
| 5 | `05-impulse.png` | `2*delta(t-2)` graph | Impulse section |
| 6 | `06-transformations.png` | Shift/scale/time transformation | Transformations section |
| 7 | `07-triangle-from-ramps.png` | Triangle constructed from ramps | Signal constructions section |
| 8 | `08-time-range.png` | Changed time interval + graph | Time range section |
| 9 | `09-toolbar.png` | Full two-row toolbar | Toolbar section |
| 10 | `10-file-menu.png` | File dropdown | File menu section |
| 11 | `11-functions-menu.png` | Functions dropdown | Functions menu section |
| 12 | `12-analysis-menu.png` | Analysis dropdown | Analysis menu section |
| 13 | `13-view-menu.png` | View dropdown | View menu section |
| 14 | `14-help-menu.png` | Help dropdown | Help menu section |
| 15 | `15-statistics.png` | Statistics dialog | Statistics section |
| 16 | `16-inspect-values.png` | Sample-value window | Inspect Values section |
| 17 | `17-compare.png` | Two signals on same graph | Compare section |
| 18 | `20-moving-cursor.png` | Cursor + value readout | Moving cursor section |
| 19 | `21-history-favorites.png` | History/Favorites menu | History/Favorites section |
| 20 | `22-export.png` | Save/export dialog | Export section |
| 21 | `23-help-book.png` | Help Book first page | Help Book section |
| 22 | `24-shortcuts.png` | Shortcut dialog | Keyboard shortcut section |
| 23 | `25-rectangular-pulse.png` | Step-built pulse | Examples section |

You do **not** need to use every optional screenshot. A polished README can look excellent with roughly 10–14 carefully chosen images.

---

## Best screenshot selection for a professional README

For a cleaner GitHub page, the highest-value screenshots are:

1. **Main application** — `01-main-expression.png`
2. **Function palette** — `02-function-palette.png`
3. **Triangle from ramps** — `07-triangle-from-ramps.png`
4. **Impulse handling** — `05-impulse.png`
5. **Analysis statistics** — `15-statistics.png`
6. **Signal comparison** — `17-compare.png`
7. **Moving cursor** — `20-moving-cursor.png`
8. **Dark mode** — add `26-dark-mode.png` if you want a theme screenshot
9. **Help Book** — `23-help-book.png`
10. **Toolbar/menu** — `09-toolbar.png`

This selection communicates what the software looks like, what it can do, and why it is useful without turning the README into a gallery.

---

# How to add screenshots to the README

Create a folder named:

```text
screenshots
```

inside the project directory.

Put your screenshot files there.

Then Markdown can display an image like this:

```markdown
![Signals & Systems Studio main window](screenshots/01-main-expression.png)
```

For a caption, use:

```markdown
*Signals & Systems Studio with a triangular signal entered as an expression.*
```

For the cleanest appearance, keep the images reasonably sized and use screenshots with the same overall window dimensions.

---

# Troubleshooting

## `ModuleNotFoundError: No module named 'numpy'`

Make sure the virtual environment is activated and install the package:

```bash
source .venv/bin/activate
python -m pip install numpy
```

---

## `ModuleNotFoundError: No module named 'matplotlib'`

Install Matplotlib:

```bash
python -m pip install matplotlib
```

---

## `_tkinter` is missing

On Homebrew Python, install the matching Tk package.

For Python 3.14:

```bash
brew install python-tk@3.14
```

It may also be useful to install:

```bash
brew install tcl-tk
```

Then verify:

```bash
python -m tkinter
```

If the virtual environment was created before fixing Tk, recreating the virtual environment is a good cleanup step:

```bash
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install numpy matplotlib
```

---

## `np.trapz` error with modern NumPy

Older code may use:

```python
np.trapz(...)
```

The current project uses:

```python
np.trapezoid(...)
```

for numerical integration so it works with the modern NumPy environment used for this project.

This affects the **Signal Statistics** and **Approximate Area** features.

---

## Help Book cannot be opened

Check that this file exists beside the Python script:

```text
Signals_and_Systems_Help_Book.pdf
```

Correct:

```text
SNS Studio/
├── just_trying_to_study.py
└── Signals_and_Systems_Help_Book.pdf
```

Incorrect:

```text
SNS Studio/
└── docs/
    └── Signals_and_Systems_Help_Book.pdf
```

unless the application code is changed to look in that different location.

---

## Trackpad scrolling does not move the sidebar

Make sure the pointer is over the left sidebar while using the two-finger gesture.

The application routes macOS high-resolution mouse-wheel/trackpad events to the sidebar when the pointer is inside it.

---

## Expression cannot be plotted

Check the expression syntax.

Correct:

```text
r(t)-2*r(t-1)+r(t-2)
```

Potentially problematic:

```text
r(t) - 2 r(t-1) + r(t-2)
```

Use `*` when explicit multiplication is clearer:

```text
r(t)-2*r(t-1)+r(t-2)
```

---

# How the program works

At a high level, the application follows this pipeline:

```text
User expression
      ↓
Normalization
      ↓
Restricted expression evaluation
      ↓
Time vector generation
      ↓
Signal samples
      ↓
Impulse extraction (when needed)
      ↓
Matplotlib rendering
      ↓
Analysis / export
```

## 1. Normalization

The program converts several common notations to a consistent internal format.

Examples include:

```text
δ → delta
− → -
× → *
^ → **
```

It also inserts multiplication in several common cases such as numeric coefficients followed by supported functions.

---

## 2. Restricted evaluation

The expression is evaluated using a restricted namespace rather than unrestricted Python built-ins.

The evaluation environment contains only the signal and mathematical functions explicitly provided by the application.

This makes expressions predictable and prevents normal Python built-ins from being exposed through the evaluator.

---

## 3. Sampling

The application creates a NumPy time vector using:

```python
np.linspace(tmin, tmax, 8000)
```

This gives 8000 sample points across the chosen visible interval.

---

## 4. Plotting

The sampled signal is sent to a Matplotlib figure embedded inside the Tkinter application.

Grid lines, zero axes, legends, autoscaling, and zoom settings are applied according to the current user configuration.

---

## 5. Impulse rendering

An ideal Dirac impulse is not an ordinary finite sampled curve.

The program therefore detects simple `delta(...)` terms separately and displays them as vertical arrows at their corresponding locations.

For example:

```text
delta(t-2)
```

is interpreted as an impulse at:

```text
t = 2
```

---

## 6. Numerical analysis

Statistics such as mean, RMS, peak location, and area are based on the sampled signal values.

The area is approximated numerically using trapezoidal integration.

Therefore these values should be interpreted as **numerical approximations over the selected visible interval**, not exact symbolic results.

---

# Limitations

This application is intentionally a practical study tool rather than a full symbolic mathematics system.

Important limitations include:

- the plot is numerical rather than symbolic
- the signal is sampled at finite resolution
- impulse support is focused on simple `delta(t±a)` forms
- some complicated piecewise expressions may require manual simplification
- `ln` and `log10` are numerically protected by the implementation rather than treated as symbolic functions
- `sqrt` is numerically constrained to avoid invalid negative-domain square roots
- numerical area and statistics depend on the chosen time interval and sampling

For advanced symbolic manipulation, MATLAB, Mathematica, SymPy, or another symbolic system may be more appropriate.

---

# Future improvements

Possible future extensions include:

- symbolic piecewise expression generation
- convolution tools
- correlation tools
- Fourier series visualization
- Fourier transform exploration
- Laplace-transform helpers
- automatic piecewise-form generation
- richer signal libraries
- parameter sliders for interactive transformations
- multi-signal plotting with expression lists
- automatic annotation of shift points and discontinuities
- persistent history/favorites storage
- project/session files
- educational exercises and quiz mode
- keyboard-friendly expression completion
- more advanced export formatting

---

# Educational use cases

Signals & Systems Studio is especially useful for studying:

### Basic signals

- step
- ramp
- impulse
- sign
- rectangular pulse
- triangular pulse
- sinc

### Operations

- amplitude scaling
- time shifting
- time reversal
- time compression
- time expansion
- addition/subtraction of signals

### Construction methods

- pulse from steps
- triangle from ramps
- finite ramp constructions
- combinations of delayed components

### Analysis

- maximum/minimum
- RMS
- mean
- area
- sample inspection
- comparison between signals

---

# Quick reference

```text
Unit step       u(t)
Unit ramp       r(t)
Impulse         delta(t)
Sign            sgn(t)
Rectangle       rect(t)
Triangle        tri(t)
Sinc            sinc(t)

Sine            sin(t)
Cosine          cos(t)
Tangent         tan(t)
Exponential     exp(t)
Square root     sqrt(t)
Absolute        abs(t)
Natural log     ln(t)
Base-10 log     log10(t)

Delay           x(t-a)
Advance         x(t+a)
Reversal        x(-t)
Amplitude       A*x(t)
Time scaling    x(a*t)

Power           x(t)**2
Product         x(t)*y(t)
Sum             x(t)+y(t)
Difference      x(t)-y(t)
```

---

# Recommended first-time workflow

A new user can learn the application in a few minutes by following this sequence:

### Step 1
Launch the program.

### Step 2
Enter:

```text
u(t)
```

and press Enter.

### Step 3
Try:

```text
u(t-2)
```

and observe the shift.

### Step 4
Try:

```text
r(t)-2*r(t-1)+r(t-2)
```

and observe the triangle.

### Step 5
Try:

```text
2*delta(t-1)
```

and observe the impulse arrow.

### Step 6
Open **Analysis → Signal Statistics**.

### Step 7
Try **Compare signal** with:

```text
r(t-1)
```

### Step 8
Use **Save PNG** or **Save PDF** to keep the graph.

### Step 9
Open the Help Book for deeper reference material.

---

# Final project presentation

For a college project, portfolio, or GitHub repository, the recommended presentation order is:

1. Project title and one-sentence description
2. Main application screenshot
3. Feature overview
4. Example: triangle from ramps
5. Example: impulse handling
6. Interface / toolbar
7. Analysis tools
8. Export features
9. Installation and run instructions
10. Technical implementation
11. Limitations and future work

This order shows the project visually before asking the reader to read technical details.

---

# License

Add the license that you intend to use for the project here.

For example, if the project is released under MIT:

```text
MIT License
Copyright (c) 2026 Shivay
```

Replace this section with the actual license text before publishing the repository.

---

## Screenshot checklist before publishing

Before pushing the README to GitHub, check that:

- [ ] all images are inside `screenshots/`
- [ ] filenames exactly match the Markdown references
- [ ] screenshots contain no private file paths or personal information
- [ ] text in screenshots is readable at normal GitHub size
- [ ] the main screenshot is placed near the top
- [ ] at least one screenshot shows a real expression being plotted
- [ ] at least one screenshot shows a signal construction
- [ ] at least one screenshot shows analysis
- [ ] at least one screenshot shows exporting or the Help Book
- [ ] dark mode screenshot is included if you want to showcase themes

---

**Signals & Systems Studio** — a small visual laboratory for learning how mathematical signal expressions become waveforms.
