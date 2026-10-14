import requests

url = "https://api.open-meteo.com/v1/forecast"

cities = {
    "Alicante": {"latitude": 38.35, "longitude": -0.48},
    "Madrid": {"latitude": 40.42, "longitude": -3.70},
    "Barcelona": {"latitude": 41.39, "longitude": 2.17}
    }

for name, coords in cities.items():
    params = {
        "latitude": coords["latitude"],
        "longitude": coords["longitude"],
        "current": "temperature_2m"
    }

    try:
        response = requests.get(url, params=params, timeout=10)
    except Exception as exc:
        print(f"{name}: не удалось получить данные ({exc})")
        continue

    if response.status_code != 200:
        print(f"{name}: сервер ответил {response.status_code}")

    data = response.json()
    temp = data["current"]["temperature_2m"]
    print(f"{name}: {temp} °C")