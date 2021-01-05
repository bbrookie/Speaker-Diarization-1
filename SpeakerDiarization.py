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
from AdjustedGtkAudioWave import AdjustedGtkAudioWave
import os
import time

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
        

class SpeakerDiarization():
    def __init__(self, wave):
        self.wave = wave
        self.colors = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd", "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        self.cycler_index = 0
        self.speakers = []
        self.wave_annotated = None

    def get_next_colors(self):
        self.cycler_index += 1
        return self.colors[self.cycler_index - 1]


    def combine_speakers_visualization(self):
        
        self.wave_annotated = AdjustedGtkAudioWave("Original Wave", self.wave, self.speakers, self.colors)
        return self.wave_annotated.make_visualization().get_visualization()


    def output_file(self, times, labels, wave):
        
        speakers_str = ""
        out_path = os.path.join("output", os.path.basename(wave)[:-4]+".txt")
        start_t = times[0][0]
        end_t   = times[0][1]
        #print(len(times))
        #print("Outtttttttttttttttttt")
        for i in range(1, len(times), 1):
            #print("Outtttttttttttttttttt")
            if (times[i][0] - times[i - 1][1] <= 0.03 and labels[i] == labels[i - 1]):
                end_t = times[i][1]
                #print("Outtttttttttttttttttt2")
                if(i == len(times) - 1):
                    #print("Outtttttttttttttttttt")
                    print("Outtttttttttttttttttt3")
                    start_str = time.strftime('%H:%M:%S', time.gmtime(start_t))
                    start_str += ".{}".format(str(int(str(start_t).split('.')[1])%100)) if str(start_t).find('.') > 0 else '.00'
                    
                    end_str = time.strftime('%H:%M:%S', time.gmtime(end_t))
                    end_str += ".{}".format(str(int(str(end_t).split('.')[1])%100)) if str(end_t).find('.') > 0 else '.00'
                    #print("Outtttttttttttttttttt")
                    speakers_str += str(labels[i - 1]) + ",{start},{end}".format(start = start_str, end = end_str)
            else:
                #print("Outtttttttttttttttttt")
                start_str = time.strftime('%H:%M:%S', time.gmtime(start_t))
                start_str += ".{}".format(str(int(str(start_t).split('.')[1])%100)) if str(start_t).find('.') > 0 else '.00'
                
                end_str = time.strftime('%H:%M:%S', time.gmtime(end_t))
                end_str += ".{}".format(str(int(str(end_t).split('.')[1])%100)) if str(end_t).find('.') > 0 else '.00'
                speakers_str += str(labels[i - 1]) + ",{start},{end}".format(start = start_str, end = end_str)+"\n"
                start_t = times[i][0]
                end_t = times[i][1]
            #print("Outtttttttttttttttttt")
        #print("Outtttttttttttttttttt")
        os.makedirs("output", exist_ok=True)
        with open(out_path, 'w') as out:
            out.write(speakers_str)

        print("Output is written in the output directory.")

    def run_diarization(self):
        labels, times = infer_one_file(self.wave)
        self.output_file(times, labels, self.wave)
        labels = np.array(labels)
        times = np.array(times)
        num_speakers = np.unique(labels)
        sw = Gtk.ScrolledWindow()
        vbox = Gtk.Box(orientation = Gtk.Orientation.VERTICAL, spacing = 6)

        for speaker in num_speakers:
            speaker_audio_wave = GtkAudioWave("Speaker: "+ str(speaker), self.wave, self.get_next_colors())
            
            speaker_audio_wave.mask_audio_segments(times[labels == speaker])
            #print(type(speaker_audio_wave.sample_array))
            speaker_audio_wave.convert_sample_array_to_audio(speaker_audio_wave.sample_array)
            #print(type(speaker_audio_wave.sample_array))
            speaker_box = speaker_audio_wave.make_visualization().get_visualization()
            self.speakers.append(speaker_audio_wave)
            speaker_audio_wave.export_file("output/Speaker" + str(speaker)+".wav")
            vbox.pack_start(speaker_box, True, True, 0)

        #vbox.pack_start(self.combine_speakers_visualization(), True, True, 0)
 
        sw.add(vbox)
        return sw