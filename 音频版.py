# code by 千秋紫营，部分代码由ChatGPT 4o编写和改进
# 导入所需的模块和库
import os
import random
import ffmpeg
import json
import sys
from concurrent.futures import ThreadPoolExecutor
import subprocess
import re

# 当前的JSON文件用于存储音频的时长信息
duration_cache_file = "duration_cache.json"

# 读取JSON时长信息
def load_duration_cache():
    if os.path.exists(duration_cache_file):
        with open(duration_cache_file, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}

# 写入JSON时长信息
def save_duration_cache(cache):
    with open(duration_cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

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

# 更新文件列表的时长信息
def update_duration_cache(files, cache):
    with ThreadPoolExecutor() as executor:
        for file in files:
            if file not in cache:
                cache[file] = calculate_duration(file)

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

# 检测音频中的大段静音并重新编码
def audio_silent(input_file, clips, silence_threshold=-30, silence_duration=2.0, reencode=False):

    print(f"检测静音段: {input_file}")
    
    try:
        # 使用 ffmpeg-python 的 filter 来应用 silencedetect
        # 设置 loglevel 为 'warning' 以减少输出，但仍捕获 silencedetect 信息
        process = (
            ffmpeg
            .input(input_file)
            .filter('silencedetect', noise=f'{silence_threshold}dB', d=silence_duration)
            .output('null', format='null')
            .global_args('-loglevel', 'warning')  # 设置日志级别
            .run(capture_stdout=True, capture_stderr=True, quiet=True)
        )
    except ffmpeg.Error as e:
        output = e.stderr.decode('utf-8')
    else:
        output = process[1].decode('utf-8')  # 捕获 stderr

    # 解析静音检测结果
    silence_starts = re.findall(r'silence_start: (\d+(\.\d+)?)', output)
    silence_ends = re.findall(r'silence_end: (\d+(\.\d+)?)', output)
    
    # 判断是否存在大于等于 silence_duration 的静音
    has_long_silence = False
    silence_pattern = re.compile(r'silence_start: (\d+(\.\d+)?)')
    for line in output.split('\n'):
        match_start = silence_pattern.search(line)
        if match_start:
            start_time = float(match_start.group(1))
            # 查找对应的 silence_end
            end_match = re.search(r'silence_end: (\d+(\.\d+)?)', line)
            if end_match:
                end_time = float(end_match.group(1))
                duration = end_time - start_time
                if duration >= silence_duration:
                    has_long_silence = True
                    break

    if has_long_silence:
        print(f"检测到大于等于 {silence_duration} 秒的静音段。需要重新编码。")
        if not reencode:
            # 定义重新编码后的文件名
            base, ext = os.path.splitext(input_file)
            reencoded_file = f"{base}_reencoded{ext}"
            
            # 重新编码并重新剪辑音频文件
            try:
                (
                    ffmpeg
                    .input('concat:' + '|'.join(clips))
                    .output(reencoded_file, acodec='libmp3lame', audio_bitrate='128k')
                    .global_args('-loglevel', 'error')  # 仅显示错误信息
                    .run(quiet=True)
                )
                print(f"重新编码并剪辑完成，保存为 {reencoded_file}")
                
                # 删除原始文件
                os.remove(input_file)
                print(f"删除原始文件: {input_file}")
                
                # 递归检测重新编码后的文件，防止无限循环
                return audio_silent(reencoded_file, clips, silence_threshold, silence_duration, reencode=True)
            except ffmpeg.Error as e:
                print(f"重新编码过程中出现错误: {e.stderr.decode('utf-8', errors='replace')}")
                return input_file
        else:
            print("已经重新编码过，跳过进一步处理。")
            return input_file
    else:
        print("未检测到大段静音。无需重新编码。")
        return input_file

# 主函数
def suiwujianji():
    # 定义文件夹路径和文件名
    dance_folder = '随舞'
    countdown_file = '倒计时.mp3'
    output_file = '随舞.mp3'
    order_file = '顺序.txt'
    music_library_folder = '曲库'

    # 读取时长信息
    duration_cache = load_duration_cache()

    # 获取曲库文件夹中的音频文件列表并更新缓存
    library_files = get_audio_files(music_library_folder)
    update_duration_cache(library_files, duration_cache)
    save_duration_cache(duration_cache)

    # 获取随舞文件夹中的音频文件列表
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

    # 统计剪辑后音频文件的总时长（遍历JSON寻找文件名匹配的时长，如果找不到则使用ffprobe重新计算）
    total_duration = 0
    for clip in clips:
        clip_name = os.path.basename(clip)
        matching_key = next((key for key in duration_cache if os.path.basename(key) == clip_name), None)
        if matching_key:
            total_duration += duration_cache[matching_key]
        else:
            # 如果缓存中没有对应时长，则重新计算并更新缓存
            duration = calculate_duration(clip)
            duration_cache[clip] = duration
            total_duration += duration

    # 保存更新后的时长信息
    save_duration_cache(duration_cache)
    total_duration_minutes = seconds_to_minutes(total_duration)
    print(f"最终剪辑出来的总时长为: {total_duration_minutes:.2f} 分钟")

    # 检查输出文件是否已存在，如果存在，则添加数字后缀
    output_file_name = output_file
    order_file_name = order_file
    counter = 1
    while os.path.exists(output_file_name):
        output_file_name = f'随舞{counter}.mp3'
        order_file_name = f'顺序{counter}.txt'
        counter += 1

    # 用户是否要开始剪辑
    user_input = input("是否要开始剪辑？(y/n): ")
    if user_input.lower() != 'y':
        print("用户取消剪辑")
        os.system("pause")
        return

    # 使用ffmpeg进行音频剪辑（非编码模式）
    try:
        (
            ffmpeg
            .input('concat:' + '|'.join(clips))
            .output(output_file_name, acodec='copy')
            .global_args('-loglevel', 'error')  # 仅显示错误信息
            .run(quiet=True)
        )
        print(f"剪辑完成，保存为 {output_file_name}")
        
        # 调用 audio_silent 函数检测并处理静音
        processed_file = audio_silent(output_file_name, clips)
        
        # 如果音频被重新编码，更新 output_file_name
        if processed_file != output_file_name:
            output_file_name = processed_file

        # 导出舞蹈顺序到文本文件
        export_dance_order(dance_files, order_file_name)
        os.system("pause")
    except ffmpeg.Error as e:
        # 处理ffmpeg错误并确保输出信息
        try:
            print(f"剪辑过程中出现错误: {e.stderr.decode('utf-8', errors='replace')}")
        except AttributeError:
            print("剪辑过程中出现错误，但无法获取详细信息")
        os.system("pause")

if __name__ == "__main__":
    try:    
        suiwujianji()
    except KeyboardInterrupt:
        print("程序已中断")
        sys.exit(0)
