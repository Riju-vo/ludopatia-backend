# Categoria B: fuentes recolectadas

## Alcance

Esta etapa se limita a recolectar y evaluar informacion para:

- **B1:** identidad canonica de selecciones.
- **B2:** fecha del partido.
- **B3:** hora exacta y zona horaria.
- **B4:** competicion y torneo.
- **B5:** fase, grupo y jornada.

No se construira todavia el catalogo canonico ni se transformaran los archivos.

Fecha del inventario: 13 de junio de 2026.

El cierre definitivo y sus reglas se documentan en
[`categoria_b_cierre.md`](categoria_b_cierre.md).

## B1: identidad canonica de selecciones

### Ranking FIFA historico local

Archivo:
`data/ranking_fifa_historical.csv`

Campos aprovechables:

- `team`
- `team_short`
- `id_num`

Cobertura observada:

- 235 nombres de seleccion distintos.
- 217 codigos cortos distintos.
- 236 pares unicos nombre/codigo.
- 17 codigos aparecen asociados a mas de un nombre.
- Un nombre aparece con mas de un codigo.

Los codigos compartidos permiten detectar aliases y cambios de denominacion:

- `Cape Verde Islands` / `Cabo Verde` -> `CPV`
- `Czech Republic` / `Czechia` -> `CZE`
- `Curacao` / `Curaçao` -> `CUW`
- `Swaziland` / `Eswatini` -> `SWZ`
- `FYR Macedonia` / `North Macedonia` -> `MKD`
- `Gambia` / `The Gambia` -> `GAM`

Limitaciones:

- No incluye confederacion.
- No indica claramente membresia FIFA actual, suspension o estado asociado.
- `id_num` debe auditarse antes de considerarlo identificador estable.
- No cubre todos los combinados no FIFA presentes en `results.csv`.

### RSSSF FIFA Country Codes

Archivo:
`data/raw/identity/rsssf_fifa_country_codes.html`

Fuente:
`https://www.rsssf.org/miscellaneous/fifa-codes.html`

Contenido:

- Nombres de asociaciones.
- Codigos FIFA.
- Codigos IOC.
- Codigos antiguos.
- Notas sobre miembros FIFA e IOC.

Hash SHA-256:

```text
C709552F351C90A5B2F1126C92E812962D22A2B1C2C31E47EB56764E8BF09CB4
```

Ventajas:

- Fuente historica especializada en estadistica futbolistica.
- Incluye codigos obsoletos utiles para sucesiones y cambios de nombre.

Limitaciones:

- No es una fuente oficial FIFA.
- La pagina no ofrece una tabla moderna de confederacion por asociacion.
- Debe contrastarse con asociaciones oficiales actuales.

### FIFA Associations

Archivo:
`data/raw/identity/fifa_associations.html`

Fuente:
`https://inside.fifa.com/associations`

Hash SHA-256:

```text
E7DB8704339752CD9D69BF4A8B90994685D6CC508E3704D26D9AD936DB5597E4
```

Uso:

- Referencia oficial de asociaciones y confederaciones actuales.
- Validacion de membresia y denominacion oficial.

Limitaciones:

- La pagina es dinamica.
- La copia HTML no constituye un dataset tabular estable.
- No resuelve por si sola aliases historicos ni equipos no FIFA.

### OpenFootball

Los archivos de Mundial 2026 incluyen una lista explicita de nombres FIFA
normalizados para varios participantes:

- `South Korea` -> `Korea Republic`
- `Iran` -> `IR Iran`
- `Cape Verde` -> `Cabo Verde`
- `DR Congo` -> `Congo DR`
- `Ivory Coast` -> `Côte d'Ivoire`
- `Czech Republic` -> `Czechia`
- `Turkey` -> `Türkiye`

Esta informacion es util como referencia, pero no reemplaza un catalogo global.

### Evaluacion B1

Estado: completamente cubierto.

Tenemos:

- Codigos para la mayoria de selecciones FIFA.
- Alias visibles en el ranking.
- Codigos historicos RSSSF.
- Referencia oficial actual de asociaciones FIFA.

El catalogo resultante se encuentra en `data/reference/teams.csv`:

- 262 equipos recientes.
- 210 miembros FIFA.
- 52 selecciones no FIFA o asociadas regionalmente.
- Codigo y confederacion para todos los miembros FIFA.
- Alias del ranking historico.
- Politica explicita de inclusion o exclusion.

## B2: fecha del partido

Fuente principal:
`data/results.csv`

