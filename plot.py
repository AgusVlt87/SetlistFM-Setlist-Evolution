import sys, os, pathlib, math, numpy, argparse, re, json, collections, math, subprocess
from matplotlib import pyplot as plt
from celluloid import Camera
from concurrent.futures import ThreadPoolExecutor
from matplotlib.animation import PillowWriter
import cv2


path = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/").strip()
cleanRegex = re.compile("[^a-zA-Z0-9]")
albumcolors = []

# Definir el FPS y tamaño del video
frame_rate = 30  # FPS del video
frame_size = (1280, 480)  # Tamaño del video, ajusta según el tamaño de las imágenes
fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # Codec para MP4

def main(args):
    # Tu código aquí, donde se establece la configuración y se carga el setlist
    if args.numprobes == -1:
        args.numprobes = 16 if args.mode == 0 else 356

    if len(args.setlistfile) <= 5:
        return

    if not (args.setlistfile[1] == ":" or args.setlistfile[0] == "/"):
        args.setlistfile = str(pathlib.Path().cwd() / args.setlistfile)

    interpFrames = 0
    if args.fps > 1000.0 / args.interval:
        interpFrames = int(args.fps / (1000.0 / args.interval) + 0.5) - 1

    setlistdata = dict()

    with open(args.setlistfile, "r") as file:
        setlistdata = json.loads(file.read())

    setlistdata = [st for st in setlistdata if len(st["songs"]) > 0]
    artist = setlistdata[0]["artist"]
    outfile = args.out if args.out else artist + ".mp4"

    artistdata = dict()

    with open(path + "/album_data/" + artist + ".json", "r") as file:
        artistdata = json.loads(file.read())

    start = max(args.start, 0)
    end = args.end if args.end > 0 else len(setlistdata) - 1
    end = min(len(setlistdata) - 1, end)

    if end - start < 0:
        if not args.quiet:
            print("End - Start < 0...")
        return

    chunksize = 100

    if args.mp < 1 or chunksize >= end - start:
        fig = plt.figure(figsize=[12.8, 4.8], dpi=100)
        fig.tight_layout()

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
            print("Plotting data for " + str(end - start + 1) + " setlists.")

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

        frame_number = 0  # Variable para numerar los fotogramas
        for i in range(len(setlistdata) - 1 - start + precollect, len(setlistdata) - end - 1 - 1, -1):

            if frame_number >= precollect and not args.quiet:
                print("\rGraph " + str(len(setlistdata) - 1 - i - precollect) + "/" + str(end), end="")

            setlist = setlistdata[i]
            if len(setlist["songs"]) <= 0:
                continue

            st = [cleanTitle(s) for s in setlist["songs"]]

            for sng in songcounts.keys():
                songcounts[sng].append(1 if sng in st else 0)

            lastvals = songvals.copy()
            songvals = dict()
            mx = 1
            for sng in songcounts.keys():
                songvals[sng] = sum(songcounts[sng])
                mx = max(mx, songvals[sng])
            for sng in songcounts.keys():
                songvals[sng] = songvals[sng] / mx

            if frame_number >= precollect:
                for j in range(1, interpFrames + 2):
                    sv = interpolateSongvals(lastvals, songvals, j, interpFrames + 1)
                    plot(fig, sv, artistdata, artistdata_cleaned, camera)

                    fig.axes[0].text(0.2, 1.02, "Promedio de los" + " " + str(args.numprobes) +
                                     " shows desde el 21.09.1991", transform=fig.axes[0].transAxes)

                    fig.tight_layout()

                    # Guardar cada fotograma como una imagen
                    filename = f'frame_{frame_number:04d}.png'
                    plt.savefig(filename)
                    frame_number += 1

                    camera.snap()

        if not args.quiet:
            print("\rRendering video.")

        create_video_from_frames()

    else:
        # Tu código para manejar el caso de procesamiento por chunks aquí...
        pass

