# SetlistFM - Setlist Evolution: Análisis de Los Piojos

Este proyecto analiza la evolución de los setlists de Los Piojos a lo largo de su carrera, combinando información de conciertos, popularidad de canciones, reproducciones en plataformas y visualizaciones avanzadas.

## Estructura del Proyecto

- **notebook_piojos.ipynb**: Análisis principal de la evolución de las canciones más tocadas, animaciones y visualizaciones de barras.
- **popularidad.ipynb**: Cálculo de un índice de popularidad para cada canción, combinando datos de Spotify, YouTube, ventas y frecuencia en vivo.
- **setlists_populares.ipynb**: Análisis de los recitales más "mainstream" y alternativos, exploración de variables que predicen la popularidad de un show, visualizaciones de ciudades y mapas.
- **vuelta_popularidad.ipynb**: Análisis específico de la "vuelta" de Los Piojos y su impacto en los setlists.
- **plot.py**: Script para generar animaciones y visualizaciones de la evolución de los temas.
- **album_data/Los Piojos.json**: Información de álbumes, canciones y colores asociados.
- **Setlists_Piojos.json / setlists_vuelta.json**: Datos de los setlists históricos y de la vuelta.
- **excels/**: Archivos exportados con resultados de popularidad y ordenamientos.
- **videos_piojos/**: Imágenes y gifs generados para visualizaciones y presentaciones.

## Principales Análisis y Visualizaciones

### 1. Evolución de Canciones en Vivo
- Se procesaron todos los setlists históricos para contar acumulativamente cuántas veces se tocó cada canción.
- Se generaron animaciones de barras mostrando el top 27 de canciones más tocadas a lo largo del tiempo, con colores por álbum.

### 2. Índice de Popularidad de Canciones
- Se creó un índice combinando:
  - Veces tocada por año de vigencia
  - Popularidad en Spotify
  - Reproducciones en YouTube
  - Streams totales en Spotify
  - Ventas del álbum
- Se usó PCA para ponderar las variables y se normalizó el índice entre 0 y 1.
- Resultados exportados a `canciones_popularidad.xlsx`.

### 3. Análisis de Recitales y Setlists Populares
- Se calculó la popularidad promedio de cada recital según las canciones tocadas.
- Se identificaron los shows más "mainstream" y alternativos.
- Se analizaron variables como aforo, ciudad, estación, cantidad de canciones y día de la semana para predecir la popularidad de un show.
- Se entrenó un modelo de Random Forest para predecir la popularidad de futuros recitales.

### 4. Visualizaciones Avanzadas
- Mapas de calor de popularidad por ciudad y año.
- Mapas interactivos de proporción de "hits" tocados por ciudad.
- Wordcloud de canciones más tocadas, coloreadas por álbum y con forma personalizada.
- Sankey diagram mostrando la incorporación de canciones nuevas por año.

### 5. Otros Análisis
- Detección de "hits" (top 25% más populares) y su frecuencia por ciudad.
- Análisis de la posición promedio de las canciones en los setlists más populares.
- Exportación de resultados a archivos Excel para su consulta y visualización externa.

## Requisitos

- Python 3.8+
- Jupyter Notebook
- Bibliotecas: pandas, numpy, matplotlib, seaborn, plotly, scikit-learn, spotipy, yt-dlp, wordcloud, pillow

## Ejecución

1. Abrir los notebooks en Jupyter o VSCode.
2. Ejecutar las celdas en orden para reproducir los análisis y visualizaciones.
3. Los resultados principales se exportan a la carpeta `excels/` y las visualizaciones a `videos_piojos/`.

## Créditos

- Datos de setlists: [Setlist.fm](https://www.setlist.fm/)
- Datos de álbumes: Discografía oficial de Los Piojos
- Análisis y visualizaciones: [Tu nombre o equipo]

---

Este proyecto es un ejemplo de análisis de datos musicales, combinando fuentes diversas y técnicas de ciencia de datos para entender la evolución de una banda