"""
TEST: Gráficos con audio simulado y spectrum.
Presiona TAB para abrir el menú y activar barras/círculo.
"""
import pygame
import math
import time
import sys
import numpy as np

sys.path.insert(0, '.')
from src.graphics import GraphicsEngine

def main():
    print("=== TEST: GRAFICOS + SPECTRUM ===")
    print("TAB = Menú | Activa Barras/Círculo desde el menú")
    print("ESC = Salir")
    print()
    
    graphics = GraphicsEngine()
    print("Ventana abierta.\n")
    
    running = True
    start = time.time()
    
    while running:
        t = time.time() - start
        
        # Simular bass/mid/treble
        bass = max(0, math.sin(t * 2.0) * 0.8 + 0.2) ** 2
        mid = max(0, math.sin(t * 3.5) * 0.5 + 0.3)
        treble = max(0, math.sin(t * 7.0) * 0.4 + 0.2)
        
        # Simular 64 bins de spectrum (ondas a diferentes frecuencias)
        spectrum = np.zeros(64, dtype=np.float32)
        for i in range(64):
            freq = 0.5 + i * 0.15
            phase = i * 0.3
            spectrum[i] = max(0, math.sin(t * freq + phase) * 0.6 + 0.3)
        
        # Base bins have more energy (like real audio)
        falloff = np.linspace(1.0, 0.3, 64).astype(np.float32)
        spectrum *= falloff
        
        # Add beat pulse to low bins
        beat = max(0, math.sin(t * 3.0)) ** 4
        spectrum[:16] += beat * 0.5
        spectrum = np.clip(spectrum, 0, 1.5)
        
        # Print (sparse)
        frame_num = int(t * 60)
        if frame_num % 60 == 0:
            bar_b = "#" * int(min(bass, 1) * 20) + "." * (20 - int(min(bass, 1) * 20))
            print(f"  Bass [{bar_b}] {bass:.2f}  t={t:.1f}s")
        
        running = graphics.render(bass, mid, treble, spectrum)
    
    pygame.quit()
    print("\n=== DONE ===")

if __name__ == "__main__":
    main()
