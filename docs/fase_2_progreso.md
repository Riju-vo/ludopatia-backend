# Progreso de Fase 2

Fecha: 13 de junio de 2026.

## Estado

Fase 2 esta **operativa** con entrenamiento, backtesting, comparacion de
configuraciones, prueba Dixon-Coles, diagnostico por segmentos e inferencia de
fixtures.

Ya quedaron implementados:

- D3: Elo prepartido cronologico.
- Union temporal del ultimo ranking FIFA anterior a cada partido.
- Snapshots equivalentes para fixtures futuros.
- Persistencia reproducible de ratings y reporte de calidad.
- E1: goles anotados y recibidos ponderados.
- E2: ataque y defensa ajustados por rival con Elo y FIFA prepartido.
- E3: forma de resultados con decaimiento temporal.
- E4: porterias a cero y partidos sin marcar.
- Baseline entrenable con `PoissonRegressor` para goles local y visitante.
- Artefacto versionado `joblib` con metadatos y predicciones de validacion.
- Backtest temporal con ventanas expansivas y reporte por fold.
- Comparador de configuraciones para vida media y ventana historica.
- Backtest especifico para Dixon-Coles contra el baseline Poisson.
- Diagnostico por segmentos sobre las mismas predicciones fuera de muestra.
- Prediccion de fixtures con probabilidades 1X2 y matriz exacta de marcador.

Sigue pendiente dentro de esta etapa ampliada:

- E6: enfrentamientos directos como opcion experimental.
- Calibracion mas fina.
- Promocion de un modelo que mejore tanto 1X2 como scoreline exacto.

## Configuracion congelada

Fuente:
`configs/modeling.yaml`

Configuracion ganadora de features:

- `half_life_days = 365`
- `history_years = 5`
- `max_history_days = 1825`

Configuracion base de backtest:

- `initial_train_days = 730`
- `validation_window_days = 180`
- `step_days = 180`

## Comandos nuevos

```powershell
predictor build-ratings
predictor build-features
predictor train-model
predictor backtest
predictor compare-feature-configs
predictor backtest-dixon-coles
predictor segment-diagnostics
predictor predict-fixtures
```

## Salidas

- `data/processed/match_ratings.csv`
- `data/processed/fixture_ratings.csv`
- `data/processed/team_elo_latest.csv`
- `data/reports/ratings_quality.json`
- `data/processed/match_features.csv`
- `data/processed/fixture_features.csv`
- `data/reports/features_quality.json`
- `artifacts/models/<version>/model.joblib`
- `artifacts/models/<version>/metadata.json`
- `artifacts/models/<version>/validation_predictions.csv`
- `data/reports/backtest_fold_metrics.csv`
- `data/reports/backtest_predictions.csv`
- `data/reports/backtest_report.json`
- `data/reports/feature_config_rankings.csv`
- `data/reports/feature_config_search.json`
- `data/reports/dixon_coles_backtest_fold_metrics.csv`
- `data/reports/dixon_coles_backtest_predictions.csv`
- `data/reports/dixon_coles_backtest_report.json`
- `data/reports/segment_diagnostics_baseline.csv`
- `data/reports/segment_diagnostics_dixon_coles.csv`
- `data/reports/segment_diagnostics_report.json`
- `data/predictions/fixture_predictions.csv`
- `data/predictions/fixture_score_matrices.json`

## Resumen de resultados

- 5.317 partidos con ratings y features prepartido.
- 70 fixtures con ratings y features prepartido.
- 10.634 observaciones historicas por equipo para construir snapshots.
- Cobertura de features en fixtures: 70 de 70 filas completas para E1-E4.
- Baseline entrenado con 4.455 partidos de entrenamiento.
- Validacion temporal holdout sobre 862 partidos.
- Backtest expansivo con 7 folds y 3.306 predicciones fuera de muestra.
- Comparacion real de 9 configuraciones de features completada.
- 70 fixtures generados con probabilidades y matrices exactas.

## Baseline actual

Version:
`baseline_poisson_20260613T143656Z`

