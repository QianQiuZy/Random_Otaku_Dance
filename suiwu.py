import os
import random
import pygame
import time

def play_music(file_path):
    pygame.mixer.init()
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(10)

def main():
    music_folder = "随舞"
    countdown_file = "倒计时.mp3"
    music_files = [f for f in os.listdir(music_folder) if f.endswith(".mp3")]
    random.shuffle(music_files)
    for music_file in music_files:
        music_path = os.path.join(music_folder, music_file)
        play_music(music_path)
        countdown_path = os.path.join(os.getcwd(), countdown_file)
        play_music(countdown_path)
    print("所有歌曲播放完成。")
    os.system("pause")

if __name__ == "__main__":
    main()
