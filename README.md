# MatchMyMusic

## Project Overview

Our project goal is to build an interactive music recommendation program that
takes a user’s favourite songs as input and generates a customized playlist based
entirely on the mathematical similarity of the tracks’ underlying audio features
by using graphs to represent and connect songs. In fact, our project does achieve
this goal. Given one or more seed songs (songs inputted by the user), MatchMyMusic computes recommendations from only the songs’ attributes such as
danceability, energy, tempo, etc., with no consideration of popularity, playlist
placement, or what other users are listening to. The results are displayed as
highlighted nodes on an interactive graph visualization and as a table showing
each recommended song’s full profile (all of its attributes and values), allowing
the user to directly see and compare why each song was recommended

## Reason behind it...
Modern music platforms give listeners access to enormous catalogs, but finding and recommending new songs for every user type that can keep that listener hooked, by just analysing a small array of the listener’s taste, is still difficult. Many recommendation systems heavily rely on collaborative filtering or other behavior-based methods, which infer what a user may like from the habits of other users. While these approaches can be effective, research on music recommendation has also shown that recommender systems often exhibit popularity bias, meaning popular items are overrepresented while less popular items are underrepresented in recommendation lists. We were motivated by this concern and by the broader idea that music discovery should be more transparent and more closely tied to how songs actually sound, rather than to opaque platform behavior or current trends.

##  Instructions for Running the Program

### Step 1: Install required libraries
- Install the required libraries by running the following command in your terminal: `pip install -r requirements.txt`
- The requirements.txt file contains the following libraries: matplotlib, networkx, and python-ta.

### Step 2: Run the program
- Run `main.py`
- On the first launch, if `graph.bin` is not present, the program
will generate the graph from scratch, which takes approximately 15–30 minutes
- If `graph.bin` is present, the graph will load in a few seconds
- Once loaded, a full screen window will appear with the following:
  - A search bar at the top where you can type a song name or artist. Press
Enter on your keyboard or click Search to see matching results appear in
the Search Results list
  - A Search Results list showing matched songs. Click a song and then click
Add Seed to add it to your Seed Songs list. Clicking any song in any list
will display its full audio attributes in the info panel on the right side of
the graph
  - A Seed Songs list showing the songs you have selected as input. Click a
song and then click Remove Seed to remove it
  - A number input where you can set how many recommended songs you
want (default is 15)
  - A Get Recommendations button which runs the algorithm and fills up
the Recommended Tracks list. Recommended songs will be highlighted in
gold on the graph, and seed songs in red-orange
  - A Recommended Tracks list showing the results. Clicking a song in this
list will zoom the graph to that song’s node
  - A Clear Highlights button that resets all highlighting on the graph
  - An interactive graph panel showing 500 randomly sampled songs as coloured
nodes, grouped by genre. You can scroll to zoom in and out, right-click
drag to pan, and click any node to see that song’s attributes
  - A Reset View button restores the original zoom and position of the interactive graph
  - If a searched song is not found in the dataset, a popup will appear asking
if you want to manually add it. You can enter the song’s name, artist,
year, genre, and rate its danceability, energy, and mood using sliders. The
song will then be added to the graph and your seed list automatically


