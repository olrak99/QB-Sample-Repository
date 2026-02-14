import sys
import math

import pyvista as pv
from pyvistaqt import QtInteractor

from PyQt5 import QtWidgets, QtCore


def reactions_point_load(P: float, a: float, L: float):
    # Simply supported: support A at x=0, support B at x=L
    # Moment about A: Rb*L = P*a => Rb = P*a/L ; Ra = P - Rb
    Rb = P * a / L
    Ra = P - Rb
    return Ra, Rb, P


def reactions_udl(w: float, L: float):
    total = w * L
    Ra = total / 2.0
    Rb = total / 2.0
    return Ra, Rb, total


class BeamApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Simple Beam Support Reactions (PyVista GUI)")
        self.resize(1100, 700)

        # ----------------- Central: 3D View -----------------
        self.plotter = QtInteractor(self)
        self.setCentralWidget(self.plotter.interactor)

        # Data (default)
        self.load_type = "Point Load"
        self.L = 6.0
        self.P = 10.0
        self.a = 3.0
        self.w = 2.0

        # Scene actors (we keep references so we can update cleanly)
        self.beam_actor = None
        self.supportA_actor = None
        self.supportB_actor = None
        self.load_actor = None
        self.text_actor_id = None

        # ----------------- Right Panel (Controls) -----------------
        self._build_controls()

        # Build initial scene
        self._draw_scene()
        self._update_results()

        # Camera
        self.plotter.view_isometric()
        self.plotter.add_axes()

    def _build_controls(self):
        dock = QtWidgets.QDockWidget("Controls", self)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea | QtCore.Qt.LeftDockWidgetArea)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

        panel = QtWidgets.QWidget()
        dock.setWidget(panel)

        layout = QtWidgets.QVBoxLayout(panel)
        layout.setSpacing(10)

        # Load type selector
        self.cmb_type = QtWidgets.QComboBox()
        self.cmb_type.addItems(["Point Load", "UDL"])
        self.cmb_type.currentTextChanged.connect(self._on_type_changed)
        layout.addWidget(QtWidgets.QLabel("Load Type"))
        layout.addWidget(self.cmb_type)

        # Span input
        self.ed_L = QtWidgets.QDoubleSpinBox()
        self.ed_L.setRange(0.1, 1e6)
        self.ed_L.setDecimals(3)
        self.ed_L.setValue(self.L)
        self.ed_L.setSuffix(" m")
        self.ed_L.valueChanged.connect(self._on_params_changed)
        layout.addWidget(QtWidgets.QLabel("Span, L"))
        layout.addWidget(self.ed_L)

        # Point load inputs
        self.grp_point = QtWidgets.QGroupBox("Point Load Inputs")
        gpl = QtWidgets.QFormLayout(self.grp_point)

        self.ed_P = QtWidgets.QDoubleSpinBox()
        self.ed_P.setRange(0.0, 1e9)
        self.ed_P.setDecimals(3)
        self.ed_P.setValue(self.P)
        self.ed_P.setSuffix(" kN")
        self.ed_P.valueChanged.connect(self._on_params_changed)

        self.ed_a = QtWidgets.QDoubleSpinBox()
        self.ed_a.setRange(0.0, 1e6)
        self.ed_a.setDecimals(3)
        self.ed_a.setValue(self.a)
        self.ed_a.setSuffix(" m")
        self.ed_a.valueChanged.connect(self._on_params_changed)

        gpl.addRow("P", self.ed_P)
        gpl.addRow("a (from left)", self.ed_a)
        layout.addWidget(self.grp_point)

        # UDL inputs
        self.grp_udl = QtWidgets.QGroupBox("UDL Inputs")
        gul = QtWidgets.QFormLayout(self.grp_udl)

        self.ed_w = QtWidgets.QDoubleSpinBox()
        self.ed_w.setRange(0.0, 1e9)
        self.ed_w.setDecimals(3)
        self.ed_w.setValue(self.w)
        self.ed_w.setSuffix(" kN/m")
        self.ed_w.valueChanged.connect(self._on_params_changed)

        gul.addRow("w", self.ed_w)
        layout.addWidget(self.grp_udl)

        # Results display
        self.grp_res = QtWidgets.QGroupBox("Results")
        grl = QtWidgets.QFormLayout(self.grp_res)

        self.lb_Ra = QtWidgets.QLabel("-")
        self.lb_Rb = QtWidgets.QLabel("-")
        self.lb_total = QtWidgets.QLabel("-")

        grl.addRow("Ra (kN)", self.lb_Ra)
        grl.addRow("Rb (kN)", self.lb_Rb)
        grl.addRow("Total Load (kN)", self.lb_total)

        layout.addWidget(self.grp_res)

        # Buttons
        btn_row = QtWidgets.QHBoxLayout()
        btn_redraw = QtWidgets.QPushButton("Redraw View")
        btn_redraw.clicked.connect(self._draw_scene)

        btn_fit = QtWidgets.QPushButton("Fit")
        btn_fit.clicked.connect(self.plotter.reset_camera)

        btn_row.addWidget(btn_redraw)
        btn_row.addWidget(btn_fit)
        layout.addLayout(btn_row)

        layout.addStretch(1)

        # Set initial visibility for groups
        self._sync_group_visibility()

    def _sync_group_visibility(self):
        is_point = (self.load_type == "Point Load")
        self.grp_point.setVisible(is_point)
        self.grp_udl.setVisible(not is_point)

    def _on_type_changed(self, text):
        self.load_type = text
        self._sync_group_visibility()
        self._on_params_changed()

    def _on_params_changed(self, *_):
        self.L = float(self.ed_L.value())
        self.P = float(self.ed_P.value())
        self.w = float(self.ed_w.value())

        # Keep 'a' within [0, L]
        self.ed_a.blockSignals(True)
        self.ed_a.setMaximum(self.L)
        if self.ed_a.value() > self.L:
            self.ed_a.setValue(self.L)
        self.ed_a.blockSignals(False)
        self.a = float(self.ed_a.value())

        self._draw_scene()
        self._update_results()

    def _clear_actors(self):
        # Remove existing meshes/actors
        self.plotter.clear()  # clears everything including text and axes
        self.plotter.add_axes()

        self.beam_actor = None
        self.supportA_actor = None
        self.supportB_actor = None
        self.load_actor = None
        self.text_actor_id = None

    def _draw_scene(self):
        if self.L <= 0:
            return

        self._clear_actors()

        # Beam geometry (a simple box)
        beam_depth = 0.25
        beam_width = 0.20
        beam_center = (self.L / 2.0, 0.0, 0.0)
        beam = pv.Box(bounds=(
            0.0, self.L,                 # x
            -beam_width/2, beam_width/2, # y
            -beam_depth/2, beam_depth/2  # z
        ))

        self.beam_actor = self.plotter.add_mesh(beam, opacity=0.85)

        # Supports as blocks under each end
        sup_w = 0.35
        sup_d = 0.35
        sup_h = 0.25

        supportA = pv.Box(bounds=(
            -0.05, 0.05,
            -sup_w/2, sup_w/2,
            -beam_depth/2 - sup_h, -beam_depth/2
        ))
        supportB = pv.Box(bounds=(
            self.L - 0.05, self.L + 0.05,
            -sup_w/2, sup_w/2,
            -beam_depth/2 - sup_h, -beam_depth/2
        ))

        self.supportA_actor = self.plotter.add_mesh(supportA, opacity=1.0)
        self.supportB_actor = self.plotter.add_mesh(supportB, opacity=1.0)

        # Load arrow(s)
        arrow_scale = max(0.7, self.L * 0.12)  # visual scale
        z_top = beam_depth/2 + 0.15

        if self.load_type == "Point Load":
            x = self.a
            start = (x, 0.0, z_top + arrow_scale)
            direction = (0.0, 0.0, -1.0)
            arrow = pv.Arrow(start=start, direction=direction, tip_length=0.35, tip_radius=0.06, shaft_radius=0.03, scale=arrow_scale)
            self.load_actor = self.plotter.add_mesh(arrow)

            # small marker line at load location on beam top
            mark = pv.Line((x, -beam_width/2, beam_depth/2), (x, beam_width/2, beam_depth/2))
            self.plotter.add_mesh(mark, line_width=3)

        else:
            # UDL: show multiple small arrows along span
            n = 9
            xs = [i * self.L / (n - 1) for i in range(n)]
            for x in xs:
                start = (x, 0.0, z_top + arrow_scale * 0.55)
                direction = (0.0, 0.0, -1.0)
                arr = pv.Arrow(start=start, direction=direction, tip_length=0.35, tip_radius=0.05, shaft_radius=0.02, scale=arrow_scale * 0.55)
                self.plotter.add_mesh(arr)

        # Labels at supports
        self.plotter.add_point_labels([(0.0, 0.0, -beam_depth/2 - sup_h - 0.05)],
                                      ["A"], point_size=0, font_size=16)
        self.plotter.add_point_labels([(self.L, 0.0, -beam_depth/2 - sup_h - 0.05)],
                                      ["B"], point_size=0, font_size=16)

        # Make it look nicer
        self.plotter.set_background("white")
        self.plotter.reset_camera()

    def _update_results(self):
        # Compute
        if self.L <= 0:
            return

        if self.load_type == "Point Load":
            Ra, Rb, total = reactions_point_load(self.P, self.a, self.L)
            load_desc = f"Point Load: P={self.P:.3f} kN at a={self.a:.3f} m"
        else:
            Ra, Rb, total = reactions_udl(self.w, self.L)
            load_desc = f"UDL: w={self.w:.3f} kN/m over L={self.L:.3f} m"

        # Update side labels
        self.lb_Ra.setText(f"{Ra:.4f}")
        self.lb_Rb.setText(f"{Rb:.4f}")
        self.lb_total.setText(f"{total:.4f}")

        # Update 3D overlay text
        overlay = (
            f"Simply Supported Beam\n"
            f"L = {self.L:.3f} m\n"
            f"{load_desc}\n\n"
            f"Ra = {Ra:.4f} kN\n"
            f"Rb = {Rb:.4f} kN\n"
            f"Total = {total:.4f} kN"
        )

        # Use a screen text overlay
        self.plotter.add_text(overlay, position="upper_left", font_size=10)
        self.plotter.render()


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = BeamApp()
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
