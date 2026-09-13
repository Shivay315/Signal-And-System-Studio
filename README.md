# Signals & Systems — Signal Plotter

A simple interactive Python tool for plotting **continuous-time signals** using standard Signals & Systems building blocks.

You can type expressions such as:

```text
r(t)
r(t+1)
r(t) + r(t+1)
r(t) - r(t-2)
u(t) - u(t-3)
2*r(t) - 2*r(t-2)
```

and plot them interactively.

## Features

* Interactive signal expression input
* Unit step function `u(t)`
* Unit ramp function `r(t)`
* Time shifting
* Amplitude scaling
* Addition and subtraction of signals
* Automatic Y-axis scaling
* Press **Enter** to plot
* Click the **PLOT** button to plot

<img width="1200" height="603" alt="image" src="https://github.com/user-attachments/assets/906a5e51-fff5-4c66-9ad8-f689370b5830" />


## Requirements

* Python 3
* NumPy
* Matplotlib

## Installation

This project uses a Python virtual environment so that packages are installed locally without modifying the system Python installation.

### 1. Create the virtual environment

From the project directory:

```bash
python3 -m venv .venv
```

### 2. Activate the virtual environment

On macOS/Linux:

```bash
source .venv/bin/activate
```

After activation, the terminal should look similar to:

```text
(.venv) shivay@Shivays-MacBook-Air Signals and System %
```

### 3. Install dependencies

```bash
python -m pip install numpy matplotlib
```

## Running the Program

Activate the virtual environment:

```bash
source .venv/bin/activate
```

Then run:

```bash
python just_trying_to_study.py
```

A window containing the signal plot and expression input box will open.

## Signal Syntax

### Unit Step

```text
u(t)
```

Examples:

```text
u(t-2)
u(t+1)
2*u(t)
```

Mathematically:

$$
u(t)=
\begin{cases}
0, & t<0\\
1, & t\geq0
\end{cases}
$$

### Unit Ramp

```text
r(t)
```

Examples:

```text
r(t+1)
r(t-2)
2*r(t)
```

Mathematically:

$$
r(t)=t\,u(t)
$$

### Combining Signals

Signals can be added or subtracted:

```text
r(t) + r(t+1)
```

```text
r(t) - r(t-2)
```

```text
u(t) - u(t-3)
```

Amplitude scaling can also be used:

```text
2*r(t)
```

```text
-3*u(t-2)
```

More complicated combinations:

```text
r(t) - 2*r(t-1) + r(t-2)
```

```text
3*u(t+1) - 2*u(t-2)
```

## Understanding Time Shifting

The program follows the standard Signals & Systems convention.

### Delay

```text
r(t-2)
```

The signal is shifted **2 units to the right**.

### Advance

```text
r(t+2)
```

The signal is shifted **2 units to the left**.

## Example

Consider:

```text
r(t) - r(t-2)
```

This creates a ramp that starts at \(t=0\) and stops increasing after \(t=2\).

Another useful example is:

```text
u(t) - u(t-3)
```

which produces a rectangular pulse from \(t=0\) to \(t=3\).

## Project Structure

```text
Signals and System/
│
├── just_trying_to_study.py
├── README.md
│
└── .venv/
```

`.venv` contains the project's isolated Python environment.

It should generally **not be uploaded to GitHub**.

If using Git, add this to `.gitignore`:

```text
.venv/
__pycache__/
*.pyc
```

## Deactivating the Environment

When you're finished:

```bash
deactivate
```

To use the project again later:

```bash
source .venv/bin/activate
```

## Future Improvements

Possible extensions:

* Unit impulse `δ(t)`
* Time scaling
* Time reversal
* More accurate impulse visualization
* Piecewise signal support
* Automatic identification of signal transformations
* Zoom and pan
* Adjustable time range
* Discrete-time signal plotting
* Export plots as PNG/PDF
* Support for expressions such as:

```text
r(2*t)
r(-t)
r(2-t)
u(3*t-2)
```

---

**Project:** Signals & Systems Signal Plotter
**Language:** Python
**Libraries:** NumPy, Matplotlib
