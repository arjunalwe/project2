"""
graph_viz.py
============
Self-contained graph visualization module for the music recommender system.

Accepts an already-loaded Graph object (from graph.py) — no pickle loading here.
The caller is responsible for loading the pickle; just pass the Graph in.
Provides a GraphVisualizer class that embeds an interactive matplotlib figure
into any tk.Frame — pan, zoom, click nodes, highlight recommendations.

Dependencies:
    pip install networkx matplotlib

Usage (standalone test):
    python graph_viz.py

Usage (inside the main UI):
    import pickle
    from graph_viz import GraphVisualizer

    with open("graph.pkl", "rb") as f:
        graph = pickle.load(f)

    viz = GraphVisualizer(
        parent_frame=some_tk_frame,
        graph=graph,
        sample_size=500,
        on_song_click=my_callback   optional: fn(song_name, attrs_dict)
    )
    viz.frame.pack(fill="both", expand=True)

    # Later, after GO is pressed:
    viz.highlight_songs(["Song A", "Song B"], seed_songs=["My Seed Song"])
    viz.focus_on_song("Song A")
"""

from __future__ import annotations

import random
import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional

import networkx as nx
import matplotlib
import matplotlib.pyplot as plt
import matplotlib.patheffects as pe
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

matplotlib.use("TkAgg")

# ---------------------------------------------------------------------------
# Colour palette — one colour per parent genre
# ---------------------------------------------------------------------------
GENRE_COLORS: dict[str, str] = {
    "Pop":                "#E91E8C",
    "Rock":               "#FF6B35",
    "Electronic/Dance":   "#00C2FF",
    "Hip-Hop/Soul":       "#9B59B6",
    "Metal/Punk":         "#607D8B",
    "Jazz/Blues":         "#F4A623",
    "Classical/Acoustic": "#27AE60",
    "Folk/Country":       "#795548",
    "World/Regional":     "#E74C3C",
    "Mood/Other":         "#90A4AE",
}
DEFAULT_NODE_COLOR   = "#90A4AE"
HIGHLIGHT_COLOR      = "#FFD700"   # gold  — recommended songs
SEED_COLOR           = "#FF4500"   # red-orange — seed songs
EDGE_COLOR           = "#555577"
BG_COLOR             = "#0d0d0d"
AXES_BG_COLOR        = "#111111"
ANNOTATION_BG        = "#1a1a2e"
ANNOTATION_FG        = "#e0e0e0"

NODE_SIZE_DEFAULT    = 40
NODE_SIZE_HIGHLIGHT  = 120
NODE_ALPHA           = 0.85


# ---------------------------------------------------------------------------
# Attribute display names — human-readable labels for the sidebar/annotation
# ---------------------------------------------------------------------------
ATTR_LABELS: dict[str, str] = {
    "artist":         "Artist",
    "genre":          "Genre",
    "year":           "Year (normalised)",
    "popularity":     "Popularity",
    "dance":          "Danceability",
    "energy":         "Energy",
    "key":            "Key (normalised)",
    "loud":           "Loudness (normalised)",
    "mode":           "Mode",
    "speech":         "Speechiness",
    "acoustic":       "Acousticness",
    "instrument":     "Instrumentalness",
    "live":           "Liveness",
    "valence":        "Valence",
    "tempo":          "Tempo (normalised)",
    "duration":       "Duration (normalised)",
    "time_signature": "Time Signature (normalised)",
}


def _song_to_attrs(song) -> dict[str, str]:
    """Convert a _Song object to a plain dict of display-ready attribute strings."""
    attrs = {}
    for attr, label in ATTR_LABELS.items():
        val = getattr(song, attr, "N/A")
        if isinstance(val, float):
            attrs[label] = f"{val:.4f}"
        else:
            attrs[label] = str(val)
    return attrs


# ---------------------------------------------------------------------------
# GraphVisualizer
# ---------------------------------------------------------------------------

