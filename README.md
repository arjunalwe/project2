Modern music platforms give listeners access to enormous catalogs, but finding and recommending new songs for every user type that can keep that listener hooked, by just analysing a small array of the listener’s taste, is still difficult. Many recommendation systems heavily rely on collaborative filtering or other behavior-based methods, which infer what a user may like from the habits of other users. While these approaches can be effective, research on music recommendation has also shown that recommender systems often exhibit popularity bias, meaning popular items are overrepresented while less popular items are underrepresented in recommendation lists. We were motivated by this concern and by the broader idea that music discovery should be more transparent and more closely tied to how songs actually sound, rather than to opaque platform behavior or current trends.

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
