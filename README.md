# SetlistFM-Setlist-Evolution
Plots graph animations showcasing setlist evolutions of bands with data parsed from setlist.fm

![alt tag](https://github.com/Deconimus/SetlistFM-Setlist-Evolution/blob/master/pic.png)

## How to use

First of all you need to make sure you have `Python 3` and `ffmpeg` installed with both being in your **system path**. Also you'll need to install a few Python libraries via `pip` namely `matplotlib` `celluloid` and `beautifulsoup4`.

There are two scripts that are used in this project. The first one does the parsing from setlist.fm the second one does all the plotting and animation work.

### Scraping Artist Setlists

Use `setlistfm.py` to scrape an artists setlists into a JSON file. You'll need to provide a URL to an **artist page** (important) for it to work properly. Here's an example:

    python setlistfm.py https://www.setlist.fm/setlists/deftones-1bd689cc.html
    
This will store all setlists from Deftones in a file called `deftones.json`. All sets will be stored in reversed chronological order (newer ones first).

### Plotting Graphs

Use `plot.py` to plot graph animations of a setlist file (deftones.json for example). You can use the `--help` command to see a list of all parameters that can be provided.

A basic program call could look like this:

    python plot.py deftones.json
    
I would however advice to make use of the `--mp n` option to specify mutliprocessor use (even `--mp 1` is faster for weird reasons).
Also using `--fps 30` f.e. will make for a smoother animation as it will calculate interpolation frames between the setlists.

The command call I used for [the animation I posted on reddit](https://www.reddit.com/r/deftones/comments/geil9d/deftones_setlist_evolution_according_to_setlistfm/) was:

    python plot.py deftones.json --fps 30 --mp 4
    
#### Plotting other artists

There's one more important thing that needs to be done if you want to plot for a band that is not one of the three provided as an example. You'll need to create a JSON file with the name of the band in the `album_data` folder. The file will contain info about the band's albums with the songs being listed and the color you want it to have in the graph. See the JSON files that are already there for examples.

Oh, and the song names do not have to be 100% perfect, all characters that are not standard english symbols or numbers will be ignored for the string matching. BUT the rest needs to match perfectly of course. Just look up the spelling the songs have in the setlists file.
