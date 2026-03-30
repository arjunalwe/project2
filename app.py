import graph
import pickle
import sys
import tkinter as tk
from tkinter import ttk, messagebox

Graph = graph.Graph
_Song = graph._Song
sys.modules["__main__"].Graph = graph.Graph
sys.modules["__main__"]._Song = graph._Song

class MusicApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Music Graph Browser")
        self.root.geometry("900x600")

        self.graph = None
        self.current_song_names = []

        self.load_graph()
        self.make_widgets()
        self.fill_song_list("")

    def load_graph(self):
        try:
            with open("graph.pkl", "rb") as file:
                self.graph = pickle.load(file)
        except FileNotFoundError:
            messagebox.showerror("Error", "graph.pkl was not found.")
            self.root.destroy()
        except Exception as error:
            messagebox.showerror("Error", f"Could not load graph.pkl\n\n{error}")
            self.root.destroy()

    def make_widgets(self):
        top_frame = tk.Frame(self.root)
        top_frame.pack(fill="x", padx=10, pady=10)

        search_label = tk.Label(top_frame, text="Search by song or artist:")
        search_label.pack(side="left")

        self.search_entry = tk.Entry(top_frame, width=40)
        self.search_entry.pack(side="left", padx=10)
        self.search_entry.bind("<KeyRelease>", self.search_songs)

        clear_button = tk.Button(top_frame, text="Clear", command=self.clear_search)
        clear_button.pack(side="left")

        main_frame = tk.Frame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        left_frame = tk.Frame(main_frame)
        left_frame.pack(side="left", fill="y")

        song_label = tk.Label(left_frame, text="Songs")
        song_label.pack()

        self.song_listbox = tk.Listbox(left_frame, width=40, height=25)
        self.song_listbox.pack(side="left", fill="y")
        self.song_listbox.bind("<<ListboxSelect>>", self.show_selected_song)

        song_scrollbar = tk.Scrollbar(left_frame, orient="vertical")
        song_scrollbar.pack(side="left", fill="y")

        self.song_listbox.config(yscrollcommand=song_scrollbar.set)
        song_scrollbar.config(command=self.song_listbox.yview)

        right_frame = tk.Frame(main_frame)
        right_frame.pack(side="left", fill="both", expand=True, padx=(20, 0))

        details_label = tk.Label(right_frame, text="Song Details")
        details_label.pack(anchor="w")

        self.details_text = tk.Text(right_frame, width=60, height=18)
        self.details_text.pack(fill="both", expand=False)
        self.details_text.config(state="disabled")

        neighbours_label = tk.Label(right_frame, text="Closest Neighbours")
        neighbours_label.pack(anchor="w", pady=(15, 0))

        self.neighbour_listbox = tk.Listbox(right_frame, width=60, height=12)
        self.neighbour_listbox.pack(fill="both", expand=True)
        self.neighbour_listbox.bind("<Double-Button-1>", self.open_neighbour)

        open_button = tk.Button(
            right_frame,
            text="Open Selected Neighbour",
            command=self.open_neighbour
        )
        open_button.pack(anchor="w", pady=8)

    def clear_search(self):
        self.search_entry.delete(0, tk.END)
        self.fill_song_list("")

    def search_songs(self, event=None):
        text = self.search_entry.get().strip().lower()
        self.fill_song_list(text)

    def fill_song_list(self, text):
        self.song_listbox.delete(0, tk.END)
        self.current_song_names = []

        all_song_names = sorted(self.graph._songs.keys())

        for song_name in all_song_names:
            song = self.graph._songs[song_name]

            song_name_text = song.name.lower()
            artist_text = song.artist.lower()

            if text == "" or text in song_name_text or text in artist_text:
                display_text = f"{song.name} - {song.artist}"
                self.song_listbox.insert(tk.END, display_text)
                self.current_song_names.append(song_name)

    def show_selected_song(self, event=None):
        selection = self.song_listbox.curselection()

        if not selection:
            return

        index = selection[0]
        song_name = self.current_song_names[index]
        song = self.graph._songs[song_name]

        details = ""
        details += f"Name: {song.name}\n"
        details += f"Artist: {song.artist}\n"
        details += f"Genre: {song.genre}\n"
        details += f"Popularity: {song.popularity:.3f}\n"
        details += f"Year: {song.year:.3f}\n"
        details += f"Dance: {song.dance:.3f}\n"
        details += f"Energy: {song.energy:.3f}\n"
        details += f"Key: {song.key:.3f}\n"
        details += f"Loudness: {song.loud:.3f}\n"
        details += f"Mode: {song.mode:.3f}\n"
        details += f"Speech: {song.speech:.3f}\n"
        details += f"Acoustic: {song.acoustic:.3f}\n"
        details += f"Instrumental: {song.instrument:.3f}\n"
        details += f"Live: {song.live:.3f}\n"
        details += f"Valence: {song.valence:.3f}\n"
        details += f"Tempo: {song.tempo:.3f}\n"
        details += f"Duration: {song.duration:.3f}\n"
        details += f"Time Signature: {song.time_signature:.3f}\n"
        details += f"Number of neighbours: {len(song.neighbours)}\n"

        self.details_text.config(state="normal")
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", details)
        self.details_text.config(state="disabled")

        self.neighbour_listbox.delete(0, tk.END)

        neighbour_items = list(song.neighbours.items())
        neighbour_items.sort(key=lambda item: item[1])

        limit = 20
        count = 0

        for neighbour_name, distance in neighbour_items:
            line = f"{neighbour_name}    distance = {distance:.3f}"
            self.neighbour_listbox.insert(tk.END, line)
            count += 1

            if count >= limit:
                break

    def open_neighbour(self, event=None):
        selection = self.neighbour_listbox.curselection()

        if not selection:
            return

        line = self.neighbour_listbox.get(selection[0])

        parts = line.split("    distance = ")
        neighbour_name = parts[0]

        self.search_entry.delete(0, tk.END)
        self.fill_song_list("")

        if neighbour_name in self.current_song_names:
            index = self.current_song_names.index(neighbour_name)
            self.song_listbox.selection_clear(0, tk.END)
            self.song_listbox.selection_set(index)
            self.song_listbox.activate(index)
            self.song_listbox.see(index)
            self.show_selected_song()


root = tk.Tk()
app = MusicApp(root)
root.mainloop()