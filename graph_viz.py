"""
CSC111 Winter 2026 Course Project: MatchMyMusic (Graph Visualization)

Module Description
==================
This module contains the GraphVisualizer class, which embeds an interactive
NetworkX and matplotlib graph into a Tkinter frame. It displays a random
sample of songs as nodes coloured by genre, draws edges between similar songs,
and supports panning, zooming, clicking nodes to view attributes, and
highlighting recommended and seed songs.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the
authors listed below. All forms of distribution of this code, whether
as given or with any changes, are expressly prohibited.
"""

from __future__ import annotations
import math
import random
import tkinter as tk
from typing import Callable, Optional, Any

import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.backend_bases import MouseEvent, PickEvent
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import PathCollection
from matplotlib.text import Annotation

import graph

GENRE_COLORS: dict[str, str] = {
    "Pop": "#E91E8C",
    "Rock": "#FF6B35",
    "Electronic/Dance": "#00C2FF",
    "Hip-Hop/Soul": "#9B59B6",
    "Metal/Punk": "#607D8B",
    "Jazz/Blues": "#F4A623",
    "Classical/Acoustic": "#27AE60",
    "Folk/Country": "#795548",
    "World/Regional": "#E74C3C",
    "Mood/Other": "#90A4AE",
}
DEFAULT_NODE_COLOR = "#90A4AE"
HIGHLIGHT_COLOR = "#FFD700"
SEED_COLOR = "#FF4500"
EDGE_COLOR = "#555577"
BG_COLOR = "#0d0d0d"
AXES_BG_COLOR = "#111111"
ANNOTATION_BG = "#1a1a2e"
ANNOTATION_FG = "#e0e0e0"

FONT_MAIN = "Arial"
FONT_MONO = "Courier New"

TEXT_LARGE = 20
TEXT_NORMAL = 18
TEXT_SMALL = 16

INFO_PANEL_WIDTH = 45
INFO_PANEL_HEIGHT = 12

PAD_X = 10
PAD_Y = 8

ANNOTATION_FONT_SIZE = 13

NODE_SIZE_DEFAULT = 75
NODE_SIZE_HIGHLIGHT = 160
NODE_ALPHA = 0.85


