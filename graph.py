"""
CSC111 Winter 2026 Course Project: MatchMyMusic (Graph)

Module Description
==================
This module contains the _Song and Graph classes used to represent songs
and the similarities between other songs as a weighted graph.
It handles loading song data from a CSV file, loading the graph's edges
using a binary file, normalizing audio attributes, and computing Euclidean
distances between songs. It also provides the recommendation algorithm,
which uses a BFS (Breadth First Search) traversal and an average feature vector across
seed songs to find and rank the most similar songs.

Copyright and Usage Information
===============================
This file is provided solely for the personal and private use of the
authors listed below. All forms of distribution of this code, whether
as given or with any changes, are expressly prohibited.

This file is Copyright (c) 2026 Reuben Kurian Mathew, Arjun Nilesh Alwe, Ritvik Aggarwal
"""

from __future__ import annotations
import csv
from collections import deque, Counter
import math
import itertools
import struct
import os

PARENT_GENRE_MAPPING = {
    'pop': 'Pop', 'indie-pop': 'Pop', 'power-pop': 'Pop', 'k-pop': 'Pop',
    'cantopop': 'Pop', 'pop-film': 'Pop',
    'rock': 'Rock', 'alt-rock': 'Rock', 'hard-rock': 'Rock', 'psych-rock': 'Rock',
    'rock-n-roll': 'Rock', 'ska': 'Rock', 'singer-songwriter': 'Rock', 'songwriter': 'Rock',
    'electronic': 'Electronic/Dance', 'dance': 'Electronic/Dance', 'electro': 'Electronic/Dance',
    'house': 'Electronic/Dance', 'techno': 'Electronic/Dance', 'edm': 'Electronic/Dance',
    'trance': 'Electronic/Dance', 'dubstep': 'Electronic/Dance', 'drum-and-bass': 'Electronic/Dance',
    'chicago-house': 'Electronic/Dance', 'detroit-techno': 'Electronic/Dance',
    'progressive-house': 'Electronic/Dance', 'minimal-techno': 'Electronic/Dance',
    'deep-house': 'Electronic/Dance', 'garage': 'Electronic/Dance', 'breakbeat': 'Electronic/Dance',
    'club': 'Electronic/Dance', 'hardstyle': 'Electronic/Dance', 'party': 'Electronic/Dance',
    'groove': 'Electronic/Dance', 'chill': 'Electronic/Dance',
    'hip-hop': 'Hip-Hop/Soul', 'soul': 'Hip-Hop/Soul', 'funk': 'Hip-Hop/Soul',
    'trip-hop': 'Hip-Hop/Soul', 'dub': 'Hip-Hop/Soul',
    'metal': 'Metal/Punk', 'heavy-metal': 'Metal/Punk', 'death-metal': 'Metal/Punk',
    'black-metal': 'Metal/Punk', 'metalcore': 'Metal/Punk', 'hardcore': 'Metal/Punk',
    'grindcore': 'Metal/Punk', 'punk': 'Metal/Punk', 'punk-rock': 'Metal/Punk',
    'emo': 'Metal/Punk', 'goth': 'Metal/Punk', 'industrial': 'Metal/Punk',
    'jazz': 'Jazz/Blues', 'blues': 'Jazz/Blues',
    'classical': 'Classical/Acoustic', 'opera': 'Classical/Acoustic', 'piano': 'Classical/Acoustic',
    'acoustic': 'Classical/Acoustic', 'new-age': 'Classical/Acoustic', 'ambient': 'Classical/Acoustic',
    'country': 'Folk/Country', 'folk': 'Folk/Country',
    'samba': 'World/Regional', 'tango': 'World/Regional', 'salsa': 'World/Regional',
    'forro': 'World/Regional', 'sertanejo': 'World/Regional', 'dancehall': 'World/Regional',
    'afrobeat': 'World/Regional', 'spanish': 'World/Regional', 'french': 'World/Regional',
    'swedish': 'World/Regional', 'german': 'World/Regional', 'indian': 'World/Regional',
    'comedy': 'Mood/Other', 'show-tunes': 'Mood/Other', 'sleep': 'Mood/Other',
    'sad': 'Mood/Other', 'romance': 'Mood/Other', 'guitar': 'Mood/Other'
}


