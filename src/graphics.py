import pygame
import moderngl
import numpy as np
from pathlib import Path
from src.utils import get_base_path
from src.menu import Menu

class GraphicsEngine:
    def __init__(self, width=1280, height=720):
        self.width = width
        self.height = height
        self.base_path = get_base_path()
        
        # Pygame Setup (only display, not mixer - avoids WASAPI conflicts)
        pygame.display.init()
        pygame.font.init()
        
        # Window state
        self.borderless = False
        self.fullscreen = False
        
        pygame.display.set_mode((self.width, self.height), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
        pygame.display.set_caption("Audio Visualizer")
        self.clock = pygame.time.Clock()
        
        # ModernGL Context
        try:
            self.ctx = moderngl.create_context()
            self.ctx.enable(moderngl.BLEND)
            self.ctx.blend_func = (moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA)
        except Exception as e:
            print(f"Graphics: ModernGL Init Failed: {e}", flush=True)
            raise
        
        self.start_time = pygame.time.get_ticks() / 1000.0
        
        # Main visualization shader
        self.prog = self._load_shader('basic.vert', 'visualizer.frag')
        
        # Overlay shader (for menu)
        self.overlay_prog = self._load_shader('basic.vert', 'overlay.frag')
        
        # Quad Geometry
        vertices = np.array([
            -1.0, -1.0, 0.0, 1.0,
             1.0, -1.0, 1.0, 1.0,
            -1.0,  1.0, 0.0, 0.0,
             1.0,  1.0, 1.0, 0.0,
        ], dtype='f4')

        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [
            (self.vbo, '2f 2f', 'in_vert', 'in_uv'),
        ])
        self.overlay_vao = self.ctx.vertex_array(self.overlay_prog, [
            (self.vbo, '2f 2f', 'in_vert', 'in_uv'),
        ])
        
        # Textures
        self.texture = None
        self.overlay_texture = None
        self.original_surface = None
        self.load_default_texture()
        
        # Spectrum texture (64x1, single RED channel, float32)
        self.spectrum_texture = self.ctx.texture((64, 1), 1, dtype='f4')
        self.spectrum_texture.filter = (moderngl.NEAREST, moderngl.NEAREST)
        
        # Menu
        self.menu = Menu()

    def _load_shader(self, vert_name, frag_name):
        vert_path = self.base_path / 'shaders' / vert_name
        frag_path = self.base_path / 'shaders' / frag_name
        
        with open(vert_path, 'r') as f:
            vert_src = f.read()
        with open(frag_path, 'r') as f:
            frag_src = f.read()
        return self.ctx.program(vertex_shader=vert_src, fragment_shader=frag_src)

    def load_default_texture(self):
        assets_path = self.base_path / 'assets'
        valid_extensions = ['.jpg', '.jpeg', '.png', '.bmp']
        
        bg_path = None
        if assets_path.exists():
            for file_path in assets_path.iterdir():
                if file_path.suffix.lower() in valid_extensions:
                    bg_path = file_path
                    break
        
        if bg_path:
            try:
                print(f"Loading background: {bg_path.name}")
                self.original_surface = pygame.image.load(str(bg_path)).convert_alpha()
            except Exception as e:
                print(f"Error loading image: {e}")
                self.original_surface = self._create_fallback_surface()
        else:
            self.original_surface = self._create_fallback_surface()
        
        iw, ih = self.original_surface.get_size()
        print(f"Image size: {iw}x{ih}")
        self._upload_texture_cover(self.original_surface)
    
    def _upload_texture_cover(self, surface):
        """Crop and scale image to fill window exactly (cover mode)."""
        iw, ih = surface.get_size()
        tw, th = self.width, self.height
        
        scale = max(tw / iw, th / ih)
        scaled_w = int(iw * scale)
        scaled_h = int(ih * scale)
        
        scaled = pygame.transform.smoothscale(surface, (scaled_w, scaled_h))
        
        crop_x = (scaled_w - tw) // 2
        crop_y = (scaled_h - th) // 2
        cropped = scaled.subsurface((crop_x, crop_y, tw, th))
        
        texture_data = pygame.image.tostring(cropped, 'RGBA')
        if self.texture:
            self.texture.release()
        self.texture = self.ctx.texture((tw, th), 4, texture_data)
        self.texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def _upload_overlay(self, surface):
        """Upload a Pygame RGBA surface as the overlay texture."""
        w, h = surface.get_size()
        texture_data = pygame.image.tostring(surface, 'RGBA')
        if self.overlay_texture:
            self.overlay_texture.release()
        self.overlay_texture = self.ctx.texture((w, h), 4, texture_data)
        self.overlay_texture.filter = (moderngl.LINEAR, moderngl.LINEAR)

    def _create_fallback_surface(self):
        w, h = 1280, 720
        surface = pygame.Surface((w, h))
        surface.fill((20, 20, 20))
        color = (100, 255, 100)
        gap = 40
        for x in range(0, w, gap):
            pygame.draw.line(surface, color, (x, 0), (x, h), 1)
        for y in range(0, h, gap):
            pygame.draw.line(surface, color, (0, y), (w, y), 1)
        return surface

    def _toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            pygame.display.set_mode((0, 0), pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
            info = pygame.display.Info()
            self.width, self.height = info.current_w, info.current_h
        else:
            self.width, self.height = 1280, 720
            flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
            if self.borderless:
                flags |= pygame.NOFRAME
            pygame.display.set_mode((self.width, self.height), flags)
        
        self.ctx.viewport = (0, 0, self.width, self.height)
        if self.original_surface:
            self._upload_texture_cover(self.original_surface)

    def _toggle_borderless(self):
        if self.fullscreen:
            return
        self.borderless = not self.borderless
        flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        if self.borderless:
            flags |= pygame.NOFRAME
        pygame.display.set_mode((self.width, self.height), flags)

    def render(self, bass, mid, treble, spectrum=None):
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Menu gets first chance at input
            if self.menu.handle_input(event):
                continue
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                if event.key == pygame.K_f:
                    self._toggle_fullscreen()
                if event.key == pygame.K_b:
                    self._toggle_borderless()
            
            if event.type == pygame.VIDEORESIZE:
                self.width, self.height = event.size
                self.ctx.viewport = (0, 0, self.width, self.height)
                if self.original_surface:
                    self._upload_texture_cover(self.original_surface)

        # Apply menu multipliers
        sensitivity = self.menu.get_value("sensitivity")
        adj_bass = bass * sensitivity * self.menu.get_value("bass_intensity")
        adj_mid = mid * sensitivity * self.menu.get_value("mid_intensity")
        adj_treble = treble * sensitivity * self.menu.get_value("treble_intensity")

        # Update spectrum texture
        if spectrum is not None:
            spec_data = (spectrum * sensitivity).astype(np.float32)
            self.spectrum_texture.write(spec_data.tobytes())

        # Clear
        self.ctx.clear(0.0, 0.0, 0.0)
        
        # Set uniforms
        current_time = pygame.time.get_ticks() / 1000.0 - self.start_time
        
        try:
            self.prog['time'].value = current_time
            self.prog['resolution'].value = (float(self.width), float(self.height))
            self.prog['bass'].value = float(adj_bass)
            self.prog['mid'].value = float(adj_mid)
            self.prog['treble'].value = float(adj_treble)
            self.prog['tex'].value = 0
            self.prog['spectrum_tex'].value = 1
            
            # Effect toggles from menu
            self.prog['fx_distortion'].value = 1.0 if self.menu.get_value("fx_distortion") > 0.5 else 0.0
            self.prog['fx_bars'].value = 1.0 if self.menu.get_value("fx_bars") > 0.5 else 0.0
            self.prog['fx_circle'].value = 1.0 if self.menu.get_value("fx_circle") > 0.5 else 0.0
            self.prog['fx_colormask'].value = 1.0 if self.menu.get_value("fx_colormask") > 0.5 else 0.0
        except Exception:
            pass

        # Bind textures and render
        self.texture.use(0)
        self.spectrum_texture.use(1)
        self.vao.render(moderngl.TRIANGLE_STRIP)
        
        # Menu overlay
        if self.menu.visible:
            menu_surface = self.menu.render_surface(self.width, self.height)
            self._upload_overlay(menu_surface)
            self.overlay_texture.use(0)
            try:
                self.overlay_prog['tex'].value = 0
            except Exception:
                pass
            self.overlay_vao.render(moderngl.TRIANGLE_STRIP)
        
        pygame.display.flip()
        self.clock.tick(60)
        
        return True
