import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import numpy as np
from matplotlib.figure import Figure
from numpy import arange, pi, random, linspace
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from AudioWave import AudioWave

class GtkAudioWave(AudioWave):
    def __init__(self, label_text, Audio_file_name, color = "#1f77b4"):
        
        super().__init__(Audio_file_name)
        self.sample_array = self.get_sample_array()
        self.label_text = label_text
        self.Audio_file_name = Audio_file_name
        self.color = color
        #if(plot_cycler is None):
        #    self.cycler = (cycler(color=list('rgb')) + cycler(linestyle=['-', '--', '-.']))
        #else:
        #    self.cycler = cycler
        
    def get_result(self):
        self.make_label(self.label_text)
        self.make_plot(self.Audio_file_name)
        result = self.combine_plot_and_label()
        return result

    def make_label(self, text):
        self.label = Gtk.Label(label = text)

    def mask_audio_segments(self, segments):
        new_sample_array = np.copy(self.sample_array)
        self.sample_array *= 0
        intervals = []
        for segment in segments:
            self.sample_array[int(segment[0] * self.sample_rate): int(segment[1] * self.sample_rate)] = \
                new_sample_array[int(segment[0] * self.sample_rate) : int(segment[1] * self.sample_rate)]


    def make_plot(self, file_name):
        self.plot = self.gtk_pyplot(file_name)

    def gtk_pyplot(self, file_name):
        fig = Figure(figsize=(5,5), dpi=100)
        ax = fig.add_subplot(111)

        signal = self.sample_array
        time = linspace(0, len(signal) / self.sample_rate, len(signal), endpoint=False)
        bars = ax.plot(time, signal, self.color)
        #ax.set_prop_cycle(self.cycler)
        #fig.suptitle("Title")
        sw = Gtk.ScrolledWindow()

        canvas = FigureCanvas(fig)
        canvas.set_size_request(400,200)
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.pack_start(canvas, True, True, 0)
        #sw.add_with_viewport(canvas)
        return hbox


    def combine_plot_and_label(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        hbox.pack_start(self.label, True, True, 0)
        self.plot.set_size_request(900, 70)
        hbox.pack_start(self.plot, True, True, 0)
        hbox.set_size_request(100, 10)
        return hbox