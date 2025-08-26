import tkinter as tk
from tkinter import messagebox
import pandas as pd
import random

class CountryCapitalQuizGUI:
    def __init__(self, master, data):
        self.master = master
        self.data = data
        self.score = 0
        self.mode = None  # 'country_to_capital' or 'capital_to_country'
        self.num_questions = 5  # Default

        self.master.title("Country Capital Quiz")
        self.master.geometry("700x500")

        self.start_frame = tk.Frame(master)
        self.quiz_frame = tk.Frame(master)

        # Get unique continents and difficulties
        self.continents = sorted(self.data['Continent'].unique().tolist())
        self.continents.insert(0, "World")
        self.difficulties = sorted(self.data['Difficulty'].unique().tolist())
        self.difficulties.insert(0, "All")

        # Start Frame Widgets
        self.lbl_welcome = tk.Label(self.start_frame, text="Choose Quiz Mode", font=("Arial", 18))
        self.lbl_continent = tk.Label(self.start_frame, text="Select Continent:", font=("Arial", 12))
        self.selected_continent = tk.StringVar(value="World")
        self.continent_menu = tk.OptionMenu(self.start_frame, self.selected_continent, *self.continents)
        self.lbl_difficulty = tk.Label(self.start_frame, text="Select Difficulty:", font=("Arial", 12))
        self.selected_difficulty = tk.StringVar(value="Easy")
        self.difficulty_menu = tk.OptionMenu(self.start_frame, self.selected_difficulty, *self.difficulties)
        self.lbl_numq = tk.Label(self.start_frame, text="Number of questions (max will update):", font=("Arial", 12))
        self.entry_numq = tk.Entry(self.start_frame, font=("Arial", 12), width=5)
        self.entry_numq.insert(0, "5")
        self.btn_country_to_capital = tk.Button(self.start_frame, text="Country → Capital", font=("Arial", 14),
                                                command=lambda: self.start_quiz('country_to_capital'))
        self.btn_capital_to_country = tk.Button(self.start_frame, text="Capital → Country", font=("Arial", 14),
                                                command=lambda: self.start_quiz('capital_to_country'))

        self.lbl_welcome.pack(pady=20)
        self.lbl_continent.pack()
        self.continent_menu.pack(pady=5)
        self.lbl_difficulty.pack()
        self.difficulty_menu.pack(pady=5)
        self.lbl_numq.pack()
        self.entry_numq.pack(pady=5)
        self.btn_country_to_capital.pack(pady=10)
        self.btn_capital_to_country.pack(pady=10)
        self.start_frame.pack(expand=True)

        # Quiz Frame Widgets
        self.lbl_question = tk.Label(self.quiz_frame, text="", font=("Arial", 16))
        self.lbl_question.pack(pady=20)

        self.var_choice = tk.StringVar()
        self.radio_buttons = []
        for i in range(4):
            rb = tk.Radiobutton(self.quiz_frame, text="", variable=self.var_choice, value="", font=("Arial", 14))
            rb.pack(anchor="w", padx=100)
            self.radio_buttons.append(rb)

        self.btn_submit = tk.Button(self.quiz_frame, text="Submit", command=self.check_answer)
        self.btn_submit.pack(pady=10)

        self.lbl_result = tk.Label(self.quiz_frame, text="", font=("Arial", 12))
        self.lbl_result.pack()

        self.lbl_funfact = tk.Label(self.quiz_frame, text="", wraplength=600, font=("Arial", 10))
        self.lbl_funfact.pack(pady=10)

        # Update max questions when continent or difficulty changes
        self.selected_continent.trace("w", self.update_max_questions)
        self.selected_difficulty.trace("w", self.update_max_questions)

    def update_max_questions(self, *args):
        continent = self.selected_continent.get()
        difficulty = self.selected_difficulty.get()
        filtered = self.data
        if continent != "World":
            filtered = filtered[filtered['Continent'] == continent]
        if difficulty != "All":
            filtered = filtered[filtered['Difficulty'] == difficulty]
        maxq = len(filtered)
        self.lbl_numq.config(text=f"Number of questions (max {maxq}):")
        try:
            if int(self.entry_numq.get()) > maxq:
                self.entry_numq.delete(0, tk.END)
                self.entry_numq.insert(0, str(maxq))
        except ValueError:
            self.entry_numq.delete(0, tk.END)
            self.entry_numq.insert(0, "1")

    def start_quiz(self, mode):
        self.mode = mode
        continent = self.selected_continent.get()
        difficulty = self.selected_difficulty.get()
        filtered = self.data
        if continent != "World":
            filtered = filtered[filtered['Continent'] == continent]
        if difficulty != "All":
            filtered = filtered[filtered['Difficulty'] == difficulty]
        try:
            num = int(self.entry_numq.get())
            if num < 1:
                raise ValueError
            if num > len(filtered):
                num = len(filtered)
        except ValueError:
            messagebox.showwarning("Invalid input", f"Please enter a valid number between 1 and {len(filtered)}.")
            return
        if len(filtered) == 0:
            messagebox.showwarning("No questions", "No questions available for this selection.")
            return
        self.num_questions = num
        self.questions = filtered.sample(frac=1).reset_index(drop=True).iloc[:self.num_questions]
        self.current = 0
        self.score = 0
        self.start_frame.pack_forget()
        self.quiz_frame.pack(expand=True)
        self.next_question()

    def next_question(self):
        if self.current < len(self.questions):
            row = self.questions.iloc[self.current]
            if self.mode == 'country_to_capital':
                question_text = f"What is the capital of {row['Country']}?"
                correct = row['Capital']
                wrong = self.questions[self.questions['Capital'] != correct]['Capital'].sample(
                    min(3, len(self.questions)-1)).tolist()
                options = wrong + [correct]
            else:
                question_text = f"{row['Capital']} is the capital of which country?"
                correct = row['Country']
                wrong = self.questions[self.questions['Country'] != correct]['Country'].sample(
                    min(3, len(self.questions)-1)).tolist()
                options = wrong + [correct]

            random.shuffle(options)
            self.lbl_question.config(text=question_text)
            self.var_choice.set(None)
            for i, option in enumerate(options):
                self.radio_buttons[i].config(text=option, value=option)
            self.lbl_result.config(text="")
            self.lbl_funfact.config(text="")
        else:
            messagebox.showinfo("Quiz Finished", f"Your score: {self.score}/{self.num_questions}")
            self.master.quit()

    def check_answer(self):
        selected = self.var_choice.get()
        if not selected:
            messagebox.showwarning("No selection", "Please select an answer!")
            return

        row = self.questions.iloc[self.current]
        if self.mode == 'country_to_capital':
            correct_answer = row['Capital']
        else:
            correct_answer = row['Country']
        fun_fact = row['Fun Facts']

        if selected == correct_answer:
            self.lbl_result.config(text="Correct!", fg="green")
            self.score += 1
        else:
            self.lbl_result.config(text=f"Wrong! The correct answer is {correct_answer}.", fg="red")

        self.lbl_funfact.config(text=f"Fun Fact: {fun_fact}")
        self.current += 1
        self.master.after(2000, self.next_question)

if __name__ == "__main__":
    df = pd.read_csv("C:/Users/binoy/OneDrive/Documents/Coding/CountryQuizApp/country-capital-quiz/data/country_capitals.csv")
    root = tk.Tk()
    app = CountryCapitalQuizGUI(root, df)
    root.mainloop()