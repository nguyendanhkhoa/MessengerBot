import os
import sys
import json
import argparse

import requests
import googleapiclient.discovery

from flask import Flask, request

app = Flask(__name__)


@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


def configureWhatToPrint(sentiment):
    if sentiment < -0.2:
        return ":-( Shit! you are having a very bad day, Im so sorry!   " + str(sentiment)
    elif sentiment > 0.2:
        return "O:) Brilliant! you are having a good day, glad to hear!   " + str(sentiment)
    elif sentiment < -0.1:
        return ":-O Hey, Sorry to hear that, it will get better!   " + str(sentiment)
    elif sentiment > 0.1:
        return "<3 haha, Wunderbar!   " + str(sentiment)
    else:
        return "-_-   " + str(sentiment)


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events

    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    result = analyze_sentiment(message_text)

                    sentiment = result["documentSentiment"]["magnitude"] * result["documentSentiment"]["score"]

                    output = configureWhatToPrint(sentiment)

                    send_message(sender_id, output) #

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()

def get_native_encoding_type():
    """Returns the encoding type that matches Python's native strings."""
    if sys.maxunicode == 65535:
        return 'UTF16'
    else:
        return 'UTF32'

def analyze_sentiment(text, encoding='UTF32'):
    body = {
        'document': {
            'type': 'PLAIN_TEXT',
            'language': 'EN',
            'content': text,
        },
        'encoding_type': encoding
    }

    service = googleapiclient.discovery.build('language', 'v1')

    request = service.documents().analyzeSentiment(body=body)
    response = request.execute()

    return response

if __name__ == '__main__':
    app.run(debug=True)
#WHYYYYYYYY?
# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(
#         description=__doc__,
#         formatter_class=argparse.RawDescriptionHelpFormatter)
#     parser.add_argument('command', choices=[
#         'entities', 'sentiment', 'syntax'])
#     parser.add_argument('text')
#
#     args = parser.parse_args()
#
#     # if args.command == 'entities':
#     #     result = analyze_entities(args.text, get_native_encoding_type())
#     if args.command == 'sentiment':
#         result = analyze_sentiment(args.text, get_native_encoding_type())
#     # elif args.command == 'syntax':
#     #     result = analyze_syntax(args.text, get_native_encoding_type())
#
#     print(json.dumps(result, indent=2))