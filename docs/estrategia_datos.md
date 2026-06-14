# Estrategia de datos

## Objetivo de este documento

Este documento funciona como inventario maestro de los datos necesarios para el
modelo. Cada elemento especifica:

- Que dato crudo necesitamos.
- Que variable predictiva construiremos con el.
- Por que puede aportar informacion.
- En que momento debe estar disponible para evitar fuga de informacion.
- Que significa considerarlo completamente cubierto.

La cobertura se evalua con un criterio estricto: si una fuente esta
desactualizada, no distingue correctamente el objetivo, tiene cobertura sesgada
o necesita ser mejorada, el elemento se marca como no cubierto.

## Convenciones

### Restriccion de costo

El proyecto utilizara exclusivamente datos gratuitos, abiertos o disponibles sin
suscripcion. No se diseñara ninguna parte esencial alrededor de una API paga,
una prueba temporal o un dataset cuyo historial requiera compra.

Si una variable solo puede obtenerse de forma completa mediante pago:

- Se descarta del alcance principal.
- Se busca un proxy gratuito y reproducible.
- El proxy solo se conserva si mejora el backtesting.
- La limitacion se documenta en la interfaz y en las metricas del modelo.

### Prioridad

- **P0 - Esencial:** necesario para entrenar un modelo valido.
- **P1 - Alto valor:** candidato fuerte para mejorar la precision.
- **P2 - Experimental:** util solo si demuestra mejora estable en backtesting.

### Momento de disponibilidad

Toda variable debe representar el estado conocido antes del inicio del partido.
No se pueden usar rankings publicados despues, alineaciones que aun no se
conocian, estadisticas del propio partido ni agregados recalculados con partidos
futuros.

### Datos crudos y features

No necesitamos buscar un dataset que ya contenga columnas como
`rolling_attack_strength`. Esa feature se calcula internamente a partir de datos
crudos historicos. Lo importante es que los datos base sean completos,
cronologicos y reproducibles.

## Inventario detallado de datos

### A. Objetivo y resultado del partido

La recoleccion de la categoria A se considera cerrada por alcance. Los 73 casos
residuales no bloquean el proyecto: se verificaran manualmente o se excluiran
antes del entrenamiento.

#### A1. Goles a los 90 minutos

- **Prioridad:** P0.
- **Dato crudo:** goles de cada seleccion al terminar el tiempo reglamentario,
  excluyendo prorroga y penales.
- **Uso:** variable objetivo de los modelos de goles y base de la matriz de
  marcadores.
- **Justificacion:** mezclar 90 y 120 minutos aumenta artificialmente los goles
  de algunos partidos eliminatorios y entrena distribuciones incompatibles.
- **Cobertura completa:** todos los partidos de entrenamiento indican marcador a
  90 minutos y permiten distinguir prorroga.
- **Estado:** cubierto por alcance. Los torneos principales estan respaldados y
  los casos residuales no verificables se excluiran.

#### A2. Prorroga y tanda de penales

- **Prioridad:** P1 para eliminatorias; no se usa en fase de grupos.
- **Dato crudo:** marcador tras prorroga, existencia de prorroga, resultado de
  penales y orden de lanzamiento cuando este disponible.
- **Uso:** modelo separado de clasificacion en rondas eliminatorias y simulacion
  completa del torneo.
- **Justificacion:** la probabilidad de ganar en 90 minutos no es igual a la de
  avanzar de ronda.
- **Cobertura completa:** estado y resultado de cada etapa identificados de forma
  independiente.
- **Estado:** cubierto por alcance. Las tandas estan identificadas, los torneos
  principales tienen detalle y los residuales se revisaran o excluiran.

#### A3. Estado del partido

- **Prioridad:** P0.
- **Dato crudo:** programado, en juego, finalizado, suspendido, cancelado o
  aplazado.
- **Uso:** separar entrenamiento, inferencia y actualizaciones del producto.
- **Justificacion:** un marcador nulo no basta para distinguir un fixture futuro
  de un partido cancelado.
- **Cobertura completa:** estado explicito y actualizado para cada fixture.
- **Estado:** cubierto por adaptacion de alcance: `scheduled`, `finished` y
  `unknown`, sin dependencia de estado en vivo.

### B. Identidad y calendario

La auditoria y las fuentes recolectadas para esta categoria se documentan en
[`categoria_b_fuentes.md`](categoria_b_fuentes.md).

#### B1. Identidad canonica de las selecciones

- **Prioridad:** P0.
- **Dato crudo:** identificador estable, nombre oficial, aliases, codigo FIFA,
  confederacion y condicion de miembro FIFA.
- **Uso:** cruzar resultados, rankings, plantillas y proveedores sin confundir
  nombres historicos.
- **Justificacion:** existen aliases como `United States`/`USA` y equipos no FIFA
  que no deben tratarse como selecciones equivalentes.
- **Cobertura completa:** catalogo versionado con todos los equipos de las
  fuentes y reglas explicitas de sucesion o cambio de nombre.
- **Estado:** completamente cubierto por `data/reference/teams.csv`.

#### B2. Fecha del partido

- **Prioridad:** P0.
- **Dato crudo:** fecha calendario.
- **Uso:** orden cronologico, ventanas historicas, decaimiento y descanso.
- **Justificacion:** toda feature prepartido depende del orden temporal.
- **Cobertura completa:** fecha valida para todos los partidos.
- **Estado:** cubierto por `results.csv`.

#### B3. Hora exacta y zona horaria