class GraphVisualizer:
    """
    Embeds an interactive NetworkX/matplotlib graph into a tk.Frame.

    Parameters
    ----------
    parent_frame : tk.Frame
        The Tkinter frame to embed everything into.
    graph : Graph
        An already-loaded Graph object from graph.py.
        The caller loads the pickle; this class just uses the graph.
    sample_size : int
        Number of songs to display (default 500).
    on_song_click : callable, optional
        Called with (song_name: str, attrs: dict) whenever the user clicks a node.
        Use this hook to update an info panel elsewhere in the UI.
    """

    def __init__(
        self,
        parent_frame: tk.Frame,
        graph,
        sample_size: int = 500,
        on_song_click: Optional[Callable[[str, dict], None]] = None,
    ) -> None:
        self.parent_frame   = parent_frame
        self._graph         = graph
        self.sample_size    = sample_size
        self.on_song_click  = on_song_click

        # Internal state
        self._nx_graph      = None   # networkx subgraph
        self._pos           = {}     # {node_name: (x, y)}
        self._sample_names  = []     # ordered list of song names in current sample
        self._scatter       = None   # the PathCollection from ax.scatter
        self._annotation    = None   # floating info box
        self._node_colors   = []     # parallel list to _sample_names
        self._node_sizes    = []     # parallel list to _sample_names
        self._highlighted   = set()  # names currently highlighted as recommended
        self._seeds         = set()  # names currently marked as seeds
        self._default_xlim  = None
        self._default_ylim  = None

        # Build the widget tree inside parent_frame
        self.frame = tk.Frame(parent_frame, bg=BG_COLOR)
        self._build_ui()

        # Sample songs and draw — no loading needed, graph is already here
        self._sample_and_build()
        self._draw()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Create matplotlib figure + toolbar + info panel inside self.frame."""
        # --- Matplotlib figure ---
        self._fig, self._ax = plt.subplots(figsize=(9, 6), facecolor=BG_COLOR)
        self._ax.set_facecolor(AXES_BG_COLOR)
        self._ax.axis("off")

        self._canvas = FigureCanvasTkAgg(self._fig, master=self.frame)
        canvas_widget = self._canvas.get_tk_widget()
        canvas_widget.configure(bg=BG_COLOR, highlightthickness=0)

        # NavigationToolbar gives pan + zoom for free
        toolbar_frame = tk.Frame(self.frame, bg="#1a1a1a")
        self._toolbar = NavigationToolbar2Tk(self._canvas, toolbar_frame)
        self._toolbar.configure(bg="#1a1a1a")
        self._toolbar.update()

        # --- Info panel (shown when a node is clicked) ---
        self._info_frame = tk.Frame(self.frame, bg="#1a1a2e", bd=0)
        self._info_title = tk.Label(
            self._info_frame, text="Click a node to see song details",
            font=("Courier New", 11, "bold"), fg="#FFD700", bg="#1a1a2e",
            anchor="w", padx=8, pady=4
        )
        self._info_title.pack(fill="x")

        self._info_text = tk.Text(
            self._info_frame, height=9, width=40,
            font=("Courier New", 9), fg=ANNOTATION_FG, bg="#1a1a2e",
            bd=0, relief="flat", state="disabled", padx=6, pady=4,
            wrap="word"
        )
        self._info_text.pack(fill="both", expand=True)

        # --- Legend ---
        legend_frame = tk.Frame(self.frame, bg=BG_COLOR)
        for genre, color in GENRE_COLORS.items():
            dot = tk.Label(legend_frame, text="●", fg=color, bg=BG_COLOR,
                           font=("Arial", 9))
            lbl = tk.Label(legend_frame, text=genre, fg="#aaaaaa", bg=BG_COLOR,
                           font=("Arial", 8))
            dot.pack(side="left", padx=(4, 0))
            lbl.pack(side="left", padx=(0, 6))

        # Highlight & seed legend entries
        tk.Label(legend_frame, text="●", fg=SEED_COLOR, bg=BG_COLOR,
                 font=("Arial", 9)).pack(side="left", padx=(10, 0))
        tk.Label(legend_frame, text="Seed", fg="#aaaaaa", bg=BG_COLOR,
                 font=("Arial", 8)).pack(side="left", padx=(0, 6))
        tk.Label(legend_frame, text="●", fg=HIGHLIGHT_COLOR, bg=BG_COLOR,
                 font=("Arial", 9)).pack(side="left", padx=(4, 0))
        tk.Label(legend_frame, text="Recommended", fg="#aaaaaa", bg=BG_COLOR,
                 font=("Arial", 8)).pack(side="left", padx=(0, 6))

        # --- Reset button ---
        reset_btn = tk.Button(
            self.frame, text="⟳  Reset View", command=self.reset_view,
            bg="#222244", fg="#aaaaff", font=("Courier New", 9),
            relief="flat", padx=8, pady=3, cursor="hand2",
            activebackground="#333366", activeforeground="#ffffff"
        )

        # --- Layout ---
        toolbar_frame.pack(side="top", fill="x")
        legend_frame.pack(side="top", fill="x", padx=4, pady=2)
        reset_btn.pack(side="top", anchor="e", padx=6, pady=2)
        canvas_widget.pack(side="left", fill="both", expand=True)
        self._info_frame.pack(side="right", fill="y", padx=(0, 4), pady=4)

        # Connect click event
        self._cid = self._canvas.mpl_connect("pick_event", self._on_pick)

    def _sample_and_build(self) -> None:
        """
        Randomly sample songs and build a NetworkX subgraph from them.
        Only edges where BOTH endpoints are in the sample are included.
        """
        all_names = list(self._graph._songs.keys())
        n = min(self.sample_size, len(all_names))
        self._sample_names = random.sample(all_names, n)
        sample_set = set(self._sample_names)

        G = nx.Graph()
        G.add_nodes_from(self._sample_names)

        for name in self._sample_names:
            song = self._graph._songs[name]
            for neighbour_name, dist in song.neighbours.items():
                if neighbour_name in sample_set:
                    if not G.has_edge(name, neighbour_name):
                        G.add_edge(name, neighbour_name, weight=1.0 - dist)

        self._nx_graph = G

        # Compute layout once — cached for the lifetime of this visualizer
        print("[graph_viz] Computing spring layout … (one-time cost)")
        self._pos = nx.spring_layout(
            G,
            weight="weight",
            k=1.2 / (n ** 0.5),   # spacing factor
            iterations=60,
            seed=42
        )
        print("[graph_viz] Layout done.")

        # Initialise colours and sizes
        self._reset_colors_and_sizes()

    def _reset_colors_and_sizes(self) -> None:
        """Set default colours (by genre) and sizes for all nodes."""
        self._node_colors = []
        self._node_sizes  = []
        for name in self._sample_names:
            song  = self._graph._songs[name]
            color = GENRE_COLORS.get(song.genre, DEFAULT_NODE_COLOR)
            if name in self._seeds:
                color = SEED_COLOR
            if name in self._highlighted:
                color = HIGHLIGHT_COLOR
            self._node_colors.append(color)
            size = NODE_SIZE_DEFAULT
            if name in self._seeds or name in self._highlighted:
                size = NODE_SIZE_HIGHLIGHT
            self._node_sizes.append(size)

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _draw(self) -> None:
        """Full redraw of the graph on the matplotlib axes."""
        self._ax.cla()
        self._ax.set_facecolor(AXES_BG_COLOR)
        self._ax.axis("off")

        if self._annotation:
            self._annotation = None

        # Draw edges
        edge_x, edge_y = [], []
        for u, v in self._nx_graph.edges():
            xu, yu = self._pos[u]
            xv, yv = self._pos[v]
            edge_x += [xu, xv, None]
            edge_y += [yu, yv, None]
        self._ax.plot(edge_x, edge_y, color=EDGE_COLOR,
                      linewidth=0.7, alpha=0.8, zorder=1)

        # Draw nodes as a scatter (picker=True enables click events)
        xs = [self._pos[n][0] for n in self._sample_names]
        ys = [self._pos[n][1] for n in self._sample_names]

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

        # Store default view limits for reset
        self._ax.autoscale()
        self._default_xlim = self._ax.get_xlim()
        self._default_ylim = self._ax.get_ylim()

        self._canvas.draw_idle()

    def _redraw_colors(self) -> None:
        """Update node colours/sizes without recomputing layout (fast)."""
        self._reset_colors_and_sizes()
        if self._scatter is not None:
            self._scatter.set_facecolor(self._node_colors)
            self._scatter.set_sizes(self._node_sizes)
        self._canvas.draw_idle()

    # ------------------------------------------------------------------
    # Interactivity
    # ------------------------------------------------------------------

    def _on_pick(self, event) -> None:
        """Fired when the user clicks on a node."""
        if event.artist is not self._scatter:
            return
        ind = event.ind[0]  # index of the clicked node
        song_name = self._sample_names[ind]
        song      = self._graph._songs[song_name]
        attrs     = _song_to_attrs(song)

        # Update the info panel
        self._update_info_panel(song_name, attrs)

        # Show a floating annotation on the graph
        self._show_annotation(song_name, ind)

        # Fire external callback if provided
        if self.on_song_click:
            self.on_song_click(song_name, attrs)

    def _update_info_panel(self, song_name: str, attrs: dict) -> None:
        """Populate the right-side info panel with this song's attributes."""
        self._info_title.configure(text=f"♪  {song_name}")
        self._info_text.configure(state="normal")
        self._info_text.delete("1.0", "end")
        for label, value in attrs.items():
            self._info_text.insert("end", f"{label}:\n  {value}\n\n")
        self._info_text.configure(state="disabled")

    def _show_annotation(self, song_name: str, node_index: int) -> None:
        """Draw a floating label near the clicked node."""
        if self._annotation:
            self._annotation.remove()
            self._annotation = None

        x, y = self._pos[song_name]
        song  = self._graph._songs[song_name]
        text  = f"{song_name}\n{song.artist}"

        self._annotation = self._ax.annotate(
            text,
            xy=(x, y),
            xytext=(12, 12),
            textcoords="offset points",
            fontsize=7,
            color=ANNOTATION_FG,
            bbox=dict(boxstyle="round,pad=0.4", fc=ANNOTATION_BG,
                      ec="#444466", alpha=0.92),
            path_effects=[pe.withStroke(linewidth=2, foreground="#000000")],
            zorder=10,
        )
        self._canvas.draw_idle()

    # ------------------------------------------------------------------
    # Public API — called by the main UI
    # ------------------------------------------------------------------

    def highlight_songs(
        self,
        recommended: list[str],
        seed_songs: Optional[list[str]] = None,
    ) -> None:
        """
        Colour recommended songs gold and seed songs red-orange.
        Songs not in the current sample are silently ignored.

        Parameters
        ----------
        recommended : list[str]
            Song names returned by the recommendation algorithm.
        seed_songs : list[str], optional
            The user's input seed songs.
        """
        sample_set = set(self._sample_names)

        self._highlighted = {n for n in recommended if n in sample_set}
        self._seeds       = set()
        if seed_songs:
            self._seeds   = {n for n in seed_songs if n in sample_set}

        # If some recommended songs aren't in the current sample, swap in
        # a portion of them so they become visible.
        missing = [n for n in recommended if n not in sample_set]
        if missing:
            self._inject_songs(missing)

        self._redraw_colors()

    def _inject_songs(self, names: list[str]) -> None:
        """
        Add songs that aren't currently in the sample so they can be shown.
        Replaces a random non-highlighted, non-seed portion of the sample.
        """
        replaceable = [
            n for n in self._sample_names
            if n not in self._highlighted and n not in self._seeds
        ]
        to_remove = replaceable[: len(names)]
        for old, new in zip(to_remove, names):
            idx = self._sample_names.index(old)
            self._sample_names[idx] = new
            self._nx_graph.remove_node(old)
            if old in self._pos:
                del self._pos[old]

            # Add new node + edges to sample
            self._nx_graph.add_node(new)
            new_song = self._graph._songs[new]
            # Place it near one of its neighbours that's already visible
            placed = False
            for nb_name in new_song.neighbours:
                if nb_name in self._pos:
                    nx_pt, ny_pt = self._pos[nb_name]
                    self._pos[new] = (
                        nx_pt + random.uniform(-0.05, 0.05),
                        ny_pt + random.uniform(-0.05, 0.05),
                    )
                    placed = True
                    break
            if not placed:
                self._pos[new] = (random.uniform(-1, 1), random.uniform(-1, 1))

            for nb_name, dist in new_song.neighbours.items():
                if nb_name in set(self._sample_names):
                    self._nx_graph.add_edge(new, nb_name, weight=1.0 - dist)

        self._draw()

    def focus_on_song(self, song_name: str, zoom_radius: float = 0.15) -> None:
        """
        Smoothly zoom and centre the view on the given song's node.

        Parameters
        ----------
        song_name : str
            The song to focus on. Must be in the current sample.
        zoom_radius : float
            Half-width/height of the zoomed viewport (in graph coordinate units).
        """
        if song_name not in self._pos:
            print(f"[graph_viz] '{song_name}' is not in the current sample.")
            return

        x, y = self._pos[song_name]
        self._ax.set_xlim(x - zoom_radius, x + zoom_radius)
        self._ax.set_ylim(y - zoom_radius, y + zoom_radius)

        # Highlight the node briefly with a ring
        ring = self._ax.scatter(
            [x], [y],
            s=500, c="none",
            edgecolors=HIGHLIGHT_COLOR,
            linewidths=2.5,
            zorder=5,
        )
        self._canvas.draw_idle()

        # Remove the ring after 1.5 s
        def _remove_ring():
            try:
                ring.remove()
                self._canvas.draw_idle()
            except Exception:
                pass

        self.parent_frame.after(1500, _remove_ring)

    def reset_view(self) -> None:
        """Reset the viewport to show the full graph."""
        if self._default_xlim and self._default_ylim:
            self._ax.set_xlim(self._default_xlim)
            self._ax.set_ylim(self._default_ylim)
        if self._annotation:
            self._annotation.remove()
            self._annotation = None
        self._canvas.draw_idle()

    def clear_highlights(self) -> None:
        """Remove all recommendation/seed highlighting."""
        self._highlighted.clear()
        self._seeds.clear()
        self._redraw_colors()

    def get_song_attributes(self, song_name: str) -> Optional[dict]:
        """
        Return the display-ready attribute dict for a song by name.
        Returns None if the song is not in the loaded graph.
        """
        song = self._graph._songs.get(song_name)
        if song is None:
            return None
        return _song_to_attrs(song)

    def search_songs(self, query: str, max_results: int = 10) -> list[str]:
        """
        Simple case-insensitive search across song names and artist names.
        Returns a list of matching song names (up to max_results).

        Useful for wiring up the search box in the main UI.
        """
        q = query.lower().strip()
        if not q:
            return []
        results = []
        for name, song in self._graph._songs.items():
            if q in name.lower() or q in song.artist.lower():
                results.append(name)
                if len(results) >= max_results:
                    break
        return results


