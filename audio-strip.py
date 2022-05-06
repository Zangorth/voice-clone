###########
# Imports #
###########
import moviepy.editor as mp
import os

source='owl-house'
##########################
# Strip Audio From Video #
##########################
if not os.path.isdir('audio-clips'):
    os.mkdir('audio-clips')

for episode in os.listdir(f'video-clips\\{source}'):
    video_file = mp.VideoFileClip(f'video-clips\\{source}\\{episode}')

    episode_name = episode.replace('.mp4', '')

    if not os.path.isdir(f"audio-clips\\{source}\\{episode_name}"):
        os.mkdir(f"audio-clips\\{source}\\{episode_name}")

    video_file.audio.write_audiofile(f'audio-clips\\{source}\\{episode_name}\\{episode_name}-full-clip.wav')