- **Prioridad:** P1 para producto y P2 para el modelo.
- **Dato crudo:** hora de inicio local, zona horaria y equivalente UTC.
- **Uso:** partidos del dia, actualizacion oportuna, descanso exacto y posible
  efecto de horario biologico.
- **Justificacion:** la fecha sola no permite ordenar dos partidos del mismo dia
  ni operar correctamente la aplicacion.
- **Cobertura completa:** kickoff UTC y zona local para todos los fixtures
  relevantes.
- **Estado:** cubierto por adaptacion de alcance. Es obligatorio para el Mundial
  y fixtures del producto, y opcional para el entrenamiento historico.

#### B4. Competicion y torneo

- **Prioridad:** P0.
- **Dato crudo:** nombre de la competicion.
- **Uso:** ponderar amistosos, eliminatorias, Nations League y torneos finales.
- **Justificacion:** los incentivos y la seleccion de jugadores cambian segun la
  competicion.
- **Cobertura completa:** competicion presente y normalizada en todos los
  partidos.
- **Estado:** completamente cubierto por
  `data/reference/competitions.csv`.

#### B5. Fase, grupo y jornada

- **Prioridad:** P1.
- **Dato crudo:** fase, grupo, jornada, ida/vuelta y condicion eliminatoria.
- **Uso:** medir contexto competitivo y construir calendario, grupos y llaves.
- **Justificacion:** un tercer partido de grupo puede tener incentivos distintos
  a una primera jornada; una vuelta depende del resultado de ida.
- **Cobertura completa:** estructura competitiva explicita para cada partido.
- **Estado:** cubierto por adaptacion de alcance para los principales torneos.
  No sera una feature global obligatoria en competiciones menores.

### C. Localia, sede y entorno

La auditoria y las fuentes de esta categoria se documentan en
[`categoria_c_fuentes.md`](categoria_c_fuentes.md).

#### C1. Equipo nominal local y visitante

- **Prioridad:** P0.
- **Dato crudo:** ambas selecciones y orden nominal.
- **Uso:** construir observaciones por equipo y presentar el encuentro.
- **Justificacion:** es parte minima del contrato de cada partido.
- **Cobertura completa:** ambos campos presentes en todos los registros.
- **Estado:** cubierto por `results.csv`.

#### C2. Campo neutral

- **Prioridad:** P0.
- **Dato crudo:** indicador de sede neutral.
- **Uso:** ajustar la ventaja local.
- **Justificacion:** en selecciones, el orden local/visitante puede ser nominal.
- **Cobertura completa:** indicador fiable para cada partido.
- **Estado:** cubierto por `results.csv`.

#### C3. Pais y ciudad de la sede

- **Prioridad:** P0 para localia; P1 para contexto.
- **Dato crudo:** ciudad y pais anfitrion.
- **Uso:** identificar anfitrion real, viaje, clima y altitud.
- **Justificacion:** jugar en el pais propio puede importar incluso si FIFA marca
  el partido como neutral.
- **Cobertura completa:** ciudad y pais presentes y normalizados.
- **Estado:** completamente cubierto por `data/reference/locations.csv`: 756 de
  756 parejas normalizadas, con coordenadas, zona horaria y correcciones
  documentadas.

#### C4. Estadio

- **Prioridad:** P1.
- **Dato crudo:** identificador, nombre y coordenadas del estadio.
- **Uso:** altitud, clima, capacidad, superficie y localia real.
- **Justificacion:** ciudad no siempre identifica de forma univoca las
  condiciones de juego.
- **Cobertura completa:** estadio e identificador estable en todos los partidos
  relevantes.
- **Estado:** cubierto por adaptacion de alcance. Los 16 estadios del Mundial
  2026 estan disponibles; el entrenamiento global usa ciudad cuando no existe
  una fuente abierta uniforme de estadio.

#### C5. Condicion de anfitrion del torneo

- **Prioridad:** P1.
- **Dato crudo:** paises anfitriones y periodo de cada competicion.
- **Uso:** feature distinta de `neutral` y del orden nominal.
- **Justificacion:** un anfitrion conserva familiaridad, apoyo y menor viaje aun
  en partidos formalmente neutrales.
- **Cobertura completa:** anfitriones vinculados a cada edicion del torneo.
- **Estado:** completamente cubierto por
  `data/reference/tournament_hosts.csv`: 36 relaciones de anfitrion para 21
  ediciones principales desde 2021.

### D. Fuerza estructural de las selecciones

La auditoria y las fuentes de esta categoria se documentan en
[`categoria_d_fuentes.md`](categoria_d_fuentes.md).

#### D1. Puntos FIFA prepartido

- **Prioridad:** P1.
- **Dato crudo:** puntos FIFA publicados mas recientemente antes de cada partido.
- **Uso:** nivel institucional de largo plazo y diferencia entre rivales.
- **Justificacion:** resume resultados con la metodologia oficial y complementa
  la forma reciente.
- **Cobertura completa:** historial hasta la fecha de prediccion, con fecha de
  publicacion y mapeo de equipos completo.
- **Estado:** completamente cubierto hasta el 11 de junio de 2026 por
  `data/ranking_fifa_historical_complete.csv` y 13 snapshots oficiales.

#### D2. Posicion FIFA prepartido

- **Prioridad:** P2.
- **Dato crudo:** posicion oficial en cada publicacion.
- **Uso:** explicabilidad y posible feature secundaria.
- **Justificacion:** es intuitiva para el usuario, aunque pierde informacion
  respecto a los puntos.
