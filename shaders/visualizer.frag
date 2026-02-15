#version 330
uniform sampler2D tex;
uniform sampler2D spectrum_tex;  // 64x1 texture with spectrum bins
uniform float time;
uniform float bass;
uniform float mid;
uniform float treble;
uniform vec2 resolution;

// Effect toggles (0.0 = off, 1.0 = on)
uniform float fx_zoom;
uniform float fx_ripple;
uniform float fx_wave;
uniform float fx_chromatic;
uniform float fx_edge_glow;

// Other effects
uniform float fx_bars;
uniform float fx_circle;
uniform float fx_colormask;
uniform float fx_destellos;  // Audio-reactive glow ("destellos")

// Audio Source Selectors (0=Bass, 1=Mid, 2=Treble)
uniform int src_zoom;
uniform int src_ripple;
uniform int src_wave;
uniform int src_chromatic;
uniform int src_edge_glow;
uniform int src_destellos;

in vec2 v_uv;
out vec4 f_color;

const float PI = 3.14159265359;
const float NUM_BINS = 64.0;

// Helper: Get value based on source ID
float get_source(int id) {
    if (id == 0) return bass;
    if (id == 1) return mid;
    return treble;
}

// Read a spectrum bin (0-63) from the 1D spectrum texture
float get_bin(float index) {
    return texture(spectrum_tex, vec2((index + 0.5) / NUM_BINS, 0.5)).r;
}

