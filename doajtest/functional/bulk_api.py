import requests, json, time
from doajtest.fixtures import ApplicationFixtureFactory

API = "http://localhost:5004/api/v1/bulk/applications"
KEY = "b711916e49494a18adb51b131c1d4490"

data = ApplicationFixtureFactory.incoming_application()
dataset = [data] * 10

resp = requests.post(API + "?api_key=" + KEY, data=json.dumps(dataset))
assert resp.status_code == 201

j = resp.json()
assert len(j) == 10

print j

ids = [r.get("id") for r in j]
print ids

time.sleep(2)

resp = requests.delete(API + "?api_key=" + KEY, data=json.dumps(ids))
assert resp.status_code == 204