class GraphVisualizer:
    """
    Embeds an interactive song graph into a tkinter frame using matplotlib and NetworkX.
    It displays a random sample of songs as coloured nodes (by genre), with edges
    connecting similar songs. It supports scrolling to zoom, right-click drag to pan,
    clicking nodes to view their attributes, and highlighting recommended/seed songs.

    Instance Attributes:
        - parent_frame: The Tkinter frame this visualizer lives inside.
        - sample_size: The number of songs to display on the graph at once.
        - on_song_click: Optional function called with (song_name, attrs) when a node is clicked.
        - frame: The outer Tkinter frame holding the canvas and UI.

    Representation Invariants:
        - self.sample_size > 0
    """
    parent_frame: tk.Frame
    sample_size: int
    on_song_click: Callable | None
    frame: tk.Frame

    # Private attributes declared to satisfy PythonTA
    _graph: graph.Graph
    _nx_graph: nx.Graph
    _pos: dict[str, tuple[float, float]]
    _sample_names: list[str]
    _scatter: PathCollection | None
    _annotation: Annotation | None
    _node_colors: list[str]
    _node_sizes: list[int]
    _highlighted: set[str]
    _seeds: set[str]
    _default_xlim: tuple[float, float] | None
    _default_ylim: tuple[float, float] | None
    _is_panning: bool
    _pan_start_x: float | None
    _pan_start_y: float | None
    _pan_start_xlim: tuple[float, float] | None
    _pan_start_ylim: tuple[float, float] | None
    _focus_rings: list
    _fig: Any
    _ax: Any
    _canvas: FigureCanvasTkAgg
    _info_frame: tk.Frame
    _info_title: tk.Label
    _info_text: tk.Text
    _cid: int

    def __init__(self, parent_frame: tk.Frame, song_graph: graph.Graph, sample_size: int = 500,
                 on_song_click: Optional[Callable[[str, dict[str, str]], None]] = None) -> None:
        """Initialize the GraphVisualizer and build the internal UI structures."""
        self.parent_frame = parent_frame
        self._graph = song_graph
        self.sample_size = sample_size
        self.on_song_click = on_song_click

        self._nx_graph = nx.Graph()
        self._pos = {}
        self._sample_names = []
        self._scatter = None
        self._annotation = None
        self._node_colors = []
        self._node_sizes = []
        self._highlighted = set()
        self._seeds = set()
        self._default_xlim = None
        self._default_ylim = None

        self._is_panning = False
        self._pan_start_x = None
        self._pan_start_y = None
        self._pan_start_xlim = None
        self._pan_start_ylim = None

        self._focus_rings = []

        # Build the template inside parent_frame
        self.frame = tk.Frame(parent_frame, bg=BG_COLOR)
        self._build_ui()

        # Sample songs and draw
        self._sample_and_build()
        self._draw()

    def _build_ui(self) -> None:
        """Create matplotlib Figure (window), navigation toolbar, info panel, legend, and reset button."""
        self._fig, self._ax = plt.subplots(figsize=(9, 6), facecolor=BG_COLOR)
        self._ax.set_facecolor(AXES_BG_COLOR)
        self._ax.axis("off")

        self._canvas = FigureCanvasTkAgg(self._fig, master=self.frame)
        canvas_widget = self._canvas.get_tk_widget()
        canvas_widget.configure(bg=BG_COLOR, highlightthickness=0)

        self._info_frame = tk.Frame(self.frame, bg="#1a1a2e", bd=0)
        self._info_title = tk.Label(
            self._info_frame, text="Click a node to see song details",
            font=(FONT_MONO, TEXT_LARGE, "bold"), fg="#FFD700", bg="#1a1a2e",
            anchor="w", padx=PAD_X, pady=PAD_Y
        )
        self._info_title.pack(fill="x")

        self._info_text = tk.Text(
            self._info_frame, height=INFO_PANEL_HEIGHT, width=INFO_PANEL_WIDTH,
            font=(FONT_MONO, TEXT_NORMAL), fg=ANNOTATION_FG, bg="#1a1a2e",
            bd=0, relief="flat", state="disabled", padx=PAD_X, pady=PAD_Y,
            wrap="word"
        )
        self._info_text.pack(fill="both", expand=True)

        legend_frame = tk.Frame(self.frame, bg=BG_COLOR)
        for genre, color in GENRE_COLORS.items():
            dot = tk.Label(legend_frame, text="●", fg=color, bg=BG_COLOR, font=(FONT_MAIN, TEXT_NORMAL))
            lbl = tk.Label(legend_frame, text=genre, fg="#aaaaaa", bg=BG_COLOR, font=(FONT_MAIN, TEXT_SMALL))
            dot.pack(side="left", padx=(PAD_X // 2, 0))
            lbl.pack(side="left", padx=(0, PAD_X))

        tk.Label(legend_frame, text="●", fg=SEED_COLOR, bg=BG_COLOR, font=(FONT_MAIN, TEXT_NORMAL)).pack(
            side="left", padx=(PAD_X, 0))
        tk.Label(legend_frame, text="Seed", fg="#aaaaaa", bg=BG_COLOR, font=(FONT_MAIN, TEXT_SMALL)).pack(
            side="left", padx=(0, PAD_X))
        tk.Label(legend_frame, text="●", fg=HIGHLIGHT_COLOR, bg=BG_COLOR, font=(FONT_MAIN, TEXT_NORMAL)).pack(
            side="left", padx=(PAD_X // 2, 0))
        tk.Label(legend_frame, text="Recommended", fg="#aaaaaa", bg=BG_COLOR, font=(FONT_MAIN, TEXT_SMALL)).pack(
            side="left", padx=(0, PAD_X))

        reset_btn = tk.Button(
            self.frame, text="⟳  Reset View", command=self.reset_view,
            bg="#222244", fg="#aaaaff", font=(FONT_MONO, TEXT_NORMAL),
            relief="flat", padx=PAD_X, pady=PAD_Y // 2, cursor="hand2",
            activebackground="#333366", activeforeground="#ffffff"
        )

        legend_frame.pack(side="top", fill="x", padx=PAD_X // 2, pady=PAD_Y // 4)
        reset_btn.pack(side="top", anchor="e", padx=PAD_X, pady=PAD_Y // 4)
        canvas_widget.pack(side="left", fill="both", expand=True)
        self._info_frame.pack(side="right", fill="y", padx=(0, PAD_X // 2), pady=PAD_Y // 2)

        self._cid = self._canvas.mpl_connect("pick_event", self._on_pick)
        self._canvas.mpl_connect("scroll_event", self._on_scroll)
        self._canvas.mpl_connect("button_press_event", self._on_press)
        self._canvas.mpl_connect("button_release_event", self._on_release)
        self._canvas.mpl_connect("motion_notify_event", self._on_motion)

    def _on_scroll(self, event: MouseEvent) -> None:
        """Zoom in or out at the mouse position when the user scrolls the mouse wheel."""
        if event.inaxes != self._ax:
            return
        if event.xdata is None or event.ydata is None:
            return

        base_scale = 1.15
        scale_factor = base_scale ** (-event.step)

        cur_xlim = self._ax.get_xlim()
        cur_ylim = self._ax.get_ylim()

        new_width = (cur_xlim[1] - cur_xlim[0]) * scale_factor
        new_height = (cur_ylim[1] - cur_ylim[0]) * scale_factor

        if new_width < 0.001 or new_height < 0.001:
            return

        xdata, ydata = event.xdata, event.ydata

        relx = (xdata - cur_xlim[0]) / (cur_xlim[1] - cur_xlim[0])
        rely = (ydata - cur_ylim[0]) / (cur_ylim[1] - cur_ylim[0])

        self._ax.set_xlim(xdata - new_width * relx, xdata + new_width * (1 - relx))
        self._ax.set_ylim(ydata - new_height * rely, ydata + new_height * (1 - rely))
        self._canvas.draw_idle()

    def _on_press(self, event: MouseEvent) -> None:
        """Start panning when the user presses the right mouse button on the graph."""
        if event.button == 3 and event.inaxes == self._ax:
            self._is_panning = True
            self._pan_start_x = event.x
            self._pan_start_y = event.y
            self._pan_start_xlim = self._ax.get_xlim()
            self._pan_start_ylim = self._ax.get_ylim()

    def _on_release(self, event: MouseEvent) -> None:
        """Stop panning when the user releases the right mouse button."""
        if event.button == 3:
            self._is_panning = False

    def _on_motion(self, event: MouseEvent) -> None:
        """Move the graph view while the user right-click drags to pan."""
        if not self._is_panning or event.inaxes != self._ax:
            return

        if (self._pan_start_x is None or self._pan_start_y is None or
                self._pan_start_xlim is None or self._pan_start_ylim is None):
            return

        dx = event.x - self._pan_start_x
        dy = event.y - self._pan_start_y

        bbox = self._ax.get_window_extent()
        data_width = self._pan_start_xlim[1] - self._pan_start_xlim[0]
        data_height = self._pan_start_ylim[1] - self._pan_start_ylim[0]

        data_dx = dx * (data_width / bbox.width)
        data_dy = dy * (data_height / bbox.height)

        self._ax.set_xlim(self._pan_start_xlim[0] - data_dx, self._pan_start_xlim[1] - data_dx)
        self._ax.set_ylim(self._pan_start_ylim[0] - data_dy, self._pan_start_ylim[1] - data_dy)
        self._canvas.draw_idle()

    def _sample_and_build(self) -> None:
        """
        Randomly pick self.sample_size songs, build a NetworkX subgraph from them,
        and compute node positions using spring layout.
        """
        all_names = self._graph.get_all_song_names()
        n = min(self.sample_size, len(all_names))
        self._sample_names = random.sample(all_names, n)
        sample_set = set(self._sample_names)

        subgraph = nx.Graph()
        subgraph.add_nodes_from(self._sample_names)

        for name in self._sample_names:
            song = self._graph.get_song(name)
            if song is None:
                continue
            for neighbour_name, dist in song.neighbours.items():
                if neighbour_name in sample_set:
                    if not subgraph.has_edge(name, neighbour_name):
                        subgraph.add_edge(name, neighbour_name, weight=1.0 - dist)

        self._nx_graph = subgraph

        try:
            self._pos = nx.spring_layout(
                subgraph, weight="weight", k=1.2 / (n ** 0.5), iterations=60, seed=42
            )
        except ImportError:
            self._pos = self._fallback_layout(self._sample_names)

        self._reset_colors_and_sizes()

    def _reset_colors_and_sizes(self) -> None:
        """Set each node's colour and size (by genre, and seed or highlighted)."""
        self._node_colors = []
        self._node_sizes = []
        for name in self._sample_names:
            song = self._graph.get_song(name)
            if song is None:
                continue

            color = GENRE_COLORS.get(song.genre, DEFAULT_NODE_COLOR)

            if name in self._seeds:
                color = SEED_COLOR
            elif name in self._highlighted:
                color = HIGHLIGHT_COLOR

            self._node_colors.append(color)

            size = NODE_SIZE_DEFAULT
            if name in self._seeds or name in self._highlighted:
                size = NODE_SIZE_HIGHLIGHT

            self._node_sizes.append(size)

    def _draw(self) -> None:
        """Clear the canvas and fully redraw all edges and nodes at their current positions and colours."""
        self._ax.cla()
        self._ax.set_facecolor(AXES_BG_COLOR)
        self._ax.axis("off")

        if self._annotation:
            self._annotation = None

        edge_x, edge_y = [], []
        for u, v in self._nx_graph.edges():
            xu, yu = self._pos[u]
            xv, yv = self._pos[v]
            edge_x += [xu, xv, None]
            edge_y += [yu, yv, None]
        self._ax.plot(edge_x, edge_y, color=EDGE_COLOR, linewidth=0.7, alpha=0.8, zorder=1)

        xs = [self._pos[name][0] for name in self._sample_names]
        ys = [self._pos[name][1] for name in self._sample_names]

        self._scatter = self._ax.scatter(
            xs, ys,
            s=self._node_sizes,
            c=self._node_colors,
            alpha=NODE_ALPHA,
            linewidths=0.5,
            edgecolors="#333333",
            zorder=2,
            picker=True,
            pickradius=6,
        )

        self._ax.autoscale()
        self._default_xlim = self._ax.get_xlim()
        self._default_ylim = self._ax.get_ylim()

        self._canvas.draw_idle()

    def _redraw_colors(self) -> None:
        """Update node colours and sizes without redrawing the whole graph."""
        self._reset_colors_and_sizes()
        if self._scatter is not None:
            self._scatter.set_color(self._node_colors)
            self._scatter.set_sizes(self._node_sizes)
        self._canvas.draw_idle()

    def _on_pick(self, event: PickEvent) -> None:
        """Updates the info panel and shows the floating label when the user clicks a node."""
        if event.mouseevent.button != 1:
            return

        if event.artist is not self._scatter:
            return

        index = event.ind[0]
        song_name = self._sample_names[index]

        attrs = self._graph.get_stats(song_name)

        if attrs:
            self._update_info_panel(song_name, attrs)
            self._show_annotation(song_name)

            if self.on_song_click is not None:
                self.on_song_click(song_name, attrs)

    def _update_info_panel(self, song_name: str, attrs: dict[str, str]) -> None:
        """Display a song's attributes onto the info panel."""
        self._info_title.configure(text=f"♪  {song_name}")
        self._info_text.configure(state="normal")
        self._info_text.delete("1.0", "end")
        for label, value in attrs.items():
            self._info_text.insert("end", f"{label}:\n  {value}\n\n")
        self._info_text.configure(state="disabled")

    def _show_annotation(self, song_name: str) -> None:
        """Draw a floating label near the clicked node that shows the song name and artist."""
        if self._annotation is not None:
            self._annotation.remove()
            self._annotation = None

        x, y = self._pos[song_name]
        song = self._graph.get_song(song_name)
        if song is None:
            return

        text = f"{song_name}\n{song.artist}"

        self._annotation = self._ax.annotate(
            text, xy=(x, y), xytext=(12, 12), textcoords="offset points",
            fontsize=ANNOTATION_FONT_SIZE, color=ANNOTATION_FG,
            bbox=dict(boxstyle="round,pad=0.4", fc=ANNOTATION_BG, ec="#444466", alpha=0.92),
            path_effects=[pe.withStroke(linewidth=2, foreground="#000000")],
            zorder=10,
        )
        self._canvas.draw_idle()

    def highlight_songs(self, recommended: list[str], seed_songs: Optional[list[str]] = None) -> None:
        """
        Colour recommended songs gold and seed_songs songs red-orange.
        Swap in any missing recommended songs if not in the current sample.
        """
        self._remove_all_rings()

        sample_set = set(self._sample_names)

        self._highlighted = {name for name in recommended if name in sample_set}
        self._seeds = set()
        if seed_songs is not None:
            self._seeds = {name for name in seed_songs if name in sample_set}

        missing = [name for name in recommended if name not in sample_set]
        if missing:
            self.inject_songs(missing)

        self._redraw_colors()

    def inject_songs(self, names: list[str]) -> None:
        """Swap songs into the current sample by replacing non-important nodes."""
        replaceable = [name for name in self._sample_names if name not in self._highlighted and name not in self._seeds]
        to_remove = replaceable[: len(names)]

        for old, new in zip(to_remove, names):
            index = self._sample_names.index(old)
            self._sample_names[index] = new
            self._nx_graph.remove_node(old)
            if old in self._pos:
                del self._pos[old]

            self._nx_graph.add_node(new)
            new_song = self._graph.get_song(new)
            if new_song is None:
                continue

            placed = False
            for nb_name in new_song.neighbours:
                if nb_name in self._pos:
                    nx_pt, ny_pt = self._pos[nb_name]
                    self._pos[new] = (nx_pt + random.uniform(-0.05, 0.05), ny_pt + random.uniform(-0.05, 0.05))
                    placed = True
                    break

            if not placed:
                self._pos[new] = (random.uniform(-1, 1), random.uniform(-1, 1))

            for nb_name, dist in new_song.neighbours.items():
                if nb_name in set(self._sample_names):
                    self._nx_graph.add_edge(new, nb_name, weight=1.0 - dist)

        self._draw()

    def display_song_info(self, song_name: str) -> None:
        """Look up a song's attributes by name and display them in the info panel."""
        attrs = self._graph.get_stats(song_name)

        if attrs:
            self._update_info_panel(song_name, attrs)

    def focus_on_song(self, song_name: str, zoom_radius: float = 0.15) -> None:
        """Zoom and centre the view on a specific node, and flash a ring around it."""
        if song_name not in self._pos:
            return

        self._remove_all_rings()

        x, y = self._pos[song_name]
        self._ax.set_xlim(x - zoom_radius, x + zoom_radius)
        self._ax.set_ylim(y - zoom_radius, y + zoom_radius)

        ring = self._ax.scatter(
            [x], [y], s=500, c="none", edgecolors=HIGHLIGHT_COLOR,
            linewidths=2.5, zorder=5,
        )
        self._focus_rings.append(ring)
        self._canvas.draw_idle()

    def _remove_all_rings(self) -> None:
        """Remove all focus rings drawn around nodes and clear the rings list."""
        for ring in self._focus_rings:
            try:
                ring.remove()
            except Exception:
                pass
        self._focus_rings.clear()

    def reset_view(self) -> None:
        """Restore the original zoom and pan, and remove any floating labels/annotation."""
        if self._default_xlim is not None and self._default_ylim is not None:
            self._ax.set_xlim(self._default_xlim)
            self._ax.set_ylim(self._default_ylim)

        if self._annotation is not None:
            self._annotation.remove()
            self._annotation = None

        self._canvas.draw_idle()
        self.clear_highlights()

    def clear_highlights(self) -> None:
        """Remove all gold and red-orange highlighting, reverting nodes back to their genre colours."""
        self._highlighted.clear()
        self._seeds.clear()
        self._remove_all_rings()
        self._redraw_colors()

    def _fallback_layout(self, names: list[str]) -> dict[str, tuple[float, float]]:
        """Build a deterministic circular layout without relying on NumPy."""
        if not names:
            return {}

        total = len(names)
        pos = {}

        for i, name in enumerate(sorted(names)):
            angle = (2 * math.pi * i) / total
            pos[name] = (math.cos(angle), math.sin(angle))

        return pos


if __name__ == '__main__':
    import doctest
    doctest.testmod()

    import python_ta
    python_ta.check_all(config={
        'extra-imports': [
            'math', 'graph', 'random', 'tkinter', 'typing', 'networkx',
            'matplotlib', 'matplotlib.backend_bases', 'matplotlib.pyplot',
            'matplotlib.patheffects', 'matplotlib.backends.backend_tkagg',
            'matplotlib.collections', 'matplotlib.text'
        ],
        'allowed-io': [],
        'max-line-length': 120,
        'disable': [
            'too-many-instance-attributes',
            'too-many-locals'
        ]
    })
