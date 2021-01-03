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
import time

def concat_segs(times, segs):
    #Concatenate continuous voiced segments
    concat_seg = []
    concat_times = []
    seg_concat = segs[0]
    time_concat = [times[0][0], times[0][0]]
    for i in range(0, len(times)-1):
        if times[i][1] == times[i+1][0]:
            seg_concat = np.concatenate((seg_concat, segs[i+1]))
            time_concat[1] = times[i + 1][1]
        else:
            concat_seg.append(seg_concat)
            concat_times.append(time_concat)
            seg_concat = segs[i+1]
            time_concat = [times[i + 1][0], times[i + 1][0]]
    else:
        concat_seg.append(seg_concat)
        concat_times.append(time_concat)
    return concat_seg, concat_times

def get_STFTs(segs, times):
    #Get 240ms STFT windows with 50% overlap
    sr = hp.data.sr
    STFT_frames = []
    STFT_times = []
    for i, seg in enumerate(segs):
        S = librosa.core.stft(y=seg, n_fft=hp.data.nfft,
                              win_length=int(hp.data.window * sr), hop_length=int(hp.data.hop * sr))
        S = np.abs(S)**2
        mel_basis = librosa.filters.mel(sr, n_fft=hp.data.nfft, n_mels=hp.data.nmels)
        S = np.log10(np.dot(mel_basis, S) + 1e-6)        
        for j in range(0, S.shape[1], int(.12/hp.data.hop)):
            if j + 24 < S.shape[1]:
                STFT_frames.append(S[:,j:j+24])
                STFT_times.append([times[i][0] + (j / int(.12/hp.data.hop)) * .12, times[i][0] + .24 + (j / int(.12/hp.data.hop)) * .12])
            else:
                break
    return STFT_frames, STFT_times

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

def align_times(embeddings, times):
    partitions = []
    window = .401
    times_partitions = []
    start = 0
    end = 0
    j = 1
    start_time = times[0][0]
    end_time = times[0][1]
    limit = 0
    append_to_partitions = True
    for i in range(len(times)):
        append_to_partitions = True
        if(i <= limit and i != 0):
            continue
        start_idx = i
        while True:
            if(i < (len(times) - 1) and times[i][1] > times[i + 1][0] and times[i + 1][1] - times[start_idx][0] < window):
                i += 1

            elif(i < (len(times) - 1) and times[i][1] < times[i + 1][0]):
                if(len(partitions) > 0):
                    partitions[-1][1] = i
                    times_partitions[-1][1] = times[i][1]
                else:
                    partitions.append([start_idx, i])
                    times_partitions.append([times[0][0], times[0][1]])
                limit = i + 1
                append_to_partitions = False
                break
            
            else:
                start = start_idx
                end = i + 1 if (i < (len(times) - 2)) else i
                limit = i + 1
                break

        if(start == end):
            continue
        if(append_to_partitions == True):
            partitions.append([start,end])
            times_partitions.append([times[start][0], times[end][1]])
    else:
        if(times[-1][1] - times_partitions[1][0] < window and times[-1][1] < times_partitions[-1][1]):
            partitions[-1] = partitions[0][len(embeddings)]
            times_partitions[-1] = [times_partitions[-1][0], times[-1][1]]
        else:
            partitions.append([(len(times) - 2), len(times) - 1])
            times_partitions.append(times[-1])
    avg_embeddings = np.zeros((len(partitions), 256))
    for i, partition in enumerate(partitions):
        avg_embeddings[i] = np.average(embeddings[partition[0]:partition[1]],axis=0) 
    return avg_embeddings, times_partitions


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

            return

        concat_seg, concat_times = concat_segs(times, segs)

        STFT_frames, STFT_times = get_STFTs(concat_seg, concat_times)
        print(type(STFT_frames), type(STFT_times))
        STFT_frames = np.stack(STFT_frames, axis=2)
        STFT_frames = torch.tensor(np.transpose(STFT_frames, axes=(2,1,0)))

        embeddings = run_model(STFT_frames, embedder_net)

        aligned_embeddings,times = align_times(embeddings.detach().numpy(), STFT_times)

        print(aligned_embeddings.shape, aligned_embeddings[1].shape)
        clusterer = SpectralClusterer(
            min_clusters=2,
            max_clusters=5,
            p_percentile=0.96,
            gaussian_blur_sigma=1)
        labels = clusterer.predict(aligned_embeddings)
        return labels, times

    else:
        raise Exception("Not a wav file")
   



if __name__ == "__main__":
    audio_path = sys.argv[1]
    labels, times = infer_one_file(audio_path)
    start_t = times[0][0]
    end_t   = times[0][1]

    kaldi_comparision = True
    other_support = True
    if (kaldi_comparision):
        for i in range(1, len(times), 1):
            if (times[i][0] - times[i - 1][1] <= 0.03 and labels[i] == labels[i - 1]):
                end_t = times[i][1]
                if(i == len(times) - 1):
                    print("SPEAKER", audio_path[:-4], "0", " {start:.2f} to {duration:.2f} <NA> <NA> {id} <NA> <NA>".format(start = start_t, duration = end_t - start_t, id = labels[ i - 1]))
            else:
                print("SPEAKER", audio_path[:-4], "0", " {start:.2f} to {duration:.2f} <NA> <NA> {id} <NA> <NA>".format(start = start_t, duration = end_t - start_t, id = labels[ i - 1]))
                start_t = times[i][0]
                end_t = times[i][1]
       
    else:
        if(other_support):
            for i in range(1, len(times), 1):
                if (times[i][0] - times[i - 1][1] <= 0.03 and labels[i] == labels[i - 1]):
                    end_t = times[i][1]
                    if(i == len(times) - 1):
                        start_str = time.strftime('%H:%M:%S', time.gmtime(start_t))
                        start_str += ".{}".format(str(start_t).split('.')[1]) if str(start_t).find('.') > 0 else '.00'

                        end_str = time.strftime('%H:%M:%S', time.gmtime(end_t))
                        end_str += ".{}".format(str(end_t).split('.')[1]) if str(end_t).find('.') > 0 else '.00'

                        print(labels[i - 1], ",{start:.2f},{end:.2f}".format(start = start_str, end = end_str))
                else:
                    print(labels[i - 1], ",{start:.2f},{end:.2f}".format(start = start_t, end = end_t))
                    start_t = times[i][0]
                    end_t = times[i][1]            
        else:
            for i in range(1, len(times), 1):
                if (times[i][0] - times[i - 1][1] <= 0.03 and labels[i] == labels[i - 1]):
                    end_t = times[i][1]
                    if(i == len(times) - 1):
                        print("Speaker", labels[i - 1], "from {start:.2f} to {end:.2f}".format(start = start_t, end = end_t))
                else:
                    print("Speaker", labels[i - 1], "from {start:.2f} to {end:.2f}".format(start = start_t, end = end_t))
                    start_t = times[i][0]
                    end_t = times[i][1]
