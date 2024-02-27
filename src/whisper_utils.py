# from faster_whisper import WhisperModel
import time

import openai
from dotenv import load_dotenv
from transcription_utils import TranscriptionWrapper

load_dotenv()

client = openai.Client()


class WhisperModelWrapper:
    def transcribe(self, file_path: str) -> TranscriptionWrapper:
        start_time = time.time()  # 処理開始時間を記録

        # 一時ファイルから音声を読み込み、APIに送信
        with open(file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                language="ja",
            )

        end_time = time.time()  # 処理終了時間を記録
        elapsed_time = end_time - start_time  # 経過時間を計算
        # print(f"処理にかかった時間: {elapsed_time:.2f}秒")  # 経過時間を表示
        return TranscriptionWrapper(
            transcript.segments,
            elapsed_time,
        )