- **Cobertura completa:** mismas condiciones que D1.
- **Estado:** completamente cubierto. La posicion nueva es oficial y la
  historica se reconstruye del orden de la tabla fuente; el solapamiento de
  septiembre de 2024 tuvo cero diferencias.

#### D3. Elo prepartido

- **Prioridad:** P0.
- **Dato crudo necesario:** resultados cronologicos, localia y tipo de torneo.
- **Feature derivada:** rating Elo de cada equipo justo antes del partido y su
  diferencia.
- **Justificacion:** ofrece una fuerza actualizada partido a partido y cubre los
  huecos entre publicaciones FIFA.
- **Cobertura completa:** pipeline Elo implementado, probado y reproducible para
  todas las selecciones elegibles.
- **Estado:** recoleccion completa. Resultados, localia y taxonomia de torneos
  ya estan disponibles; solo falta implementar y validar la feature.

### E. Rendimiento reciente derivado de resultados

Todas las features de esta seccion deben calcularse usando exclusivamente
partidos anteriores al objetivo, con ventanas y decaimiento elegidos mediante
backtesting.

La recoleccion de informacion de esta categoria esta cerrada. E1-E4 y E6 se
derivan de resultados, equipos canonicos y ratings ya disponibles. E5 fue
descartado del alcance. La estrategia detallada se documenta en
[`categoria_e_fuentes.md`](categoria_e_fuentes.md).

#### E1. Goles anotados y recibidos

- **Prioridad:** P0.
- **Features:** medias ponderadas, tasas por partido y tendencias recientes.
- **Justificacion:** aproximan capacidad ofensiva y fragilidad defensiva.
- **Cobertura completa:** goles a 90 minutos fiables y partidos correctamente
  ordenados.
- **Estado:** datos cubiertos por alcance mediante la politica de categoria A;
  feature pendiente de implementacion.

#### E2. Ataque y defensa ajustados por rival

- **Prioridad:** P0.
- **Features:** goles anotados/recibidos ponderados por Elo o fuerza del rival.
- **Justificacion:** evita valorar igual un 3-0 ante un rival debil y ante uno de
  elite.
- **Cobertura completa:** E1 y Elo prepartido completos.
- **Estado:** datos cubiertos. La feature depende de implementar D3.

#### E3. Forma de resultados

- **Prioridad:** P1.
- **Features:** puntos por partido, victorias, empates, derrotas y diferencia de
  gol con decaimiento.
- **Justificacion:** captura cambios recientes no reflejados por la fuerza de
  largo plazo.
- **Cobertura completa:** resultado a 90 minutos y cronologia fiables.
- **Estado:** datos cubiertos por alcance; feature pendiente de implementacion.

#### E4. Porterias a cero y partidos sin marcar

- **Prioridad:** P1.
- **Features:** proporciones ponderadas y rachas.
- **Justificacion:** distinguen perfiles defensivos/ofensivos que el promedio de
  goles puede ocultar.
- **Cobertura completa:** goles a 90 minutos fiables.
- **Estado:** datos cubiertos por alcance; feature pendiente de implementacion.

#### E5. Dias de descanso y carga de partidos

- **Prioridad:** descartado.
- **Features:** dias desde el ultimo partido y partidos disputados en ventanas de
  7, 14 y 30 dias.
- **Justificacion:** fatiga y rotacion pueden afectar rendimiento.
- **Cobertura completa:** fecha y, preferiblemente, hora exacta para todos los
  partidos.
- **Estado:** descartado del alcance. La carga real depende de minutos y viajes
  con clubes, sin cobertura gratuita uniforme; la aproximacion solo por fecha
  puede introducir mas ruido que informacion.

#### E6. Enfrentamientos directos

- **Prioridad:** P2.
- **Features:** resultados previos con fuerte decaimiento.
- **Justificacion:** puede capturar emparejamientos tacticos, pero las muestras
  suelen ser pequeñas y las plantillas cambian.
- **Cobertura completa:** identidad canonica y resultados a 90 minutos.
- **Estado:** datos cubiertos por alcance. Se conserva solo como feature P2
  experimental y se eliminara si no mejora la validacion temporal.

### F. Produccion ofensiva y defensiva del partido

#### F1. Tiros totales

- **Prioridad:** P1.
- **Uso:** volumen de produccion ofensiva y de ocasiones concedidas.
- **Justificacion:** es menos aleatorio que el gol observado.
- **Cobertura completa:** tiros de ambos equipos para al menos 90% de partidos
  relevantes, sin sesgo fuerte por confederacion.
- **Estado:** no cubierto.

#### F2. Tiros al arco

- **Prioridad:** P1.
- **Uso:** calidad basica de finalizacion y exigencia al portero.
- **Justificacion:** mejora la señal de ataque/defensa respecto a tiros totales.
- **Cobertura completa:** mismo criterio que F1.
- **Estado:** no cubierto.

#### F3. Expected goals y npxG

- **Prioridad:** P1 si existe cobertura consistente.
- **Uso:** calidad de ocasiones creadas y concedidas, separando penales con npxG.
- **Justificacion:** reduce el ruido de definicion y resultado.
- **Cobertura completa:** misma metodologia de xG para todo el periodo y al menos
  90% de los partidos relevantes.
- **Estado:** no cubierto.

No se deben mezclar valores xG de proveedores distintos sin una calibracion
previa: cada proveedor utiliza su propio modelo.

#### F4. Grandes ocasiones

