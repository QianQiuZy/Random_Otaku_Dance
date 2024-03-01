# code by 千秋紫莹
import os
import random
import ffmpeg
from concurrent.futures import ThreadPoolExecutor

#读取文件
def get_audio_files(folder):
    audio_files = []
    for file in os.listdir(folder):
        if file.endswith('.mp3'):
            audio_files.append(os.path.join(folder, file))
    return audio_files

#读取每个音频的时长
def calculate_duration(file):
    probe = ffmpeg.probe(file)
    audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
    return float(audio_stream['duration'])

#计算总时长
def calculate_total_duration(files):
    total_duration = 0
    with ThreadPoolExecutor() as executor:
        durations = list(executor.map(calculate_duration, files))
    total_duration = sum(durations)
    return total_duration

#秒换分钟
def seconds_to_minutes(seconds):
    return seconds / 60.0

#获取名字导出顺序
def export_dance_order(clips, output_file):
    with open(output_file, 'w', encoding='utf-8') as f:
        for clip in clips:
            dance_name = os.path.basename(clip).split()[0]
            f.write(dance_name + '\n')
    print(f"随舞顺序已导出到 {output_file}")

#主函数
def suiwujianji():
    dance_folder = '随舞'
    countdown_file = '倒计时.mp3'
    output_file = '随舞.mp3'
    order_file = '顺序.txt'

    dance_files = get_audio_files(dance_folder)
    
    if not dance_files:
        print("未找到音频文件。请确保'随舞'文件夹中包含至少一个音频文件")
        os.system("pause")        
        return

    #打乱音频顺序
    random.shuffle(dance_files)

    #创建剪辑队列
    clips = []
    for dance_file in dance_files:
        clips.append(dance_file)
        clips.append(countdown_file)

    #去掉最后一个倒计时
    clips.pop()

    #统计时长
    total_duration = calculate_total_duration(clips)
    total_duration_minutes = seconds_to_minutes(total_duration)
    print(f"最终剪辑出来的总时长为: {total_duration_minutes:.2f} 分钟")

    user_input = input("是否要开始剪辑？(y/n): ")
    if user_input.lower() != 'y':
        print("用户取消剪辑")
        os.system("pause")        
        return

    #使用ffmpeg剪辑
    try:
        (
            ffmpeg
            .input('concat:' + '|'.join(clips), format='mp3')
            .output(output_file, acodec='copy')
            .run()
        )
        print(f"剪辑完成，保存为 {output_file}")
        export_dance_order(dance_files, order_file)
        os.system("pause")
    except ffmpeg.Error as e:
        print(f"剪辑过程中出现错误: {e.stderr}")
        os.system("pause")

if __name__ == "__main__":
    suiwujianji()
