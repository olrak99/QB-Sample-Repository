import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import math
import matplotlib
matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg


# -----------------------------
# Geometry helpers (simple slope)
# -----------------------------
def slope_surface_y(x, H, beta_deg):
    """
    Piecewise ground surface:
    - From x=0 to x=L: straight slope from (0,H) to (L,0)
    - From x>L: horizontal ground at y=0
    - From x<0: horizontal at y=H (back ground)
    """
    beta = math.radians(beta_deg)
    L = H / math.tan(beta)  # run of slope
    if x < 0:
        return H
    elif x <= L:
        # line: y = H - (H/L)*x
        return H - (H / L) * x
    else:
        return 0.0


def inside_sliding_mass(x, y, H, beta_deg):
    """
    Sliding mass region (soil) is below ground surface and above a base line y = -H (for bounding).
    """
    y_surf = slope_surface_y(x, H, beta_deg)
    return (y <= y_surf) and (y >= -H)


# ------------------------------------------
# Simplified Bishop-ish factor of safety
# (educational / starter-level implementation)
# ------------------------------------------
def bishop_fs_for_circle(H, beta_deg, c, phi_deg, gamma,
                         xc, yc, R,
                         n_slices=25,
                         max_iter=60,
                         tol=1e-4):
    """
    Compute FS for a circular slip surface using a simplified Bishop-type iteration.
    Assumptions:
    - Homogeneous soil: c, phi, gamma
    - No pore pressure (u=0)
    - Circular slip
    - Vertical slices
    - Very simplified slice forces to keep it beginner-friendly

    Returns: FS (float) or None if circle doesn't intersect slope mass properly.
    """
    phi = math.radians(phi_deg)
    beta = math.radians(beta_deg)
    Lslope = H / math.tan(beta)

    # Find intersection of circle with ground surface region in x-range of interest
    # We'll search x from -0.5*Lslope to 1.5*Lslope
    x_min = -0.5 * Lslope
    x_max = 1.5 * Lslope
    xs = np.linspace(x_min, x_max, 600)

    # Circle equation: (x-xc)^2 + (y-yc)^2 = R^2
    # For each x, circle y solutions:
    # y = yc +/- sqrt(R^2 - (x-xc)^2)
    # Slip surface should be the LOWER arc (typically) bounding the mass.
    circle_mask = (R**2 - (xs - xc)**2) >= 0
    if not np.any(circle_mask):
        return None

    xs_valid = xs[circle_mask]
    y_lower = yc - np.sqrt(R**2 - (xs_valid - xc)**2)

    # We need portions where the slip surface is below the ground surface
    # and within a reasonable bounding box
    ys_surf = np.array([slope_surface_y(x, H, beta_deg) for x in xs_valid])
    below_surface = y_lower <= ys_surf

    if np.sum(below_surface) < 10:
        return None

    x_int = xs_valid[below_surface]
    y_int = y_lower[below_surface]

    # Define the slice span over the contiguous region
    # We'll use the min and max x of the region
    xL = np.min(x_int)
    xR = np.max(x_int)

    if xR - xL < 0.2:  # too tiny / invalid
        return None

    # Create slices
    x_edges = np.linspace(xL, xR, n_slices + 1)
    x_mids = 0.5 * (x_edges[:-1] + x_edges[1:])
    b = (xR - xL) / n_slices  # slice width

    # For each slice, compute:
    # height = y_surface(mid) - y_slip(mid)
    # W = gamma * area ~ gamma * height * b   (unit thickness)
    # alpha = inclination of slip surface at mid (tangent angle from horizontal)
    # l = base length ~ b / cos(alpha)
    # Driving ~ W * sin(alpha)
    # Normal ~ W * cos(alpha) (simplified)
    # Shear strength available = c*l + N*tan(phi)
    #
    # Bishop simplified uses an iterative correction involving FS in the denominator.
    # We'll implement a commonly used educational iterative structure:
    #
    # FS = sum( (c*l + (W)*tan(phi)) / (1 + (tan(phi)*tan(alpha))/FS ) ) / sum(W*sin(alpha))
    #
    # (u = 0, N approx W*cos(alpha) folded into the same simplified form)
    #
    # Note: This is intentionally simplified for learning.
    heights = []
    Ws = []
    alphas = []
    ls = []

    for xm in x_mids:
        y_s = slope_surface_y(xm, H, beta_deg)

        # slip y at xm (lower arc)
        inside = (R**2 - (xm - xc)**2) >= 0
        if not inside:
            return None
        y_sl = yc - math.sqrt(R**2 - (xm - xc)**2)

        h = y_s - y_sl
        if h <= 0.01:
            return None

        # slope angle (alpha) from derivative of circle:
        # circle: (x-xc)^2 + (y-yc)^2 = R^2
        # dy/dx = -(x-xc)/(y-yc)
        denom = (y_sl - yc)
        if abs(denom) < 1e-8:
            return None
        dydx = - (xm - xc) / denom
        alpha = math.atan(dydx)  # tangent angle
        # base length along slip surface
        l = b / math.cos(alpha)

        area = h * b
        W = gamma * area

        heights.append(h)
        Ws.append(W)
        alphas.append(alpha)
        ls.append(l)

    Ws = np.array(Ws, dtype=float)
    alphas = np.array(alphas, dtype=float)
    ls = np.array(ls, dtype=float)

    # Driving sum
    drive = np.sum(Ws * np.sin(alphas))
    if drive <= 1e-9:
        return None

    # Iterate FS
    FS = 1.5
    for _ in range(max_iter):
        denom_terms = 1.0 + (np.tan(phi) * np.tan(alphas)) / FS
        resist_terms = (c * ls + Ws * np.tan(phi)) / denom_terms
        FS_new = np.sum(resist_terms) / drive

        if not np.isfinite(FS_new) or FS_new <= 0:
            return None
        if abs(FS_new - FS) < tol:
            FS = FS_new
            break
        FS = FS_new

    return float(FS)


