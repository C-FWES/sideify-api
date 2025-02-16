import numpy as np
import matplotlib.pyplot as plt
import wave
import scipy.signal as signal
import scipy.io.wavfile as wavfile
import pandas as pd


def get_wave_info(file_path):
    with wave.open(file_path, 'rb') as wav_file:
        n_channels = wav_file.getnchannels()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        n_frames = wav_file.getnframes()
        compression_type = wav_file.getcomptype()
        compression_name = wav_file.getcompname()

        duration = n_frames / framerate

        if sample_width == 1:
            bytenumber = np.int8
        if sample_width == 2:
            bytenumber = np.int16
        if sample_width == 3:
            bytenumber = np.int32 * 3
        if sample_width == 4:
            bytenumber = np.int32

        print("Number of channels:", n_channels)
        print("Sample width (bytes):", sample_width)
        print("Frame rate (samples per second):", framerate)
        print("Number of frames:", n_frames)
        print("Compression type:", compression_type)
        print("Compression name:", compression_name)
        print("Duration (seconds):", duration)

        data = wav_file.readframes(n_frames)

        return n_channels, sample_width, framerate, n_frames, duration, data, bytenumber


def rotation(input, deg):
    theta = deg * (np.pi) / 180  # convert input deg to rad, since all internal work done in rad

    R = np.array([[np.cos(theta), -np.sin(theta)],
                  [np.sin(theta), np.cos(theta)]])

    transformed = np.dot(input, R.T)  # MATRIX MUL
    return transformed


def reduce_frames(input, transformed, interval, degree):
    if (45 < degree < 135) or (225 < degree < 315):
        trigger = 1  # sort by y values if degree above 45 and equivalent
    else:
        trigger = 0

    sortedxaxis = np.argsort(transformed[:,
                             trigger])  # sort by low-->high y values, since this is 90 deg up. what to do if at say 37 deg? maybe just put an if statement for past 45deg
    transformed = transformed[sortedxaxis]

    df = pd.DataFrame(transformed, columns=["indices", "values"])
    df["block"] = (df.index // interval)
    # print("----")
    # print(df)
    dfcalculated = pd.DataFrame(columns=["indices", "values"])
    dfcalculated["indices"] = (df.groupby("block")["indices"].mean())
    dfcalculated["values"] = (df.groupby("block")["values"].sum())
    dfcalculated = dfcalculated.sort_values(by="indices")
    # print(dfcalculated)
    reduced_array = np.column_stack((dfcalculated["indices"], dfcalculated["values"]))

    return reduced_array


def show_plots(input, transformed, extra):
    plt.scatter(input[:, 0], input[:, 1])
    plt.scatter(transformed[:, 0], transformed[:, 1])
    plt.scatter(extra[:, 0], extra[:, 1])
    plt.legend(["input", "transformed", "extra"])
    plt.show()


def script(filename, degree=0.1):
    n_channels, sample_width, framerate, n_frames, duration, data, bytenumber = get_wave_info(filename)

    # Turn bytes --> pcm
    pcm = np.frombuffer(data, dtype=bytenumber)  # PCM data, derived from raw bytes

    # Turns 1d pcm --> 2d pcm which each item being [index, value]. This is our (x,y) coordinates
    pcm_indices = np.arange(pcm.size)
    original = np.column_stack((pcm_indices, pcm))

    # Rotates the (x,y) coordinates by the specified angle
    transformed_pcm_array = rotation(original, degree)  # INPUT, DEGREE

    original_distance = abs(pcm_indices.min()) + abs(pcm_indices.max())
    transformed_distance = abs(transformed_pcm_array[:, 0].min()) + abs(
        transformed_pcm_array[:, 0].max())  # even though its vertical, there are just as many x values as indices

    distance_ratio = original_distance / transformed_distance
    distance_ratio = round(distance_ratio)

    # print(f"before, after, ratio: {original_distance}, {transformed_distance}, {distance_ratio}")

    reduced_pcm_array = reduce_frames(original, transformed_pcm_array, distance_ratio,
                                      degree)  # reduce frames based on distance ratio

    # Turns 2d pcm --> 1d pcm
    reduced_pcm = reduced_pcm_array[:, 1]  # takes value column to convert back to 1d
    # print(reduced_pcm.min(),reduced_pcm.max())
    # print(f"frame count of reduced_pcm: {len(reduced_pcm)}")
    pcm_normalized = reduced_pcm / np.max(np.abs(reduced_pcm))
    pcm_normalized = bytenumber(pcm_normalized * framerate)

    def lowpass(data, cutoff, samplerate, type='lowpass'):
        sos = signal.butter(5, cutoff, type, fs=samplerate, output='sos')
        filtered_data = signal.sosfiltfilt(sos, data)
        return filtered_data

    modified_pcm = pcm_normalized  # applies filters in hopes of making it sound better (it doesnt)
    modified_pcm = lowpass(pcm_normalized, 20000, framerate)
    modified_pcm = lowpass(modified_pcm, 80, framerate, type='highpass')

    # Turns 1d pcm --> bytes
    modified_data = modified_pcm.astype(bytenumber).tobytes()
    # show_plots(original, reduced_pcm_array, transformed_pcm_array)
    # Creates .wav with bytes as data
    with wave.open("transformedouput.wav", mode="wb") as wav_file:
        wav_file.setnchannels(n_channels)
        wav_file.setsampwidth(sample_width)
        wav_file.setframerate(framerate)
        wav_file.writeframes(modified_data)


if __name__ == "__main__":
    filename = "intentionscover.wav"
    script(filename, 0.1)