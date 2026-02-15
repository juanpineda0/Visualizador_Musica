"""
Menu overlay for the Audio Visualizer.
Renders a semi-transparent settings panel with mouse + keyboard support.
"""
import pygame

class Menu:
    def __init__(self):
        self.visible = False
        self.selected = 0
        
        # Menu items: sliders and toggles and selectors
        self.items = [
            # --- Effect Toggles & Sources ---
            # Format: {label, key, type, value, [src_key, src_value]}
            # src_value: 0=Bass, 1=Mid, 2=Treble
            
            {"label": "Zoom Pulse",       "key": "fx_zoom",       "type": "effect_row", "value": 1.0, "src_key": "src_zoom",      "src_value": 0},
            {"label": "Ripple",           "key": "fx_ripple",     "type": "effect_row", "value": 0.0, "src_key": "src_ripple",    "src_value": 0},
            {"label": "Wave Warp",        "key": "fx_wave",       "type": "effect_row", "value": 1.0, "src_key": "src_wave",      "src_value": 1},
            {"label": "Aberración Crom.", "key": "fx_chromatic",  "type": "effect_row", "value": 1.0, "src_key": "src_chromatic", "src_value": 2},
            {"label": "Brillo Bordes",    "key": "fx_edge_glow",  "type": "effect_row", "value": 0.0, "src_key": "src_edge_glow", "src_value": 2},
            
            {"label": "", "key": "_sep0", "type": "separator"},
            
            {"label": "Barras Frecuencia", "key": "fx_bars",       "type": "toggle", "value": 0.0},
            {"label": "Círculo Espectral", "key": "fx_circle",     "type": "toggle", "value": 0.0},
            {"label": "Máscara de Color",  "key": "fx_colormask",  "type": "toggle", "value": 0.0},
            
            # --- Separator ---
            {"label": "", "key": "_sep1", "type": "separator"},
            
            # --- Intensity Sliders ---
            {"label": "Intensidad Bass",   "key": "bass_intensity",   "type": "slider", "min": 0.0, "max": 2.0, "step": 0.1, "value": 1.0},
            {"label": "Intensidad Mid",    "key": "mid_intensity",    "type": "slider", "min": 0.0, "max": 2.0, "step": 0.1, "value": 1.0},
            {"label": "Intensidad Treble", "key": "treble_intensity", "type": "slider", "min": 0.0, "max": 2.0, "step": 0.1, "value": 1.0},
            {"label": "Sensibilidad",      "key": "sensitivity",      "type": "slider", "min": 0.1, "max": 3.0, "step": 0.1, "value": 1.0},
        ]
        
        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_item = pygame.font.SysFont("Segoe UI", 17)
        self.font_hint = pygame.font.SysFont("Segoe UI", 13)
        self.font_small = pygame.font.SysFont("Segoe UI", 12, bold=True)
        
        # Colors
        self.bg_color = (12, 12, 22, 230)
        self.title_color = (180, 140, 255)
        self.text_color = (200, 200, 220)
        self.selected_color = (100, 220, 255)
        self.hover_color = (80, 180, 220)
        
        self.bar_bg = (40, 40, 60)
        self.bar_fill = (80, 160, 255)
        self.bar_fill_selected = (100, 220, 255)
        
        self.toggle_on = (80, 220, 140)
        self.toggle_off = (120, 60, 60)
        
        # Source colors: Bass=Red, Mid=Green, Treble=Blue
        self.src_colors = [
            (255, 80, 80),   # Bass
            (80, 255, 100),  # Mid
            (80, 160, 255)   # Treble
        ]
        self.src_labels = ["BASS", "MID", "TREB"]
        
        self.hint_color = (110, 110, 140)
        self.separator_color = (60, 50, 100, 120)
        
        # Layout cache (updated each render)
        self._panel_rect = None
        self._item_rects = []  # [(index, pygame.Rect, type)]
        self._slider_bar_rects = {}  # {index: pygame.Rect}
        self._toggle_rects = {}  # {index: pygame.Rect}
        self._src_rects = {} # {index: pygame.Rect}
        
        # Mouse state
        self.hovered = -1
        self.dragging_slider = -1
    
    def toggle(self):
        self.visible = not self.visible
        self.dragging_slider = -1
    
    def get_value(self, key):
        for item in self.items:
            # Check main key
            if item["key"] == key:
                return item["value"]
            # Check source key if it exists
            if "src_key" in item and item["src_key"] == key:
                return item["src_value"]
        return 1.0  # Default fallback
    
    def _get_selectable_items(self):
        return [i for i, item in enumerate(self.items) if item["type"] != "separator"]
    
    def handle_input(self, event):
        """Handle keyboard and mouse input. Returns True if event was consumed."""
        # TAB toggle always works
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            self.toggle()
            return True
        
        if not self.visible:
            return False
        
        # --- Keyboard ---
        if event.type == pygame.KEYDOWN:
            selectable = self._get_selectable_items()
            if not selectable: return False
            
            current_sel_idx = 0
            if self.selected in selectable:
                current_sel_idx = selectable.index(self.selected)
            
            if event.key == pygame.K_UP:
                current_sel_idx = (current_sel_idx - 1) % len(selectable)
                self.selected = selectable[current_sel_idx]
                return True
            elif event.key == pygame.K_DOWN:
                current_sel_idx = (current_sel_idx + 1) % len(selectable)
                self.selected = selectable[current_sel_idx]
                return True
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                item = self.items[self.selected]
                if item["type"] in ("toggle", "effect_row"):
                    # Toggle value
                    item["value"] = 0.0 if item["value"] > 0.5 else 1.0
                elif item["type"] == "slider":
                    delta = item["step"] if event.key == pygame.K_RIGHT else -item["step"]
                    item["value"] = max(item["min"], min(item["max"], round(item["value"] + delta, 2)))
                return True
            elif event.key == pygame.K_s:
                # Cycle source if available on selected item
                item = self.items[self.selected]
                if item["type"] == "effect_row":
                    item["src_value"] = (item["src_value"] + 1) % 3
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                item = self.items[self.selected]
                if item["type"] in ("toggle", "effect_row"):
                    item["value"] = 0.0 if item["value"] > 0.5 else 1.0
                return True
        
        # --- Mouse ---
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = -1
            
            # Check interaction zones first (sliders/buttons)
            # But here we just check generic item rects for hover highlight
            for idx, rect, itype in self._item_rects:
                if rect.collidepoint(mx, my):
                    self.hovered = idx
                    break
            
            # Drag slider
            if self.dragging_slider >= 0 and self.dragging_slider in self._slider_bar_rects:
                self._set_slider_from_mouse(self.dragging_slider, mx)
            return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            
            if self._panel_rect and not self._panel_rect.collidepoint(mx, my):
                return False
            
            # Check specific controls first (Toggle switches vs Source buttons vs Sliders)
            
            # 1. Source Buttons
            for idx, rect in self._src_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    item = self.items[idx]
                    item["src_value"] = (item["src_value"] + 1) % 3
                    return True
            
            # 2. Toggle Switches
            for idx, rect in self._toggle_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    item = self.items[idx]
                    item["value"] = 0.0 if item["value"] > 0.5 else 1.0
                    return True

            # 3. Sliders
            for idx, rect in self._slider_bar_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    self.dragging_slider = idx
                    self._set_slider_from_mouse(idx, mx)
                    return True

            # 4. General Item Click (selects item, maybe toggles if simple check)
            for idx, rect, itype in self._item_rects:
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    return True
            
            return True
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging_slider = -1
            return True
        
        return False
    
    def _set_slider_from_mouse(self, idx, mx):
        """Set slider value based on mouse X position."""
        if idx not in self._slider_bar_rects:
            return
        bar_rect = self._slider_bar_rects[idx]
        item = self.items[idx]
        
        # Calculate normalized position (0-1)
        pct = (mx - bar_rect.x) / max(bar_rect.width, 1)
        pct = max(0.0, min(1.0, pct))
        
        # Map to value range
        raw = item["min"] + pct * (item["max"] - item["min"])
        # Snap to step
        item["value"] = round(round(raw / item["step"]) * item["step"], 2)
        item["value"] = max(item["min"], min(item["max"], item["value"]))
    
    def render_surface(self, screen_w, screen_h):
        """Render menu to a Pygame RGBA surface."""
        panel_w = min(500, screen_w - 40)
        panel_h = min(580, screen_h - 40)
        pad = 20
        
        surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        
        px = (screen_w - panel_w) // 2
        py = (screen_h - panel_h) // 2
        
        self._panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        self._item_rects = []
        self._slider_bar_rects = {}
        self._toggle_rects = {}
        self._src_rects = {}
        
        # Background
        pygame.draw.rect(surface, self.bg_color, self._panel_rect, border_radius=14)
        pygame.draw.rect(surface, (100, 80, 180, 100), self._panel_rect, 2, border_radius=14)
        
        # Title
        title = self.font_title.render("⚙  EFECTOS & AJUSTES", True, self.title_color)
        surface.blit(title, (px + (panel_w - title.get_width()) // 2, py + pad))
        
        # Separator
        sep_y = py + pad + 32
        pygame.draw.line(surface, (80, 60, 140, 120), (px + pad, sep_y), (px + panel_w - pad, sep_y), 1)
        
        # Items
        item_y = sep_y + 12
        bar_w = panel_w - pad * 2 - 200 # Slider width
        item_h = 32
        
        for i, item in enumerate(self.items):
            if item["type"] == "separator":
                sep_line_y = item_y + 8
                pygame.draw.line(surface, self.separator_color, (px + pad + 10, sep_line_y), (px + panel_w - pad - 10, sep_line_y), 1)
                item_y += 18
                continue
            
            is_selected = (i == self.selected)
            is_hovered = (i == self.hovered)
            
            # Store full row rect
            full_rect = pygame.Rect(px + 4, item_y - 2, panel_w - 8, item_h)
            self._item_rects.append((i, full_rect, item["type"]))
            
            # Colors
            if is_selected:
                color = self.selected_color
            elif is_hovered:
                color = self.hover_color
            else:
                color = self.text_color
            
            # Highlight background
            if is_selected or is_hovered:
                bg_alpha = 70 if is_selected else 30
                pygame.draw.rect(surface, (40, 60, 100, bg_alpha), full_rect, border_radius=6)
            
            # Selection indicator
            if is_selected:
                indicator = self.font_item.render("►", True, self.selected_color)
                surface.blit(indicator, (px + 8, item_y + 1))
            
            # Label
            label = self.font_item.render(item["label"], True, color)
            surface.blit(label, (px + pad + 14, item_y))
            
            # --- Type Specific Rendering ---
            
            if item["type"] in ("toggle", "effect_row"):
                # Toggle Switch (Right aligned)
                tog_x = px + panel_w - pad - 50
                tog_w, tog_h = 40, 20
                is_on = item["value"] > 0.5
                tog_color = self.toggle_on if is_on else self.toggle_off
                
                tog_rect = pygame.Rect(tog_x, item_y + 5, tog_w, tog_h)
                pygame.draw.rect(surface, tog_color, tog_rect, border_radius=10)
                self._toggle_rects[i] = tog_rect
                
                # Knob
                knob_x = tog_x + tog_w - 18 if is_on else tog_x + 2
                knob_rect = pygame.Rect(knob_x, item_y + 7, 16, 16)
                pygame.draw.rect(surface, (255, 255, 255, 230), knob_rect, border_radius=8)
                
                # If it's an "effect_row", it also has a Source Selector button
                if item["type"] == "effect_row":
                    src_val = item["src_value"]
                    src_color = self.src_colors[src_val]
                    src_label = self.src_labels[src_val]
                    
                    # Button Rect
                    btn_w = 40
                    btn_h = 20
                    btn_x = tog_x - btn_w - 20
                    btn_rect = pygame.Rect(btn_x, item_y + 5, btn_w, btn_h)
                    self._src_rects[i] = btn_rect
                    
                    # Draw Button
                    pygame.draw.rect(surface, src_color, btn_rect, border_radius=4)
                    
                    # Text
                    txt_surf = self.font_small.render(src_label, True, (20, 20, 30))
                    txt_x = btn_x + (btn_w - txt_surf.get_width()) // 2
                    txt_y = btn_y = item_y + 5 + (btn_h - txt_surf.get_height()) // 2
                    surface.blit(txt_surf, (txt_x, txt_y))

            elif item["type"] == "slider":
                # Slider bar
                bar_x = px + pad + 180
                bar_rect = pygame.Rect(bar_x, item_y + 8, bar_w, 12)
                pygame.draw.rect(surface, self.bar_bg, bar_rect, border_radius=4)
                self._slider_bar_rects[i] = bar_rect
                
                pct = (item["value"] - item["min"]) / (item["max"] - item["min"])
                fill_w = int(bar_w * pct)
                if fill_w > 0:
                    fill_color = self.bar_fill_selected if is_selected else self.bar_fill
                    fill_rect = pygame.Rect(bar_x, item_y + 8, fill_w, 12)
                    pygame.draw.rect(surface, fill_color, fill_rect, border_radius=4)
                
                # Knob
                knob_cx = bar_x + fill_w
                knob_cy = item_y + 8 + 6
                pygame.draw.circle(surface, (220, 220, 255), (knob_cx, knob_cy), 8)
                
                # Percentage
                val_text = f"{int(item['value'] * 100)}%" if item["key"] != "sensitivity" else f"{item['value']}x"
                pct_text = self.font_hint.render(val_text, True, color)
                surface.blit(pct_text, (bar_x + bar_w + 12, item_y + 5))
            
            item_y += item_h + 4
        
        # Hints at bottom
        hint_y = py + panel_h - 44
        pygame.draw.line(surface, (80, 60, 140, 120), (px + pad, hint_y - 8), (px + panel_w - pad, hint_y - 8), 1)
        
        hints = [
            "[Click/S] Cambiar Fuente (Bass/Mid/Treb)",
            "[F] Pantalla Comp.  [B] Sin bordes"
        ]
        for hint_text in hints:
            hint = self.font_hint.render(hint_text, True, self.hint_color)
            surface.blit(hint, (px + (panel_w - hint.get_width()) // 2, hint_y))
            hint_y += 18
        
        return surface
