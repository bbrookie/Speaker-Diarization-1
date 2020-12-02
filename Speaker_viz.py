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
from SpeakerDiarization import SpeakerDiarization

class MainWindow(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Speaker Diarization Viz")

        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(vbox)
        #self.resize(1280, 800)
        vseparator = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        vseparator.colors = Gdk.color_parse('black')
        #self.original_wave = GtkAudioWave("Original Sound Wave", "../testdr3_converted.wav").make_visualization().get_visualization()
        #vbox.pack_start(self.original_wave, True, True, 0)
        #vbox.pack_start(vseparator, True, True, 0)
        diarization = SpeakerDiarization("../testdr3_converted.wav")
        diarization_box = diarization.run_diarization()
        original_wave = diarization.combine_speakers_visualization()
        vbox.pack_start(original_wave, True, True, 0)
        diarization_box.set_size_request(-1, 400)
        vbox.pack_start(diarization_box, True, True, 0)



win = MainWindow()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()