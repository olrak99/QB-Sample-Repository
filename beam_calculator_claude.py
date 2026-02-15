"""
==============================================================
  Simply Supported Beam Reaction Calculator
  VS Code Dark Theme  —  Python / Tkinter GUI

  Requirements : Python 3.6+  (tkinter ships with Python)
  Run          : python beam_calculator.py

  Supported loads:
    • Point Load  – magnitude (kN) at position x from A
    • UDL         – intensity (kN/m) over [start, end]
    • Moment      – applied moment (kN·m) at position x
==============================================================
"""

import tkinter as tk
from tkinter import ttk


# ──────────────────────────────────────────────────────────────
#  VS Code Color Palette
# ──────────────────────────────────────────────────────────────
BG        = "#1e1e1e"
SIDEBAR   = "#252526"
PANEL     = "#2d2d30"
BORDER    = "#3e3e42"
ACCENT    = "#569cd6"
GREEN     = "#4ec9b0"
YELLOW    = "#dcdcaa"
ORANGE    = "#ce9178"
RED       = "#f44747"
PURPLE    = "#c586c0"
TEXT      = "#d4d4d4"
MUTED     = "#858585"
INPUTBG   = "#3c3c3c"
BTNBLUE   = "#0e639c"
BTNGREEN  = "#1a7a1a"
BTNRED    = "#8b2020"
STATUSBG  = "#007acc"
HDRBG     = "#383838"
ROWALT    = "#252527"


# ──────────────────────────────────────────────────────────────
#  Engineering Computation
# ──────────────────────────────────────────────────────────────
def compute_reactions(L, loads):
    """
    Static equilibrium for a simply supported beam.
      sum_Fy  = 0  =>  Ra + Rb = total vertical load
      sum_M_A = 0  =>  Rb = (sum of moments about A) / L
    Returns (Ra, Rb, total_fy).
    """
    total_fy = 0.0
    moment_A = 0.0

    for ld in loads:
        t = ld["type"]
        if t == "Point Load":
            P = float(ld["magnitude"])
            a = float(ld["position"])
            total_fy += P
            moment_A += P * a

        elif t == "UDL":
            w   = float(ld["intensity"])
            s   = float(ld["start"])
            e   = float(ld["end"])
            W   = w * (e - s)
            cen = (s + e) / 2.0
            total_fy += W
            moment_A += W * cen

        elif t == "Moment":
            M = float(ld["magnitude"])
            moment_A += M      # pure moment: no vertical force

    Rb = moment_A / L
    Ra = total_fy - Rb
    return Ra, Rb, total_fy