Metricas de validacion holdout:

- `home_goal_mae`: 1.0281
- `away_goal_mae`: 0.8600
- `home_goal_poisson_deviance`: 1.2031
- `away_goal_poisson_deviance`: 1.1839
- `outcome_log_loss`: 0.8107
- `outcome_brier_score`: 0.4720

Metricas agregadas de backtest:

- `home_goal_mae`: 1.0256
- `away_goal_mae`: 0.8307
- `home_goal_poisson_deviance`: 1.1999
- `away_goal_poisson_deviance`: 1.1302
- `outcome_log_loss`: 0.8548
- `outcome_brier_score`: 0.5014
- `outcome_accuracy`: 0.6120

## Comparacion de configuraciones

Ganadora:

- `half_life=365`, `history_years=5`

Top configuraciones:

1. `365 / 5`
2. `365 / 8`
3. `180 / 5`

La diferencia con `365 / 8` fue minima, pero `365 / 5` sigue siendo la mejor.

## Resultado Dixon-Coles

Promedio de `rho`:

- `0.0174`

Comparacion agregada contra baseline Poisson:

- `baseline_outcome_log_loss = 0.8547667`
- `dixon_coles_outcome_log_loss = 0.8545793`
- mejora en 1X2:
  `-0.0001874`

- `baseline_exact_score_log_loss = 2.8486122`
- `dixon_coles_exact_score_log_loss = 2.8490829`
- empeora en scoreline exacto:
  `+0.0004706`

Conclusion actual:

- Dixon-Coles mejora muy ligeramente la parte 1X2.
- No mejora el scoreline exacto agregado.
- Por ahora **no conviene promoverlo como reemplazo del baseline**.

## Diagnostico por segmentos

Cobertura comparada:

- 3.306 partidos fuera de muestra, exactamente los mismos del backtest
  expansivo.

Hallazgos mas claros:

- En partidos **no neutrales** mejora:
  `delta_log_loss = -0.0004243`
- En partidos **neutrales** empeora:
  `delta_log_loss = +0.0005813`
- En **friendlies** empeora:
  `delta_log_loss = +0.0008570`
- En `continental_qualification`, `nations_league` y
  `regional_championship` mejora de forma consistente.
- En `home_strong` mejora:
  `delta_log_loss = -0.0006358`
- En `away_edge` empeora:
  `delta_log_loss = +0.0010020`

Lectura practica:

- Dixon-Coles parece capturar mejor partidos competitivos y no neutrales.
- No muestra ventaja estable en amistosos ni en escenarios neutrales.
- La mejora global existe en 1X2, pero es demasiado pequena e inconsistente
  entre segmentos para reemplazar el baseline completo.

Decision actual:

- **Poisson baseline** sigue siendo el modelo oficial para entrenamiento e
  inferencia general.
- **Dixon-Coles** queda como ajuste experimental para una futura politica
  hibrida por segmentos.
- La siguiente comparacion razonable seria una regla conservadora:
  activar Dixon-Coles solo en partidos no neutrales y no amistosos.

## Ejemplo de prediccion

- Canada vs Bosnia y Herzegovina:
  `lambda_home=2.0323`, `lambda_away=0.6730`
- probabilidades:
  `home=0.6927`, `draw=0.1947`, `away=0.1126`
- marcador modal:
  `2-0` con probabilidad `0.1381`

## Validaciones incluidas

- El Elo prepartido no cambia al modificar resultados futuros.
- El ranking FIFA usado es el ultimo publicado antes del partido.
- Las features E1-E4 no usan el partido objetivo ni resultados futuros.
- El baseline usa solo variables prepartido.
- El backtest reentrena cronologicamente sin mezclar futuro.
- La comparacion de configuraciones reutiliza el mismo backtest para todas las
  variantes.
- Dixon-Coles se compara sobre los mismos folds y lambdas base.
- La inferencia usa la version exacta del modelo guardado.
- Fixtures y partidos usan el mismo contrato temporal.
- La CLI genera salidas reproducibles con hash o version.
