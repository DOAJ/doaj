"""
Use this script to submit an update request twice in rapid succession, to demonstrate the
concurrency prevention mechanism in action.

To use this script get an API_KEY and a JOURNAL_ID of a journal owned by that user, and place
them in the appropriate variables below
"""

import requests, json
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory

API_KEY = "c7659b4bf01a456f80ec82fcb8295bfa"
JOURNAL_ID = "abcdefghijk_journal"

source = ApplicationFixtureFactory.incoming_application()
source["admin"]["current_journal"] = JOURNAL_ID
application = json.dumps(source)

# make rapid resubmission
resp1 = requests.post(f"http://localhost:5004/api/applications?api_key={API_KEY}", data=application)
resp2 = requests.post(f"http://localhost:5004/api/applications?api_key={API_KEY}", data=application)

print(resp1.status_code)
print(resp1.text)

print(resp2.status_code)
print(resp2.text)