- **Prioridad:** P2.
- **Uso:** complemento interpretable de xG.
- **Justificacion:** puede capturar oportunidades claras, pero su definicion es
  dependiente del proveedor.
- **Cobertura completa:** definicion estable y cobertura uniforme.
- **Estado:** no cubierto.

#### F5. Posesion y pases

- **Prioridad:** P2.
- **Datos:** porcentaje de posesion, pases intentados/completados y progresion si
  existe.
- **Uso:** perfil de control y estilo.
- **Justificacion:** posesion aislada no equivale a peligro; debe combinarse con
  produccion de ocasiones.
- **Cobertura completa:** metodologia consistente y cobertura uniforme.
- **Estado:** no cubierto.

#### F6. Balon parado

- **Prioridad:** P1.
- **Datos:** corners, tiros libres peligrosos y xG de balon parado si existe.
- **Uso:** fuerza ofensiva y defensiva en acciones detenidas.
- **Justificacion:** los torneos cortos suelen decidirse por balon parado.
- **Cobertura completa:** eventos o estadisticas consistentes por partido.
- **Estado:** no cubierto.

#### F7. Disciplina

- **Prioridad:** P2.
- **Datos:** amarillas, rojas y minutos jugados en inferioridad.
- **Uso:** tendencia disciplinaria y efecto sobre rendimiento reciente.
- **Justificacion:** una roja altera mucho un resultado; no debe interpretarse
  como debilidad ordinaria sin identificarla.
- **Cobertura completa:** tarjetas y minutos de eventos para cada partido.
- **Estado:** no cubierto.

#### F8. Porteria

- **Prioridad:** P1.
- **Datos:** tiros al arco recibidos, goles evitados frente a xG post-tiro,
  porcentaje de paradas y portero titular.
- **Uso:** calidad defensiva independiente del volumen concedido.
- **Justificacion:** un portero puede cambiar materialmente la distribucion de
  goles.
- **Cobertura completa:** estadisticas historicas de portero y alineaciones con
  cobertura uniforme.
- **Estado:** no cubierto.

### G. Plantilla y disponibilidad

#### G1. Convocados y alineaciones

- **Prioridad:** P1.
- **Datos:** convocatoria, once titular, suplentes, posiciones y minutos.
- **Uso:** continuidad, experiencia, calidad disponible y cambios de sistema.
- **Justificacion:** el rating del equipo no refleja por completo una convocatoria
  debilitada o renovada.
- **Cobertura completa:** alineaciones y minutos historicos antes de cada
  prediccion; convocatoria actual con sello temporal.
- **Estado:** no cubierto.

#### G2. Lesiones, sanciones y bajas confirmadas

- **Prioridad:** P1 para inferencia; dificil para entrenamiento.
- **Datos:** jugador, motivo, fecha de confirmacion y partidos afectados.
- **Uso:** ajustar la fuerza esperada de la plantilla disponible.
- **Justificacion:** solo es valido si puede reconstruirse que informacion era
  publica antes de cada partido historico.
- **Cobertura completa:** historial con sello temporal, no una lista actual.
- **Estado:** no cubierto.

#### G3. Experiencia internacional

- **Prioridad:** P1.
- **Features:** caps, minutos internacionales, edad media y experiencia en
  torneos de la convocatoria disponible.
- **Justificacion:** puede importar bajo presion y mejora la descripcion de
  plantillas nuevas.
- **Cobertura completa:** identidad de jugadores, convocatorias y apariciones
  historicas.
- **Estado:** no cubierto.

#### G4. Calidad y forma de jugadores

- **Prioridad:** P2.
- **Datos:** minutos, rendimiento reciente y nivel de club por jugador.
- **Uso:** construir una fuerza agregada de plantilla.
- **Justificacion:** puede detectar cambios antes que los resultados de la
  seleccion, pero introduce una integracion compleja y sesgos entre ligas.
- **Cobertura completa:** datos historicos comparables para todos los jugadores y
  ligas relevantes.
- **Estado:** no cubierto.

#### G5. Valor de mercado

- **Prioridad:** P2.
- **Uso:** proxy de calidad de plantilla.
- **Justificacion:** puede ayudar, pero depende de edad, liga, contrato y sesgos
  comerciales; no debe tratarse como talento puro.
- **Cobertura completa:** snapshots historicos con licencia y fecha anterior al
  partido.
- **Estado:** no cubierto.

### H. Viaje y condiciones externas

El bloque H completo queda descartado del alcance principal. Aunque algunas
variables pueden tener efecto real, exigen itinerarios, estadios, clima y
superficies historicas con una granularidad que no compensa su costo y riesgo de
ruido para esta version.

#### H1. Distancia de viaje

- **Prioridad:** P2.
- **Datos:** ubicacion del partido anterior, concentracion y sede actual.
- **Uso:** kilometros recorridos y cambios de huso horario.
- **Justificacion:** puede afectar recuperacion, sobre todo en ventanas
  internacionales cortas.
- **Cobertura completa:** itinerario o aproximacion geografica reproducible.
- **Estado:** descartado del alcance.

#### H2. Altitud

- **Prioridad:** P1.
- **Datos:** coordenadas y elevacion del estadio.
- **Uso:** diferencia entre altitud habitual y sede.
- **Justificacion:** puede afectar fatiga y rendimiento fisiologico.
- **Cobertura completa:** estadio y altitud verificados para todos los partidos.
- **Estado:** descartado del alcance.

#### H3. Clima

