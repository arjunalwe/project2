"""
CSC111 Winter 2026 Course Project: MatchMyMusic (Main Application)

Module Description
==================
This module contains the main application for MatchMyMusic. It builds the
Tkinter user interface, which includes a song search bar, a seed song list
(list of all the user's songs), and a recommended tracks list. It also
contains the AddSongQuiz class, which allows users to manually add a song
that is not in the dataset by entering its attributes through a popup window.
When the user requests recommendations, this module calls the graph's recommendation
algorithm and displays the results as highlighted nodes in the graph visualization
and as a list of track names.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use. All forms of distribution of this code, whether
as given or with any changes, are expressly prohibited.

This file is Copyright (c)  Reuben Kurian Mathew, Arjun Nilesh Alwe, Ritvik Aggarwal
"""
import tkinter as tk
from tkinter import messagebox

import graph
from graph_viz import GraphVisualizer, BG_COLOR

WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

FONT_FAMILY = "Arial"
FONT_SIZE_LARGE = 20
FONT_SIZE_NORMAL = 19
FONT_SIZE_SMALL = 17

SEARCH_BOX_WIDTH = 45
LISTBOX_HEIGHT = 6
BUTTON_WIDTH = 12
NUMBER_INPUT_WIDTH = 5

PAD_X = 8
PAD_Y = 6

TEXT_FG_PRIMARY = "#e0e0e0"
TEXT_FG_SECONDARY = "#aaaaaa"


class AddSongQuiz(tk.Toplevel):
    def __init__(self, parent, graph_ref, viz_ref, seeds_box_ref, initial_query):
        super().__init__(parent)
        self.graph = graph_ref
        self.viz = viz_ref
        self.seeds_box = seeds_box_ref

        self.title("Add New Song")
        self.geometry("500x700")
        self.configure(bg=BG_COLOR)
        self.grab_set()

        tk.Label(self, text="Song not found! Let's add it.", fg=TEXT_FG_PRIMARY, bg=BG_COLOR,
                 font=(FONT_FAMILY, FONT_SIZE_LARGE, "bold")).pack(pady=15)

        tk.Label(self, text="Song Name:", fg=TEXT_FG_SECONDARY, bg=BG_COLOR).pack(anchor="w", padx=30)
        self.name_var = tk.StringVar(value=initial_query.title())
        tk.Entry(self, textvariable=self.name_var, font=(FONT_FAMILY, FONT_SIZE_NORMAL)).pack(fill="x", padx=30)

        tk.Label(self, text="Artist Name:", fg=TEXT_FG_SECONDARY, bg=BG_COLOR).pack(anchor="w", padx=30, pady=(15, 0))
        self.artist_var = tk.StringVar()
        tk.Entry(self, textvariable=self.artist_var, font=(FONT_FAMILY, FONT_SIZE_NORMAL)).pack(fill="x", padx=30)

        tk.Label(self, text="Release Year:", fg=TEXT_FG_SECONDARY, bg=BG_COLOR).pack(anchor="w", padx=30, pady=(15, 0))
        self.year_var = tk.StringVar(value="2024")
        tk.Entry(self, textvariable=self.year_var, font=(FONT_FAMILY, FONT_SIZE_NORMAL)).pack(fill="x", padx=30)

        tk.Label(self, text="Genre:", fg=TEXT_FG_SECONDARY, bg=BG_COLOR).pack(anchor="w", padx=30, pady=(15, 0))
        self.genre_var = tk.StringVar(value="Pop")
        genres = ["Pop", "Rock", "Electronic/Dance", "Hip-Hop/Soul", "Metal/Punk",
                  "Jazz/Blues", "Classical/Acoustic", "Folk/Country", "World/Regional", "Mood/Other"]
        tk.OptionMenu(self, self.genre_var, *genres).pack(fill="x", padx=30)

        def make_slider(label_text):
            tk.Label(self, text=label_text, fg=TEXT_FG_SECONDARY, bg=BG_COLOR).pack(anchor="w", padx=30, pady=(20, 0))
            slider = tk.Scale(self, from_=1, to=10, orient="horizontal", bg=BG_COLOR, fg=TEXT_FG_PRIMARY,
                              highlightthickness=0, length=350)
            slider.set(5)
            slider.pack(padx=30)
            return slider

        self.dance_slider = make_slider("Danceability (1=Slow, 10=Club Anthem):")
        self.energy_slider = make_slider("Energy (1=Calm, 10=Intense):")
        self.mood_slider = make_slider("Mood (1=Sad/Dark, 10=Happy/Upbeat):")

        tk.Button(self, text="Add to Graph & Seeds", command=self.submit_song,
                  font=(FONT_FAMILY, FONT_SIZE_NORMAL, "bold"), bg="#27AE60", fg="white",
                  padx=10, pady=5).pack(pady=30)

    def submit_song(self):
        name = self.name_var.get().strip()
        artist = self.artist_var.get().strip()
        year = self.year_var.get().strip()
        genre = self.genre_var.get()

        if not name or not artist or not year.isdigit():
            messagebox.showerror("Error", "Please fill out Name, Artist, and a valid Year.", parent=self)
            return

        dance = self.dance_slider.get() / 10.0
        energy = self.energy_slider.get() / 10.0
        valence = self.mood_slider.get() / 10.0
        loudness = -30.0 + (energy * 30.0)

        self.graph.add_song(
            artist=artist, name=name, popularity=0.5, year=year, genre=genre,
            dance=dance, energy=energy, key=5.0, loud=loudness, mode=1.0,
            speech=0.05, acoustic=0.2, instrument=0.0, live=0.1, valence=valence,
            tempo=120.0, duration=200000.0, time_signature=4.0)
        self.seeds_box.insert(tk.END, name)
        self.viz.inject_songs([name])

        all_seeds = list(self.seeds_box.get(0, tk.END))
        self.viz.highlight_songs([], seed_songs=all_seeds)
        self.viz.focus_on_song(name)

        song_name_display = name
        self.destroy()
        messagebox.showinfo("Success", f"'{song_name_display}' has been added to the graph and your seeds!")


