from fastapi import FastAPI, HTTPException
import httpx
from collections import deque

app = FastAPI()
THIRD_PARTY_API_BASE = "http://20.244.56.144/evaluation-service"
WINDOW_SIZE = 10
number_window = deque(maxlen=WINDOW_SIZE)
API_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJNYXBDbGFpbXMiOnsiZXhwIjoxNzQzNjAyNzUyLCJpYXQiOjE3NDM2MDI0NTIsImlzcyI6IkFmZm9yZG1lZCIsImp0aSI6IjkyYzZkY2UzLTIzMWYtNDBmYy04MjhkLTljMjhjNzhkY2NmYSIsInN1YiI6IjIyMDUyNjMwQGtpaXQuYWMuaW4ifSwiZW1haWwiOiIyMjA1MjYzMEBraWl0LmFjLmluIiwibmFtZSI6ImJvcm5payBkZWthdmlyYWoiLCJyb2xsTm8iOiIyMjA1MjYzMCIsImFjY2Vzc0NvZGUiOiJud3B3cloiLCJjbGllbnRJRCI6IjkyYzZkY2UzLTIzMWYtNDBmYy04MjhkLTljMjhjNzhkY2NmYSIsImNsaWVudFNlY3JldCI6Ik5RVFhKcnFuVnpocGFmTkYifQ.4JvAnNa8i05lkz3tiJDMdaQdoz0QzMBXT-X8ZVl_MtI"

async def fetch_numbers(number_type: str):
    url = f"{THIRD_PARTY_API_BASE}/{number_type}"
    headers = {
        "Authorization": f"Bearer {API_KEY}"
    }
    try:
        async with httpx.AsyncClient(timeout=0.5) as client:
            response = await client.get(url, headers=headers)
        if response.status_code != 200:
            print(f"API Error: {response.status_code}, {response.text}")
            return []
        data = response.json()
        print(f"API Response [{url}]: {data}")
        return data.get("numbers", [])
    except (httpx.RequestError, httpx.TimeoutException) as e:
        print(f"API Error: {e}")
        return []
@app.get("/numbers/{numberid}")
async def get_numbers(numberid: str):
    valid_types = {"p": "primes", "f": "fibo", "e": "even", "r": "rand"}
    if numberid not in valid_types:
        raise HTTPException(status_code=400, detail="Invalid number ID. Use 'p', 'f', 'e', or 'r'.")
    prev_state = list(number_window)
    fetched_numbers = await fetch_numbers(valid_types[numberid])
    print(f"Fetched Numbers: {fetched_numbers}")
    if not fetched_numbers:
        return {
            "windowPrevState": prev_state,
            "windowCurrState": prev_state,
            "numbers": [],
            "avg": round(sum(prev_state) / len(prev_state), 2) if prev_state else 0.0,
        }
    for num in fetched_numbers:
        if num not in number_window:
            number_window.append(num)
    curr_state = list(number_window)
    avg = round(sum(curr_state) / len(curr_state), 2) if curr_state else 0.0
    return {
        "windowPrevState": prev_state,
        "windowCurrState": curr_state,
        "numbers": fetched_numbers,
        "avg": avg,
    }