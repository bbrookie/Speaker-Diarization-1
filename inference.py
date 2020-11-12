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
        S = np.log10(np.dot(mel_basis, S) + 1e-6)           # log mel spectrogram of utterances
        print("S.shape", seg.shape, S.shape)
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
                #i = end_idx
                start = start_idx
                end = i + 1 if (i < (len(times) - 2)) else i
                limit = i + 1
                break
        if(start == end):
            print("Awkward Condition", times[i], times[i + 1] if i != (len(times) - 1) else "end")
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
    #print("Error")
    #print(times_partitions)
    #print("partitions")
    for i, partition in enumerate(partitions):
        #print(partition)
        #norms = [np.linalg.norm(e) for e in embeddings[partition[0]:partition[1]]]
        #avg_embeddings[i] = np.average(norms)
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
            print('No voice activity detected')
            return
        #print(times)
        #print("********************\nSegs:")
        #print([seg.shape for seg in segs], "\n***********************************\n")
        concat_seg, concat_times = concat_segs(times, segs); #print("\n\n*****\n", concat_times)
        print("length of concatednated segments", len(concat_seg), len(concat_times))
        print("concatenated segments", concat_seg)
        print()
        print("Concatenated times", concat_times)
        STFT_frames, STFT_times = get_STFTs(concat_seg, concat_times)
        STFT_frames = np.stack(STFT_frames, axis=2)
        STFT_frames = torch.tensor(np.transpose(STFT_frames, axes=(2,1,0)))
        print("STFT_frames dimensions", STFT_frames.shape, STFT_frames[0].shape, STFT_frames[1].shape)
        print("STFT_times dimensions", len(STFT_times))
        embeddings = run_model(STFT_frames, embedder_net)
        #print("This is it", len(embeddings), len(STFT_times))
        print(STFT_times)
        #print()
        aligned_embeddings,times = align_times(embeddings.detach().numpy(), STFT_times)
        #print("Aligned embeddings", aligned_embeddings.shape, len(STFT_frames), len(STFT_times))
        #print()
        #print(aligned_embeddings)
        #print()
        #print("Aligned Times", aligned_times)
        # Now that we have obtained the d-vectors, the next step to be done is Spectral Clustering 
        clusterer = SpectralClusterer(
            min_clusters=2,
            max_clusters=5,
            p_percentile=0.95,
            gaussian_blur_sigma=1)
        labels = clusterer.predict(aligned_embeddings)
        return labels, times

    else:
        raise Exception("Not a wav file")
   



if __name__ == "__main__":
    audio_path = sys.argv[1]
    labels, times = infer_one_file(audio_path)
    #for label in labels:
    #    #print(label)
    print(labels)
    print()
    print(times)
    start_t = times[0][0]
    end_t   = times[0][1]
    for i in range(1, len(times), 1):
        if (times[i][0] - times[i - 1][1] <= 0.03 and labels[i] == labels[i - 1]):
            end_t = times[i][1]
            if(i == len(times) - 1):
                print("Speaker", labels[i - 1], "from {start:.2f} to {end:.2f}".format(start = start_t, end = end_t))
        else:
            print("Speaker", labels[i - 1], "from {start:.2f} to {end:.2f}".format(start = start_t, end = end_t))
            start_t = times[i][0]
            end_t = times[i][1]

"""    print(labels.shape)

    i = 0
    label_start = 0
    labels_end = 0.40
    
    for i in range(1, len(labels), 1):
        if(labels[i] == labels[i - 1]):
            labels_end += 0.40
        else:
            print("Speaker", labels[i - 1], "from {start} to {end}".format(start = (label_start * 100) / 100, end = (labels_end * 100) / 100))
            label_start = i * 0.40
            labels_end = (i * 0.40) + 0.40
    
    print("Speaker", labels[i - 1], "from {start} to {end}".format(start = (label_start * 100) / 100, end = (labels_end * 100) / 100))
"""



