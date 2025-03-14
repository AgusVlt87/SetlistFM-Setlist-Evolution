import sys, os, pathlib, math, numpy, argparse, re, json, collections, math, subprocess
from matplotlib import pyplot as plt
from celluloid import Camera
from concurrent.futures import ThreadPoolExecutor


path = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/").strip()

cleanRegex = re.compile("[^a-zA-Z0-9]")

albumcolors = []# ["red", "lightblue", "orange", "yellow", "gray", "black", "plum"]


def main(args):
	
	if args.numprobes == -1:
		args.numprobes = 16 if args.mode == 0 else 356
		
	if len(args.setlistfile) <= 5:
		return
		
	if not (args.setlistfile[1] == ":" or args.setlistfile[0] == "/"):
		args.setlistfile = str(pathlib.Path().cwd() / args.setlistfile)
		
	interpFrames = 0
	if args.fps > 1000.0/args.interval:
		interpFrames = int(args.fps/(1000.0/args.interval) + 0.5)-1
		
	setlistdata = dict()
	
	with open(args.setlistfile, "r") as file:
		setlistdata = json.loads(file.read())
	
	setlistdata = [st for st in setlistdata if len(st["songs"]) > 0]
	
	artist = setlistdata[0]["artist"]
	outfile = args.out if args.out else artist+".mp4"
		
	artistdata = dict()
	
	with open(path + "/album_data/" + "Los Piojos" + ".json", "r") as file:
		artistdata = json.loads(file.read())
	
	start = max(args.start, 0)
	end = args.end if args.end > 0 else len(setlistdata)-1
	end = min(len(setlistdata)-1, end)
	
	if end - start < 0:
		if not args.quiet:
			print("End - Start < 0...")
		return
	
	chunksize = 100
	
	if args.mp < 1 or chunksize >=end-start:
	
		fig = plt.figure(figsize=[12.8, 4.8], dpi=100)
		fig.tight_layout()
		
		'''
		albmsngs = dict()
		for album in artistdata["albums"]:
			albmsngs[album["title"]] = []
			for song in album["tracks"]:
				albmsngs[album["title"]].append(cleanTitle(song))
			if "bsides" in album.keys():
				for song in album["bsides"]:
					albmsngs[album["title"]].append(cleanTitle(song))
		'''
		
		camera = Camera(fig)
		
		songcounts = dict()
		for album in artistdata["albums"]:
			for song in album["tracks"]:
				songcounts[cleanTitle(song)] = collections.deque(maxlen=args.numprobes)
			if "bsides" in album.keys():
				for song in album["bsides"]:
					songcounts[cleanTitle(song)] = collections.deque(maxlen=args.numprobes)
		
		visible_albums = []
		
		if not args.quiet:
			print("Plotting data for "+str(end-start+1)+" setlists.")
		
		lastvals = dict()
		songvals = dict()
		for sng in songcounts.keys():
			songvals[sng] = 0.0
			
		artistdata_cleaned = artistdata.copy()
		for album in artistdata["albums"]:
			for i in range(len(album["tracks"])):
				album["tracks"][i] = cleanTitle(album["tracks"][i])
			if "bsides" in album.keys():
				for i in range(len(album["bsides"])):
					album["bsides"][i] = cleanTitle(album["bsides"][i])
		
		
		precollect = 0
		if start > 0:
			precollect = min(args.numprobes, start)
		
		x = 0
		for i in range(len(setlistdata)-1-start+precollect, len(setlistdata)-end-1-1, -1):
			
			if x >= precollect and not args.quiet:
				print("\rGraph "+str(len(setlistdata)-1-i-precollect)+"/"+str(end), end="")
			
			setlist = setlistdata[i]
			if len(setlist["songs"]) <= 0:
				continue
			
			st = [cleanTitle(s) for s in setlist["songs"]]
			
			for sng in songcounts.keys():
				songcounts[sng].append(1 if sng in st else 0)
			
			'''
			if len(visible_albums) != len(artistdata["albums"]):
				for sng in st:
					for albumtitle in albmsngs.keys():
						if not albumtitle in visible_albums and sng in albmsngs[albumtitle]:
							visible_albums.append(albumtitle)
			'''
			
			lastvals = songvals.copy()
			songvals = dict()
			mx = 1
			for sng in songcounts.keys():
				songvals[sng] = sum(songcounts[sng])
				mx = max(mx, songvals[sng])
			for sng in songcounts.keys():
				songvals[sng] = songvals[sng] / mx
			
			'''
			allsngs = set()
			for st in setlistdata:
				for song in st["songs"]:
					allsngs.add(cleanTitle(song))
			for sng in allsngs:
				if sng in songvals.keys():
					songvals[sng] = 1
			'''
			
			if x >= precollect:
				for j in range(1, interpFrames+2):
					
					sv = interpolateSongvals(lastvals, songvals, j, interpFrames+1)
					
					plot(fig, sv, artistdata, artistdata_cleaned, camera)
					
					fig.axes[0].text(0.2, 1.02, "Average data of the last "+str(args.numprobes)+\
								" shows until "+str(setlist["year"])+"."+str(setlist["month"]).zfill(2)\
								+"."+str(setlist["day"]).zfill(2), transform=fig.axes[0].transAxes)
				
					fig.tight_layout()
					#plt.show()
					camera.snap()
					
			x += 1
				
		if not args.quiet:	
			print("\rRendering video.")
		
		interval = args.interval if interpFrames <= 0 else int(args.interval / float(interpFrames+1) + 0.5)
		animation = camera.animate(interval=interval)
		animation.save(outfile, writer="ffmpeg")
			
	else:
		
		chunks = int(math.ceil((end-start+1) / chunksize))
		
		if not args.quiet:
			print("Processing "+str(chunks)+" chunks.")
		
		txtlst = ""
		partfiles = []
		
		with ThreadPoolExecutor(max_workers=args.mp) as xec:
			for i in range(0, chunks):
				
				partfile = outfile[:-4]+".part"+str(i).zfill(3)+outfile[-4:]
				partfiles.append(partfile)
				txtlst += "file '"+partfile+"'\n"
				
				s = start + chunksize * i
				e = min(end, start + chunksize * (i+1) - 1)
				
				xec.submit(processChunk, i, s, e, partfile, args)
		
		txtfile = outfile[:-4]+"_list.txt"
		
		with open(txtfile, "w+") as f:
			f.write(txtlst)
		
		while os.path.isfile(outfile):
			outfile = outfile[:-4]+"_"+outfile[-4:]
		
		cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", txtfile, "-c", "copy", outfile]
		subprocess.run(cmd)
		
		if os.path.isfile(txtfile):
			os.remove(txtfile)
		for p in partfiles:
			if os.path.isfile(p):
				os.remove(p)
			
		
