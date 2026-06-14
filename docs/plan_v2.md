# Plan de implementacion v2: Predictor del Mundial

Fecha de actualizacion: 13 de junio de 2026.

## 1. Objetivo

Construir una plataforma entrenable y reproducible que estime probabilidades
prepartido para selecciones nacionales, con foco inicial en el Mundial 2026.

Para cada partido debe producir:

- goles esperados de ambos equipos;
- probabilidad de victoria, empate y derrota;
- matriz de probabilidades de marcador exacto;
- indicadores de forma, ataque, defensa y fuerza del rival;
- version del modelo, fecha de entrenamiento y metricas historicas.

La prioridad es la calidad de las probabilidades, no acertar un marcador unico.
El modelo debe estar calibrado, ser auditable y poder reentrenarse sin depender
del frontend.

## 2. Estado actual

La fase de recoleccion necesaria para la primera version esta cerrada.

### Datos disponibles

- `data/results.csv`: resultados y fixtures.
- `data/reference/teams.csv`: 262 identidades fuente normalizadas.
- `data/reference/competitions.csv`: taxonomia de competiciones.
- `data/reference/locations.csv`: 756 mapeos de sede normalizados, incluidos los
  fixtures del Mundial 2026.
- `data/reference/tournament_hosts.csv`: anfitriones de 21 ediciones.
- `data/ranking_fifa_historical_complete.csv`: 347 publicaciones FIFA entre
  1992 y el 11 de junio de 2026.
- Fuentes de respaldo para prorroga, penales, calendarios y estadios del Mundial.

### Categorias de datos

- A-E: recoleccion cerrada por cobertura o adaptacion de alcance.
- D3: no requiere datos externos; falta calcular el Elo prepartido.
- E1-E4: falta calcular las features cronologicas.
- E6: feature experimental.
- E5: descartada.
- H1-H4: descartadas.
- F y G: experimentales y fuera del camino critico.

No se buscaran mas datasets antes de comenzar la implementacion.

## 3. Alcance de la primera version

### Incluido

- Selecciones FIFA masculinas.
- Entrenamiento con partidos historicos verificados.
- Prediccion a 90 minutos.
- Mundial 2026 como producto principal.
- Ranking FIFA y Elo prepartido.
- Forma, ataque y defensa recientes.
- Localia, neutralidad y condicion de anfitrion.
- Importancia de la competicion.
- Matriz de marcador exacto.
- API y frontend para consultar partidos y predicciones.

### No incluido inicialmente

- Prediccion en vivo.
- Lesiones o sanciones historicas.
- Valor de mercado.
- xG, tiros y posesion globales.
- Clima, altitud, superficie o distancia de viaje.
- Carga de partidos de clubes.
- Cuotas como feature de entrenamiento.
- Modelo separado para tandas de penales.

La probabilidad de avanzar tras prorroga o penales puede incorporarse en una
version posterior. La primera version modelara exclusivamente el resultado a 90
minutos.

## 4. Principios tecnicos

1. Datos, features, entrenamiento, inferencia, API y frontend son componentes
   separados.
2. Toda feature representa informacion conocida antes del kickoff.
3. La validacion es temporal, nunca aleatoria.
4. Ningun modelo se promueve sin superar baselines definidos.
5. Datos, configuracion, artefacto y metricas se versionan juntos.
6. Las predicciones publicadas no se sobrescriben retroactivamente.
7. Los casos ambiguos se excluyen antes que imputarse sin evidencia.
8. Las ampliaciones solo entran si mejoran log loss, RPS y calibracion.

## 5. Arquitectura objetivo

```text
data/raw + data/reference
            |
            v
      ingesta y validacion
            |
            v
   partidos canonicos a 90 min
            |
            v
  Elo + features prepartido
            |
            v
 entrenamiento y backtesting
            |
            v
 artefacto promovido + metricas
            |
            v
      API de inferencia
            |
            v
       frontend web
```