def normalize(value: float, r: list[float]) -> float:
    """Return the normalized value (between 0.0 and 1.0) of a given float based on the provided [min, max] range.
    Returns 0.0 if the range represents a single value (min == max) to avoid division by zero.
    """
    return (float(value) - r[0]) / (r[1] - r[0]) if r[1] != r[0] else 0.0


class _Song:
    """A track with audio features and connections to mathematically similar songs.

    Instance Attributes:
        - artist: The name of the artist.
        - name: The title of the song combined with the artist name.
        - popularity: A normalized popularity score.
        - year: A normalized release year.
        - genre: The parent genre of the track.
        - dance: Danceability score.
        - energy: Energy score.
        - key: Normalized musical key.
        - loud: Normalized loudness.
        - mode: Modality (major/minor).
        - speech: Speechiness score.
        - acoustic: Acousticness score.
        - instrument: Instrumentalness score.
        - live: Liveness score.
        - valence: Valence (mood) score.
        - tempo: Normalized tempo.
        - duration: Normalized duration.
        - time_signature: Normalized time signature.
        - neighbours: A dictionary mapping neighbour song names to their Euclidean distance.

    Representation Invariants:
        - 0.0 <= self.popularity <= 1.0
        - 0.0 <= self.dance <= 1.0
        - 0.0 <= self.energy <= 1.0
        - 0.0 <= self.key <= 1.0
        - 0.0 <= self.loud <= 1.0
        - 0.0 <= self.mode <= 1.0
        - 0.0 <= self.speech <= 1.0
        - 0.0 <= self.acoustic <= 1.0
        - 0.0 <= self.instrument <= 1.0
        - 0.0 <= self.live <= 1.0
        - 0.0 <= self.valence <= 1.0
        - 0.0 <= self.tempo <= 1.0
        - 0.0 <= self.duration <= 1.0
        - 0.0 <= self.time_signature <= 1.0
    """
    artist: str
    name: str
    popularity: float
    year: float
    genre: str
    dance: float
    energy: float
    key: float
    loud: float
    mode: float
    speech: float
    acoustic: float
    instrument: float
    live: float
    valence: float
    tempo: float
    duration: float
    time_signature: float
    neighbours: dict[str, float]

    def __init__(self, artist: str, name: str, popularity: float, year: float, genre: str, dance: float,
                 energy: float, key: float, loud: float, mode: float, speech: float, acoustic: float,
                 instrument: float, live: float, valence: float, tempo: float, duration: float,
                 time_signature: float) -> None:
        """Initialize a new _Song object with its corresponding audio features."""
        self.name = f"{name} - {artist}"
        self.artist = artist
        self.popularity = float(popularity)
        self.year = float(year)
        self.genre = genre
        self.dance = float(dance)
        self.energy = float(energy)
        self.key = float(key)
        self.loud = float(loud)
        self.mode = float(mode)
        self.speech = float(speech)
        self.acoustic = float(acoustic)
        self.instrument = float(instrument)
        self.live = float(live)
        self.valence = float(valence)
        self.tempo = float(tempo)
        self.duration = float(duration)
        self.time_signature = float(time_signature)
        self.neighbours = {}

    def get_features(self) -> list[float]:
        """Return a list of all normalized mathematical audio features for this song."""
        return [
            self.popularity, self.year, self.dance, self.energy, self.key, self.loud,
            self.mode, self.speech, self.acoustic, self.instrument,
            self.live, self.valence, self.tempo, self.duration, self.time_signature
        ]


def _calculate_song_distance_sq(song1: _Song, song2: _Song) -> float:
    """Return the squared Euclidean distance between two songs based on their audio features.
    Songs of different genres incur a flat penalty to their distance score.
    """
    genre_dist_sq = 0.0 if song1.genre == song2.genre else 1.0
    return (
            (song1.popularity - song2.popularity) ** 2
            + (song1.year - song2.year) ** 2
            + (song1.key - song2.key) ** 2
            + (song1.loud - song2.loud) ** 2
            + (song1.tempo - song2.tempo) ** 2
            + (song1.duration - song2.duration) ** 2
            + (song1.time_signature - song2.time_signature) ** 2
            + (song1.dance - song2.dance) ** 2
            + (song1.energy - song2.energy) ** 2
            + (song1.mode - song2.mode) ** 2
            + (song1.speech - song2.speech) ** 2
            + (song1.acoustic - song2.acoustic) ** 2
            + (song1.instrument - song2.instrument) ** 2
            + (song1.live - song2.live) ** 2
            + (song1.valence - song2.valence) ** 2
            + genre_dist_sq
    )


