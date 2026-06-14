# Categoria E: rendimiento reciente derivado

Fecha de definicion: 13 de junio de 2026.

## Alcance

Se conservan:

- **E1:** goles anotados y recibidos.
- **E2:** ataque y defensa ajustados por rival.
- **E3:** forma de resultados.
- **E4:** porterias a cero y partidos sin marcar.
- **E6:** enfrentamientos directos, solo como feature experimental.

Se descarta:

- **E5:** dias de descanso y carga de partidos.

La categoria E no necesita una fuente externa adicional. Sus variables se
calcularan posteriormente a partir de datos ya recolectados y siempre usando
solo partidos anteriores al encuentro objetivo.

## Fuentes disponibles

### Resultados y cronologia

Fuente principal:
`data/results.csv`

Datos disponibles:

- fecha;
- local y visitante;
- goles;
- competicion;
- ciudad y pais;
- condicion neutral.

La categoria A ya definio la politica para separar o excluir resultados
ambiguos por prorroga. Solo los partidos aprobados por esa politica podran
alimentar las features E.

### Identidad de equipos

Fuente:
`data/reference/teams.csv`

Permite construir historiales por seleccion y enfrentamientos directos sin
duplicar equipos por aliases.

### Fuerza del rival

Fuentes:

- `data/ranking_fifa_historical_complete.csv`
- futuro Elo prepartido de D3.

El ranking FIFA esta recolectado hasta el 11 de junio de 2026. D3 no requiere
mas informacion externa, pero su calculo se realizara durante la implementacion.

## E1: goles anotados y recibidos

Objetivo:

- tasa reciente de goles anotados;
- tasa reciente de goles recibidos;
- diferencia de gol;
- tendencia ofensiva y defensiva.

Politica:

- usar exclusivamente goles a 90 minutos;
- excluir partidos ambiguos no verificados;
- separar observaciones como local y visitante cuando el backtesting lo
  justifique;
- aplicar decaimiento temporal en lugar de tratar todos los partidos igual;
- comparar ventanas de 3, 5 y 8 anos.

Estado de datos: **completo por alcance**.
Estado de feature: **pendiente de implementacion**.

## E2: ataque y defensa ajustados por rival

Objetivo:

- evitar que un mismo marcador tenga el mismo peso contra rivales de fuerza muy
  distinta;
- estimar produccion ofensiva y defensiva relativa al nivel esperado.

Se probaran dos referencias:

- Elo prepartido propio, como opcion principal;
- puntos FIFA prepartido, como referencia secundaria.

No se ajustara usando un rating posterior al partido.

Estado de datos: **completo**.
Dependencia de implementacion: **D3**.

## E3: forma de resultados

Variables candidatas:

- puntos por partido;
- proporcion de victorias, empates y derrotas;
- diferencia de gol;
- racha reciente con decaimiento.

La forma no se definira mediante una unica ventana arbitraria de cinco partidos.
La ventana y la vida media se elegiran por validacion temporal.

Estado de datos: **completo por alcance**.
Estado de feature: **pendiente de implementacion**.

## E4: porterias a cero y partidos sin marcar

Variables candidatas:

- proporcion ponderada de porterias a cero;
- proporcion ponderada de partidos sin marcar;
- rachas recientes;
- valores ajustados por fuerza del rival si mejoran el backtesting.

Estas variables complementan los promedios de goles, pero no deben duplicar
innecesariamente la misma senal.

Estado de datos: **completo por alcance**.
Estado de feature: **pendiente de implementacion**.

## E6: enfrentamientos directos

Se conserva como feature P2 experimental.

Limitaciones:

- pocas observaciones para muchas parejas;
- largos periodos entre partidos;
- cambios de entrenador y plantilla;
- riesgo de sobrevalorar narrativas historicas.

Politica:

- fuerte decaimiento temporal;
- valor nulo cuando no exista muestra suficiente;
- nunca sustituir la fuerza general ni la forma reciente;
- retirar la feature si no mejora log loss, RPS o calibracion.

Estado de datos: **completo por alcance**.
Estado de feature: **experimental y pendiente de implementacion**.

## E5 descartado

Los dias de descanso y la carga de partidos se excluyen del alcance principal.

Motivos:

- la fecha ya permite una aproximacion, pero no siempre existe kickoff exacto;
- en selecciones la carga real depende principalmente de minutos y viajes con
  clubes, datos que no tenemos con cobertura uniforme;
- una aproximacion parcial puede introducir mas ruido que informacion;
- su beneficio probable no compensa la complejidad adicional en esta version.

Puede reconsiderarse en el futuro, pero no queda como deuda del proyecto.

## Prevencion de fuga de informacion

Para cada partido objetivo:

1. Se filtran partidos con fecha estrictamente anterior.
2. Se toma el rating disponible antes del encuentro.
3. Se calculan agregados sin incluir el propio partido.
4. Las ventanas se ajustan solo dentro del conjunto de entrenamiento.
5. La validacion se realiza cronologicamente.

## Criterio de cierre

La recoleccion de E se considera cerrada porque:

- todas las features conservadas derivan de fuentes ya disponibles;
- no queda ningun dataset externo obligatorio por buscar;
- E2 tiene definidos sus ratings de ajuste;
- E5 fue descartado explicitamente;
- E6 tiene un alcance experimental y una regla clara de eliminacion.

Estado: **recoleccion cerrada; implementacion pendiente**.