Estado: completamente cubierto.

Observaciones:

- Todos los registros tienen fecha.
- El campo permite ordenar partidos y aplicar cortes temporales.
- La fecha no sustituye la hora exacta para operar el producto.

## B3: hora exacta y zona horaria

### OpenFootball World Cup

Cobertura:

- Mundial 2022: horarios disponibles, pero el desplazamiento UTC no aparece de
  forma explicita en cada partido.
- Mundial 2026: hora y desplazamiento UTC por partido.

Ejemplos de 2026:

```text
13:00 UTC-6
18:00 UTC-4
21:00 UTC-7
```

### OpenFootball Copa America

Archivos:

- `2021--brazil/copa.txt`
- `2024--usa/copa.txt`

Cobertura:

- Hora por partido.
- Desplazamiento UTC por partido.
- Fecha y sede.

### OpenFootball Euro

Archivos:

- `2021--europe/euro.txt`
- `2024--germany/euro.txt`

Cobertura:

- Hora por partido.
- Euro 2024 declara CEST (`UTC+2`) para todo el torneo.
- Euro 2021 tambien declara CEST (`UTC+2`) para un torneo jugado en once
  ciudades.

Advertencia:

La declaracion de Euro 2021 debe tratarse como horario estandarizado del archivo,
no como evidencia suficiente de la zona local real de cada estadio.

### Evaluacion B3

Estado: cubierto por adaptacion de alcance.

Cubierto:

- Mundial, Euro y Copa America mediante OpenFootball.
- Mundial 2026 y Copa America con desplazamientos explicitos.

Decision:

- Para entrenamiento historico basta la fecha; la hora no sera una feature
  obligatoria.
- Kickoff UTC y zona local seran obligatorios para el Mundial 2026 y los
  fixtures mostrados en el producto.
- Para otros torneos se conservara la hora cuando exista, sin excluir el partido
  si falta.
- No se intentara completar manualmente la hora de todos los amistosos.

## B4: competicion y torneo

### Dataset principal

`results.csv` contiene la columna `tournament` sin valores nulos observados.

Desde el 1 de enero de 2021 aparecen 66 etiquetas distintas, incluyendo:

- FIFA World Cup y eliminatorias.
- Amistosos.
- UEFA Nations League.
- CONCACAF Nations League.
- Euro y eliminatorias.
- Copa America.
- AFCON y eliminatorias.
- Copa Asia y eliminatorias.
- Gold Cup y eliminatorias.
- Torneos regionales y competiciones no FIFA.

Ventaja:

- Cada partido tiene una etiqueta de origen.

Limitaciones:

- La etiqueta es texto libre.
- No existe identificador canonico de competicion.
- No separa edicion, temporada, confederacion, nivel o formato.
- Algunos nombres cambiaron entre ediciones, por ejemplo `AFF Championship` y
  `ASEAN Championship`.
- `FIFA World Cup qualification` agrupa eliminatorias de seis confederaciones
  con formatos distintos.

### Repositorios de competiciones recolectados

Todos declaran licencia CC0:

| Repositorio | Commit recolectado | Cobertura reciente util |
|---|---|---|
| `openfootball/worldcup` | `683dae13dd79e071d4782a5ab370bf4be44c2cda` | Mundial 2022 y 2026 |
| `openfootball/euro` | `b36bf80e4afb452dbbdc24b3d02f133f107580b0` | Euro 2021 y 2024 |
| `openfootball/copa-america` | `902e4c51c282244ab924676b3bc471b4040de39a` | Copa America 2021 y 2024 |
| `openfootball/north-america-gold-cup` | `7dab27c866f1308ab7220e452706a5528e0f4670` | Solo 2011 y 2013 |

La fuente Gold Cup no cubre el periodo requerido.

### Evaluacion B4

Estado: completamente cubierto.

Tenemos:

- Nombre de torneo para todos los partidos del dataset principal.
- Estructura detallada para Mundial, Euro y Copa America.

El catalogo resultante se encuentra en `data/reference/competitions.csv`:

- 66 etiquetas fuente.
- 64 IDs canonicos.
- Organizador o alcance.
- Tipo.
- Nivel de importancia inicial.
- Politica de inclusion.
- Posibilidad de prorroga.

Edicion y temporada seguiran perteneciendo al registro de cada partido, porque
una misma competicion tiene multiples ediciones. No son atributos fijos del
catalogo.

## B5: fase, grupo y jornada

### Cobertura OpenFootball

