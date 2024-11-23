from pydub import AudioSegment
from .question_server import Questions, Answer
import tkinter as tk
from .misc import get_resource_path
from threading import Thread
from pydub.playback import play

class App:
    _questions: Questions

    time_start: float
    time_taken: float

    _window: tk.Tk
    _question_button: tk.Button
    _user_input: tk.Text
    _correct_answer_box: tk.Text
    _next_question_button: tk.Button
    _correct_label: tk.Label
    _wrong_label: tk.Label

    def init_counts(self):
        self._correct_label = tk.Label(
            self._window,
            text=f"Correct: {self._questions.correct_count}",
            font=("Helvetica", 20),
        )
        self._correct_label.configure(background="black", foreground="white")
        self._correct_label.grid(row=3, column=1, columnspan=3)

        self._wrong_label = tk.Label(
            self._window,
            text=f"Wrong: {self._questions.failures_count}",
            font=("Helvetica", 20),
        )
        self._wrong_label.configure(background="black", foreground="white")
        self._wrong_label.grid(row=4, column=1, columnspan=3)



    def update_counts(self):
        self._correct_label["text"] = f"Correct: {self._questions.correct_count}"
        self._wrong_label["text"] = f"Wrong: {self._questions.failures_count}"

    def __init__(self, questions:Questions):
        self._questions = questions

        self.time_start = 0.0
        self.time_taken = 0.0

        self._replay_last_button = None
        self._info_label = None
        self._previous_answer = None
        self._next_answer = None

        self._window = tk.Tk()
        self._window.geometry("1800x500")
        self._window.resizable(False, False)
        self._window.attributes("-type", "dialog")
        self._window.title("Dyktando")
        self._window.configure(bg="black")
        self._window.grid_columnconfigure(0, weight=1)
        self._window.grid_columnconfigure(1, weight=1)
        self._window.grid_columnconfigure(2, weight=1)

        self.init_counts()

        self._question_button = tk.Button(self._window, text="Play question")
        self._question_button.configure(background="black", foreground="white")
        self._question_button.configure(
            activebackground="black", activeforeground="white"
        )
        self._question_button.bind("<ButtonPress>", self.play_question)
        self._window.bind("<KeyPress>", self.key_pressed)
        self._question_button.grid(row=0, column=1, columnspan=3)

        self._user_input = tk.Text(self._window, font=("Helvetica", 20), height=2)
        self._user_input.configure(background="black", foreground="white", insertbackground="white")
        self._user_input.grid(row=1, column=1, columnspan=3)
        self._user_input["state"] = "normal"  # Ensure the text box is enabled

        self._correct_answer_box = tk.Text(self._window, font=("Helvetica", 20), height=2)
        self._correct_answer_box.configure(background="black", foreground="white", insertbackground="white")
        self._correct_answer_box.grid(row=2, column=1, columnspan=3)
        self._correct_answer_box["state"] = "disabled"  # Ensure the text box is readonly

        self._next_question_button = tk.Button(self._window, text="Next question")
        self._next_question_button.configure(background="black", foreground="white")
        self._next_question_button.configure(
            activebackground="black", activeforeground="white"
        )
        self._next_question_button.bind("<ButtonPress>", self.next_question)
        self._next_question_button.grid(row=5, column=2, columnspan=3)

        # self._next_question_button["state"] = "disabled"

        self._check_button = tk.Button(self._window, text="Check answer")
        self._check_button.configure(background="black", foreground="white")
        self._check_button.configure(
            activebackground="black", activeforeground="white"
        )
        self._check_button.bind("<ButtonPress>", self.check_answer)
        self._check_button.grid(row=5, column=0, columnspan=3)

        if self._questions.index >= len(self._questions):
            self.finish_popup()
        else:
            self.play_question()

    def key_pressed(self, event):
        if event.keysym == "Return":
            self.check_answer()

    def play_question(self, event=None):
        if self._question_button.config("state")[-1] == "disabled":
            return
        self._questions.get_question().play()

    def check_answer(self, event=None):
        if self._check_button.config("state")[-1] == "disabled":
            return
        user_answer = self._user_input.get("1.0", "end").strip()
        if user_answer == "":
            return
        self._next_question_button["state"] = "normal"
        self._user_input["state"] = "disabled"
        self._check_button["state"] = "disabled"
        correct = self._questions.check_answer(user_answer)
        if correct:
            song = AudioSegment.from_mp3(get_resource_path("correct.mp3"))
        else:
            song = AudioSegment.from_mp3(get_resource_path("incorrect.mp3"))
        Thread(target=play, args=(song,)).start()

        self.update_counts()

        correct_answer = self._questions.get_question().text
        self._correct_answer_box["state"] = "normal"
        self._correct_answer_box.delete("1.0", "end")
        self._correct_answer_box.insert("1.0", correct_answer)
        self._correct_answer_box["state"] = "disabled"

        if self._questions.index >= len(self._questions) - 1:
            self.finish_popup()

    def finish_popup(self):
        # self._next_question_button["state"] = "disabled"
        self._user_input["state"] = "disabled"
        self._question_button["state"] = "disabled"
        self._check_button["state"] = "disabled"
        popup = tk.Toplevel(self._window)
        popup.title("Finished")
        popup.geometry("300x150")
        popup.configure(bg="black")
        popup.resizable(False, False)
        popup.attributes("-type", "dialog")
        popup.attributes("-topmost", True)
        popup.grid_columnconfigure(0, weight=1)

        congrats_label = tk.Label(
            popup,
            text="Congratulations!",
            font=("Helvetica", 20),
        )
        congrats_label.configure(background="black", foreground="white")
        congrats_label.grid(row=0, column=0)

        correct_label = tk.Label(
            popup,
            text=f"Correct: {self._questions.correct_count}",
            font=("Helvetica", 20),
        )
        correct_label.configure(background="black", foreground="white")
        correct_label.grid(row=1, column=0)

        wrong_label = tk.Label(
            popup,
            text=f"Wrong: {self._questions.failures_count}",
            font=("Helvetica", 20),
        )
        wrong_label.configure(background="black", foreground="white")
        wrong_label.grid(row=2, column=0)

        percent_label = tk.Label(
            popup,
            text=f"Percent: {int(self._questions.correct_count / len(self._questions) * 100)}%",
            font=("Helvetica", 20),
        )
        percent_label.configure(background="black", foreground="white")
        percent_label.grid(row=3, column=0)

        popup.mainloop()

    def next_question(self, event=None):
        # if self._next_question_button.config("state")[-1] == "disabled":
        #     return
        # self._next_question_button["state"] = "disabled"
        self._check_button["state"] = "normal"
        self._questions.next_question()
        self._user_input["state"] = "normal"
        self._user_input.delete("1.0", "end")
        self._correct_answer_box["state"] = "normal"
        self._correct_answer_box.delete("1.0", "end")
        self._correct_answer_box["state"] = "disabled"
        self.play_question()

    @property
    def window(self):
        return self._window