### Machine learning

- Python 3.12 o version estable compatible.
- pandas inicialmente.
- scikit-learn para pipelines y modelos.
- SciPy para distribuciones de goles.
- joblib para artefactos.
- Pydantic para contratos y configuracion.
- pytest para pruebas.

Polars y MLflow quedan como mejoras posteriores, no como dependencias iniciales.

### Backend

- FastAPI.
- SQLAlchemy.
- Alembic.
- PostgreSQL en el producto.
- SQLite permitido para pruebas unitarias y desarrollo temprano.

### Frontend

- Next.js.
- TypeScript.
- Cliente generado o tipado desde OpenAPI.
- Visualizaciones accesibles y adaptadas a movil.

### Operacion

- Docker Compose para frontend, API y PostgreSQL.
- Comandos independientes para ingesta, entrenamiento y prediccion.
- CI con lint, tests y validacion de migraciones.

## 6. Estructura propuesta

```text
ludopatia/
|-- data/
|   |-- raw/
|   |-- reference/
|   |-- processed/
|   `-- reports/
|-- artifacts/
|   `-- models/
|-- configs/
|-- docs/
|-- src/
|   `-- predictor/
|       |-- data/
|       |-- features/
|       |-- ratings/
|       |-- models/
|       |-- evaluation/
|       |-- inference/
|       `-- cli/
|-- tests/
|-- backend/
|-- frontend/
|-- pyproject.toml
|-- .env.example
`-- docker-compose.yml
```

`data/raw` sera inmutable. Las tablas transformadas se escribiran en
`data/processed` y los resultados de auditoria en `data/reports`.

## 7. Contrato canonico de partidos

La primera tabla procesada debe tener una fila por partido:

```text
match_id
kickoff_date
kickoff_utc
status
home_team_id
away_team_id
competition_id
location_id
neutral
home_is_tournament_host
away_is_tournament_host
home_score_90
away_score_90
went_to_extra_time
went_to_penalties
data_quality_status
source_name
source_match_id
```

Reglas:

- Entrenamiento usa solo `status=finished`.
- El objetivo usa exclusivamente goles a 90 minutos.
- Los 73 casos residuales de A se verifican o se excluyen.
- Equipos no FIFA quedan fuera del modelo principal.
- Fixtures futuros no entran en entrenamiento.
- Cada exclusión conserva un motivo auditable.

## 8. Construccion de D3: Elo prepartido

D3 es la primera feature que debe implementarse.

### Requisitos

- Orden cronologico estricto.
- Elo guardado antes de actualizar el partido.
- Rating inicial configurable.
- Ventaja local anulada o reducida en campo neutral.
- Factor K segun importancia de la competicion.
- Tratamiento explicito de empates.
- Tandas ignoradas para el resultado a 90 minutos.
- Parametros ajustados solo dentro del backtesting.

### Salida por partido

```text
home_elo_pre
away_elo_pre
elo_difference
home_elo_matches
away_elo_matches
```

Debe existir una prueba que demuestre que modificar un resultado futuro no
cambia el Elo prepartido de encuentros anteriores.

## 9. Construccion de features E

Cada partido se transforma en dos observaciones conceptuales, una por equipo,
para calcular historiales sin duplicar logica.

### E1: ataque y defensa

- goles anotados ponderados;
- goles recibidos ponderados;
- diferencia de gol;
- tasas recientes;
- numero efectivo de partidos.

### E2: ajuste por rival

- ataque ajustado por Elo rival;
- defensa ajustada por Elo rival;
- variantes con puntos FIFA para comparar;
- diferencia FIFA y antiguedad del ranking.

El ajuste exacto no se fijara por intuicion. Se compararan transformaciones
simples y regularizadas dentro del backtesting.

### E3: forma

- puntos por partido;
- proporcion de victorias, empates y derrotas;
- diferencia de gol reciente;
- tendencia con decaimiento.

### E4: perfiles de anotacion

- proporcion de porterias a cero;
- proporcion de partidos sin marcar;
- rachas recientes.

### E6: enfrentamientos directos

- fuerte decaimiento temporal;
- minimo de muestra;
- valor nulo cuando no exista evidencia;
- incluida solo en experimentos.

### Ventanas temporales

Se compararan:

- ultimos 3 anos;
- ultimos 5 anos;
- ultimos 8 anos;
- historia desde 2010 con decaimiento.

Tambien se ajustara la vida media del decaimiento. La ventana promovida sera la
que generalice mejor, no necesariamente cinco anos.

## 10. Modelado

### Baselines obligatorios

1. Promedio global de goles.
2. Poisson basado solo en localia y fuerza Elo/FIFA.
3. Poisson con ataque, defensa, localia y competicion.

### Modelo principal inicial

Dos modelos de goles:

- `lambda_home`;
- `lambda_away`.

El primer candidato sera una regresion de Poisson regularizada. Sobre la matriz
conjunta se evaluara una correccion Dixon-Coles para marcadores bajos.

La matriz se calculara al menos hasta 10 goles. La interfaz puede mostrar 0-5,
pero debe conservar una categoria `6+` o informar la masa de probabilidad no
visible. No se renormalizara artificialmente el recorte mostrado.

### Candidatos posteriores

- Negative Binomial si existe sobredispersion.
- HistGradientBoosting con perdida Poisson.
- CatBoost Poisson si se justifica una nueva dependencia.
- Ensemble entre el mejor modelo estadistico y no lineal.

Un modelo mas complejo solo se promueve si mejora de forma estable y no degrada
la calibracion.

## 11. Validacion y metricas

### Backtesting

Usar ventanas expansivas:

1. Entrenar hasta una fecha de corte.
2. Predecir el siguiente bloque temporal.
3. Avanzar el corte.
4. Concatenar predicciones fuera de muestra.

Los hiperparametros se ajustan dentro de cada periodo de entrenamiento. El
Mundial y otros torneos finales deben aparecer en evaluacion fuera de muestra.

### Metricas principales

- log loss de marcador exacto;
- Ranked Probability Score para 1X2;
- Brier score;
- curvas y error de calibracion;
- Poisson deviance;
- MAE de goles.

Metricas secundarias:

- exactitud 1X2;
- exactitud de marcador;
- top-k de marcadores.

### Cortes de diagnostico

- torneo;
- confederacion;
- campo neutral;
- anfitrion;
- diferencia de Elo;
- antiguedad del ranking;
- periodo temporal.

## 12. Artefacto entrenado

Cada ejecucion produce un directorio inmutable:

```text
artifacts/models/<model_version>/
|-- model.joblib
|-- feature_schema.json
|-- config.yaml
|-- metrics.json
|-- training_manifest.json
|-- calibration.json
`-- README.md
```

