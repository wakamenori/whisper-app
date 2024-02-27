import asyncio
import os
import queue
import tempfile
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import pyaudio
from audio_utils import create_audio_stream
from scipy.io import wavfile
from transcription_utils import ReazonTranscriber, WhisperTranscriber
from vad_utils import VadWrapper


def write_into_file(text: str, file_path: str) -> None:
    with open(file_path, "a") as f:
        f.write("\n" + text)


class AudioTranscriber:
    def __init__(self) -> None:
        self.model_wrapper = WhisperTranscriber()
        self.vad_wrapper = VadWrapper()
        self.silent_chunks = 0
        self.speech_buffer: list = []
        self.audio_queue: queue.Queue[np.ndarray] = queue.Queue()
        self.reazon_speech_wrapper = ReazonTranscriber()

    async def transcribe_audio(self) -> None:
        with ThreadPoolExecutor() as executor:
            while True:
                audio_data_np = await asyncio.get_event_loop().run_in_executor(executor, self.audio_queue.get)

                audio = np.int16(audio_data_np / np.max(np.abs(audio_data_np)) * 32767)
                sample_rate = 16000
                with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmpfile:
                    wavfile.write(tmpfile.name, sample_rate, audio)
                    temp_audio_file_path = tmpfile.name

                reazon_result = await asyncio.get_event_loop().run_in_executor(
                    executor, self.reazon_speech_wrapper.transcribe, temp_audio_file_path
                )

                whisper_result = await asyncio.get_event_loop().run_in_executor(
                    executor, self.model_wrapper.transcribe, temp_audio_file_path
                )
                os.unlink(temp_audio_file_path)

                if whisper_result.avg_no_speech_prob is not None and whisper_result.avg_no_speech_prob < 0.5:
                    write_into_file(whisper_result.joined_text, "src/log/whisper.log")
                    write_into_file(reazon_result.joined_text, "src/log/reazon.log")

                    print("\033[31m" + f"REAZON: {reazon_result.joined_text}" + "\033[0m")
                    print("\033[32m" + f"WHISPER: {whisper_result.joined_text}" + "\033[0m")

    def process_audio(self, in_data, frame_count, time_info, status) -> tuple[bytes, int]:  # type: ignore
        is_speech = self.vad_wrapper.is_speech(in_data)

        if is_speech:
            self.silent_chunks = 0
            audio_data = np.frombuffer(in_data, dtype=np.int16)
            self.speech_buffer.append(audio_data)
        else:
            self.silent_chunks += 1

        if not is_speech and self.silent_chunks > self.vad_wrapper.SILENT_CHUNKS_THRESHOLD:
            if len(self.speech_buffer) > 20:
                audio_data_np = np.concatenate(self.speech_buffer)
                self.speech_buffer.clear()
                self.audio_queue.put(audio_data_np)
            else:
                # noise clear
                self.speech_buffer.clear()

        return (in_data, pyaudio.paContinue)

    def start_transcription(self, selected_device_index: int) -> None:
        stream = create_audio_stream(selected_device_index, self.process_audio)
        print("Listening...")
        asyncio.run(self.transcribe_audio())
        stream.start_stream()
        try:
            while True:
                key = input("Enterキーを押したら終了します\n")
                if not key:
                    break
        except KeyboardInterrupt:
            print("Interrupted.")
        finally:
            stream.stop_stream()
            stream.close()