Mundial 2022 y 2026:

- Grupos.
- Jornada.
- Octavos, cuartos, semifinal, tercer puesto y final.
- Playoffs de clasificacion disponibles parcialmente para 2026.

Euro 2021 y 2024:

- Grupos.
- Jornadas.
- Octavos, cuartos, semifinales y final.
- Referencias de clasificacion entre grupos en cruces eliminatorios.

Copa America 2021 y 2024:

- Grupos.
- Jornadas.
- Cuartos, semifinales, tercer puesto y final.

Gold Cup:

- El repositorio recolectado solo contiene 2011 y 2013.

### Fuentes continentales adicionales

Se recolectaron snapshots HTML de Wikimedia para:

- AFCON 2021, 2023 y 2025.
- Copa Asia 2023.
- Gold Cup 2021, 2023 y 2025.
- UEFA Nations League 2020-21, 2022-23 y 2024-25.
- CONCACAF Nations League y finales entre 2021 y 2025.

Carpetas:

- `data/raw/wikimedia/afcon`
- `data/raw/wikimedia/asian-cup`
- `data/raw/wikimedia/gold-cup`
- `data/raw/wikimedia/nations-league`

Licencia: CC BY-SA, por lo que cualquier dato derivado debe conservar
atribucion, URL y fecha de consulta.

### Evaluacion B5

Estado: recoleccion suficiente para el alcance adaptado.

Cubierto:

- Mundial, Euro y Copa America recientes mediante OpenFootball.
- AFCON, Copa Asia, Gold Cup y Nations League recientes mediante snapshots
  Wikimedia.

Decision:

- Fase, grupo, jornada e ida/vuelta seran obligatorios para el Mundial y los
  principales torneos finales.
- Para amistosos y torneos menores bastara competicion normalizada y un
  indicador de eliminatoria cuando pueda verificarse.
- Las fases desconocidas no se inventaran ni se usaran como feature global.

## Archivos y licencias locales

Repositorios:

- `data/raw/openfootball/worldcup-master`
- `data/raw/openfootball/euro/euro-master`
- `data/raw/openfootball/copa-america/copa-america-master`
- `data/raw/openfootball/gold-cup/north-america-gold-cup-master`

Documentacion:

- `data/raw/source_docs/openfootball_euro_README.md`
- `data/raw/source_docs/openfootball_euro_LICENSE.md`
- `data/raw/source_docs/openfootball_copa_america_README.md`
- `data/raw/source_docs/openfootball_copa_america_LICENSE.md`
- `data/raw/source_docs/openfootball_gold_cup_README.md`
- `data/raw/source_docs/openfootball_gold_cup_LICENSE.md`

## Resumen de cobertura

| Elemento | Estado | Motivo |
|---|---|---|
| B1 Identidad canonica | Completo | Catalogo de 262 equipos con IDs y alcance |
| B2 Fecha | Completo | Presente para todos los partidos |
| B3 Hora y zona | Completo por alcance | Obligatorio para Mundial/producto, opcional en entrenamiento |
| B4 Competicion | Completo | 66 etiquetas normalizadas en 64 IDs |
| B5 Fase/grupo/jornada | Completo por alcance | Torneos principales cubiertos; no sera feature global obligatoria |

## Trabajo manual recurrente

La categoria esta cerrada. Solo queda mantenimiento:

1. Contrastar el calendario activo del Mundial contra FIFA antes de publicarlo.
2. Clasificar nombres o torneos nuevos cuando aparezcan en la fuente.
3. Revisar cambios oficiales de nombre, membresia o confederacion.

## Siguiente busqueda recomendada

Para completar la recoleccion de B:

1. Validar asociaciones y confederaciones de los 262 equipos recientes.
2. Resolver aliases y sucesiones historicas.
3. Documentar formatos de eliminatorias mundialistas por confederacion.
4. Contrastar horarios y zonas del Mundial 2026.

## Criterio de cierre de categoria B

La categoria se considera suficientemente recolectada para avanzar cuando:

- Todos los equipos recientes tengan identidad, codigo, confederacion y estado.
- Las 66 etiquetas de torneo tengan una definicion canonica.
- Los principales torneos 2021-2026 tengan fase, grupo y jornada.
- Los fixtures del Mundial 2026 tengan kickoff UTC verificable.
- Los huecos restantes esten identificados y puedan excluirse o tratarse sin
  ambiguedad.

Con los catalogos de `data/reference`, la categoria cumple este criterio.