def processChunk(i, start, end, partfile, args):
	
	cmd = ["python", path+"/plot.py", args.setlistfile, "-s", str(start), "-e", str(end), "-o", partfile,\
			"--fps", str(args.fps), "-n", str(args.numprobes), "--interval", str(args.interval), "--mode",\
			str(args.mode), "--quiet"]
	
	subprocess.run(cmd, shell=False)
	
	if not args.quiet:
		print("Chunk "+str(i)+" finished.")
		
		
def interpolateSongvals(lastVals, vals, ind, interpFrames):
	
	if ind >= interpFrames:
		return vals
		
	sv = dict()
	for sng in vals.keys():
		lv = lastVals[sng]
		nv = vals[sng]
		sv[sng] = lv + (nv - lv) * (ind / interpFrames)
		
	return sv
	
	
def plot(fig, songvals, artistdata, artistdata_cleaned, camera, albums=None):
	
	width = 1
	pad = 1	
	
	numsongs = 0
	album_numsongs = []
	xticks = []
	
	i = 0
	for album in artistdata["albums"]:
		n = len(album["tracks"])
		if "bsides" in album.keys():
			n += len(album["bsides"])
		tick = numsongs * width + n * 0.5 * width + i * pad - 0.5 * width
		xticks.append(tick)
		numsongs += n
		album_numsongs.append(n)
		i+= 1
	
	id = 0
	i = 0
	j = 0
	for album in artistdata_cleaned["albums"]:
		if albums == None or album["title"] in albums:
			setBars(album["tracks"], j, i, id, songvals, width, pad, album, False)
			j += len(album["tracks"])
			
			if "bsides" in album.keys():
				setBars(album["bsides"], j, i, id, songvals, width, pad, album, True)
				j += len(album["bsides"])
			i += 1
		id += 1
		
	fig.axes[0].set_xticks(xticks)
	fig.axes[0].set_xticklabels([a["title"] for a in artistdata["albums"]])
	
	if artistdata["artist"] == "Paramore":
		for i in [1,4]:
			fig.axes[0].xaxis.get_majorticklabels()[i].set_y(-.04)
	elif artistdata["artist"] == "Deftones":
		fig.axes[0].xaxis.get_majorticklabels()[6].set_y(-.04)
	
	fig.axes[0].set_yticks([])
	
	
def setBars(songs, j, i, albumNr, songvals, width, pad, albumdata, bsides):
	
	color = "red"
	if "color" in albumdata.keys():
		color = albumdata["color"]
	elif len(albumcolors) > albumNr:
		color = albumcolors[albumNr]
	
	#edgecolor = "white" if color == "black" else "black"
	edgecolor = "white"
	alpha = 1.0 if not bsides else 0.5
	
	pos = [(n+j) * width + pad * i for n in range(len(songs))]
	vals = [songvals[sng] for sng in songs]
	
	plt.bar(pos, vals, width, edgecolor=edgecolor, linewidth=0.5, color=color, alpha=alpha)
		
		
def cleanTitle(s):
	
	s = s.lower()
	s = cleanRegex.sub("", s)
	s = s.strip()
	
	return s
	
	
if __name__ == "__main__":
	
	parser = argparse.ArgumentParser()
	parser.add_argument("setlistfile", metavar="infile", type=str, help="The input setlist file in json format.")
	parser.add_argument("-o", "--out", type=str, help="The output plot file.")
	parser.add_argument("-n", "--numprobes", type=int, default=-1, help="Number of setlists/days to collect for the averaging.")
	parser.add_argument("-m", "--mode", type=int, default=0, help="0 for setlist-probes (default), 1 for day-probes")
	parser.add_argument("--interval", type=int, default=150, help="Milliseconds each graph is displayed.")
	parser.add_argument("--fps", type=int, default=-1, help="Interpolate to fps.")
	parser.add_argument("-s", "--start", type=int, default=0, help="Index of setlist to start on "+\
						"(data from prev setlists for numprobes will be taken into account).")
	parser.add_argument("-e", "--end", type=int, default=-1, help="Index of last setlist to include (inclusive).")
	parser.add_argument("--mp", type=int, default=-1, help="Activate multi-processing.")
	parser.add_argument("-q", "--quiet", action="store_true")
	
	args = parser.parse_args(sys.argv[1:])
	
	main(args)