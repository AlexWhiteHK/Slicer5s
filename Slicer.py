import os
import argparse
from pydub import AudioSegment

def merge_wav_files(directory):
    if not os.path.isdir(directory):
        print("Invalid directory path.")
        return

    wav_files = [file for file in os.listdir(directory) if file.endswith(".wav")]
    if not wav_files:
        print("No WAV files found in the specified directory.")
        return

    merged_audio = AudioSegment.empty()
    for file in wav_files:
        file_path = os.path.join(directory, file)
        audio = AudioSegment.from_wav(file_path)
        merged_audio += audio

    segment_length = 5000  # 5秒，单位为毫秒
    segments = [
        merged_audio[i : i + segment_length]
        for i in range(0, len(merged_audio), segment_length)
    ]

    output_directory = os.path.join(directory, "segments")
    os.makedirs(output_directory, exist_ok=True)
    for i, segment in enumerate(segments):
        output_file = os.path.join(output_directory, f"segment_{i + 1}.wav")
        segment.export(output_file, format="wav")

    print("音频切分完成。")

def main():
    parser = argparse.ArgumentParser(description="将指定目录下的WAV文件合并并切分为5秒的小段")
    parser.add_argument("directory", help="WAV文件所在的目录路径")
    args = parser.parse_args()

    directory_path = args.directory
    merge_wav_files(directory_path)

if __name__ == "__main__":
    main()