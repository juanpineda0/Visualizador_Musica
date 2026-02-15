# Audio Visualizer para Windows

Aplicación de escritorio que captura el audio del sistema en tiempo real y genera visualizaciones interactivas con shaders OpenGL.

## Cómo funciona

### Arquitectura

```
main.py                 → Punto de entrada, orquesta todo
src/audio.py            → Captura audio del sistema (WASAPI Loopback)
src/graphics.py         → Motor gráfico OpenGL (ModernGL + Pygame)
src/menu.py             → Menú overlay con scroll, toggles, sliders
src/utils.py            → Utilidades (rutas para .exe y desarrollo)
shaders/basic.vert      → Shader de vértices (quad pantalla completa)
shaders/visualizer.frag → Shader de fragmentos (efectos visuales)
assets/                 → Carpeta para fondos personalizados (.jpg, .png, .webp)
```

### Flujo de datos

1. **Captura**: `audio.py` graba el audio que sale por los altavoces usando WASAPI Loopback (no el micrófono).
2. **Análisis**: Aplica FFT (Fast Fourier Transform) para separar el audio en bandas de frecuencia:
   - **Bass** (20-250 Hz): Bombos, sub-bass
   - **Mid** (250-4000 Hz): Voces, guitarras
   - **Treble** (4000-16000 Hz): Hi-hats, brillo
3. **Visualización**: Los valores de Bass/Mid/Treble se envían como "uniforms" al shader de fragmentos.
4. **Shader**: El shader modifica la imagen de fondo píxel a píxel en la GPU.

### Efectos disponibles

Cada efecto tiene un **toggle ON/OFF** y un **selector de fuente** (Bass/Mid/Treble):

| Efecto | Descripción |
|---|---|
| Zoom Pulse | Zoom rítmico que pulsa con la música |
| Ripple | Ondas de agua que se expanden desde el centro |
| Wave Warp | Deformación ondulada horizontal y vertical |
| Aberración Crom. | Separación de canales RGB |
| Brillo Bordes | Resplandor en contornos detectados |
| Destellos | Brillo global reactivo al audio |

Además hay 3 modos de visualización (toggle simple):
- **Barras de Frecuencia**: Espectro de 64 bins en la parte inferior
- **Círculo Espectral**: Visualizador circular en el centro
- **Máscara de Color**: Barras de color/escala de grises según amplitud

### Tecnologías usadas

| Componente | Librería | Por qué |
|---|---|---|
| Captura de Audio | `pyaudiowpatch` | Fork de PyAudio con soporte nativo WASAPI Loopback en Windows |
| Análisis FFT | `numpy` | Rápido y estándar para cálculos numéricos |
| Ventana/Contexto | `pygame` | Crea la ventana OpenGL fácilmente |
| Renderizado GPU | `moderngl` | API limpia para OpenGL moderno (shaders) |
| Empaquetado | `pyinstaller` | Genera .exe standalone |

## Controles

| Tecla | Acción |
|---|---|
| `TAB` | Abrir/cerrar menú de ajustes |
| `F` | Pantalla completa sin bordes |
| `B` | Modo ventana sin bordes |
| `ESC` | Salir |
| `↑/↓` | Navegar items del menú |
| `←/→` | Ajustar valor / cambiar imagen de fondo |
| `S` | Cambiar fuente de audio (Bass/Mid/Treble) |
| `Rueda` | Scroll en secciones del menú |

## Decisiones técnicas

### ¿Por qué `pyaudiowpatch` y no `soundcard`?

Se probó `soundcard` primero, pero falla en Windows al intentar abrir el dispositivo loopback con error `RuntimeError: invalid argument`. `pyaudiowpatch` funciona correctamente con WASAPI Loopback y es más estable.

**Test realizado** (`test_audio.py`):
```
>>> Usando loopback: Altavoces (Realtek(R) Audio) [Loopback]
[##############################] RMS=0.23842  B=53.847 M=17.494 T=3.498  ← Con música
```

### ¿Por qué shaders y no dibujar con Pygame directamente?

Los shaders procesan cada píxel en paralelo en la GPU. Esto permite efectos como distorsión, aberración cromática y cambio de color sobre la imagen de fondo a 60 FPS sin esfuerzo. Pygame solo puede dibujar formas simples encima de la imagen.

### Menú scrollable

El menú agrupa items en secciones scrollables (`"effects"`, `"visualizers"`). Cada grupo tiene un `max_visible` configurable. Cuando hay más items que el máximo, aparecen flechas ▲/▼ y se puede hacer scroll con la rueda del mouse. Esto permite añadir nuevos efectos sin desbordar el panel.

## Fondos personalizados

Coloca cualquier imagen `.jpg`, `.png` o `.webp` en la carpeta `assets/`. La app las detecta automáticamente y puedes rotar entre ellas desde el menú con los botones `< Ant` / `Sig >`.

## Ejecución

### Desde código fuente
```bash
cd Visualizer
venv\Scripts\activate
python main.py
```

### Ejecutable
```
dist\AudioVisualizer\AudioVisualizer.exe
```
