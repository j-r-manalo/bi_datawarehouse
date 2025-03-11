import os
import requests

def make_api_call(url, method='get', data=None, row_limit=None):
    """
    Make a call to the Quickbase API.

    Args:
        url (str): The API endpoint URL
        method (str): HTTP method ('get' or 'post')
        data (dict, optional): Data to send with POST requests
        row_limit (int, optional): Number of rows to return in the response
    """
    # Your API headers
    API_TOKEN = os.getenv("QUICKBASE_API_TOKEN")
    if not API_TOKEN:
        raise Exception("Quickbase API token is not set in the environment.")

    HEADERS = {
        "QB-Realm-Hostname": "precedent.quickbase.com",
        "Authorization": "QB-USER-TOKEN " + API_TOKEN,
        "User-Agent": "Reporting Agent"
    }

    # Add row limit if specified
    if row_limit is not None and 'run?' in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}top={row_limit}"

    try:
        if method == 'get':
            response = requests.get(url, headers=HEADERS)
        elif method == 'post':
            response = requests.post(url, headers=HEADERS, json=data)

        response.raise_for_status()  # Will raise an error for 4xx/5xx responses
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API call to {url}: {e}")
        return None