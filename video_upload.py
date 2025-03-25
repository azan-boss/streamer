import requests

url = 'http://127.0.0.1:8000/api1/videos/'
headers = {
    'Authorization': 'Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ0b2tlbl90eXBlIjoiYWNjZXNzIiwiZXhwIjoxNzQyOTE0MzkxLCJpYXQiOjE3NDI5MTA3OTEsImp0aSI6ImYyZDYwMWVhOTgwNzQ0YTZiOGYyNzJmZGY1NGU3Yjg0IiwidXNlcl9pZCI6IjEiLCJ1c2VybmFtZSI6InN0cmVhbXN5YyIsImVtYWlsIjoic3RyZWFtc3ljQGdtYWlsLmNvbSIsImZpcnN0X25hbWUiOiIiLCJsYXN0X25hbWUiOiIiLCJpc19zdGFmZiI6ZmFsc2UsImlzX3N1cGVydXNlciI6ZmFsc2UsInBlcm1pc3Npb25zIjpbXSwicm9sZSI6InZpZXdlciJ9.ddwE00ja-w8bkeiRo5UXDIPtuTcASteiFM7wg7Nz1jU'
}
files = {
    'original_file': open(r'C:\Users\rafy\Downloads\Video\best.mp4', 'rb')
}
data = {
    'title': 'Best Video',
    'description': 'Awesome video upload test',
    'visibility': 'public'
}

response = requests.post(url, headers=headers, files=files, data=data)
print(response.json())