El manifiesto debe incluir:

- fecha maxima de entrenamiento;
- archivos y hashes de entrada;
- partidos incluidos y excluidos;
- features y orden;
- parametros;
- version de dependencias;
- commit cuando exista repositorio Git;
- metricas por fold y globales.

La promocion actualiza un puntero o registro `current`, pero no modifica el
artefacto original.

## 13. Comandos de trabajo

La interfaz de linea de comandos debe ofrecer:

```text
predictor validate-data
predictor build-matches
predictor build-ratings
predictor build-features
predictor train
predictor backtest
predictor promote
predictor predict-fixtures
```

Cada comando debe poder ejecutarse de forma independiente y reutilizar salidas
versionadas cuando sus entradas no cambien.

## 14. Base de datos

Tablas iniciales:

- `teams`;
- `team_aliases`;
- `competitions`;
- `locations`;
- `tournament_hosts`;
- `matches`;
- `rankings_fifa`;
- `elo_ratings`;
- `feature_snapshots`;
- `model_versions`;
- `predictions`;
- `prediction_score_matrices`.

Las tablas de referencia se cargan desde los CSV curados. Las features usadas en
una prediccion deben poder reconstruirse o consultarse mediante un snapshot.

## 15. API

Endpoints publicos iniciales:

```text
GET /health
GET /matches/today
GET /matches/upcoming
GET /matches/{match_id}
GET /matches/{match_id}/prediction
GET /groups
GET /teams/{team_id}
GET /models/current
```