def main():
    music_graph = graph.make_graph()

    root = tk.Tk()
    root.title("Music recommender — graph view")
    root.configure(bg=BG_COLOR)

    try:
        root.state('zoomed')
    except tk.TclError:
        root.attributes('-zoomed', True)

    top = tk.Frame(root, bg=BG_COLOR)
    top.pack(side="top", fill="x", padx=PAD_X, pady=PAD_Y)

    tk.Label(top, text="Search song or artist:", fg=TEXT_FG_PRIMARY, bg=BG_COLOR,
             font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(anchor="w")

    search_row = tk.Frame(top, bg=BG_COLOR)
    search_row.pack(fill="x", pady=2)

    search_var = tk.StringVar()
    search_entry = tk.Entry(search_row, textvariable=search_var, width=SEARCH_BOX_WIDTH,
                            font=(FONT_FAMILY, FONT_SIZE_LARGE))
    search_entry.pack(side="left", padx=(0, PAD_X))

    lists_row = tk.Frame(top, bg=BG_COLOR)
    lists_row.pack(fill="x", pady=PAD_Y)

    left_col = tk.Frame(lists_row, bg=BG_COLOR)
    left_col.pack(side="left", fill="both", expand=True, padx=(0, PAD_X))
    tk.Label(left_col, text="Search results", fg=TEXT_FG_SECONDARY, bg=BG_COLOR,
             font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(anchor="w")

    results_scroll = tk.Scrollbar(left_col)
    results_scroll.pack(side="right", fill="y")
    results_box = tk.Listbox(
        left_col, height=LISTBOX_HEIGHT, font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        yscrollcommand=results_scroll.set, selectmode=tk.SINGLE
    )
    results_box.pack(side="left", fill="both", expand=True)
    results_scroll.config(command=results_box.yview)

    mid_col = tk.Frame(lists_row, bg=BG_COLOR)
    mid_col.pack(side="left", fill="both", expand=True, padx=(0, PAD_X))
    tk.Label(mid_col, text="Seed songs", fg=TEXT_FG_SECONDARY, bg=BG_COLOR,
             font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(anchor="w")

    seeds_scroll = tk.Scrollbar(mid_col)
    seeds_scroll.pack(side="right", fill="y")
    seeds_box = tk.Listbox(
        mid_col, height=LISTBOX_HEIGHT, font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        yscrollcommand=seeds_scroll.set, selectmode=tk.SINGLE
    )
    seeds_box.pack(side="left", fill="both", expand=True)
    seeds_scroll.config(command=seeds_box.yview)

    right_col = tk.Frame(lists_row, bg=BG_COLOR)
    right_col.pack(side="left", fill="both", expand=True)
    tk.Label(right_col, text="Recommended Tracks", fg="#FFD700", bg=BG_COLOR,
             font=(FONT_FAMILY, FONT_SIZE_SMALL, "bold")).pack(anchor="w")

    recs_scroll = tk.Scrollbar(right_col)
    recs_scroll.pack(side="right", fill="y")
    recs_box = tk.Listbox(
        right_col, height=LISTBOX_HEIGHT, font=(FONT_FAMILY, FONT_SIZE_NORMAL),
        yscrollcommand=recs_scroll.set, selectmode=tk.SINGLE
    )
    recs_box.pack(side="left", fill="both", expand=True)
    recs_scroll.config(command=recs_box.yview)

    search_results = []

    def run_search():
        results_box.delete(0, tk.END)
        search_results.clear()
        query = search_var.get().strip()
        if not query:
            return

        found = music_graph.search_songs(query)

        if not found:
            response = messagebox.askyesno(
                "Not Found",
                f"No exact matches for '{query}'.\n\nWould you like to manually add it to the graph?"
            )
            if response:
                AddSongQuiz(root, music_graph, viz, seeds_box, query)
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

        recs_box.delete(0, tk.END)
        for name in rec_names:
            recs_box.insert(tk.END, name)

        viz.highlight_songs(rec_names, seed_songs=list(seeds))
        if recs:
            for rec in rec_names:
                viz.focus_on_song(rec)
            viz.focus_on_song(rec_names[0])

    def clear_all():
        viz.clear_highlights()
        recs_box.delete(0, tk.END)

    search_entry.bind("<Return>", lambda e: run_search())

    tk.Button(search_row, text="Search", command=run_search, width=BUTTON_WIDTH,
              font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side="left")

    btn_row = tk.Frame(top, bg=BG_COLOR)
    btn_row.pack(fill="x", pady=4)

    tk.Label(btn_row, text="Number of recommendations:", fg=TEXT_FG_PRIMARY, bg=BG_COLOR,
             font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side="left")
    count_var = tk.StringVar(value="15")
    tk.Entry(btn_row, textvariable=count_var, width=NUMBER_INPUT_WIDTH,
             font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side="left", padx=6)

    tk.Button(btn_row, text="Add Seed", command=add_seed, font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side="left",
                                                                                                    padx=(20, 4))
    tk.Button(btn_row, text="Remove Seed", command=remove_seed, font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side="left",
                                                                                                          padx=4)
    tk.Button(btn_row, text="Get Recommendations", command=do_recommendations,
              font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(side="left", padx=12)
    tk.Button(btn_row, text="Clear Highlights", command=clear_all, font=(FONT_FAMILY, FONT_SIZE_SMALL)).pack(
        side="left", padx=4)

    graph_frame = tk.Frame(root, bg=BG_COLOR)
    graph_frame.pack(side="top", fill="both", expand=True, padx=PAD_X, pady=(0, PAD_X))

    viz = GraphVisualizer(
        parent_frame=graph_frame,
        song_graph=music_graph,
        sample_size=500
    )

    viz.on_song_click = lambda song_name, attrs: viz.focus_on_song(song_name)
    viz.frame.pack(fill="both", expand=True)

    def on_listbox_click(event):
        widget = event.widget
        sel = widget.curselection()

        if sel:
            song_name = widget.get(sel[0])
            viz.display_song_info(song_name)

            if widget == recs_box:
                viz.focus_on_song(song_name)

    results_box.bind("<<ListboxSelect>>", on_listbox_click)
    seeds_box.bind("<<ListboxSelect>>", on_listbox_click)
    recs_box.bind("<<ListboxSelect>>", on_listbox_click)

    root.mainloop()


if __name__ == "__main__":
    main()
