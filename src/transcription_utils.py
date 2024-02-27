import difflib
import json
import time
from typing import TypedDict

from dotenv import load_dotenv
from furigana_utils import add_furigana_to_text
from openai import Client

from reazonspeech.espnet.asr import TranscribeConfig, audio_from_path, load_model
from reazonspeech.espnet.asr import transcribe as reazon_transcribe

load_dotenv()

client = Client()


class Segment(TypedDict):
    text: str
    no_speech_prob: float | None


class TranscriptionWrapper:
    avg_no_speech_prob: float | None
    transcription_execution_time: float | None
    segments: list[Segment]
    joined_text: str

    def __init__(self, segments: list[Segment], transcription_execution_time: float | None = None):
        self.segments = segments
        self.transcription_execution_time = transcription_execution_time

        if len(segments) == 0:
            self.avg_no_speech_prob = None
        elif "no_speech_prob" in segments[0].keys() and segments[0]["no_speech_prob"] is not None:
            self.avg_no_speech_prob = sum(
                [segment["no_speech_prob"] for segment in segments]  # type: ignore
            ) / len(segments)
        else:
            self.avg_no_speech_prob = None

        self.joined_text = "".join([segment["text"] for segment in segments]).replace("\n", "")

    # def correct_transcription(self) -> str:
    #     """修正前の文字起こしの結果を修正する

    #     Returns:
    #         str: 修正後の文字起こしの結果
    #     """

    #     texts = ""
    #     for segment in self.segments:
    #         if segment["no_speech_prob"] is not None and segment["no_speech_prob"] < 0.5:
    #             texts += segment["text"] + "\n"
    #     texts = "\n".join([segment["text"] for segment in self.segments if segment["no_speech_prob"] < 0.5])

    #     texts_with_furigana = add_furigana_to_text(texts)
    #     corrected_texts = correct_transcription_with_gpt(texts_with_furigana)

    #     if corrected_texts == texts_with_furigana:
    #         corrected_texts = texts

    #     self.corrected_transcript = corrected_texts
    #     diff = difflib.unified_diff(texts.split("\n"), corrected_texts.split("\n"))
    #     diff_str = "\n".join(diff)
    #     if len(diff_str) > 0:
    #         return diff_str
    #     else:
    #         return texts


class WhisperTranscriber:
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

        return TranscriptionWrapper(
            transcript.segments,
            elapsed_time,
        )


class ReazonTranscriber:
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


# def correct_transcription_with_gpt(transcription: str) -> str:
#     """文字起こしの結果を修正する

#     Args:
#         transcription (str): 文字起こしの結果

#     Returns:
#         str: 修正後の文字起こしの結果
#     """
#     system_message = """You are a helpful assistant. 
# Your task is to correct any spelling discrepancies in the transcribed text. 
# Furigana represents pronunciation, so please give it importance. omit furigana

# ```json
# {
#     "is_error": boolean, # 文章の意味が伝わらない場合はtrue
#     "corrected_transcription": string | null # 修正後の文字起こしの結果 (is_errorがfalseの場合はnull)
# }
# ```"""
#     response = client.chat.completions.create(
#         model="gpt-4-turbo-preview",
#         messages=[
#             {"role": "system", "content": system_message},
#             {"role": "user", "content": transcription},
#         ],
#         response_format={"type": "json_object"},
#     )

#     data = response.choices[0].message.content
#     data = json.loads(data)
#     if data["is_error"]:
#         return data["corrected_transcription"]
#     else:
#         return transcription


# def merge_transcription_results(
#     whisper_result: TranscriptionWrapper, reazon_result: TranscriptionWrapper
# ) -> TranscriptionWrapper:
#     """文字起こしの結果をマージする

#     Args:
#     whisper_result (TranscriptionWrapper): WhisperModelWrapperの文字起こしの結果
#     reason_result (TranscriptionWrapper): ReazonSpeechWrapperの文字起こしの結果

#     Returns:

#     TranscriptionWrapper: マージされた文字起こしの結果
#     """
#     whisper_result_with_furigana = add_furigana_to_text(whisper_result.joined_text)
#     reazon_result_with_furigana = add_furigana_to_text(reazon_result.joined_text)
#     print(whisper_result_with_furigana)
#     print(reazon_result_with_furigana)
#     response = client.chat.completions.create(
#         model="gpt-4-turbo-preview",
#         messages=[
#             {
#                 "role": "system",
#                 "content": """You are a helpful assistant. 
# 同じ音声を元にした2つの文字起こしの結果を与えます。
# それらを参考にして、より正しいと思われる一つの自然な文字起こしを読み仮名を抜いて提供してください。
# 読み仮名に注意し、変換ミスは修正してください。文章として税率するようにしてください""",
#             },
#             {
#                 "role": "user",
#                 "content": f"""# Transcription 1
# {whisper_result_with_furigana}

# # Transcription 2
# {reazon_result_with_furigana}
# """,
#             },
#         ],
#     )
#     data = response.choices[0].message.content

#     return TranscriptionWrapper(
#         [{"text": segment, "no_speech_prob": None} for segment in data.split("\n")],
#     )
