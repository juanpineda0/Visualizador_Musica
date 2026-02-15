"""
Menu overlay for the Audio Visualizer.
Renders a semi-transparent settings panel with mouse + keyboard support.
Supports scrollable sections for effect groups.
"""
import pygame
from pathlib import Path

class Menu:
    def __init__(self):
        self.visible = False
        self.selected = 0
        
        # Image selector state
        self._image_files = []    # List of Path objects
        self._image_index = 0     # Current index
        self._on_image_change = None  # Callback: fn(path)
        
        # Scrollable group config: {group_name: max_visible}
        self._group_max_visible = {
            "effects": 4,
            "visualizers": 4,
        }
        # Scroll offset per group (index of first visible item within group)
        self._scroll_offsets = {
            "effects": 0,
            "visualizers": 0,
        }
        
        self.items = [
            # --- Image Selector ---
            {"label": "Fondo", "key": "image_selector", "type": "image_selector", "group": None},
            
            {"label": "", "key": "_sep_img", "type": "separator", "group": None},
            
            # --- Effect Toggles & Sources (scrollable group: "effects") ---
            {"label": "Zoom Pulse",       "key": "fx_zoom",       "type": "effect_row", "value": 1.0, "src_key": "src_zoom",      "src_value": 0, "group": "effects"},
            {"label": "Ripple",           "key": "fx_ripple",     "type": "effect_row", "value": 0.0, "src_key": "src_ripple",    "src_value": 0, "group": "effects"},
            {"label": "Wave Warp",        "key": "fx_wave",       "type": "effect_row", "value": 1.0, "src_key": "src_wave",      "src_value": 1, "group": "effects"},
            {"label": "Aberración Crom.", "key": "fx_chromatic",  "type": "effect_row", "value": 1.0, "src_key": "src_chromatic", "src_value": 2, "group": "effects"},
            {"label": "Brillo Bordes",    "key": "fx_edge_glow",  "type": "effect_row", "value": 0.0, "src_key": "src_edge_glow", "src_value": 2, "group": "effects"},
            {"label": "Destellos",        "key": "fx_destellos",  "type": "effect_row", "value": 1.0, "src_key": "src_destellos", "src_value": 0, "group": "effects"},
            
            {"label": "", "key": "_sep0", "type": "separator", "group": None},
            
            # --- Visualizer Toggles (scrollable group: "visualizers") ---
            {"label": "Barras Frecuencia", "key": "fx_bars",       "type": "toggle", "value": 0.0, "group": "visualizers"},
            {"label": "Círculo Espectral", "key": "fx_circle",     "type": "toggle", "value": 0.0, "group": "visualizers"},
            {"label": "Máscara de Color",  "key": "fx_colormask",  "type": "toggle", "value": 0.0, "group": "visualizers"},
            
            # --- Separator ---
            {"label": "", "key": "_sep1", "type": "separator", "group": None},
            
            # --- Intensity Sliders ---
            {"label": "Intensidad Bass",   "key": "bass_intensity",   "type": "slider", "min": 0.0, "max": 2.0, "step": 0.1, "value": 1.0, "group": None},
            {"label": "Intensidad Mid",    "key": "mid_intensity",    "type": "slider", "min": 0.0, "max": 2.0, "step": 0.1, "value": 1.0, "group": None},
            {"label": "Intensidad Treble", "key": "treble_intensity", "type": "slider", "min": 0.0, "max": 2.0, "step": 0.1, "value": 1.0, "group": None},
            {"label": "Sensibilidad",      "key": "sensitivity",      "type": "slider", "min": 0.1, "max": 3.0, "step": 0.1, "value": 1.0, "group": None},
        ]
        
        # Fonts
        pygame.font.init()
        self.font_title = pygame.font.SysFont("Segoe UI", 22, bold=True)
        self.font_item = pygame.font.SysFont("Segoe UI", 17)
        self.font_hint = pygame.font.SysFont("Segoe UI", 13)
        self.font_small = pygame.font.SysFont("Segoe UI", 12, bold=True)
        self.font_arrow = pygame.font.SysFont("Segoe UI", 14, bold=True)
        
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
        self.arrow_color = (140, 120, 200)
        self.arrow_hover_color = (180, 160, 255)
        
        # Layout cache (updated each render)
        self._panel_rect = None
        self._item_rects = []  # [(index, pygame.Rect, type)]
        self._slider_bar_rects = {}  # {index: pygame.Rect}
        self._toggle_rects = {}  # {index: pygame.Rect}
        self._src_rects = {} # {index: pygame.Rect}
        self._img_prev_rect = None
        self._img_next_rect = None
        # Scroll arrow rects: {group_name: {"up": Rect, "down": Rect}}
        self._scroll_arrow_rects = {}
        # Group area rects for mouse wheel detection: {group_name: Rect}
        self._group_area_rects = {}
        
        # Mouse state
        self.hovered = -1
        self.dragging_slider = -1
    
    # ── Scroll helpers ─────────────────────────────────────
    
    def _get_group_items(self, group_name):
        """Return list of (global_index, item) for a given group."""
        return [(i, item) for i, item in enumerate(self.items) if item.get("group") == group_name]
    
    def _scroll_group(self, group_name, delta):
        """Scroll a group by delta. Clamps to valid range."""
        if group_name not in self._group_max_visible:
            return
        group_items = self._get_group_items(group_name)
        max_vis = self._group_max_visible[group_name]
        total = len(group_items)
        if total <= max_vis:
            return  # No scrolling needed
        max_offset = total - max_vis
        self._scroll_offsets[group_name] = max(0, min(max_offset, self._scroll_offsets[group_name] + delta))
    
    def _ensure_selected_visible(self):
        """If the selected item is in a scrollable group, adjust scroll so it's visible."""
        if self.selected < 0 or self.selected >= len(self.items):
            return
        item = self.items[self.selected]
        group = item.get("group")
        if not group or group not in self._group_max_visible:
            return
        
        group_items = self._get_group_items(group)
        max_vis = self._group_max_visible[group]
        # Find position of selected within group
        group_pos = None
        for pos, (gi, _) in enumerate(group_items):
            if gi == self.selected:
                group_pos = pos
                break
        if group_pos is None:
            return
        
        offset = self._scroll_offsets[group]
        if group_pos < offset:
            self._scroll_offsets[group] = group_pos
        elif group_pos >= offset + max_vis:
            self._scroll_offsets[group] = group_pos - max_vis + 1
    
    def _is_item_visible(self, index):
        """Check if an item is currently visible (not scrolled out)."""
        item = self.items[index]
        group = item.get("group")
        if not group or group not in self._group_max_visible:
            return True  # Non-grouped items are always visible
        
        group_items = self._get_group_items(group)
        max_vis = self._group_max_visible[group]
        if len(group_items) <= max_vis:
            return True  # Group fits, all visible
        
        offset = self._scroll_offsets[group]
        group_pos = None
        for pos, (gi, _) in enumerate(group_items):
            if gi == index:
                group_pos = pos
                break
        if group_pos is None:
            return True
        
        return offset <= group_pos < offset + max_vis
    
    # ── Image Selector API ──────────────────────────────────
    
    def set_image_list(self, image_paths, current_index=0):
        """Called by GraphicsEngine to populate the image list."""
        self._image_files = list(image_paths)
        self._image_index = max(0, min(current_index, len(self._image_files) - 1))
    
    def set_on_image_change(self, callback):
        """Register callback fn(path) called when user changes image."""
        self._on_image_change = callback
    
    def _change_image(self, delta):
        """Navigate images by delta (-1 prev, +1 next)."""
        if not self._image_files:
            return
        self._image_index = (self._image_index + delta) % len(self._image_files)
        if self._on_image_change:
            self._on_image_change(self._image_files[self._image_index])
    
    def get_current_image_name(self):
        """Get display name of the current image."""
        if not self._image_files:
            return "(sin imágenes)"
        return self._image_files[self._image_index].stem
    
    def toggle(self):
        self.visible = not self.visible
        self.dragging_slider = -1
    
    def get_value(self, key):
        for item in self.items:
            if item["key"] == key:
                return item["value"]
            if "src_key" in item and item["src_key"] == key:
                return item["src_value"]
        return 1.0
    
    def _get_selectable_items(self):
        """Return indices of selectable items that are currently visible."""
        result = []
        for i, item in enumerate(self.items):
            if item["type"] == "separator":
                continue
            if not self._is_item_visible(i):
                continue
            result.append(i)
        return result
    
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
                self._ensure_selected_visible()
                return True
            elif event.key == pygame.K_DOWN:
                current_sel_idx = (current_sel_idx + 1) % len(selectable)
                self.selected = selectable[current_sel_idx]
                self._ensure_selected_visible()
                return True
            elif event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                item = self.items[self.selected]
                if item["type"] in ("toggle", "effect_row"):
                    item["value"] = 0.0 if item["value"] > 0.5 else 1.0
                elif item["type"] == "slider":
                    delta = item["step"] if event.key == pygame.K_RIGHT else -item["step"]
                    item["value"] = max(item["min"], min(item["max"], round(item["value"] + delta, 2)))
                elif item["type"] == "image_selector":
                    self._change_image(1 if event.key == pygame.K_RIGHT else -1)
                return True
            elif event.key == pygame.K_s:
                item = self.items[self.selected]
                if item["type"] == "effect_row":
                    item["src_value"] = (item["src_value"] + 1) % 3
                return True
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                item = self.items[self.selected]
                if item["type"] in ("toggle", "effect_row"):
                    item["value"] = 0.0 if item["value"] > 0.5 else 1.0
                return True
        
        # --- Mouse Wheel (scroll groups) ---
        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            for group_name, area_rect in self._group_area_rects.items():
                if area_rect.collidepoint(mx, my):
                    self._scroll_group(group_name, -event.y)  # wheel up = -1 = scroll up
                    return True
            return False
        
        # --- Mouse ---
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            self.hovered = -1
            
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
            
            # 0. Scroll arrows
            for group_name, arrows in self._scroll_arrow_rects.items():
                if "up" in arrows and arrows["up"].collidepoint(mx, my):
                    self._scroll_group(group_name, -1)
                    return True
                if "down" in arrows and arrows["down"].collidepoint(mx, my):
                    self._scroll_group(group_name, 1)
                    return True
            
            # 1. Image Selector Buttons
            if self._img_prev_rect and self._img_prev_rect.collidepoint(mx, my):
                self._change_image(-1)
                return True
            if self._img_next_rect and self._img_next_rect.collidepoint(mx, my):
                self._change_image(1)
                return True
            
            # 2. Source Buttons
            for idx, rect in self._src_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    item = self.items[idx]
                    item["src_value"] = (item["src_value"] + 1) % 3
                    return True
            
            # 3. Toggle Switches
            for idx, rect in self._toggle_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    item = self.items[idx]
                    item["value"] = 0.0 if item["value"] > 0.5 else 1.0
                    return True

            # 4. Sliders
            for idx, rect in self._slider_bar_rects.items():
                if rect.collidepoint(mx, my):
                    self.selected = idx
                    self.dragging_slider = idx
                    self._set_slider_from_mouse(idx, mx)
                    return True

            # 5. General Item Click
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
        
        pct = (mx - bar_rect.x) / max(bar_rect.width, 1)
        pct = max(0.0, min(1.0, pct))
        
        raw = item["min"] + pct * (item["max"] - item["min"])
        item["value"] = round(round(raw / item["step"]) * item["step"], 2)
        item["value"] = max(item["min"], min(item["max"], item["value"]))
    
    def render_surface(self, screen_w, screen_h):
        """Render menu to a Pygame RGBA surface."""
        panel_w = min(500, screen_w - 40)
        panel_h = min(660, screen_h - 40)
        pad = 20
        
        surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
        
        px = (screen_w - panel_w) // 2
        py = (screen_h - panel_h) // 2
        
        self._panel_rect = pygame.Rect(px, py, panel_w, panel_h)
        self._item_rects = []
        self._slider_bar_rects = {}
        self._toggle_rects = {}
        self._src_rects = {}
        self._img_prev_rect = None
        self._img_next_rect = None
        self._scroll_arrow_rects = {}
        self._group_area_rects = {}
        
        # Background
        pygame.draw.rect(surface, self.bg_color, self._panel_rect, border_radius=14)
        pygame.draw.rect(surface, (100, 80, 180, 100), self._panel_rect, 2, border_radius=14)
        
        # Title
        title = self.font_title.render("⚙  EFECTOS & AJUSTES", True, self.title_color)
        surface.blit(title, (px + (panel_w - title.get_width()) // 2, py + pad))
        
        sep_y = py + pad + 32
        pygame.draw.line(surface, (80, 60, 140, 120), (px + pad, sep_y), (px + panel_w - pad, sep_y), 1)
        
        # Items
        item_y = sep_y + 12
        bar_w = panel_w - pad * 2 - 200
        item_h = 32
        arrow_h = 18  # Height for scroll arrows
        
        # Pre-compute which groups need scrolling and their visible ranges
        group_visible_range = {}  # {group: (offset, count_visible, total)}
        for group_name, max_vis in self._group_max_visible.items():
            group_items = self._get_group_items(group_name)
            total = len(group_items)
            offset = self._scroll_offsets.get(group_name, 0)
            count_vis = min(max_vis, total)
            group_visible_range[group_name] = (offset, count_vis, total)
        
        # Track which group we've already started rendering (for arrows)
        groups_started = set()
        groups_ended = set()
        
        i = 0
        while i < len(self.items):
            item = self.items[i]
            
            # --- Separator ---
            if item["type"] == "separator":
                sep_line_y = item_y + 8
                pygame.draw.line(surface, self.separator_color,
                                 (px + pad + 10, sep_line_y),
                                 (px + panel_w - pad - 10, sep_line_y), 1)
                item_y += 18
                i += 1
                continue
            
            group = item.get("group")
            
            # --- Handle scrollable group ---
            if group and group in self._group_max_visible and group not in groups_started:
                groups_started.add(group)
                offset, count_vis, total = group_visible_range[group]
                needs_scroll = total > count_vis
                
                # Record group area start
                group_area_y_start = item_y
                
                # ▲ Arrow (if items hidden above)
                if needs_scroll and offset > 0:
                    arrow_rect = pygame.Rect(px + pad, item_y, panel_w - pad * 2, arrow_h)
                    self._scroll_arrow_rects.setdefault(group, {})["up"] = arrow_rect
                    # Draw arrow
                    arrow_txt = self.font_arrow.render("▲  ▲  ▲", True, self.arrow_color)
                    surface.blit(arrow_txt, (px + (panel_w - arrow_txt.get_width()) // 2, item_y))
                    item_y += arrow_h
                elif needs_scroll:
                    # Reserve space but show nothing (keeps layout stable)
                    item_y += arrow_h
                
                # Render only the visible items in this group
                group_items = self._get_group_items(group)
                visible_items = group_items[offset:offset + count_vis]
                
                for gi, gitem in visible_items:
                    item_y = self._render_item(surface, gi, gitem, item_y, px, py,
                                               pad, panel_w, bar_w, item_h)
                
                # ▼ Arrow (if items hidden below)
                if needs_scroll and offset + count_vis < total:
                    arrow_rect = pygame.Rect(px + pad, item_y, panel_w - pad * 2, arrow_h)
                    self._scroll_arrow_rects.setdefault(group, {})["down"] = arrow_rect
                    arrow_txt = self.font_arrow.render("▼  ▼  ▼", True, self.arrow_color)
                    surface.blit(arrow_txt, (px + (panel_w - arrow_txt.get_width()) // 2, item_y))
                    item_y += arrow_h
                elif needs_scroll:
                    item_y += arrow_h
                
                # Record group area for mouse wheel detection
                self._group_area_rects[group] = pygame.Rect(
                    px, group_area_y_start, panel_w, item_y - group_area_y_start
                )
                
                # Skip all items in this group (we already rendered the visible ones)
                groups_ended.add(group)
                # Advance i past all items in this group
                while i < len(self.items) and self.items[i].get("group") == group:
                    i += 1
                continue
            
            # If this item belongs to a group we already rendered, skip it
            if group and group in groups_ended:
                i += 1
                continue
            
            # --- Normal (non-grouped) item ---
            item_y = self._render_item(surface, i, item, item_y, px, py,
                                       pad, panel_w, bar_w, item_h)
            i += 1
        
        # Hints at bottom
        hint_y = py + panel_h - 44
        pygame.draw.line(surface, (80, 60, 140, 120),
                         (px + pad, hint_y - 8), (px + panel_w - pad, hint_y - 8), 1)
        
        hints = [
            "[←/→] Navegar Fondo   [Click/S] Fuente",
            "[F] Pantalla Comp.  [B] Sin bordes"
        ]
        for hint_text in hints:
            hint = self.font_hint.render(hint_text, True, self.hint_color)
            surface.blit(hint, (px + (panel_w - hint.get_width()) // 2, hint_y))
            hint_y += 18
        
        return surface
    
    def _render_item(self, surface, i, item, item_y, px, py, pad, panel_w, bar_w, item_h):
        """Render a single menu item. Returns the new item_y after this item."""
        is_selected = (i == self.selected)
        is_hovered = (i == self.hovered)
        
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
        
        if item["type"] == "image_selector":
            btn_w = 56
            btn_h = 24
            right_edge = px + panel_w - pad
            
            # "Sig >" button
            next_rect = pygame.Rect(right_edge - btn_w, item_y + 3, btn_w, btn_h)
            pygame.draw.rect(surface, (60, 60, 100), next_rect, border_radius=5)
            pygame.draw.rect(surface, (100, 80, 180, 160), next_rect, 1, border_radius=5)
            next_txt = self.font_small.render("Sig >", True, (200, 200, 240))
            surface.blit(next_txt, (next_rect.x + (btn_w - next_txt.get_width()) // 2,
                                     next_rect.y + (btn_h - next_txt.get_height()) // 2))
            self._img_next_rect = next_rect
            
            # "< Ant" button
            prev_rect = pygame.Rect(right_edge - btn_w * 2 - 10, item_y + 3, btn_w, btn_h)
            pygame.draw.rect(surface, (60, 60, 100), prev_rect, border_radius=5)
            pygame.draw.rect(surface, (100, 80, 180, 160), prev_rect, 1, border_radius=5)
            prev_txt = self.font_small.render("< Ant", True, (200, 200, 240))
            surface.blit(prev_txt, (prev_rect.x + (btn_w - prev_txt.get_width()) // 2,
                                     prev_rect.y + (btn_h - prev_txt.get_height()) // 2))
            self._img_prev_rect = prev_rect
            
            # Image name
            img_name = self.get_current_image_name()
            if len(img_name) > 18:
                img_name = img_name[:16] + "…"
            name_surf = self.font_hint.render(img_name, True, (160, 180, 220))
            name_x = prev_rect.x - name_surf.get_width() - 10
            surface.blit(name_surf, (name_x, item_y + 7))
        
        elif item["type"] in ("toggle", "effect_row"):
            # Toggle Switch
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
            
            # Source Selector button (effect_row only)
            if item["type"] == "effect_row":
                src_val = item["src_value"]
                src_color = self.src_colors[src_val]
                src_label = self.src_labels[src_val]
                
                btn_w = 40
                btn_h = 20
                btn_x = tog_x - btn_w - 20
                btn_rect = pygame.Rect(btn_x, item_y + 5, btn_w, btn_h)
                self._src_rects[i] = btn_rect
                
                pygame.draw.rect(surface, src_color, btn_rect, border_radius=4)
                
                txt_surf = self.font_small.render(src_label, True, (20, 20, 30))
                txt_x = btn_x + (btn_w - txt_surf.get_width()) // 2
                txt_y = item_y + 5 + (btn_h - txt_surf.get_height()) // 2
                surface.blit(txt_surf, (txt_x, txt_y))

        elif item["type"] == "slider":
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
            
            # Value text
            val_text = f"{int(item['value'] * 100)}%" if item["key"] != "sensitivity" else f"{item['value']}x"
            pct_text = self.font_hint.render(val_text, True, color)
            surface.blit(pct_text, (bar_x + bar_w + 12, item_y + 5))
        
        return item_y + item_h + 4
