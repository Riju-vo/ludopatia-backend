# Plan de Implementación: Modelo de Predicción con Ajuste por Nivel de Rival (Hasta 2026)

Este documento detalla el diseño final consolidado. Incorpora la **normalización de rendimiento basada en el nivel del rival (Ranking FIFA)**, la ventana de 5 años con decaimiento temporal y datos reales de partidos actualizados hasta **2026**.

---

## Justificación Técnica del Ajuste por Nivel de Rival (Ranking FIFA)

Es **completamente coherente y técnicamente necesario** ajustar las estadísticas por el nivel del rival. En el fútbol de selecciones existe una enorme disparidad de nivel. Sin este ajuste, el modelo tendría sesgos graves (por ejemplo, calificaría a una selección como "superofensiva" solo porque anotó muchos goles en amistosos contra rivales débiles, frente a otra selección que anotó menos goles pero jugando contra campeones continentales).

### Cómo implementaremos la normalización por Ranking FIFA:
Para cada partido en la ventana de entrenamiento de 5 años (2021-2026), el código cruzará los resultados históricos con el **historial mensual de rankings FIFA**. 

1.  **Ajuste del Ataque:**
    *   En lugar de calcular solo los goles promedio anotados por el Equipo A, calcularemos los **Goles Ajustados por Dificultad**.
    *   Un gol anotado contra un rival del Top 10 de la FIFA tendrá un peso significativamente mayor que un gol anotado contra una selección fuera del Top 100.
2.  **Ajuste de la Defensa (Portería):**
    *   Un arco en cero (clean sheet) o conceder pocos goles ante una selección de alto ranking FIFA ponderará mucho más a favor de la defensa que hacerlo ante rivales con poca capacidad ofensiva.
3.  **Diferencia de Nivel Neta:**
    *   Introduciremos como variable directa en el modelo de regresión la **Diferencia de Puntos FIFA** entre ambos equipos en el mes del partido (`Puntos_FIFA_A - Puntos_FIFA_B`). Los puntos FIFA oficiales se calculan con una fórmula Elo, lo que los hace una métrica muy objetiva de la jerarquía a largo plazo.

---

## Estructura Final de Archivos en `c:\Users\hp\Desktop\ML`

### Componentes

#### [NEW] [data_loader.py](file:///c:/Users/hp/Desktop/ML/src/data_loader.py)
*   Descarga el historial de partidos (1872-2026) y el historial de rankings FIFA.
*   Filtra la ventana de los últimos 5 años.
*   Calcula las estadísticas rodantes (últimos 10 partidos) de cada equipo.
*   **Normaliza** los goles anotados y recibidos multiplicándolos por un factor de dificultad basado en el Ranking FIFA del oponente de ese momento.

#### [NEW] [model.py](file:///c:/Users/hp/Desktop/ML/src/model.py)
*   Clase `StatsPoissonPredictor` para entrenar el modelo de Regresión de Poisson usando las estadísticas normalizadas por rival y pesos por decaimiento temporal.
*   Método para generar la matriz de probabilidad de resultados exactos ($0$-$5$ goles).

#### [NEW] [app.py](file:///c:/Users/hp/Desktop/ML/app.py)
*   Aplicación interactiva de Streamlit para seleccionar selecciones, ver sus estadísticas rodantes normales y ajustadas por rival, y simular el mapa de calor con las probabilidades de resultado.

#### [NEW] [requirements.txt](file:///c:/Users/hp/Desktop/ML/requirements.txt)
*   Dependencias del proyecto.

---

## Plan de Verificación

*   **Prueba de Ajuste de Rival:** Validaremos que un equipo que gana 1-0 a Francia obtenga un indicador de rendimiento ofensivo y defensivo mejor que uno que gana 3-0 a una selección del puesto 150 de la FIFA.
*   **Suma de Probabilidades:** Verificar que la matriz sume exactamente 100% y que las tarjetas Win/Draw/Loss coincidan con las sumas de celdas correspondientes.