- **Prioridad:** P2.
- **Datos:** temperatura, humedad, precipitacion y viento en el kickoff.
- **Uso:** contexto de ritmo y fatiga.
- **Justificacion:** el efecto probablemente es pequeño y no lineal, por lo que
  debe probarse.
- **Cobertura completa:** observacion o reanalisis historico por estadio y hora.
- **Estado:** descartado del alcance.

#### H4. Superficie

- **Prioridad:** P2.
- **Datos:** cesped natural, hibrido o artificial.
- **Uso:** familiaridad y posible efecto sobre ritmo.
- **Justificacion:** puede importar para equipos poco habituados, pero requiere
  evidencia en backtesting.
- **Cobertura completa:** historial de superficie por estadio y fecha.
- **Estado:** descartado del alcance.

### I. Informacion de mercado

#### I1. Cuotas prepartido

- **Prioridad:** P1 como benchmark; P2 como feature opcional.
- **Datos:** cuotas de apertura y cierre de varias casas, con timestamp.
- **Uso recomendado:** comparar el modelo contra el consenso del mercado y medir
  valor informativo.
- **Justificacion:** las cuotas agregan informacion sobre plantillas, noticias y
  expectativas, pero incluirlas convierte al modelo parcialmente en imitador del
  mercado.
- **Cobertura completa:** cuotas historicas sin margen, con hora y proveedor.
- **Estado:** no cubierto.

La primera version debe evaluarse contra las cuotas, no entrenarse con ellas. Su
uso como feature sera un experimento separado.

## Checklist maestro de cobertura

### Completamente cubierto

- [x] A1. Goles a los 90 minutos bajo politica de verificacion o exclusion.
- [x] A2. Prorroga y penales bajo politica de verificacion o exclusion.
- [x] B1. Identidad canonica de selecciones.
- [x] B2. Fecha calendario del partido.
- [x] B4. Competicion normalizada.
- [x] C1. Equipo nominal local y visitante.
- [x] C2. Indicador de campo neutral.

### Cubierto por adaptacion de alcance

Estos elementos tienen informacion suficiente para el producto y el modelo
gratuitos, sin exigir una cobertura global que aporte poco valor.

- [x] A3. Estado `scheduled`, `finished` o `unknown`; sin promesa de estado en
  vivo.
- [x] B3. Kickoff exacto obligatorio para Mundial/producto y opcional para el
  entrenamiento historico.
- [x] B5. Fase, grupo y jornada en Mundial y torneos principales; opcional para
  competiciones menores.

### Categorias C y D cerradas

- [x] C3. Pais y ciudad: 756/756 localidades y fixtures normalizados.
- [x] C4. Estadio: Mundial 2026 cubierto; historial global adaptado por ciudad.
- [x] C5. Anfitriones: 36 relaciones para 21 ediciones principales.
- [x] D1. Puntos FIFA: 347 publicaciones hasta el 11 de junio de 2026.
- [x] D2. Posicion FIFA: oficial en el tramo nuevo y validada en el solapamiento.

### Pendiente y viable con fuentes gratuitas

- [ ] D3. Elo prepartido.

### Categoria E cerrada en recoleccion

- [x] E1. Datos disponibles; feature pendiente.
- [x] E2. Datos disponibles; depende de implementar D3.
- [x] E3. Datos disponibles; feature pendiente.
- [x] E4. Datos disponibles; feature pendiente.
- [x] E6. Datos disponibles; feature experimental.

### Experimental por cobertura parcial gratuita

Estas variables solo se probaran en subconjuntos. No pueden convertirse en
requisito del modelo global mientras su cobertura dependa del torneo o la
confederacion.

- [ ] F1. Tiros totales.
- [ ] F2. Tiros al arco.
- [ ] F4. Grandes ocasiones.
- [ ] F5. Posesion y pases.
- [ ] F6. Balon parado.
- [ ] F7. Disciplina.
- [ ] G1. Convocados y alineaciones.
- [ ] G3. Experiencia internacional.

### Descartado del modelo principal gratuito

No se perseguiran como dependencia del producto. Pueden reconsiderarse si en el
futuro aparece una fuente abierta, historica y uniforme.

- [~] F3. xG y npxG global.
- [~] F8. Estadisticas avanzadas de porteria.
- [~] G2. Lesiones, sanciones y bajas historicas.
- [~] E5. Dias de descanso y carga de partidos.
- [~] H1-H4. Viaje, altitud, clima y superficie.
- [~] G4. Calidad y forma de jugadores en clubes.
- [~] G5. Valor de mercado historico.
- [~] I1. Cuotas prepartido completas.

## Estado actual y orden restante

Las categorias A-E ya tienen su recoleccion cerrada por cobertura o adaptacion
de alcance. El trabajo restante se separa en:

1. **D3 y E1-E4/E6:** implementacion futura de features derivadas, sin buscar
   nuevas fuentes.
2. **F1, F2 y F6:** evaluar si existe cobertura abierta suficiente para
   experimentos de produccion ofensiva y defensiva.
3. **G1 y G3:** evaluar plantillas y experiencia solo en torneos con cobertura
   consistente.

E5 y H1-H4 no forman parte del orden restante. Los 73 casos residuales de A
permanecen como cola de control para la futura preparacion, pero no bloquean la
estrategia de datos.

## Resolucion del grupo A: resultados y estado

### Cierre de la recoleccion gratuita

La recoleccion de A se considera suficiente para avanzar bajo estas reglas:

