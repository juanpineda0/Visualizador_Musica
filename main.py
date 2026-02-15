import sys
import pygame
from src.audio import AudioAnalyzer
from src.graphics import GraphicsEngine

def main():
    try:
        # Initialize Graphics
        print("Initializing Graphics...", flush=True)
        graphics = GraphicsEngine()
        print("Graphics Initialized.", flush=True)
        
        # initialize Audio Code
        print("Initializing Audio...", flush=True)
        audio = AudioAnalyzer()
        audio.start()
        
        print("Starting Main Loop...", flush=True)
        running = True
        while running:
            # Get Audio Data
            bass, mid, treble = audio.get_audio_levels()
            spectrum = audio.get_spectrum()
            
            # Render Frame
            running = graphics.render(bass, mid, treble, spectrum)
            
    except KeyboardInterrupt:
        print("User interrupted.")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()
        
    finally:
        # Cleanup
        print("Cleaning up...", flush=True)
        if 'audio' in locals():
            audio.stop()
        pygame.quit()
        # sys.exit() # Remove sys.exit to see if that helps keep window open for error reading

if __name__ == "__main__":
    main()
