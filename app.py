from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import pandas as pd
import random
import requests
import csv
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Change this to any random string

SCORES_CSV = "user_scores.csv"

# Load your CSV
df = pd.read_csv("data/country_capitals.csv")

def get_filtered_questions(continent, difficulty, num_questions):
    filtered = df.copy()
    if continent != "World":
        filtered = filtered[filtered['Continent'] == continent]
    if difficulty != "All":
        filtered = filtered[filtered['Difficulty'] == difficulty]
    if len(filtered) == 0:
        return []
    return filtered.sample(frac=1).reset_index(drop=True).iloc[:num_questions].to_dict(orient='records')

@app.route("/", methods=["GET", "POST"])
def index():
    continents = sorted(df['Continent'].unique().tolist())
    continents.insert(0, "World")
    difficulties = sorted(df['Difficulty'].unique().tolist())
    difficulties.insert(0, "All")
    maxq = len(df)
    if request.method == "POST":
        session['profile'] = request.form['profile']
        session['continent'] = request.form['continent']
        session['difficulty'] = request.form['difficulty']
        session['num_questions'] = int(request.form['num_questions'])
        session['mode'] = request.form['mode']
        session['score'] = 0
        session['current'] = 0
        session['questions'] = get_filtered_questions(
            session['continent'],
            session['difficulty'],
            session['num_questions']
        )
        if not session['questions']:
            return render_template("index.html", error="No questions available for this selection.",
                                   continents=continents, difficulties=difficulties, maxq=maxq)
        return redirect(url_for('quiz'))
    return render_template("index.html", continents=continents, difficulties=difficulties, maxq=maxq)

@app.route("/quiz", methods=["GET", "POST"])
def quiz():
    if 'questions' not in session or session['current'] >= len(session['questions']):
        return redirect(url_for('result'))

    question = session['questions'][session['current']]
    mode = session['mode']
    country_map_url = None
    lat = lng = None
    bbox_left = bbox_bottom = bbox_right = bbox_top = None
    neighbours = []
    country = question['Country']

    # Fetch country info from REST Countries API for map/flag/neighbours
    if mode in ['country_to_capital', 'flag_to_country']:
        try:
            resp = requests.get(f"https://restcountries.com/v3.1/name/{country}?fullText=true")
            if resp.ok:
                data = resp.json()[0]
                country_map_url = data.get('flags', {}).get('svg')
                neighbours = data.get('borders', [])
                if neighbours:
                    border_resp = requests.get(f"https://restcountries.com/v3.1/alpha?codes={','.join(neighbours)}")
                    if border_resp.ok:
                        neighbours = [c['name']['common'] for c in border_resp.json()]
                latlng = data.get('latlng', None)
                if latlng and len(latlng) == 2:
                    lat, lng = latlng
                    bbox_left = lng - 2
                    bbox_bottom = lat - 2
                    bbox_right = lng + 2
                    bbox_top = lat + 2
        except Exception as e:
            print("Map fetch error:", e)
            country_map_url = None

    # Quiz logic
    if mode == 'country_to_capital':
        q_text = f"What is the capital of {country}?"
        correct = question['Capital']
        wrong = [q['Capital'] for q in session['questions'] if q['Capital'] != correct]
    elif mode == 'capital_to_country':
        q_text = f"{question['Capital']} is the capital of which country?"
        correct = question['Country']
        wrong = [q['Country'] for q in session['questions'] if q['Country'] != correct]
    elif mode == 'flag_to_country':
        q_text = "Which country does this flag belong to?"
        correct = question['Country']
        wrong = [q['Country'] for q in session['questions'] if q['Country'] != correct]
    else:
        q_text = ""
        correct = ""
        wrong = []

    options = random.sample(wrong, min(3, len(wrong))) + [correct]
    random.shuffle(options)
    fun_fact = question['Fun Facts']

    show_answer = False
    is_correct = None
    selected = None

    if request.method == "POST":
        selected = request.form.get('answer')
        correct_answer = correct
        is_correct = selected == correct_answer
        show_answer = True
        if is_correct:
            session['score'] += 1

    if show_answer:
        session['current'] += 1

    return render_template(
        "quiz.html",
        q_text=q_text,
        options=options,
        q_num=session['current'] if show_answer else session['current'] + 1,
        total=len(session['questions']),
        show_answer=show_answer,
        is_correct=is_correct,
        correct=correct,
        fun_fact=fun_fact,
        selected=selected,
        country_map_url=country_map_url,
        lat=lat,
        lng=lng,
        bbox_left=bbox_left,
        bbox_bottom=bbox_bottom,
        bbox_right=bbox_right,
        bbox_top=bbox_top,
        neighbours=neighbours,
        mode=mode,
        country=country
    )

def save_score(profile, area, sub, difficulty, score, total):
    fieldnames = ['profile', 'area','sub','difficulty', 'score', 'total', 'timestamp']
    row = {
        'profile': profile,
        'area': area,
        'sub': sub,
        'difficulty': difficulty,
        'score': score,
        'total': total,
        'timestamp': datetime.now().isoformat()

    }
    try:
        with open(SCORES_CSV, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if f.tell() == 0:
                writer.writeheader()
            writer.writerow(row)
    except Exception as e:
        print("Error saving score:", e)

@app.route("/result")
def result():
    score = session.get('score', 0)
    total = len(session.get('questions', []))
    # Save score
    save_score(
        profile=session.get('profile', 'Unknown'),
        area=session.get('continent', 'World'),
        sub=session.get('mode', ''),
        difficulty=session.get('difficulty', 'All'),
        score=score,
        total=total
    )
    return render_template("result.html", score=score, total=total)

@app.route("/streaks")
def streaks():
    profile = request.args.get("profile")
    scores = []
    try:
        with open(SCORES_CSV, newline='') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row['profile'] == profile:
                    scores.append(row)
    except FileNotFoundError:
        pass
    # Sort by timestamp descending, get last 10
    scores = sorted(scores, key=lambda x: x['timestamp'], reverse=True)[:10]
    labels = [f"{s['area']} ({s['difficulty']})" for s in scores][::-1]
    values = [int(s['score']) for s in scores][::-1]
    totals = [int(s['total']) for s in scores][::-1]
    return jsonify({"labels": labels, "scores": values, "totals": totals})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True, ssl_context='adhoc')