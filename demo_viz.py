"""
demo_viz.py
===========
Generates fake but structurally realistic song data and launches the
GraphVisualizer so you can test the visualization without needing the
real dataset or the pickled graph from your teammate.

Run with:
    python demo_viz.py

What it does:
    1. Creates N fake _Song objects with random-but-plausible attributes
    2. Computes connections between songs (same logic as graph.py)
    3. Wraps everything in a mock _Graph-like object
    4. Pickles it to  demo_graph.pkl  in the current directory
    5. Launches GraphVisualizer with that pickle

Once the real graph.pkl is ready from your teammate, just run
graph_viz.py instead — demo_viz.py is only for testin
"""

from __future__ import annotations

import math
import pickle
import random
import tkinter as tk

# Import the real _Song class from graph.py so the structure is 100% identical
# to what your teammate will pickle. This means demo_graph.pkl is a valid
# drop-in for the real graph.pkl as far as graph_viz.py is concerned.
from graph import _Song

# ---------------------------------------------------------------------------
# Config — tweak these to stress-test different scenarios
# ---------------------------------------------------------------------------
NUM_SONGS       = 600    # how many fake songs to generate
SIMILARITY_THRESHOLD = 0.5   # same as _Graph.threshold in graph.py
PICKLE_PATH     = "demo_graph.pkl"
SAMPLE_SIZE     = 500    # how many nodes to show in the visualizer
RANDOM_SEED     = 42

# ---------------------------------------------------------------------------
# Fake data pools
# ---------------------------------------------------------------------------
GENRES = [
    "Pop", "Rock", "Electronic/Dance", "Hip-Hop/Soul",
    "Metal/Punk", "Jazz/Blues", "Classical/Acoustic",
    "Folk/Country", "World/Regional", "Mood/Other",
]

FIRST_WORDS = [
    "Neon", "Broken", "Golden", "Midnight", "Electric", "Silent",
    "Falling", "Running", "Lost", "Burning", "Hollow", "Crystal",
    "Fading", "Rising", "Dark", "Bright", "Cold", "Warm", "Wild",
    "Stolen", "Endless", "Shallow", "Deep", "Painted", "Faded",
]
SECOND_WORDS = [
    "Dreams", "Hearts", "Lights", "Roads", "Skies", "Waves",
    "Fire", "Rain", "Stars", "Shadows", "Memories", "Echoes",
    "Nights", "Days", "Tears", "Smiles", "Lies", "Truth",
    "Wings", "Chains", "Voices", "Colors", "Bridges", "Storms",
]
ARTISTS = [
    "The Midnight Echo", "Nova Drift", "Solstice Kings", "Clara Vane",
    "Iron Pulse", "Desert Ghost", "Lunar Archive", "Static River",
    "Ember Falls", "The Glass Waves", "Phantom Bloom", "Sky Division",
    "Orbit", "Cassette Dreams", "Velvet Thunder", "The Pale Hours",
    "Hollow Coast", "Prism Walk", "Radio Dusk", "Coastal Hymn",
    "Wavefront", "Nocturn", "The Slow Burn", "Frequency Jones",
    "Analog Heart", "Blue Circuit", "Dusk Protocol", "The Verb",
]


def _make_song_name(used: set[str]) -> str:
    """Generate a unique fake song name."""
    for _ in range(1000):
        name = f"{random.choice(FIRST_WORDS)} {random.choice(SECOND_WORDS)}"
        if name not in used:
            used.add(name)
            return name
    # Fallback with a number suffix
    base = f"{random.choice(FIRST_WORDS)} {random.choice(SECOND_WORDS)}"
    n = 2
    while f"{base} {n}" in used:
        n += 1
    used.add(f"{base} {n}")
    return f"{base} {n}"


