# Catalogos de referencia

Fecha de curacion: 13 de junio de 2026.

Estos archivos cierran la categoria B del inventario de datos. Son datos de
referencia curados, no tablas derivadas para entrenamiento.

## `teams.csv`

Catalogo de los 262 equipos que aparecen en partidos finalizados desde el 1 de
enero de 2021.

Campos:

- `team_id`: identificador interno estable.
- `source_name`: nombre exacto usado por `results.csv`.
- `canonical_name`: nombre oficial FIFA o nombre conservado para una seleccion
  no FIFA.
- `fifa_code`: codigo oficial de tres letras, vacio si no existe.
- `confederation`: confederacion oficial FIFA o asociacion regional conocida.
- `membership_status`: `fifa_member`, `confederation_member_or_associate` o
  `non_fifa_selection`.
- `model_scope`: `include` o `exclude` en el modelo principal.
- `aliases`: otros nombres encontrados en el ranking historico.
- `identity_source`: procedencia de la identidad.
- `notes`: decisiones de alcance.

Resumen:

- 262 nombres fuente.
- 210 asociaciones FIFA presentes en el periodo.
- 9 miembros o asociados regionales sin membresia FIFA.
- 43 selecciones regionales, culturales o no FIFA.
- 262 IDs internos unicos.

El modelo principal incluye por defecto solo `fifa_member`. Esta regla evita
mezclar selecciones nacionales FIFA con representativos regionales de naturaleza
distinta.

## `competitions.csv`

Catalogo de las 66 etiquetas de torneo presentes en partidos finalizados desde
2021.

Campos:

- `competition_id`: identificador canonico.
- `source_label`: texto exacto de `results.csv`.
- `canonical_name`: nombre normalizado.
- `organizer_scope`: organizador o alcance regional.
- `competition_type`: taxonomia deportiva.
- `importance_level`: escala inicial de 0 a 5.
- `model_scope`: inclusion en el modelo principal.
- `extra_time_possible`: indica si alguna fase puede admitir prorroga.
- `normalization_source`: procedencia de la clasificacion.
- `notes`: restricciones de interpretacion.

Las 66 etiquetas convergen en 64 IDs canonicos. `AFF Championship` y
`ASEAN Championship`, junto con sus clasificatorios, representan cambios de
denominacion de una misma competicion.

La importancia es una clasificacion inicial y no un hiperparametro definitivo.
Su efecto debe validarse temporalmente antes de utilizarla en Elo o en el modelo.

## Fuentes

- FIFA Member Associations:
  `https://inside.fifa.com/associations`
- RSSSF FIFA Country Codes:
  `https://www.rsssf.org/miscellaneous/fifa-codes.html`
- International football results:
  `https://github.com/martj42/international_results`

El snapshot FIFA local contiene 211 asociaciones distribuidas entre AFC, CAF,
CONCACAF, CONMEBOL, OFC y UEFA. La pagina oficial seguia declarando 211
asociaciones al verificarla el 13 de junio de 2026.

## Integridad

Hashes SHA-256:

```text
teams.csv
E46DAF52600A751BB97C50A5CB9D74F0D452EB909E0DAD7FC0E04A5BC662D41E

competitions.csv
0BB3D97A3DAC40F2BB1DB73B5D888492BDDAE23C8AEC232140067EFC4F60F88C
```

## `locations.csv`

Catalogo C3 de las 756 parejas ciudad-pais presentes en partidos finalizados o
fixtures desde 2021. Conserva valores fuente, identidad GeoNames, coordenadas,
zona horaria, metodo de resolucion y excepciones documentadas.

## `tournament_hosts.csv`

Catalogo C5 con 36 relaciones anfitrion-edicion para 21 torneos o fases finales
principales desde 2021. Cada fila enlaza a `teams.csv`, `competitions.csv` y una
referencia local.

Hashes SHA-256:

```text
locations.csv
92ACB6332B5B19C8AC1D961AEBEC2E1A724DDE8CB9399F30139B6D4919D52095

tournament_hosts.csv
F9E2B68BA9AC340A4185E9C74CB8A12E048D33DD0D4C82399C53E9E3765A97E8
```
