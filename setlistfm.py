from urllib.request import urlopen, Request
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import os, json, sys, time


path = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/").strip()

user_agent = "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"

month_abr = ["JAN", "FEB", "MAR", "APR", "MAY", "JUN", "JUL", "AUG", "SEP", "OCT", "NOV", "DEC"]


def main(url):
	
	concertUrls = getConcertUrls(url)
	concerts = gatherConcertData(concertUrls)
	
	if len(concerts) != len(concertUrls):
		print("Parsed "+str(len(concerts))+" setlists ("+str(len(concertUrls)-len(concerts))+" missing).")
	else:
		print("Parsed "+str(len(concerts))+" setlists.")
	
	writeJsonFile(concerts)
	
	
def writeJsonFile(concerts):
	
	filename = ""
	if len(concerts) == 1:
		filename = concerts[0]["artist"] + " "+concerts[0]["venue"] + " "+\
					str(concerts[0]["year"])+"_"+str(concerts[0]["month"]).zfill(2)+"_"+\
					str(concerts[0]["day"]).zfill(2)
	else:
		artists = list(set([x["artist"] for x in concerts]))
		if len(artists) == 1:
			filename = artists[0]
		else:
			filename = "various artists"
			n = 1
			while os.path.isfile(path+"/"+filename+".json"):
				filename = "various artists "+str(n).zfill(2)
				n += 1
				
	with open(path+"/"+filename+".json", "w+") as f:
		json.dump(concerts, f, indent=4, sort_keys=True)
		
	print("Wrote \""+path+"/"+filename+".json\"")
	
	
def gatherConcertData(concertUrls):
	
	concerts = []
	for i in range(len(concertUrls)):
		concerts.append(None)
	
	with ThreadPoolExecutor(max_workers=16)	as xec:
		for i in range(0, len(concertUrls)):
			xec.submit(getConcertData, i, concertUrls[i], concerts)
	
	#for i in range(0, len(concertUrls)):
	#	getConcertData(i, concertUrls[i], concerts)
		
	while None in concerts:
		concerts.remove(None)
		
	return concerts
		
	
def getConcertData(i, url, concerts):
	
	try:
		
		soup = getSoup(url)
		
		dateBlock = soup.find_all("div", {"class": "dateBlock"})[0]
		infoContainer = soup.find_all("div", {"class": "infoContainer"})[0]
		headLineDiv = infoContainer.find_all("div", {"class": "setlistHeadline"})[0]
		setlistDiv = soup.find_all("div", {"class": "setlistList"})[0]
		
		year = int(dateBlock.find_all("span", {"class": "year"})[0].getText().strip())
		month = dateBlock.find_all("span", {"class": "month"})[0].getText().strip()
		try:
			month = month_abr.index(month.upper())+1
		except:
			month = 1
		day = int(dateBlock.find_all("span", {"class": "day"})[0].getText().strip())
		
		tour = ""
		tour_a = infoContainer.find(lambda tag: tag.name=="a" and "title" in tag.attrs and "setlists by tour" in tag["title"])
		if tour_a:
			tour = tour_a.find_all("span")[0].getText().strip()
		
		venue = ""
		
		venue_a = headLineDiv.find(lambda tag: tag.name=="a" and "title" in tag.attrs and "more setlists from" in tag["title"].lower())
		if venue_a:
			venue = venue_a.find_all("span")[0].getText().strip()
		
		aritst = ""
		
		artist_strong = headLineDiv.find("strong")
		if artist_strong:
			a = artist_strong.find("a")
			if a:
				span = a.find("span")
				if span:
					artist = span.getText().strip()
		
		songs = []
		
		for a in setlistDiv.find_all("a", {"class": "songLabel"}):
			songs.append(a.getText().strip())
		
		print(str(year)+"."+str(month).zfill(2)+"."+str(day).zfill(2)+": "+venue)
		
		data = dict()
		data["artist"] = artist
		data["year"] = year
		data["month"] = month
		data["day"] = day
		data["venue"] = venue
		data["tour"] = tour
		data["songs"] = songs
		
		concerts[i] = data
		
	except:
		pass
	
	
def getConcertUrls(url):
	
	concerts = []
	pageConcerts = []
	
	soup = getSoup(url)
	last_a = soup.find_all("a", {"title": "Go to last page"})[0]
	
	num = int(last_a.getText().strip())
	
	for i in range(num):
		pageConcerts.append([])
	
	with ThreadPoolExecutor(max_workers=16)	as xec:
		for i in range(0, num):
			xec.submit(getPageConcerts, i, pageConcerts, url)
	
	#for i in range(0, num):
	#	getPageConcerts(i, pageConcerts, url)
			
	for page in pageConcerts:
		for c in page:
			concerts.append(c)
			
	return concerts
	
	
def getPageConcerts(i, pageConcerts, baseUrl):
	
	soup = getSoup(baseUrl+"?page="+str(i+1))
	
	for a in soup.find_all("a", {"class": "summary url"}):
		pageConcerts[i].append("https://www.setlist.fm/"+a["href"][3:])
		
	
def getSoup(url):
	
	soup = None
	i = 0
	while i < 100 and soup == None:
		try:
			req = Request(url)
			req.add_header("User-Agent", user_agent)
			with urlopen(req) as resp:
				soup = BeautifulSoup(resp.read(), "html.parser")
		except:
			pass
		if soup == None:
			time.sleep(0.05)
		i += 1
	
	return soup
	
	
if __name__ == "__main__":
	
	url = ""
	
	if len(sys.argv) < 2:
		print("Please specify a SetlistFM Artist URL.")
		exit()
	else:
		url = sys.argv[1].strip()
	
	if url:
		main(url)
	