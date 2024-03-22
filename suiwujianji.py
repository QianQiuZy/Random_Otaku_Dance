# code by 千秋紫莹，部分代码由ChatGPT Turbo 3.5编写和改进
# 导入所需的模块和库
import os
import random
import ffmpeg
import sys
from concurrent.futures import ThreadPoolExecutor

# 临时增加ffmpeg文件夹到PATH中以便调用
def add_folder_to_path(folder_name):
    current_dir = os.path.dirname(os.path.realpath(__file__))
    target_folder = folder_name
    folder_path = os.path.join(current_dir, target_folder)
    if os.path.exists(folder_path):
        sys.path.append(folder_path)

# 获取指定文件夹中的音频文件列表
def get_audio_files(folder):
    audio_files = []
    for file in os.listdir(folder):
        # 检查文件是否以 .mp3 或 .MP3 结尾
        if file.endswith('.mp3') or file.endswith('.MP3'):
            audio_files.append(os.path.join(folder, file))
    return audio_files

# 计算单个音频文件的时长
def calculate_duration(file):
    probe = ffmpeg.probe(file)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    return float(audio_stream['duration'])

# 计算所有音频文件的总时长
def calculate_total_duration(files):
    total_duration = 0
    with ThreadPoolExecutor() as executor:
        durations = list(executor.map(calculate_duration, files))
    total_duration = sum(durations)
    return total_duration

# 将秒数转换为分钟
def seconds_to_minutes(seconds):
    return seconds / 60.0

# 导出舞蹈顺序到文本文件
def export_dance_order(clips, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for clip in clips:
            dance_name = os.path.basename(clip).split()[0]
            f.write(dance_name + '\n')
    print(f"随舞顺序已导出到 {output_file}")

# 主函数
def suiwujianji():
    # 定义文件夹路径和文件名
    dance_folder = '随舞'
    countdown_file = '倒计时.mp3'
    output_file = '随舞.mp3'
    order_file = '顺序.txt'

    # 临时增加ffmpeg到PATH中以便调用
    add_folder_to_path("ffmpeg")

    # 获取音频文件列表
    dance_files = get_audio_files(dance_folder)
    
    # 检查是否找到音频文件
    if not dance_files:
        print("未找到音频文件。请确保'随舞'文件夹中包含至少一个音频文件")
        os.system("pause")
        return

    # 用户是否要打乱音频顺序
    user_shuffle = input("是否要打乱音频顺序？(y/n): ")
    if user_shuffle.lower() == 'y':
        random.shuffle(dance_files)

    # 创建剪辑队列，每个音频文件后面跟着一个倒计时文件
    clips = []
    for dance_file in dance_files:
        clips.append(dance_file)
        clips.append(countdown_file)

    # 去掉最后一个倒计时
    clips.pop()

    # 检查输出文件是否已存在，如果存在，则添加数字后缀
    output_file_name = output_file
    order_file_name = order_file
    counter = 1
    while os.path.exists(output_file_name):
        output_file_name = f'随舞{counter}.mp3'
        order_file_name = f'顺序{counter}.txt'
        counter += 1

    # 统计剪辑后音频文件的总时长
    total_duration = calculate_total_duration(clips)
    total_duration_minutes = seconds_to_minutes(total_duration)
    print(f"最终剪辑出来的总时长为: {total_duration_minutes:.2f} 分钟")

    # 用户是否要开始剪辑
    user_input = input("是否要开始剪辑？(y/n): ")
    if user_input.lower() != 'y':
        print("用户取消剪辑")
        os.system("pause")
        return

    # 使用ffmpeg进行音频剪辑
    try:
        (
            ffmpeg
            .input('concat:' + '|'.join(clips), format='mp3')
            .output(output_file_name, acodec='copy')
            .run(quiet=True)
        )
        print(f"剪辑完成，保存为 {output_file_name}")
        # 导出舞蹈顺序到文本文件
        export_dance_order(dance_files, order_file_name)
        os.system("pause")
    except ffmpeg.Error as e:
        print(f"剪辑过程中出现错误: {e.stderr}")
        os.system("pause")

if __name__ == "__main__":
    suiwujianji()
