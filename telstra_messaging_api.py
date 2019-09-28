#!/usr/bin/env python3

#
# Copyright 2019 me@sigsec.net
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

# Code for article:
# https://blog.sigsec.net/posts/2019/03/sending-smses-from-python.html
#

import requests


def telstra_request(endpoint, body=None, headers=None, *, token=None, method='POST'):
    send_headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
    }
    if token:  # if this is an authenticated request, add the token header
        send_headers['Authorization'] = 'Bearer ' + token
    if headers:  # add any extra headers if desired
        send_headers.update(headers)

    url = "https://tapi.telstra.com/v2/" + endpoint
    return requests.request(method, url, json=body, headers=send_headers)


def auth(app_key, app_secret):
    body = dict(client_id=app_key, client_secret=app_secret,
        grant_type="client_credentials", scope="NSMS")
    response = requests.post("https://tapi.telstra.com/v2/oauth/token", body)

    if response.status_code != 200:
        raise RuntimeError("Bad response from Telstra API! " + response.text)

    response_json = response.json()
    return response_json['access_token']


def create_subscription(token):
    response = telstra_request("messages/provisioning/subscriptions", {}, token=token)

    if response.status_code != 201:
        raise RuntimeError("Bad response from Telstra API! " + response.text)

    response_json = response.json()
    return response_json['destinationAddress']


def send_sms(token, to, body):
    payload = dict(to=to, body=body)
    response = telstra_request("messages/sms", payload, token=token)

    if response.status_code != 201:
        raise RuntimeError("Bad response from Telstra API! " + response.text)

    response_json = response.json()
    return response_json


#
# Main function, for when this file is run as a script
#

def main():
    token = auth("PutYour32CharClientKeyHereThanks", "ClientSecretHere")
    create_subscription(token)
    send_sms(token, "+61400000000", "Hello sigsec readers!")


if __name__ == '__main__':
    main()

