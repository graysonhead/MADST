import requests

class apiAuth(object):
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
                print("Recieved authentication error") #TODO Log this instead of writing to stdout
                raise ConnectionRefusedError
            elif r.status_code not in range(200, 299+1):
                print("Recieved Connection Error")
                raise ConnectionError
        except requests.exceptions.ConnectionError:
            print("A connection error occured, check the host and port and try again.")
            #TODO Log this instead of writing to stdout
        finally:
            for line in self.func(*args).iter_lines():
                print(line)
            try:
                print(self.func(*args).json())
            except ValueError:
                print("no valid json")
                return
            finally:
                return self.func(*args).json()