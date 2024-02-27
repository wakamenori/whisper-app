import time

from transcription_utils import TranscriptionWrapper

from reazonspeech.espnet.asr import TranscribeConfig, audio_from_path, load_model
from reazonspeech.espnet.asr import transcribe as reazon_transcribe


class ReazonSpeechWrapper:
    def __init__(self) -> None:
        self.model = load_model()

    def transcribe(self, file_path: str) -> TranscriptionWrapper:
        start_time = time.time()

        # 一時ファイルから音声を読み込み、APIに送信
        with open(file_path, "rb") as audio_file:
            ret = reazon_transcribe(self.model, audio_from_path(audio_file), TranscribeConfig(verbose=False))

        end_time = time.time()
        elapsed_time = end_time - start_time
        return TranscriptionWrapper(
            [{"text": segment.text, "no_speech_prob": None} for segment in ret.segments], elapsed_time
        )
