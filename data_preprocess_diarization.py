#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import glob
import os
import librosa
import numpy as np
from hparam import hparam as hp
from VAD_segments import VAD_chunk

# downloaded dataset path
audio_path = glob.glob(os.path.dirname(hp.unprocessed_data))                                        



def save_spectrogram_tisv():
    """ Full preprocess of text independent utterance. The log-mel-spectrogram is saved as numpy file.
        Each partial utterance is splitted by voice detection using DB
        and the first and the last 180 frames from each partial utterance are saved. 
        Need : utterance data set (VTCK)
    """
    print("start text independent utterance feature extraction")
    os.makedirs(hp.data.train_path, exist_ok=True)   # make folder to save train file
    os.makedirs(hp.data.test_path, exist_ok=True)    # make folder to save test file

    utter_min_len = (hp.data.tisv_frame * hp.data.hop + hp.data.window) * hp.data.sr    # lower bound of utterance length
    total_speaker_num = len(audio_path)
    train_speaker_num= (total_speaker_num//10)*9            # split total data 90% train and 10% test
    print("total speaker number : %d"%total_speaker_num)
    print("train : %d, test : %d"%(train_speaker_num, total_speaker_num-train_speaker_num))
    for i, folder in enumerate(audio_path):
        print("%dth speaker processing..."%i)
        utterances_spec = []
        for utter_name in os.listdir(folder):
            if utter_name[-4:] == '.wav':
                utter_path = os.path.join(folder, utter_name)         # path of each utterance
                times, segs = VAD_chunk(2, utter_path)
                #print("+++++++++++++++++++++++++++++", len(segs))
                for i, seg in enumerate(segs):
                    if (times[i][1]-times[i][0]) > 0.2:           # If partial utterance is sufficient long,
                        #utter_part = utter[interval[0]:interval[1]]         # save first and last 180 frames of spectrogram.
                        S = librosa.core.stft(y=seg, n_fft=hp.data.nfft,
                                              win_length=int(hp.data.window * hp.data.sr), hop_length=int(hp.data.hop * hp.data.sr))
                        S = np.abs(S) ** 2
                        mel_basis = librosa.filters.mel(sr=hp.data.sr, n_fft=hp.data.nfft, n_mels=hp.data.nmels)
                        S = np.log10(np.dot(mel_basis, S) + 1e-6)           # log mel spectrogram of utterances
                        #samples = random.sample(S, 3 * hp.data.tisv_frame)
                        #first = samples[]
                        print("************************", S.shape)
                        #if(len(S) < 360):
                        #    print("less than 360", len(S))
                        #    continue
                        for i in range(0, S.shape[1] - hp.data.tisv_frame, hp.data.tisv_frame):
                            #print("Appending of shape", S[:, i * hp.data.tisv_frame: (i + 1) * hp.data.tisv_frame].shape)
                            utterances_spec.append(S[:, i * hp.data.tisv_frame: (i + 1) * hp.data.tisv_frame    ])
                        #utterances_spec.append(S[:, :hp.data.tisv_frame])    # first 180 frames of partial utterance
                        #utterances_spec.append(S[:, -hp.data.tisv_frame:])   # last 180 frames of partial utterance
                        #print("Shape of S", S[-2].shape, S[-1].shape)
                #concat_seg, concat_times = concat_segs(times, segs)
                #STFT_frames, STFT_times = get_STFTs(concat_seg, concat_times)
                #STFT_frames = np.stack(STFT_frames, axis=2)
                #STFT_frames = np.transpose(STFT_frames, axes=(2,1,0))

                #utter, sr = librosa.core.load(utter_path, hp.data.sr)        # load utterance audio
                #intervals = librosa.effects.split(utter, top_db=30)         # voice activity detection 
                # this works fine for timit but if you get array of shape 0 for any other audio change value of top_db
                # for vctk dataset use top_db=100
                """for interval in intervals:
                    if (interval[1]-interval[0]) > utter_min_len:           # If partial utterance is sufficient long,
                        utter_part = utter[interval[0]:interval[1]]         # save first and last 180 frames of spectrogram.
                        S = librosa.core.stft(y=utter_part, n_fft=hp.data.nfft,
                                              win_length=int(hp.data.window * sr), hop_length=int(hp.data.hop * sr))
                        S = np.abs(S) ** 2
                        mel_basis = librosa.filters.mel(sr=hp.data.sr, n_fft=hp.data.nfft, n_mels=hp.data.nmels)
                        S = np.log10(np.dot(mel_basis, S) + 1e-6)           # log mel spectrogram of utterances
                        utterances_spec.append(S[:, :hp.data.tisv_frame])    # first 180 frames of partial utterance
                        utterances_spec.append(S[:, -hp.data.tisv_frame:])   # last 180 frames of partial utterance
                """
        utterances_spec = np.array(utterances_spec)
        print("utterances_spec", utterances_spec.shape)
        if(utterances_spec.shape[0] == 0):
            continue
        #print(utterances_spec.shape)
        if i<train_speaker_num:      # save spectrogram as numpy file
            np.save(os.path.join(hp.data.train_path, "speaker%d.npy"%i), utterances_spec)
        else:
            np.save(os.path.join(hp.data.test_path, "speaker%d.npy"%(i-train_speaker_num)), utterances_spec)


if __name__ == "__main__":
    save_spectrogram_tisv()

