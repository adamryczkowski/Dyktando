from __future__ import annotations

from pathlib import Path
from threading import Thread
from typing import Optional

from pydantic import BaseModel
from pydub import AudioSegment
from pydub.playback import play
from typing import Optional

from .speech import TextToAudio


class Answer(BaseModel):
    text: str
    correct: bool


class Question:
    text: str
    audio: AudioSegment

    def __init__(self, text: str, audio: AudioSegment):
        self.text = text
        self.audio = audio

    def play(self):
        Thread(target=play, args=(self.audio,)).start()

    def get_answer(self, user_answer:str)->Answer:
        correct = (user_answer == self.text)
        return Answer(text=user_answer, correct=correct)


class Questions:
    _tta: TextToAudio
    _questions: list[str | Question]
    _index: int
    _answers: list[Answer]
    _cache_correct_count: Optional[int]
    _answers_file: Path

    def __init__(self, input_file: Path, answers_file: Path):
        assert isinstance(input_file, Path)
        assert input_file.exists()
        assert isinstance(answers_file, Path)
        self._tta = TextToAudio()
        self._index = 0
        self._answers = []
        self._cache_correct_count = None
        self._questions = []

        self._read_questions(input_file)

        if answers_file.exists():
            self._read_answers(answers_file)
        else:
            answers_file.parent.mkdir(parents=True, exist_ok=True)
        self._answers_file = answers_file

    def _read_answers(self, answers_file: Path):
        with open(answers_file, "r") as f:
            for line in f:
                answer = Answer.parse_raw(line)
                self._answers.append(answer)

                self._index += 1


    def _read_questions(self, input_file: Path):
        with open(input_file, "r") as f:
            for line in f:
                text = line.strip()
                self._questions.append(text)

    def get_question(self) -> Optional[Question]:
        if self._index >= len(self._questions):
            return None
        question = self._questions[self._index]
        if isinstance(question, str):
            self._questions[self._index] = Question(question, self._tta.convert(question))
        return self._questions[self._index]

    def save_answers(self):
        # Saves self._answers to the JSON file using pydantic
        with open(self._answers_file, "w") as f:
            # f.write(Answer.schema_json(indent=2))
            for answer in self._answers:
                f.write(answer.json() + "\n")


    def put_answer(self, answer: Answer):
        if len(self._answers) > self._index:
            self._answers[self._index] = answer
        else:
            if len(self._answers) == self._index:
                self._answers.append(answer)
            else:
                self._answers.append(answer)
                # assert False
        self.save_answers()

    def next_question(self):
        self._index += 1

    def check_answer(self, user_answer:str)->bool:
        if user_answer == "":
            return False
        # Tokenize
        correct = (user_answer == self.get_question().text)
        answer = Answer(text=user_answer, correct=correct)
        self.put_answer(answer)
        self._cache_correct_count = None
        return correct

    @property
    def index(self) -> int:
        return self._index

    def _count_correct(self):
        if self._cache_correct_count is not None:
            return
        self._cache_correct_count = 0
        for answer in self._answers:
            if answer.correct:
                self._cache_correct_count += 1

    @property
    def correct_count(self) -> int:
        self._count_correct()
        return self._cache_correct_count

    @property
    def failures_count(self) -> int:
        self._count_correct()
        return len(self._answers) - self._cache_correct_count

    def __len__(self):
        return len(self._questions)
