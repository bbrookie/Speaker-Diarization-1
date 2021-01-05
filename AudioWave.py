from pydub import AudioSegment
from pydub.playback import play
from pydub.generators import WhiteNoise
from pydub.utils import mediainfo
import numpy as np
from pydub.playback import play
from threading import Thread
from time import sleep
from multiprocessing import Process
#import librosa
from pydub.silence import split_on_silence
audio_in_file = "in_sine.wav"
audio_out_file = "out_sine.wav"
import simpleaudio
import os

class AudioWave:
    def __init__(self, input_wave_file):
        self.input_wave_file = input_wave_file
        self.audio = AudioSegment.from_wav(input_wave_file)
        self.audio_info = mediainfo(input_wave_file)
        self.sample_rate = int(self.audio_info['sample_rate'])
        

    #def match_target_amplitude(self, sound, target_dBFS):
    #    change_in_dBFS = 2 * target_dBFS - sound.dBFS
    #    return sound.apply_gain(change_in_dBFS)

    def match_target_amplitude(self, aChunk, target_dBFS):
        change_in_dBFS = target_dBFS - aChunk.dBFS
        return aChunk.apply_gain(change_in_dBFS)

    def convert_sample_array_to_audio(self, sample_array):
        self.audio = AudioSegment(sample_array.astype("int16").tobytes(), frame_rate=self.audio.frame_rate, sample_width=2, channels=1)

    def play_audio(self):
        playback = simpleaudio.play_buffer(self.audio.raw_data, num_channels=self.audio.channels, bytes_per_sample=self.audio.sample_width,
         sample_rate=self.audio.frame_rate)
        return playback

    def get_sample_array(self):
        print(type(self.audio.get_array_of_samples()))
        return np.array(list(self.audio.get_array_of_samples()))

    def generate_white_noise(self, noise_duration, reduction = 10):
        noise = WhiteNoise().to_audio_segment(duration=noise_duration).set_frame_rate(int(self.audio_info['sample_rate']))
        return noise - 10

    def combine_noise_to_audio(self, noise):
        self.audio = self.audio.overlay(noise)

    def add_silence_beginning(self, silence_duration = 400, noisy = False):
        if(noisy == True):
            noise = self.generate_white_noise(silence_duration)
            noise = self.match_target_amplitude(noise, self.audio.dBFS)
            silence = AudioSegment.silent(duration = silence_duration)
            silence = silence.overlay(noise)
        else:
            silence = AudioSegment.silent(duration = silence_duration)
        
        self.audio = silence + self.audio
        return self.audio 

    def add_silence_end(self, silence_duration = 400, noisy = False):
        if(noisy == True):
            noise = self.generate_white_noise(silence_duration)
            noise = self.match_target_amplitude(noise, self.audio.dBFS)
            silence = AudioSegment.silent(duration = silence_duration)
            silence = silence.overlay(noise)
        else:
            silence = AudioSegment.silent(duration = silence_duration)
        
        self.audio = self.audio + silence
        return self.audio 

    def add_silence_beginning_and_end(self, beginning_silence_duration, end_silence_duration, noisy = False):
        self.audio = self.add_silence_beginning(silence_duration = beginning_silence_duration, noisy = True)
        self.audio = self.add_silence_end(silence_duration = end_silence_duration, noisy = True)
        return self.audio
    
    def export_file(self, path, export_format = "wav"):
        self.audio.export(path, format = export_format)



    def VAD_chunk(self, out_dir, output_length = 8000, added_silence = 400):
        

        #song = AudioSegment.from_mp3(in_path)
        out_path = os.path.join(out_dir, os.path.basename(self.input_wave_file[:-4]))
        os.makedirs(out_dir, exist_ok=True)
        chunks = split_on_silence (
            self.audio, 
            min_silence_len = 400,
            silence_thresh = -35,
            keep_silence=output_length/2
        )

        target_length = output_length - added_silence * 2
        output_chunks = chunks[0]
        chunk_id = 0
        for i, chunk in enumerate(chunks[1:]):
            
            if len(output_chunks + chunk) <= target_length:
                output_chunks += chunk
            else:
                # if the last output chunk is longer than the target length,
                # we can start a new one
                

                silence_chunk = AudioSegment.silent(duration=added_silence)

                audio_chunk = silence_chunk + output_chunks + silence_chunk


                normalized_chunk = self.match_target_amplitude(audio_chunk, -20.0)

                print("Exporting {}_{}.wav.".format(out_path, chunk_id))
                normalized_chunk.export(
                    "{}_{}.wav".format(out_path, chunk_id),
                    format = "wav"
                )

                chunk_id += 1
                output_chunks = chunk
        else:
            silence_chunk = AudioSegment.silent(duration=added_silence)

            audio_chunk = silence_chunk + output_chunks + silence_chunk


            normalized_chunk = self.match_target_amplitude(audio_chunk, -20.0)

            print("Exporting {}_{}.wav.".format(out_path, chunk_id))
            normalized_chunk.export(
                "{}_{}.wav".format(out_path, chunk_id),
                format = "wav"
            )



        