# ---------------------------------------------------------------------------
# Standalone test — run `python graph_viz.py` to see it in action
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    # import pickle
    import graph

    # PICKLE_PATH = "graph.pkl"
    # Patch __main__ so pickle can find Graph and _Song when loading
    import sys

    sys.modules['__main__'].Graph = graph.Graph
    sys.modules['__main__']._Song = graph._Song
    Graph = graph.make_graph()

    root = tk.Tk()
    root.title("Music Graph Visualizer — Standalone Test")
    root.configure(bg=BG_COLOR)
    root.geometry("1200x720")
    """
    # ---- Load the graph (pickle handled here, not inside GraphVisualizer) ----
    status = tk.Label(
        root, text="Loading graph from pickle…",
        font=("Courier New", 12), fg="#aaaaff", bg=BG_COLOR
    )
    status.pack(pady=20)
    root.update()

    try:
        with open(PICKLE_PATH, "rb") as f:
            graph = pickle.load(f)
        print(f"[graph_viz] Loaded {len(graph._songs)} songs from '{PICKLE_PATH}'")
    except FileNotFoundError:
        status.configure(
            text=f"Pickle file '{PICKLE_PATH}' not found. Run graph.py first.",
            fg="#ff6666"
        )
        root.mainloop()
        sys.exit(1)
    """

    # ---- Build the visualizer ----
    container = tk.Frame(root, bg=BG_COLOR)
    container.pack(fill="both", expand=True, padx=8, pady=4)

    def on_click(song_name, attrs):
        print(f"\n[Clicked] {song_name}")
        for k, v in attrs.items():
            print(f"  {k}: {v}")

    viz = GraphVisualizer(
        parent_frame=container,
        graph=Graph,
        sample_size=500,
        on_song_click=on_click,
    )
    viz.frame.pack(fill="both", expand=True)
    # status.destroy()

    # ---- Demo buttons ----
    btn_frame = tk.Frame(root, bg=BG_COLOR)
    btn_frame.pack(fill="x", padx=8, pady=4)

    style_btn = dict(
        bg="#222244", fg="#aaaaff", font=("Courier New", 9),
        relief="flat", padx=10, pady=4, cursor="hand2",
        activebackground="#333366", activeforeground="#ffffff"
    )

    def demo_highlight():
        if not viz._sample_names:
            return
        picks  = random.sample(viz._sample_names, min(5, len(viz._sample_names)))
        seeds  = random.sample(viz._sample_names, min(2, len(viz._sample_names)))
        print(f"\n[Demo] Highlighting: {picks}")
        print(f"[Demo] Seeds: {seeds}")
        viz.highlight_songs(picks, seed_songs=seeds)

    def demo_focus():
        if not viz._highlighted:
            demo_highlight()
        target = next(iter(viz._highlighted), None)
        if target:
            print(f"\n[Demo] Focusing on: {target}")
            viz.focus_on_song(target)

    def demo_search():
        query   = "love"
        results = viz.search_songs(query, max_results=5)
        print(f"\n[Demo] Search '{query}': {results}")

    tk.Button(btn_frame, text="🎵  Demo Highlight",
              command=demo_highlight, **style_btn).pack(side="left", padx=4)
    tk.Button(btn_frame, text="🔍  Demo Focus",
              command=demo_focus, **style_btn).pack(side="left", padx=4)
    tk.Button(btn_frame, text="🔎  Demo Search 'love'",
              command=demo_search, **style_btn).pack(side="left", padx=4)
    tk.Button(btn_frame, text="✕  Clear Highlights",
              command=viz.clear_highlights, **style_btn).pack(side="left", padx=4)

    root.mainloop()
