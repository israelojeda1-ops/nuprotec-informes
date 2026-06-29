# World Cup Predictor — Tarea Pendiente

## Contexto del Repositorio

- **Repo:** `israelojeda1-ops/nuprotec-informes` (público)
- **Rama de trabajo:** `claude/world-cup-predictor-v2nc5h`
- **Rama base:** `main`

## Objetivo

Crear un predictor de resultados de partidos del Mundial 2026 que genere un **HTML estático** con los partidos del día, consumiendo datos reales o simulados con las siguientes estadísticas por partido:

| Campo | Descripción |
|---|---|
| Resultado predicho | Marcador probable del partido |
| Posibles anotadores | Jugadores con mayor probabilidad de gol |
| Tiros al arco | Predicción de SOT (Shots on Target) por equipo |
| Tiros totales | Total de disparos esperados por equipo |
| Amarillas probables | Jugadores con historial de tarjetas |
| Corners | Tiros de esquina esperados por equipo |
| Pases (histórico) | Estadística de pases de partidos anteriores del torneo |
| Faltas | Faltas esperadas por equipo |
| Tacles | Tacles esperados por equipo |

## Decisiones de Diseño Sugeridas

- **Sin backend:** HTML + JavaScript puro, desplegable con GitHub Pages
- **Datos:** Hardcodeados con fixtures reales del Mundial 2026 (o fixture del día vía API pública gratuita como `https://v3.football.api-sports.io` o similar)
- **Actualización diaria:** GitHub Actions que regenera el HTML cada día con los partidos del día
- **Estilo:** Consistente con el dashboard existente (`Dashboard_NUPROTEC_2026.html`) — dark mode moderno

## Estructura de Archivos a Crear

```
world-cup-predictor/
├── index.html              ← HTML principal del predictor
├── predictor.js            ← Lógica de predicción y render
├── styles.css              ← Estilos (dark mode, cards por partido)
└── data/
    └── fixtures_2026.json  ← Datos del torneo (fechas, equipos, grupos)
```

Y en `.github/workflows/`:
```
world-cup-daily.yml  ← Action que regenera index.html con partidos del día
```

## Estado Actual

- [ ] Archivos HTML/JS/CSS creados
- [ ] Datos del Mundial 2026 cargados
- [ ] GitHub Actions configurado
- [ ] GitHub Pages habilitado

## Partidos del Mundial 2026 (referencia)

El Mundial 2026 es co-organizado por **USA, Canadá y México**.
- Inicio fase de grupos: **11 de junio de 2026**
- Final: **19 de julio de 2026**
- 48 equipos, 104 partidos

Hoy es **29 de junio de 2026** — la fase de grupos está en curso.

## Instrucciones para Continuar

1. Ir a la rama: `git checkout claude/world-cup-predictor-v2nc5h`
2. Crear la carpeta `world-cup-predictor/`
3. Implementar `index.html` con el diseño de cards por partido
4. Implementar la lógica de predicción en `predictor.js`
5. Crear el workflow de GitHub Actions
6. Hacer push a la rama y habilitar GitHub Pages apuntando a `/world-cup-predictor`

## Prompt Sugerido para la Próxima Sesión

> Continúa la tarea del predictor del Mundial 2026. El archivo `WORLD_CUP_PREDICTOR_TASK.md` en la raíz del repo tiene el plan completo. La rama de trabajo es `claude/world-cup-predictor-v2nc5h`. Crea todos los archivos listados en "Estructura de Archivos a Crear", con datos reales de los partidos del 29 de junio de 2026 del Mundial 2026, usando HTML+CSS+JS puro (sin framework), dark mode moderno, y desplegable en GitHub Pages.