def create_video_from_frames():
    # Crear el objeto VideoWriter
    out = cv2.VideoWriter('output.mp4', fourcc, frame_rate, frame_size)

    frame_number = 0
    while os.path.exists(f'frame_{frame_number:04d}.png'):
        img = cv2.imread(f'frame_{frame_number:04d}.png')  # Leer la imagen
        img = cv2.resize(img, frame_size)  # Asegurarse de que todas las imágenes tengan el mismo tamaño
        out.write(img)  # Escribir la imagen en el video
        frame_number += 1

    # Liberar el objeto VideoWriter y limpiar
    out.release()
    cv2.destroyAllWindows()

    # El video ahora está guardado como 'output.mp4'
    print("Video generado con éxito: 'output.mp4'")

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
    # Primero, limpiamos el eje para evitar que se superpongan
    # elementos de fotogramas previos.
    ax = fig.axes[0]
    ax.clear()

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
        i += 1

    id = 0
    i = 0
    j = 0
    for album in artistdata_cleaned["albums"]:
        # Si 'albums' es None, plotea todos los álbumes
        if albums is None or album["title"] in albums:
            setBars(album["tracks"], j, i, id, songvals, width, pad, album, False)
            j += len(album["tracks"])

            if "bsides" in album.keys():
                setBars(album["bsides"], j, i, id, songvals, width, pad, album, True)
                j += len(album["bsides"])
            i += 1
        id += 1

    # Configuramos los ejes
    ax.set_xticks(xticks)
    ax.set_xticklabels([a["title"] for a in artistdata["albums"]])
    ax.set_yticks([])

    # Ajustes específicos según el artista
    if artistdata["artist"] == "Los Piojos":
        for i in [1, 6]:
            ax.xaxis.get_majorticklabels()[i].set_y(-.04)
    elif artistdata["artist"] == "Deftones":
        ax.xaxis.get_majorticklabels()[6].set_y(-.04)

    # Título (puedes ajustar el texto según necesites)
    ax.set_title("Promedio de los shows desde el 21.09.1991")

    fig.axes[0].set_yticks([])


def setBars(songs, j, i, albumNr, songvals, width, pad, albumdata, bsides):
    # Obtener el color del álbum
    color = "red"
    if "color" in albumdata.keys():
        color = albumdata["color"]  # Tomamos el color del álbum desde el JSON
    elif len(albumcolors) > albumNr:
        color = albumcolors[albumNr]

    edgecolor = "white"
    alpha = 1.0 if not bsides else 0.5

    pos = [(n + j) * width + pad * i for n in range(len(songs))]
    vals = [songvals[sng] for sng in songs]

    # Graficar las barras con el color asignado
    plt.bar(pos, vals, width, edgecolor=edgecolor, linewidth=0.5, color=color, alpha=alpha)

def cleanTitle(s):
    s = s.lower()
    s = cleanRegex.sub("", s)
    s = s.strip()
    return s

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("setlistfile", metavar="infile", type=str, help="El archivo de entrada de setlist en formato JSON.")
    parser.add_argument("-o", "--out", type=str, help="El archivo de salida del gráfico.")
    parser.add_argument("-n", "--numprobes", type=int, default=-1, help="Número de setlists/días para recolectar para el promedio.")
    parser.add_argument("-m", "--mode", type=int, default=0, help="0 para setlist-probes (por defecto), 1 para day-probes")
    parser.add_argument("--interval", type=int, default=150, help="Milisegundos que se muestra cada gráfico.")
    parser.add_argument("--fps", type=int, default=-1, help="Interpolar a fps.")
    parser.add_argument("-s", "--start", type=int, default=0, help="Índice del setlist por el que comenzar (se tomará en cuenta los datos de los setlists anteriores para numprobes).")
    parser.add_argument("-e", "--end", type=int, default=-1, help="Índice del último setlist a incluir (inclusive).")
    parser.add_argument("--mp", type=int, default=0, help="Usar procesamiento paralelo.")
    parser.add_argument("-q", "--quiet", action="store_true", help="No mostrar progreso.")


    args = parser.parse_args()

    main(args)