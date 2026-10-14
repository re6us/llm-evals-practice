import requests

url = "https://api.coingecko.com/api/v3/simple/price"

params = {
    "ids": "bitcoin,solana,dogecoin",
    "vs_currencies": "usd",
    "include_24hr_change": "true"
    }

try:
    response = requests.get(url, params=params, timeout=10)
except Exception as exc:
    print(f"Не удалось получить данные ({exc})")
    exit()

if response.status_code != 200:
    print(f"Cервер ответил {response.status_code}")
    exit()

data = response.json()  
for coin in data:
    clean_data = data[coin]
    price = clean_data["usd"]
    change = clean_data["usd_24h_change"]
    print(f"{coin}: {price}, {change:.2f}")

##except Exception as exc:
    ##print(f"{name}: не удалось получить данные ({exc})")
    ##continue

##if response.status_code != 200:
    ##print(f"{name}: сервер ответил {response.status_code}")

##data = response.json()
##temp = data["ids"]["s_currencies"]
##print(f"{name}: {vs_currencies} $")