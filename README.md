# World Cup Predictor

Predictor probabilistico entrenable para partidos internacionales, con foco en
el Mundial 2026.

## Inicio local

```powershell
.\.venv\Scripts\Activate.ps1
Copy-Item .env.example .env
predictor validate-data
predictor build-matches
predictor build-ratings
predictor build-features
predictor train-model
predictor backtest
predictor compare-feature-configs
predictor backtest-dixon-coles
predictor segment-diagnostics
predictor predict-fixtures
pytest
```

`DATABASE_URL` acepta una URL PostgreSQL externa. Para SQLAlchemy asincrono debe
usar el esquema `postgresql+asyncpg://`. Las URLs `postgres://` y
`postgresql://` entregadas por Railway o proveedores compatibles se normalizan
automaticamente.

Para iniciar la API local:

```powershell
uvicorn predictor.presentation.api.main:app --reload
```

Con la estructura actual usando `src/`, el comando recomendado es:

```powershell
python -m uvicorn predictor.presentation.api.main:app --reload --app-dir src
```

La configuracion de VS Code apunta a `.venv\Scripts\python.exe`.

## Estado

- Fase 0: completada.
- Fase 1: completada con politica conservadora para prorroga.
- Fase 2: ratings y features E1-E4 implementadas.
- Configuracion de features congelada en `configs/modeling.yaml`.
- Baseline entrenable: Poisson versionado con validacion temporal.
- Backtesting temporal: ventanas expansivas con reporte por fold.
- Comparacion de configuraciones: vida media y ventana historica evaluables por
  CLI.
- Dixon-Coles: evaluado contra el baseline, todavia no promovido.
- Diagnostico por segmentos: disponible para medir donde Dixon-Coles ayuda y
  donde conviene quedarse con Poisson.
- Inferencia de fixtures: probabilidades 1X2 y matriz exacta de marcador.
- Backend: arquitectura limpia preparada; endpoints funcionales se anaden tras
  estabilizar el nucleo ML.

Detalles: [`docs/fases_0_1.md`](docs/fases_0_1.md) y
[`docs/fase_2_progreso.md`](docs/fase_2_progreso.md).

## Railway

El backend esta preparado para desplegarse como servicio independiente en
Railway con [`railway.json`](railway.json).

Variables recomendadas:

```env
APP_ENV=production
LOG_LEVEL=INFO
API_REPOSITORY_BACKEND=database
DATABASE_URL=<postgres-url-de-railway>
CORS_ALLOWED_ORIGINS=https://<tu-frontend>.up.railway.app
```

Notas:

- `DATABASE_URL` puede venir como `postgres://` o `postgresql://`; la app la
  normaliza automaticamente a `postgresql+asyncpg://`.
- El healthcheck queda en `/health`.
