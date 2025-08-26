# main.py

import pandas as pd
import random

class CountryCapitalQuiz:
    def __init__(self, dataset_path):
        print(dataset_path)
        self.data = pd.read_csv(dataset_path)
        self.score = 0

    def ask_question(self):
        question = random.choice(self.data.index)
        country = self.data.at[question, 'Country']
        capital = self.data.at[question, 'Capital']
        fun_facts = self.data.at[question, 'Fun Facts']
        
        print(f"What is the capital of {country}?")
        answer = input("Your answer: ")
        
        if answer.lower() == capital.lower():
            print("Correct!")
            self.score += 1
            print(f"Fun Fact: {fun_facts}")
        else:
            print(f"Wrong! The capital of {country} is {capital}.")
            print(f"Fun Fact: {fun_facts}")

    def start_quiz(self):
        print("Welcome to the Country Capital Quiz!")
        num_questions = int(input("How many questions would you like to answer? "))
        
        for _ in range(num_questions):
            self.ask_question()
        
        print(f"Your final score is: {self.score}/{num_questions}")

if __name__ == "__main__":
    quiz = CountryCapitalQuiz('C:/Users/binoy/OneDrive/Documents/Coding/CountryQuizApp/country-capital-quiz/data/country_capitals.csv')
    quiz.start_quiz()