# Speaker-Diarization

[//]: # (Image References)
[logo]: ./Images/logo.png
[diarization_sample]: ./Images/diarization_sample.png

## Overview

![alt text][logo]

Speaker diarization is a a solution to the "Who spoke When" problem. It doesn't address the problem of speaker seperation nor speaker change problems. The solution implemented in this repository is the Google's Speaker Diarization with LSTM. It's an offline Diarization system, which means that it takes the whole utterance and then runs diarization on it.

## Steps performed by the pipeline

1. Voice segments are detected and segmented using VAD.
2. Contingous segments are concatenated into one segment.
3. Frequency Spectrun is then obtained using STFT.
4. The spectrun is devided into 240ms windows with a 120ms shift between every two windows.
5. These windows are infered through the LSTM model to get the D-Vectors.
6. Windows and times of 400 ms are obtained.
7. Windows are preprocessed and then are clustered using offline spectral clustering.

The output can be visualized using a GUI made to diarize and play the diarized results. A non-GUI results can also be obtained in two formates:

1. Kaldi format (Used later for comparison with kaldi results)
2. normal formats.

---

## LSTM Model

A huge part of the solution implemented is depenent on the D-Vectors method. It's a method that gets encoding of utterances depending on Deep neural networks, hence the name D-Vectors. For more info about the D-vectors please refer to the original [paper](https://arxiv.org/abs/1710.10468) proposed by google. The dataset used were TIMIT plus an additional 100 speakers from a private dataset.

### To Train the dataset

#### To Preprocess the data

run `python data_preprocess.py`

#### To train the model

1. Make sure that the training parameter in the config/config.yaml is set to true `training: !!bool "true"`
2. run `python train_speech_embedder.py`

### Inference

To infer and get the D-vectors:

1. Make sure that the training parameter in the config/config.yaml is set to true `training: !!bool "false"`
2. run `python infer.py`

### GUI

To use a simple and easy to use GUI for the diarization problem:

1. Run `python Speaker_viz.py`
2. Press file and then open.
3. Select the desired `.wav` file.

The GUI will get a result like this:

![alt text][diarization_sample]

## Dependencies

### Diarization Dependencies

If you want to use the diarization without GUI, the following dependencies have to exist in your environment:

1. Pytorch
2. numpy
3. librosa
4. simpleaudio
5. hparam
6. pydub

If you want to use the GUI, you should have the following dependencies in addition to the previous ones.

1. gi
2. GTK
3. matplotlib

The python version used in the repository is python 3.8
