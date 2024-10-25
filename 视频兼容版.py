import os
import random
import ffmpeg
import subprocess
from concurrent.futures import ThreadPoolExecutor
import time

# 获取指定文件夹中的视频文件列表
def get_video_files(folder):
    video_files = []
    for file in os.listdir(folder):
        # 检查文件是否以 .mp4 或 .MP4 结尾
        if file.endswith('.mp4') or file.endswith('.MP4'):
            video_files.append(os.path.join(folder, file))
    return video_files

# 计算单个视频文件的时长
def calculate_duration(file):
    probe = ffmpeg.probe(file)
    video_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'video'), None)
    return float(video_stream['duration'])

# 计算所有视频文件的总时长
def calculate_total_duration(files):
    total_duration = 0
    with ThreadPoolExecutor(max_workers=10) as executor:
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

# 检测是否有硬件加速器可用，并返回编码器的名称
def detect_hardware_encoder():
    try:
        result = subprocess.run(['ffmpeg', '-hide_banner', '-hwaccels'], capture_output=True, text=True)
        output = result.stdout
        if 'qsv' in output:
            return 'h264_qsv'  # 英特尔QSV
        elif 'cuda' in output or 'nvenc' in output:
            return 'h264_nvenc'  # 英伟达NVENC
        elif 'vdpau' in output or 'vce' in output:
            return 'h264_amf'  # AMD VCE
        else:
            return 'libx264'  # 使用软件编码
    except Exception as e:
        print(f"硬件加速检测失败喵，只能使用软解了喵: {str(e)}")
        return 'libx264'  # 如果检测失败，则使用软件编码

# 估计输出进度（每秒检查一次文件大小）
def estimate_progress(output_file, total_duration_seconds):
    start_time = time.time()
    total_size = 0

    print("开始进度监控...")

    while not os.path.exists(output_file):  # 等待文件生成
        time.sleep(1)

    while total_size == 0:  # 等待文件有大小
        total_size = os.path.getsize(output_file)
        time.sleep(1)

    while True:
        current_size = os.path.getsize(output_file)
        elapsed_time = time.time() - start_time
        
        if elapsed_time > 0:  # 防止除以0
            estimated_duration = (current_size / total_size) * total_duration_seconds
            progress = min((elapsed_time / estimated_duration) * 100, 100)
            print(f"进度: {progress:.2f}%/n正在编码ing此过程消耗时间较长，请不要着急喵~")
        
        time.sleep(0.5)
        if progress >= 100:
            print("视频处理完成！感谢耐心等待喵~")
            time.sleep(1)
            break

# 主函数
def suiwujianji():
    # 定义文件夹路径和文件名
    dance_folder = '随舞'
    countdown_folder = '倒计时'
    output_file = '随舞.mp4'
    order_file = '顺序.txt'

    # 获取视频文件列表
    dance_files = get_video_files(dance_folder)
    
    # 检查是否找到视频文件
    if not dance_files:
        print("未找到视频文件。请确保'随舞'文件夹中包含至少一个视频文件")
        os.system("pause")
        return

    # 获取倒计时文件
    countdown_files = get_video_files(countdown_folder)
    
    # 检查倒计时文件夹是否包含且仅包含一个倒计时文件
    if len(countdown_files) != 1:
        print(f"倒计时文件夹中有 {len(countdown_files)} 个倒计时文件喵，请确保该文件夹中仅包含一个倒计时视频文件")
        os.system("pause")
        return

    countdown_file = countdown_files[0]

    # 用户是否要打乱视频顺序
    user_shuffle = input("是否要打乱视频顺序？(y/n): ")
    if user_shuffle.lower() == 'y':
        random.shuffle(dance_files)

    # 创建剪辑队列，每个视频文件后面跟着一个倒计时文件
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
        output_file_name = f'随舞{counter}.mp4'
        order_file_name = f'顺序{counter}.txt'
        counter += 1

    # 统计剪辑后视频文件的总时长
    total_duration = calculate_total_duration(clips)
    total_duration_minutes = seconds_to_minutes(total_duration)
    print(f"最终剪辑出来的总时长为: {total_duration_minutes:.2f} 分钟")

    # 用户是否要开始剪辑
    user_input = input("是否要开始剪辑？(y/n): ")
    if user_input.lower() != 'y':
        print("用户取消剪辑")
        os.system("pause")
        return

    # 检测硬件加速器并选择编码器
    encoder = detect_hardware_encoder()
    print(f"使用的编码器: {encoder}，加速喵！")

    # 使用ffmpeg进行视频剪辑和重新编码
    try:
        # 使用 ffmpeg 命令行实现视频合并、重新编码并静默运行
        input_files = '|'.join(clips)
        
        # 开始进度监控线程
        print(f"剪辑处理中，输出文件为: {output_file_name}")
        progress_thread = ThreadPoolExecutor().submit(estimate_progress, output_file_name, total_duration)
        
        process = (
            ffmpeg
            .input(f'concat:{input_files}', format='concat', safe=0)
            .output(output_file_name, vcodec=encoder, acodec='aac', video_bitrate='2500k')
            .run(quiet=True)  # 静默运行，避免输出信息
        )
        
        # 等待进度监控结束
        progress_thread.result()

        print(f"剪辑完成，保存为 {output_file_name}")
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
    suiwujianji()