def _genre_attrs(genre: str) -> dict:
    """
    Return genre-typical attribute ranges so songs cluster realistically
    by genre in the spring layout (similar attributes → similar position).
    """
    profiles = {
        "Pop":               dict(dance=(0.55, 0.85), energy=(0.5, 0.8),  tempo=(0.45, 0.7),  acoustic=(0.0, 0.35), valence=(0.4, 0.85)),
        "Rock":              dict(dance=(0.3, 0.65),  energy=(0.6, 0.95), tempo=(0.45, 0.75), acoustic=(0.0, 0.3),  valence=(0.2, 0.65)),
        "Electronic/Dance":  dict(dance=(0.6, 0.95),  energy=(0.65, 1.0), tempo=(0.55, 0.9),  acoustic=(0.0, 0.15), valence=(0.3, 0.8)),
        "Hip-Hop/Soul":      dict(dance=(0.6, 0.9),   energy=(0.4, 0.75), tempo=(0.35, 0.65), acoustic=(0.0, 0.35), valence=(0.2, 0.7)),
        "Metal/Punk":        dict(dance=(0.1, 0.45),  energy=(0.75, 1.0), tempo=(0.55, 0.95), acoustic=(0.0, 0.15), valence=(0.1, 0.5)),
        "Jazz/Blues":        dict(dance=(0.3, 0.65),  energy=(0.2, 0.6),  tempo=(0.25, 0.6),  acoustic=(0.2, 0.7),  valence=(0.2, 0.65)),
        "Classical/Acoustic":dict(dance=(0.1, 0.4),   energy=(0.05, 0.45),tempo=(0.2, 0.55),  acoustic=(0.5, 1.0),  valence=(0.1, 0.6)),
        "Folk/Country":      dict(dance=(0.3, 0.6),   energy=(0.2, 0.6),  tempo=(0.3, 0.6),   acoustic=(0.3, 0.8),  valence=(0.3, 0.75)),
        "World/Regional":    dict(dance=(0.4, 0.8),   energy=(0.3, 0.75), tempo=(0.3, 0.7),   acoustic=(0.1, 0.6),  valence=(0.3, 0.8)),
        "Mood/Other":        dict(dance=(0.2, 0.6),   energy=(0.1, 0.55), tempo=(0.2, 0.6),   acoustic=(0.1, 0.7),  valence=(0.1, 0.65)),
    }
    return profiles.get(genre, profiles["Mood/Other"])


def _rand(lo: float, hi: float) -> float:
    return round(random.uniform(lo, hi), 4)


def generate_fake_songs(n: int) -> dict[str, _Song]:
    """Generate n fake _Song objects with plausible normalised attributes."""
    random.seed(RANDOM_SEED)
    songs: dict[str, _Song] = {}
    used_names: set[str] = set()

    for _ in range(n):
        name   = _make_song_name(used_names)
        artist = random.choice(ARTISTS)
        genre  = random.choice(GENRES)
        prof   = _genre_attrs(genre)

        song = _Song(
            artist        = artist,
            name          = name,
            popularity    = round(random.uniform(0.0, 1.0), 4),
            year          = round(random.uniform(0.0, 1.0), 4),   # already normalised
            genre         = genre,
            dance         = _rand(*prof["dance"]),
            energy        = _rand(*prof["energy"]),
            key           = round(random.uniform(0.0, 1.0), 4),
            loud          = round(random.uniform(0.0, 1.0), 4),
            mode          = random.choice([0.0, 1.0]),
            speech        = round(random.uniform(0.0, 0.5), 4),
            acoustic      = _rand(*prof["acoustic"]),
            instrument    = round(random.uniform(0.0, 0.5), 4),
            live          = round(random.uniform(0.0, 0.4), 4),
            valence       = _rand(*prof["valence"]),
            tempo         = _rand(*prof["tempo"]),
            duration      = round(random.uniform(0.1, 0.9), 4),
            time_signature= round(random.choice([3/7, 4/7, 5/7]), 4),
        )
        songs[name] = song

    return songs


def build_connections(songs: dict[str, _Song], threshold: float) -> None:
    """
    Connect songs whose Euclidean distance is below the threshold.
    Mirrors _Graph._make_connections() / _calculate_song_distance() exactly.
    """
    import itertools
    song_list = list(songs.values())
    connected = 0

    for s1, s2 in itertools.combinations(song_list, 2):
        genre_dist_sq = 0.0 if s1.genre == s2.genre else 1.0
        dist = math.sqrt(
            (s1.year - s2.year) ** 2 +
            (s1.key  - s2.key)  ** 2 +
            (s1.loud - s2.loud) ** 2 +
            (s1.tempo- s2.tempo)** 2 +
            (s1.duration - s2.duration) ** 2 +
            (s1.time_signature - s2.time_signature) ** 2 +
            genre_dist_sq
        )
        if dist < threshold:
            s1.neighbours[s2] = dist
            s2.neighbours[s1] = dist
            connected += 1

    print(f"[demo_viz] {connected} edges created across {len(song_list)} songs.")


