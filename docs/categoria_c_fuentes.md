# Categoria C: fuentes y estrategia

Fecha de cierre: 13 de junio de 2026.

## Alcance

- **C1:** equipo nominal local y visitante.
- **C2:** campo neutral.
- **C3:** pais y ciudad de la sede.
- **C4:** estadio.
- **C5:** condicion de anfitrion del torneo.

Esta etapa corresponde unicamente a recoleccion y curacion de informacion. No
implementa features ni pipelines del modelo.

## Estado final

La categoria C queda cerrada por cobertura y adaptacion de alcance:

- C1 y C2 estan completos en `data/results.csv`.
- C3 esta completamente normalizado para los partidos finalizados desde 2021.
- C4 esta completo para el Mundial 2026 y adaptado por ciudad para el historial
  global.
- C5 esta catalogado para los torneos finales principales desde 2021.

## C3: localidades normalizadas

Catalogo:
`data/reference/locations.csv`

Cobertura:

- 756 parejas unicas `source_city` y `source_country`, incluyendo Seattle para
  los fixtures del Mundial 2026.
- 752 localidades canonicas: cuatro grupos de aliases convergen en el mismo
  lugar.
- 756 registros con latitud, longitud, zona horaria y pais canonico.
- 754 mapeos enlazados a GeoNames, correspondientes a 750 IDs GeoNames
  distintos.
- 2 excepciones documentadas con coordenadas de la sede:
  `Faro-Loule` y `Sao Joao da Venda`.
- 4 correcciones explicitas de pais fuente:
  Berrechid, Fos-sur-Mer, Miercurea-Ciuc y Saint George's.

Metodos de resolucion:

- 625 coincidencias exactas unicas.
- 80 coincidencias priorizadas por poblacion y contexto.
- 7 desambiguaciones contextuales.
- 34 resoluciones desde extractos nacionales completos de GeoNames.
- 3 aliases.
- 4 correcciones de pais.
- 2 excepciones documentadas.

El catalogo conserva el nombre y pais originales junto a la identidad canonica.
Las correcciones no sobrescriben silenciosamente la fuente.

Fuentes:

- GeoNames `cities500` y extractos nacionales, licencia CC BY 4.0.
- `international_results`, licencia CC0.

Hash SHA-256:

```text
locations.csv
92ACB6332B5B19C8AC1D961AEBEC2E1A724DDE8CB9399F30139B6D4919D52095
```

## C4: estadio

El archivo
`data/raw/openfootball/worldcup-master/2026--usa/cup_stadiums.csv`
contiene los 16 estadios del Mundial 2026, con ciudad, capacidad, coordenadas,
zona horaria y Wikidata.

Decision de alcance:

- El estadio es obligatorio para los fixtures del Mundial 2026.
- Se incorporara en otros torneos cuando exista una fuente abierta fiable.
- Para entrenamiento global, ciudad normalizada es el nivel geografico minimo.
- No se inferira un estadio a partir de una ciudad con varias sedes.

Esta adaptacion evita bloquear el modelo por un dato global que no existe con
cobertura abierta uniforme.

## C5: anfitriones de torneo

Catalogo:
`data/reference/tournament_hosts.csv`

Cobertura:

- 36 relaciones edicion-anfitrion.
- 21 ediciones de torneos finales o fases finales desde 2021.
- 9 familias de competiciones.
- Todos los anfitriones enlazan con `data/reference/teams.csv`.
- Todas las competiciones enlazan con `data/reference/competitions.csv`.
- Cada fila apunta a una referencia local existente.

Incluye Mundial, Euro, Copa America, Copa Africana, Copa Asia, Gold Cup,
Nations League de UEFA y Concacaf, y OFC Nations Cup. En Nations League se
catalogan solo las fases finales con sede central.

En ediciones aplazadas se conservan por separado `edition` y `played_year`.
Los torneos multinacionales guardan una fila por anfitrion.

Hash SHA-256:

```text
tournament_hosts.csv
F9E2B68BA9AC340A4185E9C74CB8A12E048D33DD0D4C82399C53E9E3765A97E8
```

## Criterio de cierre

- C3 cumple 756/756 localidades y sedes de fixtures normalizadas.
- C4 cumple el producto principal y tiene politica explicita para el historial.
- C5 cumple las ediciones principales definidas desde 2021.
- No quedan datos externos obligatorios por recolectar para esta categoria.

Estado: **cerrada**.
