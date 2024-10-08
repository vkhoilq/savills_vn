import requests
import json
import pydantic

def generate_curl_command(response):
    req = response.request

    command = "curl -X {method} -H {headers} -d '{data}' '{uri}'"
    method = req.method
    uri = req.url
    data = req.body
    headers = ['"{0}: {1}"'.format(k, v) for k, v in req.headers.items()]
    headers = " -H ".join(headers)
    return command.format(method=method, headers=headers, data=data, uri=uri)


class BaseRESTClient:
    def __init__(self, user, password, base_url,login_endpoint="/login"):
        self.user = user
        self.password = password
        self.base_url = base_url
        self.token = None
        self.login_endpoint = login_endpoint

    def login(self):
        """Attempts to log in and obtain an authentication token."""
        try:
            response = requests.post(
                f"{self.base_url}/{self.login_endpoint}",
                json={"username": self.user, "password": self.password}
            )
            response.raise_for_status()

            data = response.json()
            self.token = data["token"]
            return True
        except requests.exceptions.RequestException as e:
            print(f"Login failed: {e}")
            return False

    def _make_request(self, method, endpoint, data=None):
        """Makes a REST request with the given method, endpoint, and data.

        Handles token authentication, network errors, and invalid responses.
        """
        headers = {
        'Host': f'{self.base_url.replace("https://", "")}',
        'Accept': 'application/json',
        'api-version': '2',
        'Devicetypeid': '2',
        'Cache-Control': 'no-cache',
        'Authorization': f"Bearer {self.token}",
        #'Content-Type': 'application/json',
        'Accept-Encoding': 'gzip',
        'User-Agent': 'okhttp/4.9.2',
        'content-type': 'application/json',
        'Cookie': 'ApplicationGatewayAffinity=4d41f1ce71536351747e651ab04cb5f4; ApplicationGatewayAffinityCORS=4d41f1ce71536351747e651ab04cb5f4'
        }

        try:
            if data:
                response = requests.request(method, f"{self.base_url}/{endpoint}", json=data, headers=headers)
            else:
                response = requests.request(method, f"{self.base_url}/{endpoint}", headers=headers)                
            
            #print(generate_curl_command(response))
            response.raise_for_status()
            
            
            
            try:
                return response.json()
            except json.JSONDecodeError:
                raise Exception("Invalid JSON response")
        except requests.exceptions.RequestException as e:
            if response.status_code == 401:  # Unauthorized
                if not self.login():  # Attempt to re-login
                    raise Exception("Login failed")
                return self._make_request(method, endpoint, data)
            else:
                raise Exception(f"Network error: {e}\n Response: {response.text}")

    def get(self, endpoint, data=None):
        """Makes a GET request to the specified endpoint."""
        return self._make_request("GET", endpoint, data)

    def post(self, endpoint, data=None):
        """Makes a POST request to the specified endpoint."""
        return self._make_request("POST", endpoint, data)

    def put(self, endpoint, data=None):
        """Makes a PUT request to the specified endpoint."""
        return self._make_request("PUT", endpoint, data)

    def delete(self, endpoint, data=None):
        """Makes a DELETE request to the specified endpoint."""
        return self._make_request("DELETE", endpoint, data)