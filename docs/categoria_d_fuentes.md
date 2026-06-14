# Categoria D: fuentes y estrategia

Fecha de cierre de recoleccion: 13 de junio de 2026.

## Alcance

- **D1:** puntos FIFA prepartido.
- **D2:** posicion FIFA prepartido.
- **D3:** Elo prepartido propio.

## Resultado ejecutivo

D1 y D2 fueron reconstruidos mediante las APIs publicas que utiliza la pagina
oficial de FIFA. El historial ahora llega hasta la publicacion del 11 de junio
de 2026, sin prolongar artificialmente los valores de septiembre de 2024.

D3 no requiere mas fuentes externas. Su implementacion queda para la futura
fase de modelado.

## Publicaciones oficiales reconstruidas

Se conservaron 13 snapshots entre el 19 de septiembre de 2024 y el 11 de junio
de 2026:

- 19 de septiembre, 24 de octubre, 28 de noviembre y 19 de diciembre de 2024.
- 3 de abril, 10 de julio, 18 de septiembre, 17 de octubre, 19 de noviembre y
  22 de diciembre de 2025.
- 19 de enero, 1 de abril y 11 de junio de 2026.

FIFA cambio el servicio usado por su tabla durante este periodo:

- Publicaciones con ID `idNNNNN`:
  `https://inside.fifa.com/api/ranking-overview`
- Publicaciones con ID `FRS_*`:
  `https://api.fifa.com/api/v3/fifarankings/rankings/rankingsbyschedule`

El calendario de fechas e IDs se obtuvo del JSON `__NEXT_DATA__` de la pagina
oficial del ranking masculino.

Snapshots:
`data/raw/rankings/fifa_publications_2024-2026/`

Manifiesto:
`data/raw/rankings/fifa_publications_2024-2026_manifest.csv`

El manifiesto conserva fecha, ID oficial, URL, numero de filas, ruta local,
fecha de descarga y hash SHA-256 de cada respuesta.

## D1: puntos FIFA

Archivo oficial reconstruido:
`data/ranking_fifa_official_2024_2026.csv`

- 2.743 filas.
- 13 publicaciones.
- Periodo: 19 de septiembre de 2024 a 11 de junio de 2026.
- Puntos, codigo FIFA, nombre, confederacion y puntos anteriores.

Archivo historico consolidado:
`data/ranking_fifa_historical_complete.csv`

- 70.426 filas.
- 347 publicaciones.
- Periodo: 31 de diciembre de 1992 a 11 de junio de 2026.
- El archivo original se conserva sin modificaciones.

Uso futuro:

- Para cada partido se seleccionara exclusivamente la ultima publicacion
  anterior al kickoff.
- Se calculara `ranking_age_days`.
- Nunca se usara una publicacion posterior al partido.

Estado de recoleccion: **completo**.

## D2: posicion FIFA

Las 13 publicaciones nuevas contienen la posicion oficial. Para el historial
anterior se conserva el orden de la tabla fuente, que coincide con el orden
publicado; los equipos sin puntos permanecen sin posicion.

Validacion de union:

- 211 codigos comunes en la publicacion del 19 de septiembre de 2024.
- 0 diferencias de puntos.
- 0 diferencias de posicion.

La publicacion del 11 de junio de 2026 contiene 211 selecciones con posicion
oficial.

La posicion se recomienda principalmente para interfaz y explicabilidad. Los
puntos conservan mas informacion para el modelo.

Estado de recoleccion: **completo**.

## D3: Elo propio

Los insumos externos necesarios ya estan disponibles:

- resultados cronologicos;
- equipos canonicos;
- campo neutral y localidad;
- competicion normalizada;
- politica para partidos ambiguos de categoria A.

La futura implementacion debera ser estrictamente cronologica y guardar el Elo
prepartido antes de actualizarlo. Los parametros, ventaja local y factores K se
elegiran mediante validacion temporal.

Estado de recoleccion: **completo**.
Estado de feature: **pendiente de implementacion por decision del proyecto**.

## Integridad

```text
ranking_fifa_official_2024_2026.csv
311B31EB1BE36F11C926F3546EA172046722C5DFE2FBB62211B00C66124350FF

ranking_fifa_historical_complete.csv
9F39262F7510BCA90801434A9BF5D8837D15BA822040770C9187C2D2CF04CE1D

fifa_publications_2024-2026_manifest.csv
AC441201B62725F8739F4A10EAE9CAA89F1371E9BED64D54239E3BAFE6E94A77
```

## Criterio de cierre

- Todas las fechas oficiales del hueco 2024-2026 estan identificadas.
- Puntos y posiciones estan disponibles para las 13 publicaciones.
- Cada respuesta oficial tiene snapshot, URL y hash.
- El solapamiento con el historico local fue validado sin diferencias.
- D3 no necesita recolectar otro dataset.

Estado: **recoleccion de categoria D cerrada**.
