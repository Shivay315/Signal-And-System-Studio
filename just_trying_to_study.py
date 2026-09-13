import numpy as np
import matplotlib.pyplot as plt
from matplotlib.widgets import TextBox, Button


# ============================================================
# SIGNAL FUNCTIONS
# ============================================================

def u(t):
    """Unit step function."""
    return np.where(t >= 0, 1.0, 0.0)


def r(t):
    """Unit ramp function."""
    return np.maximum(t, 0.0)


def impulse(t, location=0, amplitude=1):
    """
    Approximate impulse for plotting.
    The impulse is represented as a vertical arrow.
    """
    return amplitude if np.isclose(t, location, atol=0.01) else 0


# ============================================================
# INITIAL SETTINGS
# ============================================================

t = np.linspace(-10, 10, 5000)

fig, ax = plt.subplots(figsize=(12, 6))
plt.subplots_adjust(bottom=0.22)

ax.set_title("Signals & Systems — Signal Plotter")
ax.set_xlabel("t")
ax.set_ylabel("x(t)")
ax.grid(True, alpha=0.3)
ax.axhline(0, color="black", linewidth=1)
ax.axvline(0, color="black", linewidth=1)

# Initial expression
initial_expression = "r(t) + r(t+1)"

# Plot initial signal
x = eval(
    initial_expression,
    {
        "np": np,
        "u": u,
        "r": r,
        "t": t
    }
)

line, = ax.plot(t, x, linewidth=2.5, label=initial_expression)
ax.legend()


# ============================================================
# TEXT INPUT BOX
# ============================================================

input_ax = plt.axes([0.12, 0.08, 0.65, 0.06])

text_box = TextBox(
    input_ax,
    "x(t) = ",
    initial=initial_expression
)


# ============================================================
# PLOT FUNCTION
# ============================================================

def plot_signal(expression=None):

    if expression is None:
        expression = text_box.text

    expression = expression.strip()

    try:

        # ----------------------------------------------------
        # Replace common notation with Python-compatible forms
        # ----------------------------------------------------

        expression = expression.replace("^", "**")
        expression = expression.replace("−", "-")

        # Allow expressions such as:
        #
        # 2r(t)
        # 3u(t)
        #
        # by converting them to:
        #
        # 2*r(t)
        # 3*u(t)

        import re

        expression = re.sub(
            r'(?<![\w)])(\d+(?:\.\d+)?)\s*(u|r)\(',
            r'\1*\2(',
            expression
        )

        # ----------------------------------------------------
        # Evaluate expression
        # ----------------------------------------------------

        x = eval(
            expression,
            {
                "__builtins__": {},
                "np": np,
                "u": u,
                "r": r,
                "t": t
            }
        )

        # ----------------------------------------------------
        # Plot
        # ----------------------------------------------------

        ax.clear()

        ax.axhline(0, color="black", linewidth=1)
        ax.axvline(0, color="black", linewidth=1)

        ax.plot(
            t,
            x,
            linewidth=2.5,
            label=expression
        )

        ax.set_title("Signals & Systems — Signal Plotter")
        ax.set_xlabel("t")
        ax.set_ylabel("x(t)")
        ax.grid(True, alpha=0.3)
        ax.legend()

        ax.set_xlim(-10, 10)

        # Automatically adjust Y-axis
        finite_values = x[np.isfinite(x)]

        if len(finite_values) > 0:

            ymin = np.min(finite_values)
            ymax = np.max(finite_values)

            if ymin == ymax:
                ymin -= 1
                ymax += 1

            margin = 0.1 * (ymax - ymin)

            ax.set_ylim(
                ymin - margin,
                ymax + margin
            )

        fig.canvas.draw_idle()

    except Exception as e:

        ax.clear()

        ax.text(
            0.5,
            0.5,
            f"Error:\n{e}\n\nExamples:\nr(t) + r(t+1)\nu(t) - u(t-2)\n2*r(t) - 3*r(t-2)",
            ha="center",
            va="center",
            transform=ax.transAxes,
            fontsize=12
        )

        ax.set_axis_off()

        fig.canvas.draw_idle()


# ============================================================
# ENTER KEY
# ============================================================

text_box.on_submit(plot_signal)


# ============================================================
# PLOT BUTTON
# ============================================================

button_ax = plt.axes([0.80, 0.08, 0.12, 0.06])

plot_button = Button(
    button_ax,
    "PLOT"
)


plot_button.on_clicked(
    lambda event: plot_signal()
)


# ============================================================
# EXAMPLES
# ============================================================

print("""
============================================================
        SIGNALS & SYSTEMS SIGNAL PLOTTER
============================================================

Type expressions such as:

    u(t)

    u(t-2)

    r(t)

    r(t+1)

    r(t) + r(t+1)

    r(t) - r(t-2)

    u(t) - u(t-3)

    2*r(t) - 2*r(t-2)

    3*u(t+1) - 2*u(t-2)

Use * for multiplication when needed:

    2*r(t)

    -3*u(t-2)

Press ENTER in the input box or click PLOT.

============================================================
""")


plt.show()
