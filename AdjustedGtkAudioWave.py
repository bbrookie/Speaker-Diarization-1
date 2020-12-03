import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
#from gtk_pyplot import gtk_pyplot
from inference import infer_one_file
from AudioWave import AudioWave
import numpy as np
from matplotlib.figure import Figure
from numpy import arange, pi, random, linspace
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from GtkAudioWave import GtkAudioWave
import matplotlib.pyplot as plt

class AdjustedGtkAudioWave(GtkAudioWave):
    def __init__(self, label_text, Audio_file_name, speakers, colors):
        self.speakers = speakers
        self.colors = colors
        super().__init__(label_text, Audio_file_name)


    def make_static_plot(self):

        for i, speaker in enumerate(self.speakers):
            time = linspace(0, speaker.audio_length, len(speaker.sample_array), endpoint=False)
            self.ax.plot(time, speaker.sample_array, self.colors[i])

        self.y_max = self.ax.get_ylim()[1]
        self.y_min = self.ax.get_ylim()[0]
        self.vl = self.ax.axvline(0, ls='-', color='r', lw=1, zorder=10)