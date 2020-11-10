"""
Created on Wed Nov 1 2020

@author: Mahmoud-Selim
Repo: https://github.com/Mahmoud-Selim/Speaker-Diarization.git
"""
import glob
import os
import librosa
import numpy as np
import sys
from hparam import hparam as hp
from speech_embedder_net import SpeechEmbedder, GE2ELoss, get_centroids, get_cossim
from VAD_segments import VAD_chunk
from spectralcluster import SpectralClusterer
import torch

def concat_segs(times, segs):
    #Concatenate continuous voiced segments
    concat_seg = []
    seg_concat = segs[0]
    for i in range(0, len(times)-1):
        if times[i][1] == times[i+1][0]:
            seg_concat = np.concatenate((seg_concat, segs[i+1]))
        else:
            concat_seg.append(seg_concat)
            seg_concat = segs[i+1]
    else:
        concat_seg.append(seg_concat)
    return concat_seg

def get_STFTs(segs):
    #Get 240ms STFT windows with 50% overlap
    sr = hp.data.sr
    STFT_frames = []
    for seg in segs:
        S = librosa.core.stft(y=seg, n_fft=hp.data.nfft,
                              win_length=int(hp.data.window * sr), hop_length=int(hp.data.hop * sr))
        S = np.abs(S)**2
        mel_basis = librosa.filters.mel(sr, n_fft=hp.data.nfft, n_mels=hp.data.nmels)
        S = np.log10(np.dot(mel_basis, S) + 1e-6)           # log mel spectrogram of utterances
        for j in range(0, S.shape[1], int(.12/hp.data.hop)):
            if j + 24 < S.shape[1]:
                STFT_frames.append(S[:,j:j+24])
            else:
                break
    return STFT_frames

def align_embeddings(embeddings):
    partitions = []
    start = 0
    end = 0
    j = 1
    for i, embedding in enumerate(embeddings):
        if (i*.12)+.24 < j*.401:
            end = end + 1
        else:
            partitions.append((start,end))
            start = end
            end = end + 1
            j += 1
    else:
        partitions.append((start,end))
    avg_embeddings = np.zeros((len(partitions),256))
    for i, partition in enumerate(partitions):
        avg_embeddings[i] = np.average(embeddings[partition[0]:partition[1]],axis=0) 
    return avg_embeddings

def init_model(model_path):
    embedder_net = SpeechEmbedder()
    embedder_net.load_state_dict(torch.load(model_path))
    embedder_net.eval()
    return embedder_net

def run_model(X, embedder_net):
    embeddings = embedder_net(X)
    return embeddings

def infer_one_file(wav):
    embedder_net = init_model('model.model')

    if wav[-4:] == '.WAV' or wav[-4:] == '.wav':
        times, segs = VAD_chunk(2, wav)
        if segs == []:
            print('No voice activity detected')
            return
        print(segs)
        concat_seg = concat_segs(times, segs)
        STFT_frames = get_STFTs(concat_seg)
        STFT_frames = np.stack(STFT_frames, axis=2)
        STFT_frames = torch.tensor(np.transpose(STFT_frames, axes=(2,1,0)))
        embeddings = run_model(STFT_frames, embedder_net)
        aligned_embeddings = align_embeddings(embeddings.detach().numpy())
        
        # Now that we have obtained the d-vectors, the next step to be done is Spectral Clustering 
        clusterer = SpectralClusterer(
            min_clusters=2,
            max_clusters=3,
            p_percentile=0.95,
            gaussian_blur_sigma=1)
        labels = clusterer.predict(aligned_embeddings)
        return labels

    else:
        raise Exception("Not a wav file")
   



if __name__ == "__main__":
    audio_path = sys.argv[1]
    labels = infer_one_file(audio_path)
    print(labels)
    print()
    print(labels.shape)

    i = 0
    label_start = 0
    labels_end = 0.4
    
    for i in range(1, len(labels), 1):
        if(labels[i] == labels[i - 1]):
            labels_end += 0.4
        else:
            print("Speaker", labels[i - 1], "from {start} to {end}".format(start = (label_start * 100) / 100, end = (labels_end * 100) / 100))
            label_start = i * 0.4
            labels_end = (i * 0.4) + 0.4
    
    print("Speaker", labels[i - 1], "from {start} to {end}".format(start = (label_start * 100) / 100, end = (labels_end * 100) / 100))


