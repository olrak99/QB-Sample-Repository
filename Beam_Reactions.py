import tkinter as tk
from tkinter import ttk, messagebox


def compute_reactions():
    try:
        L = float(span_var.get())
        if L <= 0:
            raise ValueError("Span L must be > 0.")

        load_type = load_type_var.get()

        if load_type == "Point Load (P at a)":
            P = float(P_var.get())
            a = float(a_var.get())
            if P < 0:
                raise ValueError("Point load P must be ≥ 0.")
            if not (0 <= a <= L):
                raise ValueError("Distance a must be between 0 and L.")

            # Simply supported beam: A at x=0, B at x=L
            Rb = P * a / L
            Ra = P - Rb
            total_load = P

        elif load_type == "UDL (w over full span)":
            w = float(w_var.get())
            if w < 0:
                raise ValueError("UDL w must be ≥ 0.")

            total_load = w * L
            Ra = total_load / 2
            Rb = total_load / 2

        else:
            raise ValueError("Please select a load type.")

        # Display results
        Ra_out.set(f"{Ra:.4f}")
        Rb_out.set(f"{Rb:.4f}")
        total_out.set(f"{total_load:.4f}")

    except ValueError as e:
        messagebox.showerror("Input Error", str(e))
    except Exception:
        messagebox.showerror("Error", "Something went wrong. Please check inputs.")


def update_inputs(*_):
    """Show/hide inputs depending on load type."""
    lt = load_type_var.get()

    # Hide all first
    point_frame.grid_remove()
    udl_frame.grid_remove()

    if lt == "Point Load (P at a)":
        point_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))
    elif lt == "UDL (w over full span)":
        udl_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=(0, 10))


# ---------------- GUI ----------------
root = tk.Tk()
root.title("Simple Beam Support Reactions (Simply Supported)")
root.resizable(False, False)

main = ttk.Frame(root, padding=12)
main.grid(row=0, column=0, sticky="nsew")

# Variables
span_var = tk.StringVar(value="6.0")
load_type_var = tk.StringVar(value="Point Load (P at a)")

P_var = tk.StringVar(value="10.0")   # kN
a_var = tk.StringVar(value="3.0")    # m

w_var = tk.StringVar(value="2.0")    # kN/m

Ra_out = tk.StringVar(value="-")
Rb_out = tk.StringVar(value="-")
total_out = tk.StringVar(value="-")

# Row 0: Span
ttk.Label(main, text="Beam Span, L (m):").grid(row=0, column=0, sticky="w")
ttk.Entry(main, textvariable=span_var, width=18).grid(row=0, column=1, sticky="w")

# Row 1: Load type
ttk.Label(main, text="Load Type:").grid(row=1, column=0, sticky="w", pady=(8, 2))
load_combo = ttk.Combobox(
    main,
    textvariable=load_type_var,
    values=["Point Load (P at a)", "UDL (w over full span)"],
    state="readonly",
    width=24
)
load_combo.grid(row=1, column=1, sticky="w", pady=(8, 2))
load_combo.bind("<<ComboboxSelected>>", update_inputs)

# Row 2: Dynamic input frames
point_frame = ttk.LabelFrame(main, text="Point Load Inputs", padding=10)
ttk.Label(point_frame, text="Point Load, P (kN):").grid(row=0, column=0, sticky="w")
ttk.Entry(point_frame, textvariable=P_var, width=18).grid(row=0, column=1, sticky="w", padx=(8, 0))

ttk.Label(point_frame, text="Distance from left support, a (m):").grid(row=1, column=0, sticky="w", pady=(6, 0))
ttk.Entry(point_frame, textvariable=a_var, width=18).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

udl_frame = ttk.LabelFrame(main, text="UDL Inputs", padding=10)
ttk.Label(udl_frame, text="UDL, w (kN/m):").grid(row=0, column=0, sticky="w")
ttk.Entry(udl_frame, textvariable=w_var, width=18).grid(row=0, column=1, sticky="w", padx=(8, 0))

# Show default
update_inputs()

# Buttons
btns = ttk.Frame(main)
btns.grid(row=3, column=0, columnspan=2, sticky="ew")

ttk.Button(btns, text="Calculate Reactions", command=compute_reactions).grid(row=0, column=0, padx=(0, 8), pady=6)
ttk.Button(btns, text="Clear Outputs", command=lambda: (Ra_out.set("-"), Rb_out.set("-"), total_out.set("-"))).grid(row=0, column=1, pady=6)

# Outputs
out = ttk.LabelFrame(main, text="Results", padding=10)
out.grid(row=4, column=0, columnspan=2, sticky="ew", padx=0, pady=(6, 0))

ttk.Label(out, text="Left Reaction, Ra (kN):").grid(row=0, column=0, sticky="w")
ttk.Label(out, textvariable=Ra_out, font=("Segoe UI", 10, "bold")).grid(row=0, column=1, sticky="w", padx=(8, 0))

ttk.Label(out, text="Right Reaction, Rb (kN):").grid(row=1, column=0, sticky="w", pady=(6, 0))
ttk.Label(out, textvariable=Rb_out, font=("Segoe UI", 10, "bold")).grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

ttk.Label(out, text="Total Load (kN):").grid(row=2, column=0, sticky="w", pady=(6, 0))
ttk.Label(out, textvariable=total_out).grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(6, 0))

# Small note
note = ttk.Label(
    main,
    text="Assumes simply supported beam with supports at x=0 and x=L.\n"
         "Point load: P at distance a from left. UDL: w over full span.",
    foreground="gray"
)
note.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

root.mainloop()
