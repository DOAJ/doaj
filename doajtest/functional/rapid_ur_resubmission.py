"""
Use this script to submit an update request twice in rapid succession, to demonstrate the
concurrency prevention mechanism in action.

To use this script get an API_KEY and a JOURNAL_ID of a journal owned by that user, and place
them in the appropriate variables below
"""

import requests, json
from doajtest.fixtures.v2.applications import ApplicationFixtureFactory


def rapid_resubmit(base_url, key, jid):
    source = ApplicationFixtureFactory.incoming_application()
    source["admin"]["current_journal"] = jid
    application = json.dumps(source)

    # make rapid resubmission
    resp1 = requests.post(f"{base_url}/api/applications?api_key={key}", data=application)
    resp2 = requests.post(f"{base_url}/api/applications?api_key={key}", data=application)

    return {"resp1": resp1, "resp2": resp2}

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--url", help="Base URL")
    parser.add_argument("-k", "--key", help="API key")
    parser.add_argument("-j", "--journal", help="Journal ID")
    args = parser.parse_args()

    print("Submitting duplicate responses in rapid succession...")
    responses = rapid_resubmit(args.url, args.key, args.journal)

    print("# Initial request:")
    print("-- Response code: ", responses["resp1"].status_code, " (Expected: 201)")
    print("-- Response body:\n", responses["resp1"].text)
    print("\n")

    print("# Second request:")
    print("-- Response code: ", responses["resp2"].status_code, " (Expected: 400)")
    print("-- Response body:\n", responses["resp2"].text)