- Los ocho torneos principales recientes tienen fuentes de respaldo.
- Los 73 casos residuales se revisan manualmente o se excluyen.
- El modelo principal aprende exclusivamente resultados a 90 minutos.
- La aplicacion no depende de una API comercial de resultados en vivo.

No hace falta perseguir cobertura perfecta de todos los torneos menores. La
calidad se garantiza haciendo que el 100% de los partidos finalmente incluidos
tenga duracion confiable.

### Recomendacion gratuita

Usar una estrategia de fuentes abiertas y exclusion conservadora:

1. **`international_results` como columna vertebral**.
2. **`goalscorers.csv` y `shootouts.csv` como enriquecimiento automatico**.
3. **OpenFootball World Cup y repositorios CC0 equivalentes** para Mundial,
   eliminatorias y partidos de torneo documentados.
4. **Fuentes oficiales publicas** para verificar el subconjunto residual.
5. **Excluir del entrenamiento** cualquier partido eliminatorio cuya duracion y
   marcador a 90 minutos no puedan demostrarse.

No se debe reemplazar `results.csv` inmediatamente. Primero se vincularan los
partidos entre fuentes y se conservara procedencia por campo. Un mismo registro
podra tener, por ejemplo, identidad y sede de una fuente, marcador a 90 minutos
de otra y una marca de validacion cruzada.

### Auditoria de los archivos auxiliares gratuitos

El repositorio `martj42/international_results` tambien publica:

- `goalscorers.csv`: 47.606 eventos de gol con minuto, equipo, goleador,
  autogol y penal.
- `shootouts.csv`: 678 tandas con ganador y, parcialmente, primer lanzador.

Cruce realizado sobre los 5.685 partidos finalizados desde 2021:

- 2.538 partidos tienen al menos un evento de gol disponible: 44,64%.
- Se identifican 115 tandas de penales.
- Se detectan 27 partidos con goles posteriores al minuto 90 y lista de goles
  consistente.
- La cobertura de eventos cambia mucho por año y competicion.

Estos archivos permiten corregir y validar una parte del historial, pero no
demuestran que la ausencia de un evento posterior al minuto 90 signifique que no
hubo prorroga. Por eso el cierre de A depende de excluir cualquier caso residual
que no pueda verificarse.

### Valor de OpenFootball

`openfootball/worldcup` publica datos CC0 del Mundial y sus eliminatorias. El
formato distingue expresiones como:

- `a.e.t.` para prorroga.
- Marcador a 90 minutos y marcador tras 120.
- Resultado de la tanda.
- Horario, zona, estadio, ciudad, fase y grupo.

Es especialmente valioso porque cubre con detalle el Mundial 2022 y el calendario
2026, que son los partidos de mayor importancia para el producto. No reemplaza
por si solo todos los amistosos y torneos continentales.

### Politica para A1: marcador a 90 minutos

Clasificar cada partido en una de estas categorias:

1. `regular_time_confirmed`: el marcador final es de 90 minutos.
2. `extra_time_confirmed`: existe marcador separado de 90 y 120 minutos.
3. `shootout_confirmed`: existe marcador de 90/120 y tanda.
4. `duration_ambiguous`: el resultado existe, pero no puede demostrarse si
   incluye prorroga.

Solo las tres primeras categorias entraran al entrenamiento. La cuarta se
excluira, aunque eso reduzca ligeramente la muestra. Es preferible perder unas
decenas de partidos que corromper la variable objetivo.

Los partidos que por formato no admiten prorroga, como amistosos y fases de liga
o grupo, pueden marcarse como `regular_time_confirmed` mediante reglas de
competicion verificadas.

### Politica para A2: prorroga y penales

La prorroga y la tanda no formaran parte del primer modelo de goles. El modelo
principal predecira exclusivamente 90 minutos.

Para mostrar probabilidad de clasificacion en eliminatorias se añadira despues
un modulo separado:

- Probabilidad de ganar en 90 minutos: modelo principal.
- Si hay empate, simulacion de prorroga con tasas ajustadas a 30 minutos.
- Si persiste el empate, probabilidad de tanda inicialmente simetrica o basada en
  un modelo gratuito independiente.

No se mezclaran goles de prorroga en el entrenamiento de 90 minutos.

### Politica para A3: estado del partido

Para el producto del Mundial se construira un estado interno:

- `scheduled`: kickoff futuro y sin resultado.
- `in_progress`: solo si una fuente abierta actualizada lo confirma.
- `finished`: resultado verificado.
- `postponed`, `cancelled` o `suspended`: solo con confirmacion explicita.
- `unknown`: no hay evidencia suficiente.

OpenFootball y el calendario oficial se usaran para fixtures, horario, fase y
sede. `results.csv` se usara para resultados terminados. Sin una API en vivo, la
aplicacion no prometera actualizacion segundo a segundo; mostrara la hora de la
ultima sincronizacion.

### Campos canonicos del grupo A

La tabla normalizada de partidos debe guardar:

```text
status
kickoff_utc
home_score_90
away_score_90
home_score_extra_time
away_score_extra_time
home_score_penalties
away_score_penalties
went_to_extra_time
went_to_penalties
result_after_90
qualified_team_id
source_match_id
source_name
source_updated_at
data_quality_status
```

`home_score_extra_time` y `away_score_extra_time` deben representar solo los
goles anotados durante la prorroga, no el marcador acumulado. Esta convencion
debe aplicarse igual a todas las fuentes.

### Auditoria gratuita para A1-A3

#### Muestra

No hace falta auditar aleatoriamente todos los partidos. Se dividira el universo:

- Partidos cuyo formato garantiza final a 90 minutos.
- Partidos con tanda identificada.
- Partidos con goles posteriores al minuto 90.
- Partidos de fases eliminatorias potencialmente ambiguos.

La revision detallada se concentra en el ultimo grupo, que debe ser mucho menor
que los 5.685 partidos recientes.

#### Datos que se comprobaran

- Existencia del fixture.
- ID estable.
- Estado del partido.
- Hora UTC.
- Marcador a 90 minutos.
- Marcador o goles de prorroga.
- Resultado de tanda.
- Consistencia con `results.csv`.
- Fecha de ultima actualizacion.

#### Umbrales de aprobacion

- 100% de los partidos incluidos en entrenamiento tienen duracion verificada.
- 100% de los casos de prorroga incluidos tienen marcador a 90 separado.
- 100% de las tandas incluidas estan separadas del marcador de juego.
- Los casos no verificables se excluyen y quedan registrados.
- Todos los datos usados tienen licencia o condiciones compatibles.

No existe un objetivo de cubrir el 100% del universo original. El objetivo es que
el 100% de la muestra finalmente usada sea confiable.

### Reglas de precedencia y calidad

Cada campo debe conservar su fuente. Propuesta inicial:

1. Marcador a 90/prorroga/penales de una fuente abierta estructurada y
   verificable.
2. Datos CC0 de OpenFootball cuando la competicion este cubierta.
3. Validacion contra eventos de `goalscorers.csv` y `shootouts.csv`.
4. Marcador final y metadatos generales de `results.csv`.
5. Revision manual solo para conflictos residuales de partidos importantes.

Estados sugeridos:

- `verified_two_sources`
- `verified_one_structured_source`
- `derived_from_events`
- `final_score_only`
- `conflict_requires_review`

### Siguiente accion

Implementar un pipeline gratuito que:

1. Descargue snapshots de `results.csv`, `goalscorers.csv`, `shootouts.csv` y
   OpenFootball.
2. Identifique automaticamente amistosos, grupos y formatos sin prorroga.
3. Marque tandas y goles posteriores al minuto 90.
4. Genere una cola de partidos potencialmente ambiguos.
5. Enriquezca los ambiguos con OpenFootball y fuentes oficiales publicas.
6. Excluya cualquier caso que siga sin poder verificarse.
7. Produzca `matches_verified.csv` y un reporte de cobertura.

## Decision ejecutiva

Los dos CSV actuales no bastan como dataset final para un modelo avanzado, pero
uno de ellos si es una buena base:

- `results.csv`: conservar como columna vertebral de resultados y fixtures.
- `ranking_fifa_historical.csv`: conservar solo como fuente secundaria hasta
  septiembre de 2024. No usarlo como unica medida de fuerza.
- Rating Elo propio: calcularlo secuencialmente desde los resultados y usarlo
  como medida principal de nivel del rival.
- Estadisticas detalladas: buscar una segunda fuente consistente para
  2021-2026 antes de incorporarlas al modelo.

No hace falta eliminar del archivo los partidos antiguos. La ingesta puede
conservar la fuente completa y generar una tabla de entrenamiento filtrada. El
periodo optimo no debe fijarse por intuicion: se compararan ventanas de 3, 5, 8
anos y una historia completa con decaimiento temporal.

## Auditoria de los archivos actuales

Auditoria realizada el 13 de junio de 2026.

### `results.csv`

- 49.477 registros totales.
- 5.755 registros desde el 1 de enero de 2021.
- 5.685 partidos finalizados desde 2021.
- 70 fixtures sin marcador entre el 12 y el 27 de junio de 2026.
- 262 equipos o selecciones distintos en los partidos recientes finalizados.
- No hay filas completamente duplicadas.
- Hay dos claves repetidas de fecha, local y visitante:
  - Tahiti vs New Caledonia, 17 de febrero de 1974, con resultados opuestos.
  - Gibraltar vs Cayman Islands, 6 de junio de 2026, mismo resultado y distinta
    ciudad.
- Los 48 equipos del Mundial tienen entre 47 y 101 partidos desde 2021; la
  mediana es 68,5. La cantidad es suficiente para un primer modelo.

Fortalezas:

- Buena cobertura global de partidos internacionales masculinos.
- Incluye torneo, sede y condicion neutral.
- Se mantiene actualizado y tiene licencia CC0.
- Cobertura suficiente de las selecciones del Mundial.

Limitaciones:

- Solo contiene resultado y metadatos basicos.
- Incluye selecciones no FIFA y combinados regionales.
- El marcador incluye prorroga, pero no identifica todos los partidos que
  llegaron a prorroga. Esto contamina un objetivo de goles a 90 minutos.
- Mezcla partidos terminados y fixtures futuros.
- No contiene tiros, posesion, xG, alineaciones, lesiones ni plantillas.
- La informacion proviene de varias fuentes comunitarias y requiere controles.

### `ranking_fifa_historical.csv`

- 67.894 registros.
- Cobertura desde el 31 de diciembre de 1992 hasta el 19 de septiembre de 2024.
- Solo 26 fechas de ranking desde 2021.
- 1.737 partidos recientes son posteriores a la ultima fecha disponible.
- 67 nombres del CSV de partidos no coinciden exactamente con el ranking.
- Parte de esas diferencias son aliases; otras corresponden a equipos no FIFA.

Conclusion:

