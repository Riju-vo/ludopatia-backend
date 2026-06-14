# Categoria A: fuentes recolectadas

## Alcance

Esta etapa se limita a recolectar y evaluar informacion para:

- **A1:** marcador al finalizar los 90 minutos.
- **A2:** prorroga y tanda de penales.
- **A3:** estado del partido.

Todavia no se transformaran los archivos ni se implementara el pipeline. Las
reglas definitivas de integracion se decidiran cuando finalice la recoleccion de
las categorias de datos.

Fecha del inventario: 13 de junio de 2026.

## Archivos locales

### Resultados internacionales

Archivo: `data/results.csv`

Fuente:
`https://github.com/martj42/international_results`

Contenido:

- 49.477 partidos.
- Cobertura: 30 de noviembre de 1872 a 27 de junio de 2026.
- Fecha.
- Seleccion local y visitante.
- Marcador final.
- Competicion.
- Ciudad y pais.
- Indicador de campo neutral.

Hash SHA-256:

```text
4E7CA92CE61F305177A5BDE45FE35383E8EF3B411D0B10E71CC5F1D468FA7539
```

Utilidad para categoria A:

- Fuente principal de identidad y marcador final.
- Permite separar fixtures con marcador vacio de partidos con resultado.
- No distingue por si solo 90 minutos, prorroga y penales.
- El README indica que el marcador incluye prorroga y excluye la tanda.

### Eventos de gol

Archivo: `data/raw/goalscorers.csv`

Fuente:
`https://github.com/martj42/international_results`

Contenido:

- 47.606 eventos.
- Cobertura: 2 de julio de 1916 a 11 de junio de 2026.
- Partido y seleccion anotadora.
- Goleador.
- Minuto.
- Indicador de penal.
- Indicador de autogol.

Hash SHA-256:

```text
9C4EE939B5A728AD03A07A8B1E38FD3DE66CE7AD7B5CE3FCE39BD27F5D51CB93
```

Utilidad para categoria A:

- Puede reconstruir el marcador a 90 minutos cuando la lista de goles es
  completa.
- Permite identificar goles posteriores al minuto 90.
- No cubre uniformemente todos los partidos.
- Un partido sin eventos posteriores al minuto 90 no demuestra por si solo que
  no hubo prorroga.

### Tandas de penales

Archivo: `data/raw/shootouts.csv`

Fuente:
`https://github.com/martj42/international_results`

Contenido:

- 678 tandas.
- Cobertura: 22 de agosto de 1967 a 6 de junio de 2026.
- Partido.
- Ganador de la tanda.
- Primer lanzador cuando esta disponible.

Hash SHA-256:

```text
E52E503BADC11021D5D243DDF2288346F63AD028BF8DE75AE9CFB72C5475D807
```

Utilidad para categoria A:

- Identifica que un partido llego a penales.
- Permite separar el ganador de la tanda del resultado del juego.
- No contiene el marcador numerico de todas las tandas.
- No contiene por si solo el marcador a 90 o 120 minutos.

## OpenFootball World Cup

Carpeta:
`data/raw/openfootball/worldcup-master`

Fuente:
`https://github.com/openfootball/worldcup`

Licencia: dominio publico/CC0. La copia de la licencia se encuentra en:
`data/raw/source_docs/openfootball_worldcup_LICENSE.md`.

### Mundial 2022

Archivos principales:

- `2022--qatar/cup.txt`
- `2022--qatar/cup_finals.txt`
- `2022--qatar/cup_stadiums.csv`
- `2022--qatar/NOTES.md`

Informacion disponible:

- Horarios.
- Fase y grupo.
- Estadio y ciudad.
- Marcador.
- Marcador al descanso.
- Marcador a 90 minutos en partidos con prorroga.
- Resultado tras prorroga.
- Marcador de tanda.
- Eventos de gol descritos en texto.

Ejemplo del formato:

```text
Argentina 3-3 a.e.t. (2-2, 2-0), 4-2 pen. France
```

En ese ejemplo:

- 90 minutos: 2-2.
- Tras la prorroga: 3-3.
- Tanda: 4-2.

### Mundial 2026

Archivos principales:

- `2026--usa/cup.txt`
- `2026--usa/cup_finals.txt`
- `2026--usa/cup_stadiums.csv`
- `2026--usa/quali_playoffs.txt`

Informacion disponible:

- Grupos.
- Fixtures.
- Horario local y desplazamiento UTC.
- Ciudad y estadio.
- Resultados incorporados hasta la version descargada.
- Plantilla de rondas eliminatorias.
- Playoffs de clasificacion.

Advertencia:

OpenFootball es un proyecto comunitario. Se conservara como snapshot y se
contrastara con el calendario o Match Centre oficial para partidos del Mundial.

## Documentacion y licencias

Archivos locales:

- `data/raw/source_docs/international_results_README.md`
- `data/raw/source_docs/international_results_LICENSE.txt`
- `data/raw/source_docs/openfootball_worldcup_README.md`
- `data/raw/source_docs/openfootball_worldcup_LICENSE.md`

La fuente `international_results` se distribuye bajo CC0 segun su repositorio.
OpenFootball tambien declara sus datos en dominio publico/CC0.

## Referencias oficiales

### FIFA Match Centre

URL:
`https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026/match-center`

Uso previsto:

- Validar calendario del Mundial.
- Confirmar estado y resultado de partidos importantes.
- Resolver discrepancias residuales.

Limitacion:

- Es una referencia web, no un dataset historico abierto y estable.
- La estructura puede cambiar.
- No debe ser la unica fuente reproducible.

## Cobertura observada desde 2021

Sobre los 5.685 partidos finalizados de `results.csv` desde el 1 de enero de
2021:

- 2.538 tienen al menos un evento de gol en `goalscorers.csv`: 44,64%.
- 3.000 tienen una cuenta de eventos compatible con el total del marcador:
  52,77%. Esta cifra incluye partidos 0-0 sin eventos.
- 115 aparecen en `shootouts.csv`.
- 27 tienen goles posteriores al minuto 90 y eventos consistentes.

La cobertura de eventos no es uniforme entre años, torneos y confederaciones.

## Evaluacion provisional

### A1: marcador a 90 minutos

Estado: recoleccion suficiente para el alcance adaptado, con revision manual
residual.

Cubierto para:

- Mundial 2022 mediante OpenFootball.
- Partidos con lista de eventos completa.
- Competiciones o fases donde las reglas garanticen que no existe prorroga,
  siempre que esas reglas se documenten.

Las fuentes locales adicionales cubren ahora las fases eliminatorias de los
principales torneos continentales recientes:

- Euro 2021 y 2024.
- Copa America 2021 y 2024.
- AFCON 2021, 2023 y 2025.
- Copa Asia 2023.
- Gold Cup 2021, 2023 y 2025.
- UEFA Nations League 2020-21, 2022-23 y 2024-25.
- CONCACAF Nations League 2021-2025.

Pendiente:

- Revisar o excluir los casos residuales de torneos menores y clasificatorios.
- Confirmar formatos especiales cuando no exista una fuente estructurada.

### A2: prorroga y penales

Estado: recoleccion suficiente para el alcance adaptado, con revision manual
residual.

Cubierto para:

- Mundial 2022 mediante OpenFootball.
- Identificacion de 678 tandas mediante `shootouts.csv`.
- Partidos con goles posteriores al minuto 90 en `goalscorers.csv`.

Pendiente:

- Marcador numerico de tandas de competiciones menores.
- Confirmacion de prorroga sin goles en los casos residuales.
- Marcador separado a 90 y 120 minutos en clasificatorios no cubiertos.

### A3: estado del partido

Estado: cubierto por adaptacion de alcance.

Cubierto para:

- Fixtures futuros identificables por fecha y marcador vacio.
- Partidos finalizados con resultado.
- Calendario del Mundial 2026 en OpenFootball.

Decision:

- El producto gratuito distinguira `scheduled`, `finished` y `unknown`.
- `postponed`, `cancelled` y `suspended` se registraran solo cuando una fuente
  publica los confirme.