# ---------------------------------------------------------------------------
# Minimal mock _Graph — structurally identical to the real one
# graph_viz.py only accesses ._songs, so this is all we need.
# ---------------------------------------------------------------------------
class _MockGraph:
    """
    A lightweight stand-in for _Graph that graph_viz.py can load from pickle.
    Only exposes the attributes that graph_viz.py actually reads.
    """
    def __init__(self, songs: dict[str, _Song]) -> None:
        self._songs = songs


# ---------------------------------------------------------------------------
# Build, pickle, launch
# ---------------------------------------------------------------------------

def build_demo_pickle() -> None:
    """Generate fake data and save to PICKLE_PATH."""
    print(f"[demo_viz] Generating {NUM_SONGS} fake songs…")
    songs = generate_fake_songs(NUM_SONGS)

    print(f"[demo_viz] Building connections (threshold={SIMILARITY_THRESHOLD})…")
    build_connections(songs, SIMILARITY_THRESHOLD)

    mock_graph = _MockGraph(songs)

    with open(PICKLE_PATH, "wb") as f:
        pickle.dump(mock_graph, f)

    print(f"[demo_viz] Saved demo graph to '{PICKLE_PATH}'")


def launch_visualizer() -> None:
    """Open the Tkinter window with the demo graph loaded."""
    # Import here so we don't accidentally trigger TkAgg before Tk() exists
    from graph_viz import GraphVisualizer

    root = tk.Tk()
    root.title("Music Graph Visualizer — DEMO MODE")
    root.configure(bg="#0d0d0d")
    root.geometry("1280x760")

    # ---- Header banner so it's obvious this is demo mode ----
    banner = tk.Label(
        root,
        text="⚠  DEMO MODE — using generated fake data, not the real dataset  ⚠",
        font=("Courier New", 10, "bold"),
        fg="#FFD700", bg="#1a1a00", pady=5
    )
    banner.pack(fill="x")

    # ---- Main container ----
    container = tk.Frame(root, bg="#0d0d0d")
    container.pack(fill="both", expand=True, padx=6, pady=4)

    # ---- Info panel on click ----
    def on_click(song_name: str, attrs: dict) -> None:
        print(f"\n[Clicked] {song_name}")
        for k, v in attrs.items():
            print(f"  {k}: {v}")

    print("[demo_viz] Launching visualizer…")
    viz = GraphVisualizer(
        parent_frame=container,
        pickle_path=PICKLE_PATH,
        sample_size=SAMPLE_SIZE,
        on_song_click=on_click,
    )
    viz.frame.pack(fill="both", expand=True)

    # ---- Demo control buttons ----
    btn_frame = tk.Frame(root, bg="#0d0d0d")
    btn_frame.pack(fill="x", padx=6, pady=4)

    style = dict(
        bg="#222244", fg="#aaaaff", font=("Courier New", 9),
        relief="flat", padx=10, pady=4, cursor="hand2",
        activebackground="#333366", activeforeground="#ffffff"
    )

    def demo_highlight() -> None:
        sample = viz._sample_names
        if not sample:
            return
        recs  = random.sample(sample, min(5, len(sample)))
        seeds = random.sample([s for s in sample if s not in recs],
                              min(2, len(sample)))
        print(f"\n[Demo] Highlighting recommended: {recs}")
        print(f"[Demo] Seeds: {seeds}")
        viz.highlight_songs(recs, seed_songs=seeds)

    def demo_focus() -> None:
        if not viz._highlighted:
            demo_highlight()
        target = next(iter(viz._highlighted), None)
        if target:
            print(f"\n[Demo] Focusing on: {target}")
            viz.focus_on_song(target)

    def demo_search() -> None:
        for query in ["Neon", "Broken", "Electric"]:
            results = viz.search_songs(query, max_results=5)
            print(f"[Demo] search('{query}'): {results}")

    tk.Button(btn_frame, text="🎵  Highlight 5 random songs",
              command=demo_highlight, **style).pack(side="left", padx=4)
    tk.Button(btn_frame, text="🔍  Focus on highlighted",
              command=demo_focus, **style).pack(side="left", padx=4)
    tk.Button(btn_frame, text="🔎  Search demo",
              command=demo_search, **style).pack(side="left", padx=4)
    tk.Button(btn_frame, text="✕  Clear highlights",
              command=viz.clear_highlights, **style).pack(side="left", padx=4)
    tk.Button(btn_frame, text="⟳  Reset view",
              command=viz.reset_view, **style).pack(side="left", padx=4)

    root.mainloop()


if __name__ == "__main__":
    build_demo_pickle()
    launch_visualizer()