No se debe imputar el ranking de septiembre de 2024 hasta 2026 como si siguiera
vigente. Eso introduce una medicion congelada precisamente en el periodo mas
importante.

## Fuente principal propuesta

### Resultados y fixtures

Usar `martj42/international_results` como fuente inicial. Guardar cada descarga
como snapshot inmutable con:

- URL y fecha de descarga.
- Hash SHA-256.
- Version o commit de origen.
- Numero de filas y rango de fechas.
- Reporte automatico de calidad.

En entrenamiento se incluiran solo partidos finalizados y anteriores a la fecha
de corte. Los fixtures futuros iran a una tabla separada.

### Fuerza de selecciones

Calcular un Elo propio a partir de los resultados:

- Actualizacion estrictamente cronologica.
- Rating utilizado en cada partido igual al disponible antes de jugarlo.
- Factor K dependiente de la importancia del torneo.
- Ajuste por localia, sede neutral y diferencia de goles.
- Reinicio o regresion parcial entre ciclos, sujeto a backtesting.

Ventajas:

- Actualizado hasta el ultimo partido disponible.
- Reproducible.
- Sin dependencia de una fuente de ranking incompleta.
- Permite medir fuerza incluso entre publicaciones FIFA.

El ranking FIFA historico puede agregarse como feature secundaria cuando exista,
junto con una variable que indique su antiguedad. Nunca debe rellenarse
silenciosamente durante casi dos anos.

## Estadisticas detalladas

### Politica gratuita

No existe actualmente una fuente abierta que ofrezca tiros, posesion, xG,
alineaciones y lesiones con cobertura uniforme para todos los partidos de
selecciones entre 2021 y 2026.

Por tanto:

- Estas variables no seran requisito del modelo global.
- No se rellenaran faltantes con ceros ni promedios por proveedor.
- No se mezclaran subconjuntos con cobertura sesgada por confederacion.
- Podran estudiarse en modelos experimentales separados.
- Solo se promoveran si existe una fuente gratuita suficientemente uniforme.

### StatsBomb Open Data

Es excelente para experimentar con datos de eventos y validar ideas de xG,
presion o calidad de ocasiones. No cubre de forma uniforme todos los partidos de
selecciones de los ultimos cinco anos, por lo que no debe ser el dataset principal
del modelo global.

### OpenFootball y fuentes CC0

Son utiles para Mundial, eliminatorias, horarios, sedes, fases, alineaciones
puntuales y separacion de prorroga. Se usaran para enriquecer partidos cubiertos,
pero el modelo no dependera de una columna que solo exista en esos torneos.

### Datos que se descartan del alcance principal

Mientras no aparezca una fuente abierta y uniforme, quedan fuera del modelo
promovido:

- xG y post-shot xG global.
- Lesiones historicas con sello temporal.
- Valor de mercado historico.
- Metricas avanzadas de portero.
- Tiros y posesion para todo el universo.
- Cuotas historicas completas.

Descartar una variable no implica ignorar su posible valor. Significa evitar que
la precision aparente dependa de datos incompletos, sesgados o irreproducibles.

## Uso de Kaggle

Kaggle es un catalogo y canal de distribucion, no una garantia de calidad. De
hecho, `results.csv` ya corresponde a un dataset publicado en Kaggle y mantenido
en GitHub.

Un dataset de Kaggle solo se incorporara si cumple:

- Fuente primaria identificable.
- Licencia compatible con almacenamiento y publicacion.
- Fecha de actualizacion reciente.
- Cobertura historica por partido, no solo agregados actuales.
- Diccionario de datos.
- Identificadores que puedan cruzarse de forma estable.
- Ausencia de features calculadas con informacion futura.
- Pruebas de duplicados, faltantes y coherencia.

No se combinara automaticamente un conjunto de CSV de Kaggle por tener muchas
columnas. Primero se verificara su procedencia y se comparara una muestra contra
fuentes oficiales.

## Ventana temporal

Los cinco anos son una buena hipotesis inicial, no una regla definitiva.

Experimentos minimos:

- Ultimos 3 anos.
- Ultimos 5 anos.
- Ultimos 8 anos.
- Historia desde 2010 con decaimiento exponencial.

La validacion sera temporal. La ventana y la vida media se elegiran por log loss,
Ranked Probability Score y calibracion, no por exactitud de marcador.

Para equipos con pocos partidos se usara regularizacion hacia:

- Promedio de su confederacion.
- Rating Elo.
- Promedio global.

## Dataset minimo viable

La primera version puede entrenarse bien con:

- Resultado a 90 minutos o una politica explicita para prorrogas.
- Local, visitante, fecha, torneo, sede y neutralidad.
- Elo prepartido.
- Ranking FIFA prepartido cuando este disponible.
- Forma, ataque y defensa calculados solo con partidos anteriores.
- Dias de descanso.
- Importancia del torneo.

Las estadisticas avanzadas deben demostrar mejora en backtesting antes de entrar
al modelo promovido.

## Trabajo previo a implementar el modelo

1. Congelar y versionar las fuentes actuales.
2. Definir el objetivo: resultado a 90 minutos o resultado tras prorroga.
3. Crear catalogo canonico de selecciones FIFA y aliases.
4. Separar finalizados y fixtures.
5. Implementar auditoria automatica de datos.
6. Construir Elo cronologico.
7. Integrar `goalscorers.csv`, `shootouts.csv` y OpenFootball.
8. Verificar o excluir partidos con duracion ambigua.
9. Documentar licencias y procedencia por campo.
10. Construir features gratuitas y entrenar baselines.
