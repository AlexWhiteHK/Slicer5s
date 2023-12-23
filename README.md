# 音频合并与切分工具
这个 Python 程序可以用来合并指定目录下的多个 WAV 文件，并将合并后的音频切分成时长均为 5 秒的小段。
## 安装依赖
在运行程序之前，请确保已经安装了以下依赖库：
- pydub
可以使用以下命令安装依赖库：
pip install pydub
## 使用方法
在命令行中运行以下指令来调用程序：
python merge_and_split_audio.py directory_path
- `merge_and_split_audio.py`：程序的主要 Python 脚本文件名。
- `directory_path`：包含要合并的 WAV 文件的目录路径。
合并和切分过程完成后，程序将在指定目录下创建一个名为 "segments" 的文件夹，并将切分后的音频段保存在其中。每个音频段的命名格式为 "segment_1.wav"，"segment_2.wav"，以此类推。
如果需要更改时长，可以直接编辑代码内容，1000ms=1s
## 注意事项
- 确保指定的目录路径包含有效的 WAV 文件。
- WAV 文件必须具有相同的采样率和声道数。
## 示例
合并和切分 WAV 文件的示例：
python merge_and_split_audio.py /path/to/wav/files
以上指令将合并 `/path/to/wav/files` 目录中的 WAV 文件，并将切分后的音频段保存在相应的目录。
## 贡献
如果你发现了任何问题，或者有任何改进的建议，欢迎提出 Issue 或者提交 Pull Request。
## 许可证
本项目使用 MIT 许可证。请查阅 [LICENSE](LICENSE) 文件了解详细信息。