void main() {
    vec2 uv = v_uv;
    vec2 center = vec2(0.5, 0.5);
    float dist = distance(uv, center);
    
    // ========== DISTORTION EFFECTS ==========
    
    // 1. Zoom Pulse
    if (fx_zoom > 0.5) {
        float src = get_source(src_zoom);
        float zoom = 1.0 - (src * 0.04);
        uv = center + (uv - center) * zoom;
    }
    
    // 2. Ripple
    if (fx_ripple > 0.5) {
        float src = get_source(src_ripple);
        float ripple = sin(dist * 20.0 - time * 5.0) * 0.5 + 0.5;
        float ds = src * 0.035;
        vec2 dir = normalize(uv - center + 0.001);
        uv += dir * ripple * ds;
    }

    // 3. Wave Warp
    if (fx_wave > 0.5) {
        float src = get_source(src_wave);
        float wave_x = sin(uv.y * 15.0 + time * 3.0) * src * 0.03;
        float wave_y = cos(uv.x * 12.0 + time * 2.5) * src * 0.02;
        uv += vec2(wave_x, wave_y);
    }

    // Sample background (with Chromatic Aberration if enabled)
    float r, g, b;
    bool chromatic_active = (fx_chromatic > 0.5);
    
    if (chromatic_active) {
        float src = get_source(src_chromatic);
        // Shift depends on intensity
        float shift = src * 0.02 + 0.002; 
        
        r = texture(tex, uv + vec2(shift, shift * 0.5)).r;
        g = texture(tex, uv).g;
        b = texture(tex, uv - vec2(shift, shift * 0.5)).b;
    } else {
        vec3 c = texture(tex, uv).rgb;
        r = c.r; g = c.g; b = c.b;
    }
    vec3 color = vec3(r, g, b);

    // 4. Edge Glow
    if (fx_edge_glow > 0.5) {
        float src = get_source(src_edge_glow);
        if (src > 0.05) {
            vec2 px = vec2(1.0) / resolution;
            vec3 left_c  = texture(tex, uv - vec2(px.x, 0.0)).rgb;
            vec3 right_c = texture(tex, uv + vec2(px.x, 0.0)).rgb;
            vec3 up_c    = texture(tex, uv - vec2(0.0, px.y)).rgb;
            vec3 down_c  = texture(tex, uv + vec2(0.0, px.y)).rgb;
            
            float edge = length(right_c - left_c) + length(down_c - up_c);
            
            // Color based on source (Bass=Reddish, Mid=Greenish, Treble=Blueish) logic could be added
            // For now, keep it blue-ish
            color += edge * src * vec3(0.4, 0.6, 1.0) * 1.5;
        }
    }

    // Vignette (always on — basic darkening at edges)
    float vig_raw = 1.0 - smoothstep(0.3, 1.2, dist);
    color *= mix(0.7, 1.0, vig_raw);

    // Destellos (audio-reactive glow)
    if (fx_destellos > 0.5) {
        float src = get_source(src_destellos);
        color += vec3(src * 0.08);
    }

    // ========== FREQUENCY BARS ==========
    if (fx_bars > 0.5) {
        float bar_region_h = 0.35;  // Bars occupy bottom 35%
        float bar_y_start = 1.0 - bar_region_h;
        
        if (v_uv.y > bar_y_start) {
            float norm_y = (v_uv.y - bar_y_start) / bar_region_h;  // 0 at top of region, 1 at bottom
            float bar_height_y = 1.0 - norm_y;  // 0 at bottom, 1 at top
            
            // Which bin?
            float bin_index = floor(v_uv.x * NUM_BINS);
            float bin_frac = fract(v_uv.x * NUM_BINS);
            float amp = get_bin(bin_index);
            
            // Gap between bars
            float bar_width = 0.75;
            
            if (bin_frac > (1.0 - bar_width) * 0.5 && bin_frac < 1.0 - (1.0 - bar_width) * 0.5) {
                if (bar_height_y < amp) {
                    // Color gradient: blue at bottom -> cyan -> magenta at top
                    float t = bar_height_y / max(amp, 0.01);
                    vec3 bar_color = mix(
                        vec3(0.1, 0.4, 1.0),   // Blue base
                        vec3(1.0, 0.3, 0.8),    // Magenta top
                        t
                    );
                    
                    // Glow at tip
                    float tip_glow = smoothstep(amp - 0.05, amp, bar_height_y) * 0.5;
                    bar_color += vec3(tip_glow);
                    
                    // Alpha blend on top of background
                    float alpha = 0.85;
                    color = mix(color, bar_color, alpha);
                }
            }
        }
    }

    // ========== CIRCULAR VISUALIZER ==========
    if (fx_circle > 0.5) {
        vec2 aspect_uv = vec2(v_uv.x, v_uv.y * resolution.y / resolution.x);
        vec2 aspect_center = vec2(0.5, 0.5 * resolution.y / resolution.x);
        
        float c_dist = distance(aspect_uv, aspect_center);
        float angle = atan(aspect_uv.y - aspect_center.y, aspect_uv.x - aspect_center.x);
        float norm_angle = (angle + PI) / (2.0 * PI);  // 0 to 1
        
        // Map angle to bin
        float bin_index = floor(norm_angle * NUM_BINS);
        float bin_frac = fract(norm_angle * NUM_BINS);
        float amp = get_bin(bin_index);
        
        // Circle parameters
        float inner_r = 0.08;
        float max_bar_len = 0.12;
        float outer_r = inner_r + amp * max_bar_len;
        
        // Bar gap (angular)
        float bar_active = (bin_frac > 0.15 && bin_frac < 0.85) ? 1.0 : 0.0;
        
        // Draw if in ring
        if (c_dist > inner_r && c_dist < outer_r && bar_active > 0.5) {
            float t = (c_dist - inner_r) / max(outer_r - inner_r, 0.001);
            
            // Color: cyan center -> purple outside
            vec3 ring_color = mix(
                vec3(0.0, 0.9, 1.0),   // Cyan
                vec3(0.8, 0.2, 1.0),   // Purple
                t
            );
            
            // Glow at tip
            float tip = smoothstep(outer_r - 0.005, outer_r, c_dist);
            ring_color += vec3(0.3) * (1.0 - tip);
            
            color = mix(color, ring_color, 0.9);
        }
        
        // Inner circle glow
        float inner_glow = smoothstep(inner_r, inner_r - 0.015, c_dist);
        vec3 glow = vec3(0.1, 0.3, 0.6) * inner_glow * (0.5 + bass * 0.5);
        color += glow;
        
        // Outer ring outline
        float ring_line = smoothstep(0.002, 0.0, abs(c_dist - inner_r));
        color += vec3(0.2, 0.5, 0.8) * ring_line * 0.5;
    }

    // ========== COLOR MASK BARS ==========
    if (fx_colormask > 0.5) {
        // Save original color
        vec3 original_color = color;
        
        // Convert to grayscale (luminance)
        float gray = dot(color, vec3(0.299, 0.587, 0.114));
        vec3 bw = vec3(gray);
        
        // 24 wide bars, no gaps, full screen height
        float num_mask_bars = 24.0;
        float bar_index = floor(v_uv.x * num_mask_bars);
        
        // Map to spectrum bins (spread 64 bins across 24 bars)
        float bin_center = (bar_index + 0.5) * (NUM_BINS / num_mask_bars);
        float amp = get_bin(bin_center);
        
        // Bar goes from bottom up: v_uv.y=1 is bottom, amp=1 means full height
        float bar_top = 1.0 - amp;  // y position where color starts
        
        if (v_uv.y > bar_top) {
            // Inside bar region: show original color
            // Smooth transition at the bar edge
            float edge_soft = smoothstep(bar_top, bar_top + 0.02, v_uv.y);
            color = mix(bw, original_color, edge_soft);
            
            // Subtle glow at the bar tip
            float tip_intensity = smoothstep(bar_top + 0.03, bar_top, v_uv.y) * 0.4;
            color += vec3(0.3, 0.5, 1.0) * tip_intensity;
        } else {
            // Above bar: grayscale
            color = bw;
        }
    }

    f_color = vec4(color, 1.0);
}
