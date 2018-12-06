#!/usr/bin/env python3

import requests
import json

# TODO: ENTER THE API KEY YOU HAVE RECEIVED FROM CRUNCHBASE
class Crunchbase:
    def __init__(self):
        self.shared_endpoint = 'https://api.crunchbase.com/v3.1'
        self.organizations = '?data=key_set_url?relationships=funding_rounds,founders,board_members_and_advisors,acquisitions,ipo'
        self.persons = '?data=key_set_url?relationships=primary_affiliation,degrees,jobs,advisory_roles,founded_companies,investments,headquarters'
        self.key = '&user_key=<ENTER_USER_KEY_HERE>'

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        pass

    def company(self, permalink):
        response = json.loads(requests.get(
            self.shared_endpoint
            + permalink
            + self.organizations
            + self.key
            ).text)
        return(response)

    def person(self, permalink):
        response = json.loads(requests.get(
            self.shared_endpoint
            + permalink
            + self.persons
            + self.key
            ).text)
        return(response)
