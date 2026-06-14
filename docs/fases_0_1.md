# Cierre de fases 0 y 1

Fecha: 13 de junio de 2026.

## Fase 0: inicializacion tecnica

Estado: **completada**.

### Entorno

- Python 3.12.10 instalado.
- Entorno virtual: `.venv`.
- Dependencias declaradas en `pyproject.toml`.
- Grupos opcionales `dev` y `ml`.
- Comando instalado: `predictor`.
- VS Code configurado para utilizar el interprete de `.venv`.

### Calidad

- Ruff configurado para lint y formato.
- pytest configurado.
- 8 pruebas aprobadas.
- Cobertura inicial: 68%.
- La advertencia restante proviene de la compatibilidad futura entre
  `fastapi.testclient`, Starlette y httpx; no afecta la aplicacion.

### Arquitectura

El paquete `src/predictor` se divide en:

- `domain`: entidades y reglas sin frameworks.
- `application`: casos de uso y puertos.
- `infrastructure`: configuracion, datos y base de datos.
- `presentation`: API y CLI.

FastAPI y SQLAlchemy no son dependencias del dominio.

### Base de datos

- PostgreSQL es el objetivo.
- SQLAlchemy usa el driver asincrono `asyncpg`.
- Alembic esta inicializado.
- La URL se lee desde `DATABASE_URL`.
- Se aceptan URLs con esquema `postgres://`, `postgresql://` o
  `postgresql+asyncpg://`.
- No se requiere una base conectada para construir datos o entrenar.

Cuando exista la instancia remota:

```text
DATABASE_URL=postgresql://usuario:password@host:puerto/database
```

## Fase 1: dataset canonico

Estado: **completada para el primer baseline**.

### Comandos

```powershell
predictor validate-data
predictor build-matches --minimum-date 2021-01-01
```

### Fuentes validadas

| Fuente | Filas |
|---|---:|
| `results.csv` | 49.477 |
| `teams.csv` | 262 |
| `competitions.csv` | 66 |
| `locations.csv` | 756 |
| `goalscorers.csv` | 47.606 |
| `shootouts.csv` | 678 |

Todos los esquemas cumplen el contrato esperado.

### Salidas

- `data/processed/matches.csv`
- `data/processed/fixtures.csv`
- `data/reports/match_exclusions.csv`
- `data/reports/data_quality.json`

Resultado desde el 1 de enero de 2021:

- 5.755 filas fuente.
- 5.317 partidos aptos para entrenamiento.
- 70 fixtures.
- 368 exclusiones.
- 0 referencias desconocidas.
- 0 IDs duplicados.
- 0 solapamientos entre entrenamiento y fixtures.

Exclusiones:

- 238 partidos fuera del alcance FIFA principal.
- 130 partidos FIFA con marcador a 90 minutos ambiguo.
- 137 partidos totales muestran evidencia de tanda o gol posterior al minuto
  90; siete tambien estan fuera del alcance del modelo.

La cifra conservadora de 130 es mayor que la cola residual de recoleccion porque
todavia no se han convertido los respaldos de torneos principales en overrides
estructurados. Esos partidos no se pierden: permanecen en el reporte y pueden
reincorporarse cuando su marcador a 90 minutos quede materializado.

### Hashes de salida

```text
matches.csv
27C50534C908BF6BEE86743BE63EF5BE5827D46D2ABB7A2519C2B1422EE8064E

fixtures.csv
4DDF425C8D9B0B9FAB891728DDF5FA66768B4DE08BCAC89B187D6E90CBE9725E

match_exclusions.csv
C4C9A0BC39C3D8F983BA90EBFF5F91AF08FBCAD31DB553664533FFED89AE00FA
```

`data_quality.json` conserva tambien los hashes de todas las fuentes.

### Politica aplicada

- Solo miembros FIFA y competiciones incluidas.
- Solo partidos finalizados para entrenamiento.
- Fixtures almacenados por separado.
- Marcadores parciales rechazados.
- Tandas y goles posteriores al minuto 90 excluidos de forma conservadora.
- Identidad de equipo, competicion y localidad obligatoria.
- Condicion de anfitrion derivada por edicion y ano jugado.

## Siguiente fase

La siguiente tarea es la Fase 2:

1. Implementar Elo prepartido D3.
2. Unir el ultimo ranking FIFA publicado antes de cada partido.
3. Construir E1-E4 sin fuga temporal.
4. Mantener E6 detras de una opcion experimental.

