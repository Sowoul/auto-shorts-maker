import random
import asyncio
import edge_tts
from moviepy import AudioFileClip, TextClip, CompositeVideoClip, CompositeAudioClip
from moviepy.video.tools.subtitles import SubtitlesClip
from moviepy.video.io.VideoFileClip import VideoFileClip
import os
import srt
import moviepy.audio.fx as afx
from moviepy.video.fx import FadeOut
import re

def split_text(text, max_duration=60, words_per_minute=150 + 0.25*150):
    words = text.split()
    chunk_size = (max_duration * words_per_minute) // 60
    sentences = re.split(r'(?<=[.!?]) ', text)

    chunks = []
    current_chunk = []
    current_word_count = 0

    for sentence in sentences:
        sentence_words = sentence.split()
        if current_word_count + len(sentence_words) > chunk_size and current_chunk:
            chunks.append(" ".join(current_chunk))
            current_chunk = []
            current_word_count = 0
        current_chunk.extend(sentence_words)
        current_word_count += len(sentence_words)

    if current_chunk:
        chunks.append(" ".join(current_chunk))

    return chunks

async def generate_voice_and_subtitles(text, part, voice="en-US-AriaNeural"):
    audio_file = f"voice_part_{part}.mp3"
    srt_file = f"subtitles_part_{part}.srt"

    communicate = edge_tts.Communicate(text, voice, rate="+25%")
    cues = []

    with open(audio_file, "wb") as audio:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                end_timestamp = srt.timedelta(microseconds=(chunk["offset"] + chunk["duration"]) // 10)
                cue = srt.Subtitle(
                    index=len(cues) + 1,
                    start=srt.timedelta(microseconds=chunk["offset"] // 10),
                    end=end_timestamp,
                    content=chunk["text"]
                )
                cues.append(cue)

    with open(srt_file, "w", encoding="utf-8") as file:
        file.write(srt.compose(cues))

    return audio_file, srt_file

def render_video(text, background_video="vertical_3.mp4", output_prefix="output", voice="en-US-AriaNeural"):
    text_parts = split_text(text)

    for i, part in enumerate(text_parts):
        audio_file, srt_file = asyncio.run(generate_voice_and_subtitles(part, i))

        audio = AudioFileClip(audio_file)
        duration = audio.duration + 2
        video = VideoFileClip(background_video)
        max_start_time = max(0, video.duration - duration)
        start_time = random.uniform(0, max_start_time)
        video = video.subclipped(start_time, start_time + duration).with_effects([FadeOut(1)])

        font_path = "/usr/share/fonts/TTF/FiraCode-Regular.ttf"
        def generator(text):
            return TextClip(text=text, font=font_path, font_size=48, color='white', stroke_color="darkviolet", stroke_width=4)

        subtitles = SubtitlesClip(srt_file, make_textclip=generator, encoding="utf-8")
        background_audio = AudioFileClip("bg.mp3").subclipped(1, duration + 1).with_effects([afx.MultiplyVolume(0.33)])

        final_video = CompositeVideoClip([video, subtitles.with_position(('center'))])
        final_video = final_video.with_audio(CompositeAudioClip([background_audio, audio]))
        os.makedirs(output_prefix, exist_ok=True)
        output_video = os.path.join(output_prefix, f"(PART {i+1}) {output_prefix}.mp4")
        final_video.write_videofile(output_video, fps=24, codec='libx264', threads=16, preset='ultrafast')

        os.remove(audio_file)
        os.remove(srt_file)

if __name__ == "__main__":
    with open("text.txt",'r') as file:
        render_video(file.read(), output_prefix="output")
