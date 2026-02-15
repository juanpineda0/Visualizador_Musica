"""
Audio Analyzer using pyaudiowpatch (WASAPI Loopback).
Captures system audio output and computes frequency bands (Bass, Mid, Treble).
"""
import pyaudiowpatch as pyaudio
import numpy as np
import threading

class AudioAnalyzer:
    def __init__(self, sample_rate=None, buffer_size=2048):
        self.buffer_size = buffer_size
        self.running = False
        self.lock = threading.Lock()
        
        # These will be set when we find the loopback device
        self.sample_rate = sample_rate
        self.channels = 2
        self.device_index = None
        self.device_name = "No device"
        
        # Audio Data
        self.bass = 0.0
        self.mid = 0.0
        self.treble = 0.0
        
        # Spectrum bins (64 logarithmic bins for visualizer bars/circle)
        self.num_bins = 64
        self.spectrum_bins = np.zeros(self.num_bins, dtype=np.float32)
        
        # Smoothing (0.0 = no smoothing, 1.0 = frozen)
        self.smooth_factor = 0.7
        self.spectrum_smooth = 0.6
        
        # Find loopback device at init
        self._find_loopback_device()
        
    def _find_loopback_device(self):
        """Find the WASAPI loopback device for the default output."""
        p = pyaudio.PyAudio()
        
        try:
            # Find WASAPI host API
            wasapi_info = None
            for i in range(p.get_host_api_count()):
                info = p.get_host_api_info_by_index(i)
                if "WASAPI" in info["name"]:
                    wasapi_info = info
                    break
            
            if wasapi_info is None:
                print("ERROR: WASAPI not found.")
                p.terminate()
                return
            
            # Get default output device
            default_output = wasapi_info["defaultOutputDevice"]
            default_info = p.get_device_info_by_index(default_output)
            print(f"Default Speaker: {default_info['name']}")
            
            # Find its loopback counterpart
            for i in range(p.get_device_count()):
                dev = p.get_device_info_by_index(i)
                if (dev["hostApi"] == wasapi_info["index"] 
                    and dev.get("isLoopbackDevice", False)
                    and default_info["name"] in dev["name"]):
                    self.device_index = dev["index"]
                    self.device_name = dev["name"]
                    self.channels = dev["maxInputChannels"]
                    if self.sample_rate is None:
                        self.sample_rate = int(dev["defaultSampleRate"])
                    print(f"Loopback device found: {self.device_name}")
                    print(f"  Channels: {self.channels}, Rate: {self.sample_rate}")
                    break
            
            if self.device_index is None:
                # Fallback: any loopback device
                for i in range(p.get_device_count()):
                    dev = p.get_device_info_by_index(i)
                    if dev.get("isLoopbackDevice", False):
                        self.device_index = dev["index"]
                        self.device_name = dev["name"]
                        self.channels = dev["maxInputChannels"]
                        if self.sample_rate is None:
                            self.sample_rate = int(dev["defaultSampleRate"])
                        print(f"Fallback loopback: {self.device_name}")
                        break
                        
        except Exception as e:
            print(f"Error finding loopback: {e}")
        finally:
            p.terminate()
        
        if self.sample_rate is None:
            self.sample_rate = 44100  # Last resort default

    def start(self):
        if self.device_index is None:
            print("WARNING: No loopback device found. Audio will not work.")
            return
        self.running = True
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()
        
    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2)

    def _capture_loop(self):
        p = pyaudio.PyAudio()
        
        try:
            stream = p.open(
                format=pyaudio.paFloat32,
                channels=self.channels,
                rate=self.sample_rate,
                input=True,
                input_device_index=self.device_index,
                frames_per_buffer=self.buffer_size,
            )
            
            while self.running:
                data = stream.read(self.buffer_size, exception_on_overflow=False)
                samples = np.frombuffer(data, dtype=np.float32)
                
                # Mono conversion
                if self.channels > 1:
                    samples = samples.reshape(-1, self.channels).mean(axis=1)
                
                self._process_audio(samples)
            
            stream.stop_stream()
            stream.close()
            
        except Exception as e:
            print(f"Audio Capture Error: {e}")
        finally:
            p.terminate()

    def _process_audio(self, data):
        # Hanning window
        windowed = data * np.hanning(len(data))
        
        # FFT
        fft = np.abs(np.fft.rfft(windowed))
        freqs = np.fft.rfftfreq(len(data), 1/self.sample_rate)
        
        # Energy per band
        def band_energy(low, high):
            mask = (freqs >= low) & (freqs < high)
            return np.mean(fft[mask]) if np.any(mask) else 0.0
        
        bass_raw = band_energy(20, 250)
        mid_raw = band_energy(250, 4000)
        treble_raw = band_energy(4000, 16000)
        
        # Scale
        bass_scaled = min(bass_raw / 50.0, 2.0)
        mid_scaled = min(mid_raw / 10.0, 2.0)
        treble_scaled = min(treble_raw / 3.0, 2.0)
        
        # Spectrum bins (64 log-spaced bins)
        new_bins = self._compute_spectrum_bins(fft, freqs)
        
        # Smooth everything
        s = self.smooth_factor
        ss = self.spectrum_smooth
        with self.lock:
            self.bass = self.bass * s + bass_scaled * (1 - s)
            self.mid = self.mid * s + mid_scaled * (1 - s)
            self.treble = self.treble * s + treble_scaled * (1 - s)
            self.spectrum_bins = self.spectrum_bins * ss + new_bins * (1 - ss)

    def _compute_spectrum_bins(self, fft, freqs):
        """Compute 64 logarithmically-spaced spectrum bins."""
        log_edges = np.logspace(np.log10(20), np.log10(16000), self.num_bins + 1)
        bins = np.zeros(self.num_bins, dtype=np.float32)
        
        for i in range(self.num_bins):
            mask = (freqs >= log_edges[i]) & (freqs < log_edges[i + 1])
            if np.any(mask):
                bins[i] = np.mean(fft[mask])
        
        # Normalize: scale to roughly 0-1 range
        # Use a fixed reference (from test: bass peaks ~90, treble ~3)
        # Low bins get more energy, so use per-bin scaling
        ref_scale = np.linspace(40.0, 3.0, self.num_bins)
        bins = np.minimum(bins / ref_scale, 1.5)
        
        return bins

    def get_audio_levels(self):
        with self.lock:
            return self.bass, self.mid, self.treble
    
    def get_spectrum(self):
        with self.lock:
            return self.spectrum_bins.copy()
