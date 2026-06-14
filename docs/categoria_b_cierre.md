# Cierre de categoria B

Fecha de cierre: 13 de junio de 2026.

## Resultado

La categoria B se considera cerrada para el alcance gratuito del proyecto.

El cierre no significa que todos los partidos internacionales tengan hora,
zona, grupo y jornada. Significa que:

- La identidad de todos los equipos del periodo esta resuelta.
- Todas las etiquetas de competicion estan normalizadas.
- La fecha esta completa.
- El Mundial 2026 tiene calendario, horario y estructura suficientes.
- Los metadatos no disponibles globalmente dejaron de ser dependencias
  obligatorias del modelo.

## B1: identidad canonica

Archivo:
`data/reference/teams.csv`

Cobertura:

- 262 equipos recientes.
- 210 miembros FIFA incluidos en el modelo principal.
- 52 selecciones no FIFA o asociadas regionalmente excluidas por defecto.
- 262 IDs internos unicos.
- Codigo y confederacion oficial para todos los miembros FIFA.
- Alias historicos disponibles en el ranking vinculados por codigo.

Fuente principal:
snapshot de FIFA Member Associations, contrastado con RSSSF y el ranking local.

Decision:

- No se asignan codigos FIFA ficticios.
- No se fusionan representativos regionales con selecciones nacionales.
- Los cambios de nombre conservan el mismo ID FIFA.
- El nombre exacto de `results.csv` se conserva en `source_name`.

Estado: completo.

## B2: fecha

Fuente:
`data/results.csv`

Todos los partidos tienen fecha calendario.

Estado: completo.

## B3: hora y zona horaria

Para entrenamiento:

- La fecha es obligatoria.
- La hora es opcional.
- No se excluye un partido historico solo por carecer de kickoff.
- Los dias de descanso se calcularan inicialmente por fecha.

Para el producto:

- Kickoff y desplazamiento UTC son obligatorios para el Mundial 2026.
- La conversion a la zona del usuario se realizara a partir de UTC.
- La zona IANA del estadio se añadira en la futura tabla de sedes.

Cobertura Mundial 2026:

- 104 partidos.
- 72 partidos de grupos.
- 32 partidos eliminatorios.
- 12 grupos.
- Horario y desplazamiento UTC presentes en el calendario recolectado.
- 16 ciudades anfitrionas.

La referencia operativa es OpenFootball y la validacion final debe realizarse
contra FIFA Match Centre antes de publicar o actualizar horarios. Esto es una
verificacion de producto, no un faltante del dataset de entrenamiento.

Estado: completo para el alcance definido.

## B4: competicion normalizada

Archivo:
`data/reference/competitions.csv`

Cobertura:

- 66 etiquetas fuente.
- 64 IDs canonicos.
- Organizador o alcance.
- Tipo de competicion.
- Nivel de importancia inicial.
- Politica de inclusion.
- Posibilidad de prorroga por formato.

Taxonomia:

- `world_final`
- `world_qualification`
- `continental_final`
- `continental_qualification`
- `intercontinental_final`
- `nations_league`
- `regional_championship`
- `regional_qualification`
- `invitational`
- `friendly`
- `non_fifa_competition`
- `other_cup`

La importancia va de 0 a 5:

- 5: Mundial.
- 4: clasificatorio mundialista o torneo continental principal.
- 3: clasificatorio continental o Nations League.
- 2: torneo regional.
- 1: amistoso o invitacional.
- 0: competicion no FIFA excluida.

Esta escala es una hipotesis documentada. Antes de usarla como peso debe
validarse mediante backtesting.

Estado: completo.

## B5: fase, grupo y jornada

Cobertura obligatoria:

- Mundial 2022 y 2026.
- Euro 2021 y 2024.
- Copa America 2021 y 2024.
- AFCON 2021, 2023 y 2025.
- Copa Asia 2023.
- Gold Cup 2021, 2023 y 2025.
- UEFA y CONCACAF Nations League recientes.

Cobertura Mundial 2026:

- Grupos A-L.
- Tres jornadas competitivas por grupo.
- Ronda de 32.
- Octavos.
- Cuartos.
- Semifinales.
- Tercer puesto.
- Final.

Regla para el modelo:

- Fase detallada se usa cuando la fuente la conoce.
- Para competiciones menores puede quedar `unknown`.
- Nunca se infiere una fase a partir del orden del archivo.
- La feature global minima sera el tipo de competicion y, cuando se conozca, el
  indicador de eliminatoria.

Estado: completo para el alcance definido.

## Validaciones

- No hay IDs de equipo duplicados.
- No faltan nombres fuente ni canonicos.
- Todos los miembros FIFA tienen codigo y confederacion.
- Todas las etiquetas de torneo tienen tipo, importancia y politica de alcance.
- Las 66 etiquetas originales se conservan para trazabilidad.
- Los aliases de AFF/ASEAN convergen en el mismo ID canonico.

## Mantenimiento

Antes de cada nueva temporada o entrenamiento:

1. Detectar nombres de equipo nuevos en `results.csv`.
2. Detectar etiquetas de torneo nuevas.
3. Revisar cambios de membresia, suspension o nombre oficial.
4. Validar el calendario activo contra la fuente oficial.
5. Crear una nueva version de los catalogos en lugar de modificar decisiones
   historicas sin registro.

