import json
import requests
import datetime
import time
import socket
from decimal import Decimal
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)


def fetch_details():
    hostname = socket.gethostname()
    ip = socket.gethostbyname(hostname)
    return str(hostname), str(ip)


# Returns weather in Kyiv
def get_weather():
    weather_url = 'http://api.openweathermap.org/data/2.5/weather?q=Kyiv,ua&APPID=94a623b565f3f96b4137c967ef3ad363'
    response = requests.get(weather_url)
    final = json.loads(response.text)
    weather_short = {'description': final['weather'][0]['description'],
                        'temperature': int(round(Decimal(str(final['main']['temp']))-Decimal('273.15')))}
    #weather_json = json.dumps(weather_short)
    return weather_short


# Returns the day of closest Monday, Tuesday, etc. Technical function
def get_closest_dates_of_each_day():
    target_dict = {}
    today = datetime.datetime.now()
    today = today.replace(hour=0, minute=0, second=0, microsecond=0)
    # In Python: 0 = Mon, 1 = Tue, ..., 6 = Sun; so we have to add 1 manually
    pointer_weekday = today.weekday() + 1
    pointer_date = today
    for i in range(7):
        target_dict[f'weekday{pointer_weekday}'] = pointer_date
        pointer_weekday += 1
        if pointer_weekday == 8:
            pointer_weekday = 1
        pointer_date += datetime.timedelta(days=1)
    return target_dict


# Returns the complete list of flights from today 00:00 until 6 days later 23:59
# type of schedule = 0 for departures, 1 for arrivals. Must be integer, not string
def get_schedule_for_week(type_of_schedule):
    closest_days = get_closest_dates_of_each_day()
    with open(f'schedule_{type_of_schedule}.json', 'r') as schedule_file:
        all_flights_in_theory = json.load(schedule_file)
    all_flights_of_week = []
    for key, value in all_flights_in_theory.items():
        for weekday in range(1, 8):
            if value[f'weekday{weekday}'] == 1:
                closest_day_of_that_weekday = closest_days[f'weekday{weekday}']
                hours = int(value['time'][:2])
                minutes = int(value['time'][3:5])
                flight = {
                    'number': key,
                    'city': value['city'],
                    'time': closest_day_of_that_weekday + datetime.timedelta(hours=hours, minutes=minutes)
                    }
                all_flights_of_week.append(flight)
    return sorted(all_flights_of_week, key=lambda d: d['time'])


# Returns the list 
# type of schedule = 0 for departures, 1 for arrivals. Must be integer, not string
def closest_schedule(type_of_schedule):
    schedule_for_week = get_schedule_for_week(type_of_schedule)
    display_start_time = datetime.datetime.now()
    if type_of_schedule == 1:
        display_start_time -= datetime.timedelta(hours=2)
    display_flights = []
    for flight in schedule_for_week:
        if flight['time'] >= display_start_time:
            display_flights.append(flight)
        if len(display_flights) >= 30:
            break
    for flight in display_flights:
        datetime_obj = flight['time']
        flight['time'] = '{:02d}:{:02d}'.format(datetime_obj.hour, datetime_obj.minute)
    #flights_json = json.dumps(display_flights)
    return display_flights


@app.route('/')
def main_page():
    weather = get_weather()
    departure_flights = closest_schedule(0)
    arrival_flights = closest_schedule(1)
    hostname, ip = fetch_details()
    return render_template('main.html', weather=weather, departure_flights=departure_flights, arrival_flights=arrival_flights, hostname=hostname, ip=ip)


@app.route('/kyiv_weather')
def api_weather():
    response = jsonify(get_weather())
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/departures')
def api_departures():
    response = jsonify(closest_schedule(0))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/arrivals')
def api_arrivals():
    response = jsonify(closest_schedule(1))
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


@app.route('/health')
def api_health():
    response = jsonify(status="UP")
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=443)