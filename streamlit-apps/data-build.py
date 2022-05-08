###########
# Imports #
###########
from sqlalchemy import create_engine
from pydub import AudioSegment
import streamlit as st
from math import floor
import pandas as pd
import numpy as np
import urllib
import pysrt
import os

st.set_page_config(page_title='Data Build', layout='wide')
st.title('Data Build')

####################
# Define Functions #
####################
def upload(dataframe, schema, table, exists='append'):
    conn_str = (
        r'Driver={ODBC Driver 17 for SQL Server};'
        r'Server=ZANGORTH;'
        r'Database=HomeBase;'
        'Trusted_Connection=yes;'
    )
    con = urllib.parse.quote_plus(conn_str)
    engine = create_engine(f'mssql+pyodbc:///?odbc_connect={con}')
    dataframe.to_sql(name=table, con=engine, schema=schema, if_exists=exists, index=False)

    return None

###########
# Options #
###########
sidebar = st.sidebar

if 'chdir' not in st.session_state:
    # Streamlit doesn't import your working directory so you have to manually set the project directory
    with sidebar.form('directory_form'):
        chdir = st.text_input('Working Directory:', 'C:/Users/Samuel/Google Drive/Portfolio/Voice Clone')
        directory_submit = st.form_submit_button()

    if directory_submit:
        os.chdir(chdir)
        st.session_state['chdir'] = True
        st.experimental_rerun()

elif 'panda' not in st.session_state:
    # Select the episode that you want to label
    with sidebar.form('episode_form'):
        source = st.selectbox('Data Source', os.listdir('video-clips/'))
        episode = st.selectbox('Episode', os.listdir(f'video-clips/{source}/'))
        episode_submit = st.form_submit_button()

    if episode_submit:
        # Pull in the transcript file
        transcript = pysrt.open(f'subtitles/{source}/{episode.replace(".mp4", ".srt")}')

        # Pull in the audio file
        audio_path = f'audio-clips/{source}/{episode.replace(".mp4", "")}/{episode.replace(".mp4", "-full-clip.wav")}'
        st.session_state['audio'] = AudioSegment.from_file(audio_path)

        panda = pd.DataFrame({'source': source,
                              'episode': episode.replace('-', ''),
                              'speaker': np.nan,
                              'start': [text.start.seconds + text.start.milliseconds / 1000 for text in transcript],
                              'end': [text.end.seconds + text.end.milliseconds / 1000 for text in transcript],
                              'text': [text.text for text in transcript]})

        st.session_state['panda'] = panda.copy()
        st.session_state['source'] = source
        st.session_state['episode'] = episode

        st.experimental_rerun()

####################
# Video/Transcript #
####################
elif 'submitted' not in st.session_state:
    episode = st.session_state['episode']
    source = st.session_state['source']

    current = st.session_state['panda'].loc[st.session_state['panda']['speaker'].isnull()].copy()
    next = {'start': current.iloc[1, 3], 'end': current.iloc[1, 4], 'text': current.iloc[1, 5]}
    current = {'start': current.iloc[0, 3], 'end': current.iloc[0, 4], 'text': current.iloc[0, 5]}

    current['text'] = current['text'].replace('\n', '')
    next['text'] = next['text'].replace('\n', '')

    st.write(f'Current ({current["start"]} - {current["end"]}): {current["text"]}')
    st.write(f'Next ({next["start"]} - {next["end"]}): {next["text"]}')

    character_list = ['Alador', 'Amity', 'Bat Queen', 'Boscha', 'Camila', 'Collector', 'Darius', 'Eda', 'Edric',
                      'Emira', 'Erroneous', 'Belos', 'Gus', 'Gwendolyn', 'Hooty', 'Hunter', 'Kikimora', 'King',
                      'Lilith', 'Luz', 'Odalia', 'Principal Bump', 'Raine', 'Steve', 'Vee', 'Willow']

    speaker = sidebar.selectbox('Speaker', character_list)

    left, right = sidebar.columns(2)
    speaker_submit = left.button('Submit')
    combine = right.button('Same Speaker?')

    # Assign a speaker to the text and save out the audio clip related to that text
    if speaker_submit:
        st.session_state['panda'].loc[st.session_state['panda']['start'] == current['start'], 'speaker'] = speaker

        audio = st.session_state['audio'][current['start']*1000:current['end']*1000]

        start_seconds = f'0000{floor(current["start"])}'[-4:]
        end_seconds = f'0000{floor(current["end"])}'[-4:]

        audio_path = f'audio-clips/{source}/{episode.replace(".mp4", "")}/'
        audio_path += episode.replace('.mp4', f'-seconds-{start_seconds}-{end_seconds}.wav')

        audio.export(audio_path, format='wav')

        st.experimental_rerun()

    # Sometimes the transcript splits the same sentence into two chunks, so we combine them here
    if combine:
        st.session_state['panda'].loc[st.session_state['panda']['start'] == current['start'], 'text'] = current['text'] + ' ' + next['text']
        st.session_state['panda'].loc[st.session_state['panda']['start'] == current['start'], 'end'] = next['end']
        st.session_state['panda'] = st.session_state['panda'].loc[st.session_state['panda']['start'] != next['start']]
        st.session_state['panda'] = st.session_state['panda'].reset_index(drop=True)

        st.experimental_rerun()

    submit = sidebar.button('Push Data to SQL?')

    to_upload = st.session_state['panda'].loc[st.session_state['panda']['speaker'].notnull()].copy()

    if submit:
        to_upload = st.session_state['panda'].loc[st.session_state['panda']['speaker'].notnull()].copy()
        upload(to_upload, schema='voiceclone', table=source)
        st.session_state['submitted'] = True

        st.experimental_rerun()

else:
    st.write('Data has been pushed to SQL; clear cache and rerun if you wish to proceed')