- No se ofrecera estado en vivo segundo a segundo.
- La interfaz mostrara la fecha y hora de la ultima sincronizacion.

Esta adaptacion evita convertir una API comercial en dependencia esencial.

## Fuentes continentales adicionales recolectadas

Se guardaron snapshots HTML de Wikimedia para cubrir los torneos que no tienen
un repositorio OpenFootball reciente:

- `data/raw/wikimedia/afcon`
- `data/raw/wikimedia/asian-cup`
- `data/raw/wikimedia/gold-cup`
- `data/raw/wikimedia/nations-league`

Los snapshots incluyen paginas generales y, cuando existe una pagina separada,
las fases eliminatorias. Permiten consultar fase, resultado, prorroga, tanda,
fecha, hora y sede segun la competicion.

Licencia: CC BY-SA. Al utilizar datos derivados de estas paginas se debe
conservar la URL de origen, la fecha de consulta y la atribucion correspondiente.
No tienen la misma prioridad que una fuente oficial o CC0, pero son suficientes
como respaldo verificable para datos factuales y revision manual.

## Cola residual de revision manual

Auditoria del 13 de junio de 2026 sobre partidos finalizados desde 2021:

- 115 partidos llegaron a tanda de penales.
- 47 tandas pertenecen a los ocho torneos principales cubiertos.
- 68 tandas quedan fuera de esos torneos.
- 27 partidos tienen goles registrados despues del minuto 90.
- 21 pertenecen a torneos principales cubiertos.
- 6 quedan fuera.
- Hay un partido presente en ambos grupos residuales.
- La union final es de **73 partidos unicos** para revisar manualmente.

Distribucion principal de la cola:

| Competicion | Partidos |
|---|---:|
| FIFA World Cup qualification | 14 |
| COSAFA Cup | 9 |
| FIFA Series | 8 |
| Gold Cup qualification | 6 |
| Baltic Cup | 5 |
| King's Cup | 4 |
| Island Games | 4 |
| Arab Cup | 3 |
| Al Ain International Cup | 3 |
| Arab Cup qualification | 3 |
| SAFF Cup | 2 |
| UEFA Euro qualification | 2 |
| Otras competiciones, un caso cada una | 10 |

### Opciones para cerrar esos 73 casos

1. **Revision manual:** consultar la federacion, organizador, RSSSF o pagina del
   torneo y anotar marcador a 90, a 120, tanda y URL.
2. **Conservadora:** excluir del entrenamiento cualquier caso no verificable.
3. **Hibrida recomendada:** revisar primero los 14 partidos de clasificacion al
   Mundial y excluir los torneos menores que no afecten a las selecciones o al
   periodo objetivo.

La opcion hibrida ofrece casi todo el valor predictivo con una carga manual
pequena.

## Informacion que todavia debemos buscar

Prioridad alta:

1. Fuentes de los 14 casos residuales de clasificacion al Mundial.
2. Reglas de las competiciones residuales que admiten prorroga.
3. Calendario oficial del Mundial 2026 como validacion final.

Prioridad media:

1. Horarios UTC completos de los fixtures 2026.
2. Estados historicos de partidos suspendidos, cancelados o adjudicados.
3. Marcadores numericos de tandas no presentes en OpenFootball.

## Criterio de cierre de categoria A

La recoleccion de categoria A se considera suficiente para avanzar cuando:

- Los principales torneos internacionales de 2021-2026 tengan una fuente
  documentada para sus partidos eliminatorios.
- Sepamos que partidos pueden considerarse de 90 minutos por regla.
- Tengamos una lista explicita de casos ambiguos que deberan excluirse.
- El calendario del Mundial 2026 este contrastado con una fuente oficial.
- Todas las fuentes utilizadas tengan procedencia y condiciones de uso
  registradas.

Los datos no se consideran transformados ni listos para entrenar hasta revisar o
excluir la cola residual. Esa tarea corresponde a la futura fase de preparacion,
no a la recoleccion actual.