class Graph:
    """A graph representing a network of songs connected by their acoustic similarities.

    Instance Attributes:
        - genres: A set of all genres found in the dataset.
        - parent_genres: A list of standard parent genres used for classification.
        - threshold: The maximum Euclidean distance allowed for two songs to be connected.

    Private Instance Attributes:
        - _songs: A dictionary mapping song names to their corresponding _Song objects.
        - _year_range: The [min, max] range of release years in the dataset.
        - _key_range: The [min, max] range of keys in the dataset.
        - _loudness_range: The [min, max] range of loudness in the dataset.
        - _tempo_range: The [min, max] range of tempos in the dataset.
        - _duration_range: The [min, max] range of durations in the dataset.
        - _time_sig_range: The [min, max] range of time signatures in the dataset.

    Representation Invariants:
        - self.threshold > 0.0
    """
    _songs: dict[str, _Song]
    _year_range: list[float]
    _key_range: list[float]
    _loudness_range: list[float]
    _tempo_range: list[float]
    _duration_range: list[float]
    _time_sig_range: list[float]
    genres: set[str]
    parent_genres: list[str]
    threshold: float

    def __init__(self, dataset: str, threshold: float, build_edges: bool = True) -> None:
        """Initialize the Graph with a dataset of songs and a similarity threshold.
        If build_edges is True, it will calculate O(n^2) edges from scratch and save them to a binary file.
        If False, it will attempt to load pre-calculated edges from a binary file to save time.
        """
        self._songs = {}
        self._year_range = []
        self._key_range = []
        self._loudness_range = []
        self._tempo_range = []
        self._duration_range = []
        self._time_sig_range = []
        self.genres = set()
        self.threshold = threshold
        self.parent_genres = [
            "Pop", "Rock", "Electronic/Dance", "Hip-Hop/Soul", "Metal/Punk",
            "Jazz/Blues", "Classical/Acoustic", "Folk/Country", "World/Regional", "Mood/Other"
        ]

        self._load_songs(dataset)

        if build_edges:
            self._make_connections()
            self._save_state()
        else:
            self._load_save()

    def _load_songs(self, dataset: str) -> None:
        """Read song data from the provided CSV file, create _Song objects, and determine normalization ranges."""
        years = []
        keys = []
        louds = []
        tempos = []
        durations = []
        time_sigs = []

        with open(dataset, 'r', encoding='utf-8') as songs:
            reader = csv.reader(songs)
            next(reader, None)

            for song_data in reader:
                artist = song_data[0]
                name = song_data[1]
                popularity = float(song_data[2]) / 100.0
                year = float(song_data[3])

                original_genre = song_data[4]
                genre = PARENT_GENRE_MAPPING.get(original_genre, "Mood/Other")

                dance = float(song_data[5])
                energy = float(song_data[6])
                key = float(song_data[7])
                loud = float(song_data[8])
                mode = float(song_data[9])
                speech = float(song_data[10])
                acoustic = float(song_data[11])
                instrument = float(song_data[12])
                live = float(song_data[13])
                valence = float(song_data[14])
                tempo = float(song_data[15])
                duration = float(song_data[16])
                time_signature = float(song_data[17])

                new_song = _Song(artist, name, popularity, year, genre, dance, energy, key, loud, mode, speech,
                                 acoustic, instrument, live, valence, tempo, duration, time_signature)
                self._songs[new_song.name] = new_song

                years.append(year)
                keys.append(key)
                louds.append(loud)
                tempos.append(tempo)
                durations.append(duration)
                time_sigs.append(time_signature)

        self._year_range = [min(years), max(years)]
        self._key_range = [min(keys), max(keys)]
        self._loudness_range = [min(louds), max(louds)]
        self._tempo_range = [min(tempos), max(tempos)]
        self._duration_range = [min(durations), max(durations)]
        self._time_sig_range = [min(time_sigs), max(time_sigs)]

        for song_obj in self._songs.values():
            self._process_song_data(song_obj)

    def _make_connections(self) -> None:
        """Calculate the Euclidean distance between all pairs of songs
        and create an edge if it is below the threshold."""
        threshold_sq = self.threshold ** 2

        for song1, song2 in itertools.combinations(list(self._songs.values()), 2):
            dist_sq = _calculate_song_distance_sq(song1, song2)
            if dist_sq < threshold_sq:
                exact_dist = math.sqrt(dist_sq)
                song1.neighbours[song2.name] = exact_dist
                song2.neighbours[song1.name] = exact_dist

    def _process_song_data(self, song: _Song) -> None:
        """Normalize the scale-dependent audio features of a song so they fall between 0.0 and 1.0."""
        song.year = normalize(song.year, self._year_range)
        song.key = normalize(song.key, self._key_range)
        song.loud = normalize(song.loud, self._loudness_range)
        song.tempo = normalize(song.tempo, self._tempo_range)
        song.duration = normalize(song.duration, self._duration_range)
        song.time_signature = normalize(song.time_signature, self._time_sig_range)

    def _save_state(self) -> None:
        """Serialize the graph's edges and save them to a binary file using the struct module to compress size."""
        song_names = list(self._songs.keys())
        name_to_idx = {s_name: idx for idx, s_name in enumerate(song_names)}

        with open("graph.bin", "wb") as f:
            for idx, s_name in enumerate(song_names):
                song = self._songs[s_name]
                for neighbor, dist in song.neighbours.items():
                    if s_name < neighbor:
                        binary_data = struct.pack('iif', idx, name_to_idx[neighbor], dist)
                        f.write(binary_data)

    def _load_save(self) -> None:
        """Load pre-computed edges from a binary file to rapidly reconstruct the graph."""
        song_names = list(self._songs.keys())
        edge_size = struct.calcsize('iif')

        with open("graph.bin", "rb") as f:
            chunk = f.read(edge_size)
            while chunk:
                u_idx, v_idx, dist = struct.unpack('iif', chunk)
                u_name, v_name = song_names[u_idx], song_names[v_idx]

                self._songs[u_name].neighbours[v_name] = dist
                self._songs[v_name].neighbours[u_name] = dist
                chunk = f.read(edge_size)

    def add_song(self, artist: str, name: str, popularity: float, year: float, genre: str, dance: float,
                 energy: float, key: float, loud: float, mode: float, speech: float, acoustic: float,
                 instrument: float, live: float, valence: float, tempo: float, duration: float,
                 time_signature: float) -> None:
        """Create a new song, normalize its features, and connect it to its nearest neighbors in the existing graph."""
        song = _Song(artist, name, popularity, year, genre, dance, energy, key, loud, mode, speech, acoustic,
                     instrument, live, valence, tempo, duration, time_signature)
        self._process_song_data(song)

        threshold_sq = self.threshold ** 2

        for existing_song in self._songs.values():
            dist_sq = _calculate_song_distance_sq(song, existing_song)

            if dist_sq < threshold_sq:
                exact_dist = math.sqrt(dist_sq)
                song.neighbours[existing_song.name] = exact_dist
                existing_song.neighbours[song.name] = exact_dist

        self._songs[song.name] = song

    def recommend(self, songs: list[str], num_req: int = 10) -> list[_Song]:
        """Perform a Breadth-First Search starting from the provided seed songs to find recommendations.
        Calculates a centroid 'average' song based on the seeds, traverses out to depth 2, and ranks candidates
        by their distance to the centroid, rewarding songs that act as co-citations between multiple seeds.
        """
        if not songs:
            return []

        num_seeds = len(songs)
        seed_songs = [s_obj for n in songs if (s_obj := self.get_song(n)) is not None]
        genres = [s_obj.genre for s_obj in seed_songs]
        most_common_genre = Counter(genres).most_common(1)[0][0]

        seed_features = [s_obj.get_features() for s_obj in seed_songs]
        avg_features = [sum(col) / num_seeds for col in zip(*seed_features)]

        avg_song = _Song("User", "Average Song", avg_features[0], avg_features[1],
                         most_common_genre, *avg_features[2:])

        discovered = {}
        queue = deque([(seed.name, 0) for seed in seed_songs])

        while queue:
            curr_name, depth = queue.popleft()

            if depth >= 2:
                continue

            curr_song = self._songs[curr_name]

            for neighbor_name in curr_song.neighbours:
                if neighbor_name in songs:
                    continue

                if neighbor_name not in discovered:
                    discovered[neighbor_name] = {'depth': depth + 1, 'count': 1}
                    queue.append((neighbor_name, depth + 1))
                else:
                    discovered[neighbor_name]['count'] += 1

        candidates = []
        threshold_sq = self.threshold ** 2

        for neighbor_name, stats in discovered.items():
            neighbor_song = self._songs[neighbor_name]
            dist_sq = _calculate_song_distance_sq(avg_song, neighbor_song)

            if dist_sq < threshold_sq:
                repeats = (stats['count'] - 1) * 0.15
                final_score = dist_sq - repeats
                candidates.append((final_score, neighbor_song))

        candidates.sort(key=lambda x: x[0])

        return [s_obj for score, s_obj in candidates[:num_req]]

    def get_song(self, name: str) -> _Song | None:
        """Return the _Song object corresponding to the given name, or None if it does not exist."""
        return self._songs.get(name)

    def search_songs(self, query: str, limit: int = 20) -> list[str]:
        """Search the graph for songs whose title or artist matches the query string (case-insensitive)."""
        found = []
        q = query.lower()
        for name, song in self._songs.items():
            if q in name.lower() or q in song.artist.lower():
                found.append(name)
            if len(found) >= limit:
                break
        return found

    def get_all_song_names(self) -> list[str]:
        """Return a list of the names of all songs currently loaded in the graph."""
        return list(self._songs.keys())

    def get_stats(self, song_name: str) -> dict[str, str]:
        """Reverse normalization math to return clean, formatted, human-readable statistics for a specific song."""
        song = self.get_song(song_name)
        if not song:
            return {}

        def denormalize(norm_val: float, val_range: list[float]) -> float:
            """Helper function to reverse the 0.0 to 1.0 normalization process using the original bounds."""
            if not val_range or val_range[1] == val_range[0]:
                return val_range[0] if val_range else 0.0
            return (norm_val * (val_range[1] - val_range[0])) + val_range[0]

        year = round(denormalize(song.year, self._year_range))
        key = round(denormalize(song.key, self._key_range))
        loud = denormalize(song.loud, self._loudness_range)
        tempo = denormalize(song.tempo, self._tempo_range)
        duration_ms = denormalize(song.duration, self._duration_range)
        time_sig = round(denormalize(song.time_signature, self._time_sig_range))

        seconds = int((duration_ms / 1000) % 60)
        minutes = int((duration_ms / (1000 * 60)) % 60)
        duration_formatted = f"{minutes}:{seconds:02d}"

        popularity_raw = round(song.popularity * 100)

        return {
            "Artist": song.artist,
            "Genre": song.genre,
            "Release Year": str(year),
            "Popularity": f"{popularity_raw}/100",
            "Danceability": f"{song.dance:.2f}",
            "Energy": f"{song.energy:.2f}",
            "Key": str(key),
            "Loudness": f"{loud:.1f} dB",
            "Mode": "Major" if song.mode >= 0.5 else "Minor",
            "Speechiness": f"{song.speech:.2f}",
            "Acousticness": f"{song.acoustic:.2f}",
            "Instrumentalness": f"{song.instrument:.2f}",
            "Liveness": f"{song.live:.2f}",
            "Valence (Mood)": f"{song.valence:.2f}",
            "Tempo": f"{tempo:.0f} BPM",
            "Duration": duration_formatted,
            "Time Signature": f"{time_sig}/4"
        }


def make_graph() -> Graph:
    """Initialize and return the main Graph object by loading the dataset and determining if edges need to be built."""
    dataset_file = "spotify_19k.csv"
    threshold = 0.7

    if os.path.exists("graph.bin"):
        print("Found save file!")
        graph = Graph(dataset_file, threshold, build_edges=False)
    else:
        print("Save file not found. Generating new graph...")
        graph = Graph(dataset_file, threshold)

    return graph


if __name__ == '__main__':
    import doctest

    doctest.testmod()

    import python_ta

    python_ta.check_all(config={
        'extra-imports': [
            'csv', 'collections', 'typing', 'math', 'itertools', 'struct', 'os'
        ],
        'allowed-io': [
            '_load_songs', '_save_state', '_load_save', 'make_graph'
        ],
        'max-line-length': 120,
        'disable': [
            'E1136',
            'too-many-instance-attributes',
            'too-many-arguments',
            'too-many-locals'
        ]
    })
