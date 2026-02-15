# Resumen del Proyecto: Cyberpunk Audio Visualizer
**Para copiar en el nuevo chat:**

## Estado Actual
El proyecto es un **Visualizador de Audio en Tiempo Real** desarrollado en Python utilizando:
-   **pygame**: Gestión de ventanas, eventos y UI.
-   **moderngl**: Renderizado gráfico de alto rendimiento con Shaders GLSL.
-   **numpy**: Análisis de audio FFT.

## Funcionalidades Implementadas (Estables)
1.  **Gestión de Ventanas Avanzada**:
    -   **Pantalla Completa Sin Bordes (`F`)**: Ocupa toda la pantalla real, posicionado en `(0,0)` con API de Windows, sin minimizarse al perder foco.
    -   **Modo Ventana (`B`)**: Sin bordes pero redimensionable.

2.  **Sistema de Efectos Modular** (6 efectos, cada uno con toggle ON/OFF + selector Bass/Mid/Treble):
    1.  **Zoom Pulse**: Zoom rítmico.
    2.  **Ripple**: Ondas de agua.
    3.  **Wave Warp**: Deformación ondulada.
    4.  **Aberración Cromática**: Separación RGB.
    5.  **Brillo Bordes**: Resplandor en contornos.
    6.  **Destellos**: Brillo reactivo al audio (glow global).
    -   **Menú de Control (TAB)**: Interruptores individuales para cada efecto.
    -   Cada efecto se modula con los deslizadores de **Intensidad por canal** y **Sensibilidad general**.

3.  **Selector de Fuente de Audio**:
    -   Cada efecto tiene un **selector de frecuencia (Bass, Mid, Treble)**.
    -   Se cambia haciendo clic en el botón de color (🟥, 🟩, 🟦) o pulsando `S`.

4.  **Selector de Imágenes de Fondo**:
    -   Botones **"< Ant"** y **"Sig >"** en el menú.
    -   Rota entre las imágenes `.jpg`/`.png`/`.webp` de la carpeta `assets/`.
    -   También se navega con **← / →** cuando el selector está seleccionado.

5.  **Vignette**: Oscurecimiento decorativo de bordes (siempre activo).

6.  **Menú Scrollable**:
    -   Los effect rows se muestran **máximo 4 a la vez** con flechas ▲/▼.
    -   Los toggles de visualización también tienen infraestructura de scroll lista.
    -   Scroll con **rueda del mouse**, **clic en flechas**, y **auto-scroll con teclado**.
    -   Preparado para escalar con más efectos sin desbordar el panel.

## Repositorio
El código está limpio, funcional y guardado en la rama `main`.