La prediccion devuelve:

- probabilidades 1X2;
- lambdas;
- matriz;
- marcadores mas probables;
- features explicativas seleccionadas;
- version del modelo y timestamp.

Ingesta, entrenamiento y promocion no seran endpoints publicos.

## 16. Frontend

### Pagina principal

- partidos del dia;
- proximos partidos;
- estado y horario local;
- resumen de probabilidades.

### Calendario y grupos

- jornadas;
- grupos;
- resultados;
- acceso al detalle.

### Detalle del partido

- equipos, fecha, sede y fase;
- probabilidades 1X2;
- matriz de marcador;
- goles esperados;
- forma reciente;
- comparacion Elo/FIFA;
- ataque y defensa;
- explicacion de limitaciones;
- version y fecha del modelo.

La interfaz no debe presentar la prediccion como certeza ni ocultar la masa de
probabilidad fuera de la matriz visible.

## 17. Fases de implementacion

### Fase 0: inicializacion tecnica

Estado actual: **completada el 13 de junio de 2026**.

- Crear entorno virtual y `pyproject.toml`.
- Crear paquete, configuracion y estructura de carpetas.
- Fijar dependencias y herramientas de calidad.
- Agregar pruebas basicas y comandos CLI vacios.

Criterio de salida:

- instalacion reproducible;
- imports sin errores;
- `pytest` y lint ejecutables.

### Fase 1: dataset canonico

Estado actual: **completada para el primer baseline el 13 de junio de 2026**.

- Cargar fuentes y catalogos.
- Normalizar equipos, competiciones y sedes.
- Separar finalizados y fixtures.
- Aplicar politica A a prorroga y casos ambiguos.
- Generar reporte de exclusiones y calidad.

Criterio de salida:

- tabla canonica reproducible;
- cero IDs desconocidos;
- objetivos a 90 minutos validos;
- hashes y conteos documentados.

### Fase 2: ratings y features

Estado actual: **cerrada el 13 de junio de 2026**.

- Implementar D3.
- Unir el ultimo ranking FIFA anterior a cada partido.
- Implementar E1-E4.
- Implementar E6 detras de una opcion experimental.
- Agregar pruebas anti-leakage.

Criterio de salida:

- todas las filas de entrenamiento tienen features prepartido validas;
- ninguna feature usa el propio resultado ni datos futuros;
- reconstruccion determinista.

Resultado consolidado:

- D3 implementado y validado cronologicamente.
- Snapshots FIFA integrados para partidos historicos y fixtures.
- E1-E4 implementadas y cubiertas en entrenamiento e inferencia.
- E6 queda como ampliacion experimental futura.
- Configuracion congelada en `configs/modeling.yaml`.
- Politica hibrida Poisson + Dixon-Coles se pospone para una fase posterior.

### Fase 3: baselines y backtesting

Estado actual: **cerrada el 13 de junio de 2026**.

- Entrenar los tres baselines.
- Implementar folds temporales.
- Generar metricas y graficos de calibracion.
- Comparar ventanas y decaimientos.

Criterio de salida:

- reporte fuera de muestra reproducible;
- baseline de referencia elegido;
- fallos de calibracion identificados.

Resultado consolidado:

- Baseline Poisson entrenable implementado.
- Backtest temporal expansivo operativo.
- Comparacion de configuraciones completada.
- Baseline oficial actual: `Poisson`.

### Fase 4: modelo principal

Estado actual: **cerrada para la primera version el 13 de junio de 2026**.

