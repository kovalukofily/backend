import os
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
    start_time = time.time()
    weather_url = 'http://api.openweathermap.org/data/2.5/weather?q=Kyiv,ua&APPID=94a623b565f3f96b4137c967ef3ad363'
    response = requests.get(weather_url)
    final = json.loads(response.text)
    weather_short = {'description': final['weather'][0]['description'],
                        'temperature': int(round(Decimal(str(final['main']['temp']))-Decimal('273.15')))}
    weather_short["exec_time"] = time.time() - start_time
    print(f"Time Measurement f:get_weather {weather_short['exec_time']}")
    #weather_json = json.dumps(weather_short)
    return weather_short


# Returns the complete list of flights from today 00:00 until 6 days later 23:59
# type of schedule = 0 for departures, 1 for arrivals. Must be integer, not string
@app.route('/schedule_week')
def get_schedule_for_week():
    type_of_schedule = request.args.get('type_of_schedule')
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
    response = jsonify(sorted(all_flights_of_week, key=lambda d: d['time']))
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')
    return response


# Returns the list 
# type of schedule = 0 for departures, 1 for arrivals. Must be integer, not string
def closest_schedule(type_of_schedule):
    start_time = time.time()
    converter = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                 'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    #schedule_for_week = get_schedule_for_week(type_of_schedule).json
    schedule_for_week = requests.get(f'https://kovalukofily-lab4.herokuapp.com/schedule_week?type_of_schedule={type_of_schedule}').json()
    display_start_time = datetime.datetime.now()
    if type_of_schedule == 1:
        display_start_time -= datetime.timedelta(hours=2)
    display_flights = []
    for flight in schedule_for_week:
        flight_time = datetime.datetime(year=int(flight['time'][12:16]),
                                        month=converter[flight['time'][8:11]],
                                        day=int(flight['time'][5:7]),
                                        hour=int(flight['time'][17:19]),
                                        minute=int(flight['time'][20:22]))
        if flight_time >= display_start_time:
            display_flights.append(flight)
        if len(display_flights) >= 30:
            break
    for flight in display_flights:
        #datetime_obj = flight['time']
        flight_time = datetime.datetime(year=int(flight['time'][12:16]),
                                        month=converter[flight['time'][8:11]],
                                        day=int(flight['time'][5:7]),
                                        hour=int(flight['time'][17:19]),
                                        minute=int(flight['time'][20:22]))
        flight['time'] = '{:02d}:{:02d}'.format(flight_time.hour, flight_time.minute)
    #flights_json = json.dumps(display_flights)
    newdict = {}
    newdict["flights"] = display_flights
    newdict["exec_time"] = time.time() - start_time
    print(f"Time Measurement f:closest_schedule {newdict['exec_time']}")
    return newdict


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
    response.headers.add('Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')
    return response


@app.route('/departures')
def api_departures():
    response = jsonify(closest_schedule(0))
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')
    return response


@app.route('/arrivals')
def api_arrivals():
    response = jsonify(closest_schedule(1))
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')
    return response


@app.route('/health')
def api_health():
    response = jsonify(status="UP")
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Methods', 'PUT, POST, GET, DELETE, OPTIONS')
    return response


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=os.environ.get("PORT", 443), debug=False)
