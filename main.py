import sys
import tkinter as tk
from tkinter import messagebox

import graph
from graph_viz import GraphVisualizer, BG_COLOR

def main():
    sys.modules["__main__"].Graph = graph.Graph
    sys.modules["__main__"]._Song = graph._Song

    music_graph = graph.make_graph()

    root = tk.Tk()
    root.title("Music recommender — graph view")
    root.configure(bg=BG_COLOR)
    root.geometry("1280x800")

    # --- Top: search and lists ---
    top = tk.Frame(root, bg=BG_COLOR)
    top.pack(side="top", fill="x", padx=8, pady=6)

    tk.Label(top, text="Search song or artist:", fg="#e0e0e0", bg=BG_COLOR).pack(anchor="w")

    search_row = tk.Frame(top, bg=BG_COLOR)
    search_row.pack(fill="x", pady=2)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_row, textvariable=search_var, width=45, font=("Arial", 10))
    search_entry.pack(side="left", padx=(0, 8))

    lists_row = tk.Frame(top, bg=BG_COLOR)
    lists_row.pack(fill="x", pady=6)

    left_col = tk.Frame(lists_row, bg=BG_COLOR)
    left_col.pack(side="left", fill="both", expand=True, padx=(0, 8))
    tk.Label(left_col, text="Search results", fg="#aaaaaa", bg=BG_COLOR).pack(anchor="w")

    results_scroll = tk.Scrollbar(left_col)
    results_scroll.pack(side="right", fill="y")
    results_box = tk.Listbox(
        left_col, height=6, font=("Arial", 9),
        yscrollcommand=results_scroll.set, selectmode=tk.SINGLE
    )
    results_box.pack(side="left", fill="both", expand=True)
    results_scroll.config(command=results_box.yview)

    right_col = tk.Frame(lists_row, bg=BG_COLOR)
    right_col.pack(side="left", fill="both", expand=True)
    tk.Label(right_col, text="Seed songs (used for recommendations)", fg="#aaaaaa", bg=BG_COLOR).pack(anchor="w")

    seeds_scroll = tk.Scrollbar(right_col)
    seeds_scroll.pack(side="right", fill="y")
    seeds_box = tk.Listbox(
        right_col, height=6, font=("Arial", 9),
        yscrollcommand=seeds_scroll.set, selectmode=tk.SINGLE
    )
    seeds_box.pack(side="left", fill="both", expand=True)
    seeds_scroll.config(command=seeds_box.yview)

    search_results = []  # same order as results_box lines

    def run_search():
        results_box.delete(0, tk.END)
        search_results.clear()
        query = search_var.get().strip()
        if not query:
            return
        found = []
        q = query.lower()
        for name, song in music_graph._songs.items():
            if q in name.lower() or q in song.artist.lower():
                found.append(name)
            if len(found) >= 20:
                break
        if not found:
            messagebox.showinfo("Search", "No songs matched. Try different words.")
            return
        search_results.extend(found)
        for name in found:
            results_box.insert(tk.END, name)

    def add_seed():
        sel = results_box.curselection()
        if not sel:
            messagebox.showinfo("Seeds", "Select a song in Search results first.")
            return
        song_name = search_results[sel[0]]
        current = list(seeds_box.get(0, tk.END))
        if song_name in current:
            messagebox.showinfo("Seeds", "That song is already a seed.")
            return
        seeds_box.insert(tk.END, song_name)

    def remove_seed():
        sel = seeds_box.curselection()
        if not sel:
            messagebox.showinfo("Seeds", "Select a seed to remove.")
            return
        seeds_box.delete(sel[0])

    search_entry.bind("<Return>", lambda e: run_search())

    tk.Button(search_row, text="Search", command=run_search, width=10).pack(side="left")

    btn_row = tk.Frame(top, bg=BG_COLOR)
    btn_row.pack(fill="x", pady=4)

    tk.Label(btn_row, text="Number of recommendations:", fg="#e0e0e0", bg=BG_COLOR).pack(side="left")
    count_var = tk.StringVar(value="15")
    tk.Entry(btn_row, textvariable=count_var, width=5).pack(side="left", padx=6)

    # Graph + visualizer (created before button commands that use viz)
    graph_frame = tk.Frame(root, bg=BG_COLOR)
    graph_frame.pack(side="top", fill="both", expand=True, padx=8, pady=(0, 8))

    def on_song_click(song_name, attrs):
        pass  # Details already show inside GraphVisualizer

    viz = GraphVisualizer(
        parent_frame=graph_frame,
        song_graph=music_graph,
        sample_size=500,
        on_song_click=on_song_click,
    )
    viz.frame.pack(fill="both", expand=True)

    def do_recommendations():
        seeds = list(seeds_box.get(0, tk.END))
        if not seeds:
            messagebox.showinfo("Recommendations", "Add at least one seed song.")
            return
        try:
            n = int(count_var.get().strip())
            if n < 1:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Recommendations", "Enter a positive whole number.")
            return

        recs = music_graph.recommend([*seeds], n)
        if not recs:
            messagebox.showinfo(
                "Recommendations",
                "No neighbours found for these seeds in the graph (try other seeds).",
            )
            return

        rec_names = [rec.name for rec in recs]
        viz.highlight_songs(rec_names, seed_songs=list(seeds))
        if recs:
            viz.focus_on_song(rec_names[0])

    tk.Button(btn_row, text="Add as seed", command=add_seed).pack(side="left", padx=(20, 4))
    tk.Button(btn_row, text="Remove seed", command=remove_seed).pack(side="left", padx=4)
    tk.Button(btn_row, text="Get Recommendations", command=do_recommendations).pack(side="left", padx=12)
    tk.Button(btn_row, text="Clear graph highlights", command=viz.clear_highlights).pack(side="left", padx=4)

    root.mainloop()


if __name__ == "__main__":
    main()
