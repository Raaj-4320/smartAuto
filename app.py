from flask import Flask, request, render_template, redirect, url_for
from flask_cors import CORS
from openai import OpenAI
from flask import jsonify
import os
import pandas as pd

app = Flask(__name__, template_folder='.', static_folder='static')
CORS(app)

#  API key
client = OpenAI(api_key="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")

# Store response globally for rendering dashboard
response_data = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/form')
def form():
    return render_template('form.html')

@app.route('/buyer', methods=['POST'])
def handle_buyer():
    data = request.form
    manufacturer = data.get('manufacturer')
    year = data.get('year')
    car_type = data.get('model')
    accident = data.get('accident')
    owner = data.get('owner')
    price_drop = data.get('priceDrop')
    mileage = data.get('mileage')
    fuel_type = data.get('fuel_type')
    transmission = data.get('transmission')
    mpg = data.get("mpg")
    
    prompt = (
        f"Given the following car details:\n"
        f"Manufacturer: {manufacturer}\n"
        f"Year: {year}\n"
        f"Car Type: {car_type}\n"
        f"Accident: {accident}\n"
        f"Owners: {owner}\n"
        f"Price Drop: {price_drop}\n"
        f"Mileage: {mileage} km\n\n"
        f"Transmission: {transmission}\n"
        f"Fuel Type: {fuel_type}\n"
        f"MPG: {mpg}\n"
        f"Generate:\n"
        f"1. Estimated resale value (USD only).\n"
        f"2. 5 Pros of buying this car (short, bullet points, professional).\n"
        f"3. 5 Cons of buying this car (short, bullet points, professional).\n"
        f"and A brief 2-sentence recommendation summary."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        result = response.choices[0].message.content
        lines = result.split('\n')

        # Parse response
        price_line = next((line for line in lines if "Estimated resale value" in line or "$" in line), "N/A")
        price = price_line.split(":")[-1].strip() if ":" in price_line else price_line

        # Extract bullet points (simple heuristic)
        bullets = [line.strip('-• ').strip() for line in lines if line.strip().startswith(('-', '•'))]
        pros = bullets[:5]
        cons = bullets[5:10]

        # Summary is assumed at the end
        summary = lines[-1] if lines[-1] else "No summary available."

        global response_data
        response_data = {
            "price": price,
            "pros": pros,
            "cons": cons,
            "summary": summary
        }

    except Exception as e:
        response_data = {
            "price": "N/A",
            "pros": ["Error generating pros."],
            "cons": ["Error generating cons."],
            "summary": str(e)
        }

    return redirect(url_for('dashboard'))

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html',
        price=response_data.get("price", "N/A"),
        pros=response_data.get("pros", []),
        cons=response_data.get("cons", []),
        summary=response_data.get("summary", "No summary.")
    )

@app.route('/seller', methods=['POST'])
def handle_seller():
    data = request.form
    manufacturer = data.get('manufacturer')
    year = data.get('year')
    car_type = data.get('model')
    accident = data.get('accident')
    owner = data.get('owner')
    expected_price = data.get('expectedprice')
    mileage = data.get('mileage')
    fuel_type = data.get('fuel_type')
    transmission = data.get('transmission')
    mpg = data.get("mpg")
    
    prompt = (
        f"Given the following car details:\n"
        f"Manufacturer: {manufacturer}\n"
        f"Year: {year}\n"
        f"Car Type: {car_type}\n"
        f"Accident: {accident}\n"
        f"Owners: {owner}\n"
        f"Expected price form owner: {expected_price}\n"
        f"Mileage: {mileage} km\n\n"
        f"Transmission: {transmission}\n"
        f"Fuel Type: {fuel_type}\n"
        f"Fuel Efficiency (in km per gallon): {mpg}\n"
        f"Generate:\n"
        f"1. Estimated resale value (USD only).\n"
        f"2. 5 Points of effecting car price(short, bullet points, professional).\n"
        # f"3. 5 Cons of buying this car (short, bullet points, professional).\n"
        f"and A brief recommendation summary of what kind of aspect are effecting car price if its lower than expected price of user."
    )

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}]
        )
        result = response.choices[0].message.content
        lines = result.split('\n')

        # Parse response
        price_line = next((line for line in lines if "Estimated resale value" in line or "$" in line), "N/A")
        price = price_line.split(":")[-1].strip() if ":" in price_line else price_line

        # Extract bullet points (simple heuristic)
        bullets = [line.strip('-• ').strip() for line in lines if line.strip().startswith(('-', '•'))]
        pros = bullets[:5]
        # cons = bullets[5:10]

        # Summary is assumed at the end
        summary = lines[-1] if lines[-1] else "No summary available."

        global response_data
        response_data = {
            "price": price,
            "pros": pros,
            # "cons": cons,
            "summary": summary
        }

    except Exception as e:
        response_data = {
            "price": "N/A",
            "pros": ["Error generating pros."],
            "summary": str(e)
        }

    return redirect(url_for('sellerdashboard'))


@app.route('/sellerdashboard')
def sellerdashboard():
    return render_template('sellerdashboard.html',
        price=response_data.get("price", "N/A"),
        pros=response_data.get("pros", []),
        summary=response_data.get("summary", "No summary.")
    )



# Read CSV once when app starts
df = pd.read_csv('cars.csv')

# Get unique manufacturers
@app.route('/api/manufacturers')
def get_manufacturers():
    manufacturers = df['manufacturer'].unique().tolist()
    return jsonify(manufacturers)

# Get models for a selected manufacturer
@app.route('/api/models/<manufacturer>')
def get_models(manufacturer):
    models = df[df['manufacturer'] == manufacturer]['model'].unique().tolist()
    return jsonify(models)

if __name__ == '__main__':
    app.run(debug=True)