- Entrenar Poisson regularizado.
- Implementar matriz y Dixon-Coles.
- Evaluar sobredispersion.
- Calibrar probabilidades 1X2 si es necesario.
- Persistir y recargar el artefacto.

Criterio de salida:

- supera el baseline acordado;
- matriz suma uno incluyendo la cola;
- predicciones estables al recargar;
- modelo promovido con manifiesto.

Resultado consolidado:

- El modelo principal promovido para la primera version es el baseline Poisson
  actual.
- Dixon-Coles fue evaluado, documentado y retenido como linea experimental.
- Se habilito diagnostico por segmentos para futuras politicas hibridas.

### Fase 5: backend y persistencia

Estado actual: **iniciada el 13 de junio de 2026**.

- Crear FastAPI.
- Crear modelos y migraciones.
- Importar datos de referencia.
- Guardar fixtures, predicciones y versiones.
- Implementar endpoints publicos.

Criterio de salida:

- API documentada por OpenAPI;
- prediccion recuperable por partido;
- historial inmutable de predicciones.

### Fase 6: frontend

- Implementar home, calendario, grupos y detalle.
- Construir matriz y comparativas.
- Integrar estados de carga, error y ausencia de prediccion.
- Validar escritorio y movil.

Criterio de salida:

- flujo completo desde partido hasta prediccion;
- interfaz accesible y comprensible;
- datos y version del modelo visibles.

### Fase 7: automatizacion

- Actualizar resultados y fixtures.
- Reconstruir features.
- Generar predicciones antes de cada jornada.
- Definir reentrenamiento controlado.
- Monitorear rendimiento y calibracion.

## 18. Estrategia de pruebas

### Datos

- esquemas y tipos;
- IDs y claves unicas;
- fechas validas;
- exclusiones documentadas;
- goles y estados coherentes.

### Ratings y features

- Elo prepartido;
- ausencia de fuga temporal;
- comportamiento de equipos sin historial;
- ranking anterior correcto;
- decaimiento y ventanas.

### Modelo

- probabilidades finitas y no negativas;
- suma total igual a uno;
- consistencia 1X2 con la matriz;
- serializacion y recarga;
- reproducibilidad con semilla fija.

### API y producto

- contratos;
- migraciones;
- consultas por fecha;
- version de prediccion;
- zonas horarias;
- comportamiento sin modelo promovido.

## 19. Primer hito entregable

Antes de construir la web debe existir una demostracion completa del nucleo:

1. Dataset canonico de entrenamiento.
2. Elo prepartido.
3. Features E1-E4 sin leakage.
4. Baselines y backtest temporal.
5. Modelo Poisson/Dixon-Coles versionado.
6. Comando que recibe un fixture y devuelve JSON con lambdas, 1X2 y matriz.

Este hito valida que el producto tiene una base predictiva real y evita construir
una interfaz atractiva alrededor de un modelo todavia inestable.

## 20. Decisiones consolidadas

- Mundial 2026 es el foco del producto inicial.
- El objetivo principal es el resultado a 90 minutos.
- Solo se usan fuentes gratuitas.
- Elo propio es la medida principal de fuerza.
- FIFA es una feature secundaria y explicativa.
- La ventana historica se elige por backtesting.
- E5 y H quedan fuera.
- F y G no bloquean el primer modelo.
- PostgreSQL es la base objetivo.
- El artefacto inicial se persiste con joblib.
- Backend y frontend se construyen despues de validar el nucleo ML.

## 21. Primera tarea de implementacion

La implementacion debe comenzar por la Fase 0 y la Fase 1:

1. Inicializar el paquete Python y el entorno.
2. Definir configuracion y contratos de datos.
3. Construir la tabla canonica de partidos.
4. Generar el primer reporte reproducible de calidad y exclusiones.

No se empezara por FastAPI, PostgreSQL o Next.js hasta que el dataset canonico
sea estable.