def search_critical_circle(H, beta_deg, c, phi_deg, gamma,
                           n_slices, xc_min, xc_max, yc_min, yc_max,
                           n_xc, n_yc, R_min, R_max, n_R):
    """
    Grid-search circle centers and radii.
    Returns best (min FS) and its parameters.
    """
    best = {
        "FS": None,
        "xc": None,
        "yc": None,
        "R": None
    }

    xcs = np.linspace(xc_min, xc_max, n_xc)
    ycs = np.linspace(yc_min, yc_max, n_yc)
    Rs = np.linspace(R_min, R_max, n_R)

    for xc in xcs:
        for yc in ycs:
            for R in Rs:
                FS = bishop_fs_for_circle(H, beta_deg, c, phi_deg, gamma, xc, yc, R, n_slices=n_slices)
                if FS is None:
                    continue
                if (best["FS"] is None) or (FS < best["FS"]):
                    best.update({"FS": FS, "xc": xc, "yc": yc, "R": R})

    return best


# -----------------------------
# GUI App
# -----------------------------
class SlopeStabilityApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Slope Stability (LEM - Simplified Bishop Search) | Learning GUI")
        self.geometry("1100x700")

        self._build_ui()
        self._build_plot()

    def _build_ui(self):
        left = ttk.Frame(self, padding=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        ttk.Label(left, text="Slope Geometry", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))

        self.H_var = tk.DoubleVar(value=10.0)
        self.beta_var = tk.DoubleVar(value=45.0)

        self._add_entry(left, "Height H (m)", self.H_var)
        self._add_entry(left, "Slope angle β (deg)", self.beta_var)

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(left, text="Soil Parameters", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.c_var = tk.DoubleVar(value=10.0)        # kPa (but we use consistent units with gamma in kN/m^3)
        self.phi_var = tk.DoubleVar(value=30.0)      # degrees
        self.gamma_var = tk.DoubleVar(value=18.0)    # kN/m^3

        self._add_entry(left, "c (kPa = kN/m²)", self.c_var)
        self._add_entry(left, "φ (deg)", self.phi_var)
        self._add_entry(left, "γ (kN/m³)", self.gamma_var)

        ttk.Separator(left).pack(fill="x", pady=8)

        ttk.Label(left, text="Search Settings", font=("Segoe UI", 11, "bold")).pack(anchor="w", pady=(0, 6))
        self.n_slices_var = tk.IntVar(value=25)

        self._add_entry(left, "Number of slices", self.n_slices_var)

        # Search bounds (defaults scale with H when run)
        self.xc_min_var = tk.DoubleVar(value=-10.0)
        self.xc_max_var = tk.DoubleVar(value=25.0)
        self.yc_min_var = tk.DoubleVar(value=-20.0)
        self.yc_max_var = tk.DoubleVar(value=5.0)
        self.R_min_var = tk.DoubleVar(value=8.0)
        self.R_max_var = tk.DoubleVar(value=40.0)

        self.n_xc_var = tk.IntVar(value=18)
        self.n_yc_var = tk.IntVar(value=14)
        self.n_R_var = tk.IntVar(value=14)

        self._add_entry(left, "xc min", self.xc_min_var)
        self._add_entry(left, "xc max", self.xc_max_var)
        self._add_entry(left, "yc min", self.yc_min_var)
        self._add_entry(left, "yc max", self.yc_max_var)
        self._add_entry(left, "R min", self.R_min_var)
        self._add_entry(left, "R max", self.R_max_var)
        self._add_entry(left, "grid xc", self.n_xc_var)
        self._add_entry(left, "grid yc", self.n_yc_var)
        self._add_entry(left, "grid R", self.n_R_var)

        ttk.Separator(left).pack(fill="x", pady=10)

        self.run_btn = ttk.Button(left, text="Run Search (Find Critical FS)", command=self.run_analysis)
        self.run_btn.pack(fill="x", pady=6)

        self.result_lbl = ttk.Label(left, text="FS: --", font=("Segoe UI", 11, "bold"))
        self.result_lbl.pack(anchor="w", pady=(10, 0))

        tip = (
            "Notes:\n"
            "- This is an educational Simplified Bishop-type LEM.\n"
            "- No pore pressure (u=0). Homogeneous soil.\n"
            "- Units: c in kPa (kN/m²), γ in kN/m³, H in m.\n"
        )
        ttk.Label(left, text=tip, justify="left", foreground="#444").pack(anchor="w", pady=(10, 0))

    def _add_entry(self, parent, label, var):
        row = ttk.Frame(parent)
        row.pack(fill="x", pady=2)
        ttk.Label(row, text=label, width=18).pack(side=tk.LEFT)
        ent = ttk.Entry(row, textvariable=var, width=12)
        ent.pack(side=tk.RIGHT)

    def _build_plot(self):
        right = ttk.Frame(self, padding=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.fig = plt.Figure(figsize=(7.5, 5.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title("Slope + Critical Slip Circle")
        self.ax.set_xlabel("x (m)")
        self.ax.set_ylabel("y (m)")
        self.ax.grid(True)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._plot_base_geometry()

    def _plot_base_geometry(self):
        self.ax.clear()
        H = float(self.H_var.get())
        beta = float(self.beta_var.get())
        L = H / math.tan(math.radians(beta))

        xs = np.linspace(-0.5 * L, 1.5 * L, 400)
        ys = [slope_surface_y(x, H, beta) for x in xs]

        self.ax.plot(xs, ys, label="Ground surface")
        # fill a rough soil region
        self.ax.fill_between(xs, ys, [-H]*len(xs), alpha=0.15)

        self.ax.set_aspect("equal", adjustable="box")
        self.ax.set_xlim(min(xs), max(xs))
        self.ax.set_ylim(-H, H * 1.2)
        self.ax.legend()
        self.canvas.draw()

    def run_analysis(self):
        try:
            H = float(self.H_var.get())
            beta = float(self.beta_var.get())
            c = float(self.c_var.get())
            phi = float(self.phi_var.get())
            gamma = float(self.gamma_var.get())

            n_slices = int(self.n_slices_var.get())

            xc_min = float(self.xc_min_var.get())
            xc_max = float(self.xc_max_var.get())
            yc_min = float(self.yc_min_var.get())
            yc_max = float(self.yc_max_var.get())
            R_min = float(self.R_min_var.get())
            R_max = float(self.R_max_var.get())

            n_xc = int(self.n_xc_var.get())
            n_yc = int(self.n_yc_var.get())
            n_R = int(self.n_R_var.get())
        except Exception:
            messagebox.showerror("Input Error", "Please check your inputs.")
            return

        if H <= 0 or gamma <= 0 or n_slices < 10:
            messagebox.showerror("Input Error", "H, γ must be > 0 and slices should be >= 10.")
            return

        self.run_btn.config(state="disabled")
        self.update_idletasks()

        best = search_critical_circle(
            H, beta, c, phi, gamma,
            n_slices=n_slices,
            xc_min=xc_min, xc_max=xc_max, yc_min=yc_min, yc_max=yc_max,
            n_xc=n_xc, n_yc=n_yc,
            R_min=R_min, R_max=R_max, n_R=n_R
        )

        self.run_btn.config(state="normal")

        if best["FS"] is None:
            self.result_lbl.config(text="FS: -- (no valid circle found)")
            self._plot_base_geometry()
            return

        FS = best["FS"]
        self.result_lbl.config(text=f"FS: {FS:.3f}   (xc={best['xc']:.2f}, yc={best['yc']:.2f}, R={best['R']:.2f})")

        # Plot result
        self._plot_base_geometry()

        xc, yc, R = best["xc"], best["yc"], best["R"]
        t = np.linspace(0, 2*np.pi, 600)
        xC = xc + R*np.cos(t)
        yC = yc + R*np.sin(t)

        # show circle
        self.ax.plot(xC, yC, linewidth=1.5, label="Slip circle")

        # highlight lower arc portion within view
        self.ax.legend()
        self.canvas.draw()


if __name__ == "__main__":
    app = SlopeStabilityApp()
    app.mainloop()
