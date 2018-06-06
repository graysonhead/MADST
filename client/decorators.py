import requests
import json

class ApiAuth(object):
    def __init__(self, func):
        """
        callable wrapper class for handling auth and connection errors on API calls
        returns json object
        :return:
        """
        self.func = func

    def __call__(self, *args):
        try:
            r = self.func(*args)
            if r.status_code == 401:
                # TODO Log this instead of writing to stdout
                raise ConnectionRefusedError(r.json())
            elif r.status_code not in range(200, 299+1):
                raise ConnectionError(r.json())
            else:
                return r.json()
        except requests.exceptions.ConnectionError:
            raise

