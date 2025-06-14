from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
import requests
from datetime import date
import json
import os

app = Flask(__name__)
CORS(app)

DATA_FILE = 'salary_data.json'
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, 'r') as f:
        salary_data = json.load(f)
else:
    salary_data = {}

def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(salary_data, f)

EXCHANGE_API_BASE = 'https://open.er-api.com/v6/latest'

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/api/currencies')
def get_currencies():
    try:
        res = requests.get(f"{EXCHANGE_API_BASE}/USD")
        data = res.json()
        return jsonify(sorted(list(data['rates'].keys())))
    except Exception as e:
        return jsonify({'error': 'Could not load currencies', 'details': str(e)}), 500

@app.route('/api/convert', methods=['POST'])
def convert():
    try:
        req = request.json
        from_curr = req['from']
        to_curr = req['to']
        amount = float(req['amount'])

        res = requests.get(f"{EXCHANGE_API_BASE}/{from_curr}")
        data = res.json()
        rate = data['rates'].get(to_curr)

        if rate is None:
            return jsonify({'error': 'Currency not supported'}), 400

        converted = round(amount * rate, 2)
        return jsonify({'rate': rate, 'converted': converted})
    except Exception as e:
        return jsonify({'error': 'Conversion error', 'details': str(e)}), 500

@app.route('/api/salary/day', methods=['POST'])
def salary_day():
    try:
        req = request.json
        start = int(req['start'])
        end = int(req['end'])
        rate = float(req['rate'])

        if not (0 <= start <= 24) or not (0 <= end <= 24):
            return jsonify({'error': 'Start and end hours must be between 0 and 24'}), 400

        if end >= start:
            hours = end - start
        else:
            hours = (24 - start) + end

        salary = round(hours * rate, 2)
        today = str(date.today())

        salary_data[today] = {
            'start': start,
            'end': end,
            'rate': rate,
            'hours': hours,
            'daily_salary': salary
        }

        save_data()
        return jsonify({'date': today, 'daily_salary': salary, 'hours': hours})
    except Exception as e:
        return jsonify({'error': 'Salary calculation failed', 'details': str(e)}), 500

@app.route('/api/salary/summary')
def salary_summary():
    try:
        total = sum(day['daily_salary'] for day in salary_data.values())
        return jsonify({
            'days': salary_data,
            'total_month': round(total, 2)
        })
    except Exception as e:
        return jsonify({'error': 'Summary error', 'details': str(e)}), 500

@app.route('/api/salary/<string:day>')
def get_day_salary(day):
    if day in salary_data:
        return jsonify(salary_data[day])
    return jsonify({'message': 'No data for that day'}), 404

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
