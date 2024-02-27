# About this project

This is a simple application that uses the ReazonSpeech V2 and Whisper API to convert speech to text real-time.
The main logic is based on the article [[ローカル環境] faster-whisperを利用してリアルタイム文字起こしに挑戦](https://qiita.com/reriiasu/items/920227cf604dfb8b7949).


# Installation

## 1. Clone the repository
```sh
git clone https://github.com/wakamenori/whisper-app.git
```

```sh
cd whisper-app
```

## 2. Clone ReazonSpeech repository
```sh
git clone https://github.com/reazon-research/ReazonSpeech
```

## 3. Install the requirements
```sh
poetry install
```

## 4. Set the environment variables
```sh
cp .env.example .env
```

`OPENAI_API_KEY`: Your OpenAI API key

If you want to add furigana to the text to correct transcriptions, you need to set `YAHOO_APP_ID`.
But it is currently not used and commented out in the codej

# Usage
```sh
poetry run python src/main.py
```

or

```sh
make run
```

Transcription will be displayed in the terminal and saved in `src/log/` directory.