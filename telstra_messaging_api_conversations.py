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
# https://blog.sigsec.net/posts/2019/03/sms-conversations-with-python.html
#

import requests
from time import sleep
from datetime import datetime


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


def get_sms(token):
    response = telstra_request("messages/sms", {}, token=token, method='GET')

    if response.status_code != 200:
        raise RuntimeError("Bad response from Telstra API! " + response.text)

    return response.json()


def handle_all_messages(token):
    while True:
        try:
            message = get_sms(token)
        except RuntimeError as ex:
            print(ex)
            return
        
        if message['status'] == "EMPTY":
            break
        handle_message(token, message)


#
# Code for the stopwatch example
#

STOPWATCH_START = None
STOPWATCH_END = None


def handle_message(token, message):
    global STOPWATCH_START, STOPWATCH_END
    
    print('At ' + str(datetime.now()) + ' I received "' + message['message'] + '"!')
    
    if message['message'] == 'START':
        STOPWATCH_START = datetime.now()
        STOPWATCH_END = None
        
        send_sms(token, message['senderAddress'], 'The timer has been reset and is running!')
        
    elif message['message'] == 'STOP':
        if not STOPWATCH_START:  # if we haven't started yet
            send_sms(token, message['senderAddress'], 'The timer wasn\'t running! Say "START" first.')
        elif STOPWATCH_END:  # if we've already ended
            send_sms(token, message['senderAddress'], 'The timer is already stopped! Say "START" to reset.')
        else:  # we are currently running
            STOPWATCH_END = datetime.now()
            send_sms(token, message['senderAddress'], 'The timer ran for ' + str(STOPWATCH_END - STOPWATCH_START))
        
    elif message['message'] == 'TIME':
        if not STOPWATCH_START:  # if we haven't started yet
            send_sms(token, message['senderAddress'], 'The timer isn\'t running! Say "START" first.')
        elif STOPWATCH_END:  # if we've already ended
            send_sms(token, message['senderAddress'], 'The timer ran for ' + str(STOPWATCH_END - STOPWATCH_START))
        else:  # we are currently running
            send_sms(token, message['senderAddress'], 'The timer is still going and is currently at ' + str(datetime.now() - STOPWATCH_START))
        
    else:  # unknown command
        send_sms(token, message['senderAddress'], 'Sorry! I only understand "START", "STOP" and "TIME" exactly.')


#
# Main function, for when this file is run as a script
#

def main():
    token = auth("PutYour32CharClientKeyHereThanks", "ClientSecretHere")
    create_subscription(token)
    send_sms(token, "+61400000000", 'Stopwatch app online! I understand "START", "STOP" and "TIME".')
    
    print('Stopwatch app online at ' + str(datetime.now()) + '!')
    
    while True:
        handle_all_messages(token)
        sleep(1)


if __name__ == '__main__':
    main()

