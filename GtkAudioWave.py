import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
import numpy as np
from matplotlib.figure import Figure
from numpy import arange, pi, random, linspace
from matplotlib.backends.backend_gtk3cairo import FigureCanvasGTK3Cairo as FigureCanvas
from AudioWave import AudioWave
from enum import Enum
import matplotlib.animation as animation
import matplotlib.pyplot as plt
from time import sleep
import threading

class PlayBtnState(Enum):
    Playing = 1
    Paused = 2

class GtkAudioWave(AudioWave):
    def __init__(self, label_text, Audio_file_name, color = "#1f77b4"):
        
        super().__init__(Audio_file_name)
        self.sample_array = self.get_sample_array()
        self.label_text = label_text
        self.Audio_file_name = Audio_file_name
        self.color = color
        self.state = PlayBtnState.Paused
        self.audio_thread = None
        self.audio_position = 0
        
    def get_result(self):
        self.make_label(self.label_text)
        self.make_plot(self.Audio_file_name)
        self.make_play_btn()
        result = self.combine_elements()
        return result

    def make_label(self, text):
        self.label = Gtk.Label(label = text)

    def make_play_btn(self):
        self.icon = Gtk.Image().new_from_file('Images/play.png')
        self.play_btn = Gtk.Button()
        self.play_btn.add(self.icon)
        self.play_btn.connect("clicked", self.play_btn_clicked)
        self.play_btn.set_hexpand(False)
        self.play_btn.set_valign(Gtk.Align.CENTER)
        self.play_btn.set_vexpand(False)
        self.play_btn.set_halign(Gtk.Align.CENTER)
        self.play_btn.set_size_request(50, 50)
    
    
    def do_every (self, interval, worker_func, iterations = 0):
        if iterations != 1:
            self.a = threading.Timer (
            interval,
            self.do_every, [interval, worker_func, 0 if iterations == 0 else iterations-1]
            )
        self.a.start ()
        worker_func ()

    def run_animation(self):
        self.audio_position += 1
        self.animate(0, self.audio_position - 1)


    def play_btn_clicked(self, w):
        if(self.state == PlayBtnState.Paused):
            self.audio_thread = self.play_audio()
            self.icon = Gtk.Image().new_from_file('Images/stop.png')
            self.play_btn.set_image(self.icon)
            self.state = PlayBtnState.Playing
            self.play_btn.set_size_request(50, 50)
            self.do_every((self.audio_length / 300), self.run_animation)
        else:
            self.icon = Gtk.Image().new_from_file('Images/play.png')
            self.play_btn.set_image(self.icon)
            self.audio_thread.stop()
            self.state = PlayBtnState.Paused
            self.play_btn.set_size_request(50, 50)
            self.a.cancel()
            self.audio_position = 0
            self.animate(0, 0)
            
            

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
        self.fig = Figure(figsize=(5,5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.signal = self.sample_array
        self.audio_length = len(self.signal) / self.sample_rate
        self.time = linspace(0, self.audio_length, len(self.signal), endpoint=False)

        self.bars = self.ax.plot(self.time, self.signal, self.color)
        #ax.set_prop_cycle(self.cycler)
        #fig.suptitle("Title")
        self.y_min = self.ax.get_ylim()[0]
        self.y_max = self.ax.get_ylim()[1]
        self.refreshPeriod = 100



        self.vl = self.ax.axvline(0, ls='-', color='r', lw=1, zorder=10)

        #self.ani = animation.FuncAnimation(
        #    self.fig, self.animate, frames=int(2/(self.refreshPeriod/1000)), fargs=(self.vl,self.refreshPeriod), interval=self.refreshPeriod)

        #plt.show()
        #print("????")
        #ax.plot()
        #ani.show()
        self.sw = Gtk.ScrolledWindow()

        self.canvas = FigureCanvas(self.fig)
        #canvas.set_size_request(400,200)
        self.hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.hbox.pack_start(self.canvas, True, True, 0)
        #sw.add_with_viewport(canvas)
        #self.animate(0, self.vl, 100)
        #self.animate(0, self.vl, 200)
        return self.hbox

    
    def animate(self,i, percentage):
        #line.set_ydata(np.sin(x + i / 50))  # update the data.
        #line.axvline(x + i / 50)
        #t = x * i / 1000
        #vl.set_xdata([t,t])
        #return line,
        #i = 100
        #print(self.audio_length)
        self.ax.clear()
        self.ax.plot(self.time, self.signal, self.color)
        #ax.plot(time, np.sin(x))
        self.vl = self.ax.axvline(0, ls='-', color='r', lw=1, zorder=10)
        t = (percentage / 300) * self.audio_length
        self.vl.set_xdata([t,t])
        self.ax.fill_between(np.arange(0, t, 0.01), self.y_min, self.y_max, facecolor='grey', alpha=0.4)
        #plt.fill_between(0, 0, i, "grey")
        #return vl,
        self.plot.queue_draw()

    def combine_elements(self):
        hbox = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.pack_start(self.label, True, True, 0)
        vbox.pack_start(self.play_btn, True, True, 0)
        hbox.pack_start(vbox, True, True, 0)
        self.plot.set_size_request(900, 200)
        hbox.pack_start(self.plot, True, True, 0)
        hbox.set_size_request(300, 300)
        return hbox