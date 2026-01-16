import requests
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

OPEN_ROUTER_API = os.getenv("OPENROUTER_API_KEY")
HEADERS = {"Authorization": f"Bearer {OPEN_ROUTER_API}"}

def check_key_metadata():   
    url = "https://openrouter.ai/api/v1/key"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        print("\n🔑 API Key Metadata & Usage:")
        # print("Limit: ",response.json())
        print("Limit remaining: $",response.json()["data"]["limit_remaining"])
    else:
        print(f"Error fetching key metadata: {response.status_code} {response.text}")

def check_credits():
    url = "https://openrouter.ai/api/v1/credits"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        print("\n💳 Credit Info:")
        print(response.json())
    else:
        print(f"Error fetching credits: {response.status_code} {response.text}")

if __name__ == "__main__":
    check_key_metadata()
    # check_credits()





