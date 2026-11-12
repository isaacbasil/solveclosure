import numpy as np


def save_surface_average_plot(closure_data, path, *, window=0.5):
    """
    Saves a png of the corrected global surface average of the closure variable against time.

    The plot shows the transient surface average, its steady value (dashed line), the last part of
    the run over which steady state is checked (shaded), and the times at which the solver was
    continued to reach steady state (dotted lines).

    Args:
        closure_data (dict): The processed closure data (from closure_data.pickle).
        path (str): The path of the png to write.
        window (float): The fraction of the run, at its end, over which steady state is checked. Default 0.5.

    Returns:
    """
    from matplotlib.figure import Figure

    t = np.asarray(closure_data["times for transient data"], dtype=float)
    s = np.asarray(closure_data["global s surface average transient"], dtype=float)
    s_steady = closure_data["global s surface average steady"]
    dimensionless = closure_data.get("dimensionless", True)

    # the same measure as the steady-state check: range over the window relative to the largest magnitude
    t_start = t[-1] * (1 - window)
    in_window = np.concatenate([[np.interp(t_start, t, s)], s[t > t_start]])
    scale = np.max(np.abs(s))
    relative_range = (np.max(in_window) - np.min(in_window)) / scale if scale > 0 else 0.0

    fig = Figure(figsize=(7, 4.5), layout="constrained")
    ax = fig.add_subplot()
    ax.axvspan(t_start, t[-1], color="0.9", label=f"steady-state check window (range {relative_range:.3%})")
    ax.plot(t, s, color="#4C72B0", lw=1.8, label="transient")
    ax.axhline(s_steady, color="#C44E52", ls="--", lw=1.2, label=f"steady value = {s_steady:.6g}")

    # times at which the solver was continued (end time doubled each time)
    continuations = closure_data.get("continuations") or 0
    end_time = closure_data.get("end time")
    if continuations and end_time:
        first_end_time = end_time / 2 ** continuations
        for k in range(continuations):
            ax.axvline(first_end_time * 2 ** k, color="0.4", ls=":", lw=1,
                       label="solver continued" if k == 0 else None)

    if dimensionless:
        ax.set_xlabel("Dimensionless time $\\hat{t}$")
        ax.set_ylabel("Corrected surface average of $\\hat{s}$")
    else:
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Corrected surface average of $s$")
    ax.set_xlim(0, t[-1])
    ax.set_title("Closure variable surface average evolving with time")
    ax.legend(loc="best", fontsize=9)
    ax.grid(alpha=0.3)
    fig.savefig(path, dpi=150)