# ──────────────────────────────────────────────────────────────
#  Beam Diagram Canvas
# ──────────────────────────────────────────────────────────────
class BeamDiagram(tk.Canvas):
    MX = 80    # horizontal margin px
    BY = 90    # beam centre y px

    def __init__(self, parent, **kw):
        kw.setdefault("bg", "#1a1a1a")
        kw.setdefault("height", 150)
        kw.setdefault("highlightthickness", 1)
        kw.setdefault("highlightbackground", BORDER)
        super().__init__(parent, **kw)
        self._L         = 10.0
        self._loads     = []
        self._reactions = None
        self.bind("<Configure>", lambda _e: self._draw())

    def refresh(self, L, loads, reactions=None):
        self._L         = max(float(L), 0.01)
        self._loads     = loads
        self._reactions = reactions
        self._draw()

    def _draw(self):
        self.delete("all")
        W  = self.winfo_width()
        H  = self.winfo_height()
        if W < 20:
            self.after(60, self._draw)
            return

        mx = self.MX
        by = self.BY
        L  = self._L
        sc = (W - 2 * mx) / L

        def px(pos):
            return mx + pos * sc

        # beam bar
        self.create_rectangle(mx, by - 7, W - mx, by + 7,
                               fill="#4a4a4f", outline="#666")
        self.create_text(W // 2, by + 22,
                         text="L = {} m".format(L),
                         fill=MUTED, font=("Consolas", 9))

        # support A (pin triangle)
        ax = mx
        self.create_polygon(ax, by + 7, ax - 13, by + 27, ax + 13, by + 27,
                            fill=GREEN, outline=GREEN)
        self.create_line(ax - 15, by + 29, ax + 15, by + 29,
                         fill=GREEN, width=2)
        self.create_text(ax, by + 37, text="A",
                         fill=GREEN, font=("Consolas", 8, "bold"))

        # support B (roller)
        bx = W - mx
        self.create_polygon(bx, by + 7, bx - 13, by + 27, bx + 13, by + 27,
                            fill=ORANGE, outline=ORANGE)
        for cx in (bx - 9, bx, bx + 9):
            self.create_oval(cx - 4, by + 29, cx + 4, by + 37,
                             outline=ORANGE, width=2)
        self.create_text(bx, by + 45, text="B",
                         fill=ORANGE, font=("Consolas", 8, "bold"))

        # reactions
        if self._reactions:
            Ra, Rb, _ = self._reactions
            self.create_line(ax, by + 55, ax, by + 9,
                             fill=GREEN, width=2,
                             arrow=tk.LAST, arrowshape=(8, 10, 4))
            self.create_text(ax, by + 64,
                             text="RA={:.3f} kN".format(Ra),
                             fill=GREEN, font=("Consolas", 8))
            self.create_line(bx, by + 55, bx, by + 9,
                             fill=ORANGE, width=2,
                             arrow=tk.LAST, arrowshape=(8, 10, 4))
            self.create_text(bx, by + 64,
                             text="RB={:.3f} kN".format(Rb),
                             fill=ORANGE, font=("Consolas", 8))

        # loads
        for ld in self._loads:
            t = ld["type"]
            if t == "Point Load":
                x = px(ld["position"])
                self.create_line(x, by - 48, x, by - 8,
                                 fill=ACCENT, width=2,
                                 arrow=tk.LAST, arrowshape=(8, 10, 4))
                self.create_text(x, by - 56,
                                 text="{} kN".format(ld["magnitude"]),
                                 fill=ACCENT, font=("Consolas", 8))

            elif t == "UDL":
                x1 = px(ld["start"])
                x2 = px(ld["end"])
                self.create_line(x1, by - 28, x2, by - 28,
                                 fill=YELLOW, width=2)
                span  = x2 - x1
                count = max(3, int(span // 16))
                for j in range(count + 1):
                    ax2 = x1 + j * span / count
                    self.create_line(ax2, by - 28, ax2, by - 8,
                                     fill=YELLOW, width=1,
                                     arrow=tk.LAST, arrowshape=(5, 7, 3))
                self.create_text((x1 + x2) / 2, by - 38,
                                 text="{} kN/m".format(ld["intensity"]),
                                 fill=YELLOW, font=("Consolas", 8))

            elif t == "Moment":
                x = px(ld["position"])
                self.create_text(x, by - 18, text="[M]",
                                 fill=PURPLE, font=("Consolas", 11, "bold"))
                self.create_text(x, by - 36,
                                 text="{} kN.m".format(ld["magnitude"]),
                                 fill=PURPLE, font=("Consolas", 8))


# ──────────────────────────────────────────────────────────────
#  Main Application
# ──────────────────────────────────────────────────────────────
class BeamApp(tk.Tk):

    def __init__(self):
        super().__init__()
        self.title("beam_calculator.py  -  Simply Supported Beam  VS Code")
        self.geometry("980x820")
        self.minsize(800, 600)
        self.configure(bg=BG)

        self._loads   = []
        self._results = None

        self._build_titlebar()
        self._build_tabbar()

        body = tk.Frame(self, bg=BG)
        body.pack(fill=tk.BOTH, expand=True)
        self._build_sidebar(body)
        self._build_editor(body)

        self._build_statusbar()

        # status depends on _beamlen_var existing
        self.after(100, self._update_status)

    # ── chrome ────────────────────────────────────────────────
    def _build_titlebar(self):
        bar = tk.Frame(self, bg="#323233", height=28)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        tk.Label(bar, text="  [beam_calculator.py]  -  VS Code  ",
                 bg="#323233", fg=MUTED,
                 font=("Consolas", 10)).pack(side=tk.LEFT)
        for name in ("File", "Edit", "View", "Run", "Terminal", "Help"):
            tk.Label(bar, text=name, bg="#323233", fg=TEXT,
                     font=("Consolas", 10)).pack(side=tk.LEFT, padx=6)

    def _build_tabbar(self):
        bar = tk.Frame(self, bg=SIDEBAR, height=34)
        bar.pack(fill=tk.X)
        bar.pack_propagate(False)
        tab = tk.Frame(bar, bg=BG)
        tab.pack(side=tk.LEFT)
        tk.Label(tab, text=" [py] ", bg=BG, fg=YELLOW,
                 font=("Consolas", 11)).pack(side=tk.LEFT, pady=5)
        tk.Label(tab, text="beam_calculator.py ",
                 bg=BG, fg=TEXT, font=("Consolas", 11)
                 ).pack(side=tk.LEFT, pady=5)

    def _build_statusbar(self):
        bar = tk.Frame(self, bg=STATUSBG, height=22)
        bar.pack(fill=tk.X, side=tk.BOTTOM)
        bar.pack_propagate(False)
        tk.Label(bar, text="  main  |  Beam Calculator v2.0  ",
                 bg=STATUSBG, fg="white",
                 font=("Consolas", 9)).pack(side=tk.LEFT)
        self._status_var = tk.StringVar(value="")
        tk.Label(bar, textvariable=self._status_var,
                 bg=STATUSBG, fg="white",
                 font=("Consolas", 9)).pack(side=tk.RIGHT, padx=10)

    def _update_status(self):
        try:
            L = self._beamlen_var.get()
        except Exception:
            L = "?"
        n     = len(self._loads)
        state = "Solved" if self._results else "Ready"
        self._status_var.set(
            "{} load{}  |  L = {} m  |  {}  ".format(
                n, "s" if n != 1 else "", L, state)
        )

    # ── sidebar ───────────────────────────────────────────────
    def _build_sidebar(self, parent):
        sb = tk.Frame(parent, bg=SIDEBAR, width=200)
        sb.pack(side=tk.LEFT, fill=tk.Y)
        sb.pack_propagate(False)

        def hdr(text):
            tk.Label(sb, text=text, bg=SIDEBAR, fg=MUTED,
                     font=("Consolas", 9, "bold"),
                     anchor=tk.W).pack(fill=tk.X, padx=12, pady=(8, 2))
            tk.Frame(sb, bg=BORDER, height=1).pack(fill=tk.X)

        hdr("EXPLORER")
        for txt, col, px, wt in [
            ("BEAM_PROJECT",          TEXT,   10, "bold"),
            ("|- beam_calculator.py", ACCENT, 20, "normal"),
            ("|- supports.json",      MUTED,  20, "normal"),
            ("`- loads.csv",          MUTED,  20, "normal"),
        ]:
            tk.Label(sb, text=txt, bg=SIDEBAR, fg=col,
                     font=("Consolas", 10, wt),
                     anchor=tk.W).pack(fill=tk.X, padx=px, pady=1)

        tk.Frame(sb, bg=BORDER, height=1).pack(fill=tk.X, pady=(8, 2))
        hdr("OUTLINE")
        for fn in ("simply_supported_beam()", "add_load()",
                   "compute_reactions()",    "draw_diagram()"):
            row = tk.Frame(sb, bg=SIDEBAR)
            row.pack(fill=tk.X, padx=8, pady=1)
            tk.Label(row, text="f ", bg=SIDEBAR, fg=GREEN,
                     font=("Consolas", 9)).pack(side=tk.LEFT)
            tk.Label(row, text=fn, bg=SIDEBAR, fg=YELLOW,
                     font=("Consolas", 10)).pack(side=tk.LEFT)

    # ── scrollable editor ─────────────────────────────────────
    def _build_editor(self, parent):
        outer = tk.Frame(parent, bg=BG)
        outer.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        vbar = tk.Scrollbar(outer, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)

        self._sc = tk.Canvas(outer, bg=BG, highlightthickness=0,
                             yscrollcommand=vbar.set)
        self._sc.pack(fill=tk.BOTH, expand=True)
        vbar.config(command=self._sc.yview)

        self._inner = tk.Frame(self._sc, bg=BG)
        self._win   = self._sc.create_window(
            (0, 0), window=self._inner, anchor=tk.NW)

        self._inner.bind("<Configure>",
                         lambda _e: self._sc.configure(
                             scrollregion=self._sc.bbox("all")))
        self._sc.bind("<Configure>",
                      lambda e: self._sc.itemconfig(
                          self._win, width=e.width))

        # mouse-wheel scroll (Windows + macOS + Linux)
        self._sc.bind_all("<MouseWheel>",
                          lambda e: self._sc.yview_scroll(
                              int(-1 * (e.delta / 120)), "units"))
        self._sc.bind_all("<Button-4>",
                          lambda _e: self._sc.yview_scroll(-1, "units"))
        self._sc.bind_all("<Button-5>",
                          lambda _e: self._sc.yview_scroll(1, "units"))

        # build sections
        self._sec_beam   = self._make_section(
            [(">> ", GREEN), ("beam_setup", YELLOW), ("()  ", TEXT),
             ("# Simply Supported Beam", MUTED)])
        self._sec_load   = self._make_section(
            [("+ ", ACCENT), ("add_load", YELLOW), ("()", TEXT)])
        self._sec_table  = self._make_section(
            [("# ", GREEN), ("loads[ ]", TEXT)])
        self._sec_result = self._make_section(
            [(">> ", GREEN), ("compute_reactions", GREEN), ("()", TEXT)])

        self._build_beam_section()
        self._build_addload_section()
        self._render_table()
        self._render_results()

    def _make_section(self, title_parts):
        """Card with a dark header row and a body frame."""
        card = tk.Frame(self._inner, bg=PANEL,
                        highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill=tk.X, padx=20, pady=6)
        hdr = tk.Frame(card, bg=HDRBG)
        hdr.pack(fill=tk.X)
        for txt, col in title_parts:
            tk.Label(hdr, text=txt, bg=HDRBG, fg=col,
                     font=("Consolas", 10)).pack(side=tk.LEFT,
                                                  padx=4, pady=4)
        body = tk.Frame(card, bg=PANEL)
        body.pack(fill=tk.X, padx=14, pady=10)
        return body

    def _entry_row(self, parent, label, lcolor, hint, row):
        tk.Label(parent, text=label, bg=PANEL, fg=lcolor,
                 font=("Consolas", 10), width=22,
                 anchor=tk.W).grid(row=row, column=0, sticky=tk.W, pady=3)
        var = tk.StringVar()
        ent = tk.Entry(parent, textvariable=var,
                       bg=INPUTBG, fg=TEXT, insertbackground=TEXT,
                       relief=tk.FLAT, font=("Consolas", 10), width=12,
                       highlightthickness=1, highlightbackground=BORDER)
        ent.grid(row=row, column=1, sticky=tk.W, padx=8, pady=3)
        tk.Label(parent, text=hint, bg=PANEL, fg=MUTED,
                 font=("Consolas", 9)).grid(row=row, column=2, sticky=tk.W)
        return var

    # ── beam section ──────────────────────────────────────────
    def _build_beam_section(self):
        b = self._sec_beam
        tk.Label(b, text="beam_length  =", bg=PANEL, fg=ACCENT,
                 font=("Consolas", 10), width=22,
                 anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=3)
        self._beamlen_var = tk.StringVar(value="10")
        tk.Entry(b, textvariable=self._beamlen_var,
                 bg=INPUTBG, fg=ORANGE, insertbackground=TEXT,
                 relief=tk.FLAT, font=("Consolas", 10), width=12,
                 highlightthickness=1, highlightbackground=BORDER
                 ).grid(row=0, column=1, sticky=tk.W, padx=8)
        tk.Label(b, text="# metres", bg=PANEL, fg=MUTED,
                 font=("Consolas", 9)).grid(row=0, column=2, sticky=tk.W)

        self._beamlen_var.trace("w", lambda *_: self._refresh_diagram())

        self._diagram = BeamDiagram(b, height=150)
        self._diagram.grid(row=1, column=0, columnspan=4,
                           sticky=tk.EW, pady=(10, 0))
        b.columnconfigure(3, weight=1)

    # ── add load section ──────────────────────────────────────
    def _build_addload_section(self):
        b = self._sec_load

        tk.Label(b, text="load_type    =", bg=PANEL, fg=ACCENT,
                 font=("Consolas", 10), width=22,
                 anchor=tk.W).grid(row=0, column=0, sticky=tk.W, pady=3)
        self._loadtype_var = tk.StringVar(value="Point Load")
        ttk.Combobox(b, textvariable=self._loadtype_var,
                     values=["Point Load", "UDL", "Moment"],
                     state="readonly", width=26,
                     font=("Consolas", 10)
                     ).grid(row=0, column=1, columnspan=2,
                             sticky=tk.W, padx=8)
        self._loadtype_var.trace("w", lambda *_: self._refresh_fields())

        self._fields = tk.Frame(b, bg=PANEL)
        self._fields.grid(row=1, column=0, columnspan=4,
                          sticky=tk.EW, pady=(4, 0))
        self._refresh_fields()

        # buttons
        br = tk.Frame(b, bg=PANEL)
        br.grid(row=2, column=0, columnspan=4, sticky=tk.W, pady=(12, 0))
        tk.Button(br, text="+ Add Load",
                  bg=BTNBLUE, fg="white",
                  activebackground="#1177bb", activeforeground="white",
                  relief=tk.FLAT, font=("Consolas", 10),
                  padx=12, pady=5, cursor="hand2",
                  command=self._add_load).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(br, text="X  Clear All",
                  bg=BTNRED, fg="white",
                  activebackground="#a03030", activeforeground="white",
                  relief=tk.FLAT, font=("Consolas", 10),
                  padx=12, pady=5, cursor="hand2",
                  command=self._clear_all).pack(side=tk.LEFT, padx=(0, 8))
        tk.Button(br, text=">>  Compute Reactions",
                  bg=BTNGREEN, fg="white",
                  activebackground="#218a21", activeforeground="white",
                  relief=tk.FLAT, font=("Consolas", 10, "bold"),
                  padx=14, pady=5, cursor="hand2",
                  command=self._compute).pack(side=tk.LEFT)

        self._err_var = tk.StringVar()
        tk.Label(b, textvariable=self._err_var,
                 bg=PANEL, fg=RED,
                 font=("Consolas", 9)
                 ).grid(row=3, column=0, columnspan=4,
                         sticky=tk.W, pady=(6, 0))

    def _refresh_fields(self, *_):
        for w in self._fields.winfo_children():
            w.destroy()
        t = self._loadtype_var.get()
        if t == "Point Load":
            self._f_mag = self._entry_row(
                self._fields, "magnitude    =", ACCENT,
                "# kN  (downward positive)", 0)
            self._f_pos = self._entry_row(
                self._fields, "position     =", ACCENT,
                "# m from support A", 1)
        elif t == "UDL":
            self._f_int   = self._entry_row(
                self._fields, "intensity    =", YELLOW, "# kN/m", 0)
            self._f_start = self._entry_row(
                self._fields, "start        =", YELLOW, "# m from A", 1)
            self._f_end   = self._entry_row(
                self._fields, "end          =", YELLOW, "# m from A", 2)
        elif t == "Moment":
            self._f_mag = self._entry_row(
                self._fields, "magnitude    =", PURPLE,
                "# kN.m  (counter-clockwise positive)", 0)
            self._f_pos = self._entry_row(
                self._fields, "position     =", PURPLE,
                "# m from support A", 1)

    # ── loads table ───────────────────────────────────────────
    def _render_table(self):
        for w in self._sec_table.winfo_children():
            w.destroy()
        if not self._loads:
            tk.Label(self._sec_table,
                     text="  # no loads added yet",
                     bg=PANEL, fg=MUTED,
                     font=("Consolas", 10, "italic")
                     ).pack(anchor=tk.W, pady=4)
            return

        for c, (hd, wd) in enumerate(
                zip(["idx", "type", "parameters", "del"],
                    [6, 14, 56, 4])):
            tk.Label(self._sec_table, text=hd, bg=HDRBG, fg=MUTED,
                     font=("Consolas", 9, "bold"), width=wd,
                     anchor=tk.W).grid(row=0, column=c,
                                        padx=2, pady=(0, 4))

        tc = {"Point Load": ACCENT, "UDL": YELLOW, "Moment": PURPLE}
        for i, ld in enumerate(self._loads):
            rbg   = BG if i % 2 == 0 else ROWALT
            color = tc.get(ld["type"], TEXT)
            tk.Label(self._sec_table, text="[{}]".format(i),
                     bg=rbg, fg=MUTED, font=("Consolas", 10),
                     width=6, anchor=tk.W
                     ).grid(row=i+1, column=0, padx=2, pady=1)
            tk.Label(self._sec_table, text=ld["type"],
                     bg=rbg, fg=color, font=("Consolas", 10),
                     width=14, anchor=tk.W
                     ).grid(row=i+1, column=1, padx=2, pady=1)

            t = ld["type"]
            if t == "Point Load":
                params = "P={} kN  @  x={} m".format(
                    ld["magnitude"], ld["position"])
            elif t == "UDL":
                params = "w={} kN/m  from {} m  to {} m".format(
                    ld["intensity"], ld["start"], ld["end"])
            else:
                params = "M={} kN.m  @  x={} m".format(
                    ld["magnitude"], ld["position"])

            tk.Label(self._sec_table, text=params,
                     bg=rbg, fg=TEXT, font=("Consolas", 10),
                     width=56, anchor=tk.W
                     ).grid(row=i+1, column=2, padx=2, pady=1)
            tk.Button(self._sec_table, text="X",
                      bg=rbg, fg=RED, relief=tk.FLAT,
                      font=("Consolas", 9), cursor="hand2",
                      command=lambda ix=i: self._delete_load(ix)
                      ).grid(row=i+1, column=3, padx=2, pady=1)

    # ── results ───────────────────────────────────────────────
    def _render_results(self):
        for w in self._sec_result.winfo_children():
            w.destroy()
        if self._results is None:
            tk.Label(self._sec_result,
                     text="  # Press  >>  Compute Reactions  to solve",
                     bg=PANEL, fg=MUTED,
                     font=("Consolas", 10, "italic")
                     ).pack(anchor=tk.W, pady=6)
            return

        Ra, Rb, total = self._results
        ok = abs(Ra + Rb - total) < 1e-6
        L  = self._beamlen_var.get()

        out = tk.Frame(self._sec_result, bg="#1a1a1a",
                       highlightthickness=1, highlightbackground=BORDER)
        out.pack(fill=tk.X)

        lines = [
            ("# sum_Fy=0  |  sum_M_A=0  |  L={} m".format(L), MUTED),
            ("", TEXT),
            ("RA  =  {:+.4f}  kN    # Reaction at A  (pin, left)".format(Ra),
             GREEN),
            ("RB  =  {:+.4f}  kN    # Reaction at B  (roller, right)".format(Rb),
             ORANGE),
            ("", TEXT),
            ("Total applied load  =  {:.4f} kN".format(total), TEXT),
            ("RA + RB             =  {:.4f} kN    {}".format(
                Ra + Rb,
                "CHECK OK - Equilibrium verified" if ok
                else "ERROR - Check inputs"),
             GREEN if ok else RED),
        ]
        for txt, col in lines:
            tk.Label(out, text="  {}".format(txt),
                     bg="#1a1a1a", fg=col,
                     font=("Consolas", 11), anchor=tk.W
                     ).pack(fill=tk.X, pady=2)

    # ── actions ───────────────────────────────────────────────
    def _get_L(self):
        try:
            L = float(self._beamlen_var.get())
            if L > 0:
                return L
        except (ValueError, AttributeError):
            pass
        return None

    def _refresh_diagram(self):
        L = self._get_L()
        if L and hasattr(self, "_diagram"):
            self._diagram.refresh(L, self._loads, self._results)

    def _add_load(self):
        self._err_var.set("")
        L = self._get_L()
        if L is None:
            self._err_var.set("  Enter a valid beam length first.")
            return
        t = self._loadtype_var.get()
        try:
            if t == "Point Load":
                mag = float(self._f_mag.get())
                pos = float(self._f_pos.get())
                if not (0 <= pos <= L):
                    raise ValueError(
                        "Position must be 0 to {} m.".format(L))
                self._loads.append({"type": t,
                                    "magnitude": mag, "position": pos})

            elif t == "UDL":
                w = float(self._f_int.get())
                s = float(self._f_start.get())
                e = float(self._f_end.get())
                if s < 0 or e > L or s >= e:
                    raise ValueError(
                        "UDL start/end must satisfy 0<=start<end<={}.".format(L))
                self._loads.append({"type": t,
                                    "intensity": w, "start": s, "end": e})

            elif t == "Moment":
                mag = float(self._f_mag.get())
                pos = float(self._f_pos.get())
                if not (0 <= pos <= L):
                    raise ValueError(
                        "Position must be 0 to {} m.".format(L))
                self._loads.append({"type": t,
                                    "magnitude": mag, "position": pos})

        except ValueError as exc:
            msg = str(exc) if str(exc) else "Enter valid numeric values."
            self._err_var.set("  {}".format(msg))
            return

        self._results = None
        self._refresh_fields()
        self._render_table()
        self._render_results()
        self._refresh_diagram()
        self._update_status()

    def _delete_load(self, idx):
        self._loads.pop(idx)
        self._results = None
        self._render_table()
        self._render_results()
        self._refresh_diagram()
        self._update_status()

    def _clear_all(self):
        self._loads   = []
        self._results = None
        self._render_table()
        self._render_results()
        self._refresh_diagram()
        self._update_status()

    def _compute(self):
        self._err_var.set("")
        L = self._get_L()
        if L is None:
            self._err_var.set("  Enter a valid beam length.")
            return
        if not self._loads:
            self._err_var.set("  Add at least one load first.")
            return
        try:
            Ra, Rb, total = compute_reactions(L, self._loads)
            self._results = (Ra, Rb, total)
        except Exception as exc:
            self._err_var.set("  {}".format(exc))
            return
        self._render_results()
        self._refresh_diagram()
        self._update_status()


# ──────────────────────────────────────────────────────────────
#  Entry Point
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    app = BeamApp()

    # style the combobox dropdown to match dark theme
    style = ttk.Style(app)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TCombobox",
                    fieldbackground=INPUTBG,
                    background=INPUTBG,
                    foreground=TEXT,
                    selectbackground=INPUTBG,
                    selectforeground=TEXT,
                    bordercolor=BORDER,
                    arrowcolor=MUTED)
    style.map("TCombobox",
              fieldbackground=[("readonly", INPUTBG)],
              foreground=[("readonly", TEXT)],
              selectbackground=[("readonly", INPUTBG)])

    app.mainloop()
