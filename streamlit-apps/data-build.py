###########
# Imports #
###########
from pydub import AudioSegment
import streamlit as st
from math import floor
import pandas as pd
import numpy as np
import pysrt
import os

st.set_page_config(page_title='Data Build', layout='wide')
st.title('Data Build')

###########
# Options #
###########
sidebar = st.sidebar

if 'chdir' not in st.session_state:
    with sidebar.form('directory_form'):
        chdir = st.text_input('Working Directory:', 'C:/Users/Samuel/Google Drive/Portfolio/Voice Clone')
        directory_submit = st.form_submit_button()

    if directory_submit:
        st.session_state['chdir'] = chdir
        st.experimental_rerun()

elif 'panda' not in st.session_state:
    os.chdir(st.session_state['chdir'])

    with sidebar.form('episode_form'):
        source = st.selectbox('Data Source', os.listdir('video-clips/'))
        episode = st.selectbox('Episode', os.listdir(f'video-clips/{source}/'))
        episode_submit = st.form_submit_button()

    if episode_submit:
        transcript = pysrt.open(f'subtitles/{source}/{episode.replace(".mp4", ".srt")}')

        audio_path = f'audio-clips/{source}/{episode.replace(".mp4", "")}/{episode.replace(".mp4", "-full-clip.wav")}'
        st.session_state['audio'] = AudioSegment.from_file(audio_path)

        panda = pd.DataFrame({'start': [text.start.seconds + text.start.milliseconds / 1000 for text in transcript],
                              'end': [text.end.seconds + text.end.milliseconds / 1000 for text in transcript],
                              'text': [text.text for text in transcript],
                              'speaker': np.nan})

        st.session_state['panda'] = panda.copy()
        st.session_state['source'] = source
        st.session_state['episode'] = episode

        st.experimental_rerun()

####################
# Video/Transcript #
####################
else:
    episode = st.session_state['episode']
    source = st.session_state['source']

    st.dataframe(st.session_state['panda'])

    current = st.session_state['panda'].loc[st.session_state['panda']['speaker'].isnull()].copy()
    next = {'start': current.iloc[1, 0], 'end': current.iloc[1, 1], 'text': current.iloc[1, 2]}
    current = {'start': current.iloc[0, 0], 'end': current.iloc[0, 1], 'text': current.iloc[0, 2]}

    st.write(f'Current ({current["start"]} - {current["end"]}): {current["text"]}')
    st.write(f'Next ({next["start"]} - {next["end"]}): {next["text"]}')

    character_list = ['Alador', 'Amity', 'Bat Queen', 'Boscha', 'Camila', 'Collector', 'Darius', 'Eda', 'Edric',
                      'Emira', 'Erroneous', 'Belos', 'Gus', 'Gwendolyn', 'Hooty', 'Hunter', 'Kikimora', 'King',
                      'Lilith', 'Luz', 'Odalia', 'Principal Bump', 'Raine', 'Steve', 'Vee', 'Willow']

    speaker = sidebar.selectbox('Speaker', character_list)

    left, right = sidebar.columns(2)
    speaker_submit = left.button('Submit')
    combine = right.button('Same Speaker?')

    if speaker_submit:
        st.session_state['panda'].loc[st.session_state['panda']['start'] == current['start'], 'speaker'] = speaker

        audio = st.session_state['audio'][current['start']*1000:current['end']*1000]

        start_seconds = f'0000{floor(current["start"])}'[-4:]
        end_seconds = f'0000{floor(current["end"])}'[-4:]

        audio_path = f'audio-clips/{source}/{episode.replace(".mp4", "")}/'
        audio_path += episode.replace('.mp4', f'-seconds-{start_seconds}-{end_seconds}.wav')

        audio.export(audio_path, format='wav')

        st.experimental_rerun()

    if combine:
        st.session_state['panda'].loc[st.session_state['panda']['start'] == current['start'], 'text'] = current['text'] + ' ' + next['text']
        st.session_state['panda'].loc[st.session_state['panda']['start'] == current['start'], 'end'] = next['end']
        st.session_state['panda'] = st.session_state['panda'].loc[st.session_state['panda']['start'] != next['start']]
        st.session_state['panda'] = st.session_state['panda'].reset_index(drop=True)

        st.experimental_rerun()

    st.video(open(f'video-clips/{source}/{episode}', 'rb').read(), start_time=floor(current['start']))
