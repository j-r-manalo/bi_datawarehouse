import os
import requests
from itc_common_utilities.logger.logger_setup import setup_logger

# Initialize the logger for this module
logger = setup_logger(__name__)

def make_api_call(url, method='get', data=None, row_limit=None):
    """
    Make a call to the Quickbase API.

    Args:
        url (str): The API endpoint URL
        method (str): HTTP method ('get' or 'post')
        data (dict, optional): Data to send with POST requests
        row_limit (int, optional): Number of rows to return in the response
    """
    # Retrieve the API token from the environment
    API_TOKEN = os.getenv("QUICKBASE_API_TOKEN")
    if not API_TOKEN:
        logger.error("Quickbase API token is not set in the environment.")
        raise Exception("Quickbase API token is not set in the environment.")

    HEADERS = {
        "QB-Realm-Hostname": "precedent.quickbase.com",
        "Authorization": "QB-USER-TOKEN " + API_TOKEN,
        "User-Agent": "Reporting Agent"
    }

    # Add row limit if specified
    # Append row limit if specified and applicable
    if row_limit is not None and 'run?' in url:
        separator = '&' if '?' in url else '?'
        url = f"{url}{separator}top={row_limit}"
        logger.debug(f"Applied row_limit parameter: {row_limit}. Updated URL: {url}")

    try:
        logger.debug(f"Making {method.upper()} request to URL: {url}")
        if method == 'get':
            response = requests.get(url, headers=HEADERS)
        elif method == 'post':
            response = requests.post(url, headers=HEADERS, json=data)
        else:
            logger.error(f"Unsupported HTTP method: {method}")
            return None

        response.raise_for_status()  # Raises an error for 4xx/5xx responses

        # Log an informational message on a successful API call
        logger.info(f"API call to {url} succeeded with status code {response.status_code}")
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error making API call to {url}: {e}")
        # Log a warning before the error for additional context on exceptions
        logger.warning(f"Request exception encountered for URL {url}: {e}")
        logger.error(f"Error making API call to {url}: {e}")
        return None