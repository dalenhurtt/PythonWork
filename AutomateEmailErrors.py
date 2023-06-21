'''Dalen Hurtt
Script to automate sending an email twice a day
of Outgoing Message in ClickSoftware
Revision 05/25/23 - Dalen Hurtt
'''

'''Imports'''

import smtplib
import datetime
from email.mime.text import MIMEText
import requests
import sys

'''Variables'''


argumentU = str(sys.argv[1])
argumentP = str(sys.argv[2])
prodCheck = bool(sys.argv[3])
if argumentU[16:] == 'sb':
    env = 'DEV'
elif argumentU[16:] == 'd2':
    env = 'QA'
else:
    env = 'PROD'
object = 'OutgoingMessage'

'''Functions'''


def prodObjectCheck(prod):
    # api-endpoint
    URL_Objects = "https://fse-na-sb-int01.cloud.clicksoftware.com/so/api/objects/"
    PRODURL_Objects = "https://fse-na-int01.cloud.clicksoftware.com/so/api/objects/"
    if prod:
        return PRODURL_Objects
    else:
        return URL_Objects

def GetClickObject(obj, PARAMS, url, username, password):
    print(url + obj + "?" + PARAMS)
    ObjList = []
    # Get REST Call
    try:
        from requests.auth import HTTPBasicAuth
        r = requests.get(url=url + obj + "?" + PARAMS,
                         auth=(username, password))
        print(r.status_code)
        if (r.status_code == 200 or r.status_code == 500):
            # convert string response to Python JSON
            data = r.json()
            # loop through objects and create an object List
            for item in data:
                ObjList.append(item)
            return ObjList
    except Exception as e:
        print(e)


def currentDateTimeminusHours():
    # If its 12 pst go back to 6 am else if its 4 pm pst go back 4 hours to 12
    # Covers the whole day
    if datetime.datetime.utcnow().hour == 19:
        current_Time = datetime.datetime.utcnow() - datetime.timedelta(hours=6)
    else:
        current_Time = datetime.datetime.utcnow() - datetime.timedelta(hours=4)
    date_format = datetime.datetime.__format__(current_Time, '%Y-%m-%dT%H:%M:%SZ')
    return date_format


def currentDateTimeFormat():
    current_Time = datetime.datetime.utcnow()
    date_format = datetime.datetime.__format__(current_Time, '%Y-%m-%dT%H:%M:%SZ')
    return date_format


# Currently not in use but canbe used to change time period to 2 weeks back in time
def calculateDate2WeeksPastandFormat():
    timeDiff = datetime.datetime.utcnow() - datetime.timedelta(days=14)
    timeDiff_format = datetime.datetime.__format__(timeDiff, '%Y-%m-%dT%H:%M:%SZ')
    return timeDiff_format


def contructParamforClickObject(currentDate, pastDate, messageName, messageNum):
    param = "$select=TimeCreated_Minute,Body,MessageName,MessageStatus&$filter=TimeCreated_Minute gt %s " \
            "and TimeCreated_Minute lt %s " \
            "and MessageStatus eq %d and MessageName eq '%s'" % (pastDate, currentDate, messageNum, messageName)
    return param


def contructEmail(objs):
    result = ''
    # Create the body for the email and set it to result
    for o in objs:
        result += "\n" + "Key: " + str(o["Key"]) + "\n" + "MessageName: " + str(o['MessageName']) + "\n" + \
                  "MessageStatus: " + str(o['MessageStatus']) + "\n" + \
                  "Body: " + str(o['Body']) + '\n'

    '''Variables'''
    smtp_port = 00
    smtp_server = ''
    sender_email = ""
    reciever_email = ""
    subject = f"{env}:Integration Monitor AssignmentComplete Error(s)"
    body = result
    '''Message object'''
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = sender_email
    message["To"] = reciever_email
    '''Server set up and connection'''
    try:
        smtp_obj = smtplib.SMTP(smtp_server, smtp_port)

        smtp_obj.sendmail(sender_email, reciever_email, message.as_string())
        smtp_obj.quit()

        print("Email Success")
        print(f'From: {sender_email}')
        print(f'To: {reciever_email}')
        print(f'Subject::{subject}')
        print(f'Body:{body}')
    except smtplib.SMTPException as e:
        print("Error:", str(e))


'''Main'''

objs = GetClickObject(object, contructParamforClickObject(currentDateTimeFormat(), currentDateTimeminusHours(),
                                                          messageName='AssignmentCompleted', messageNum=2),
                      prodObjectCheck(prodCheck), argumentU, argumentP)
print(argumentU)
print(argumentP)
print(prodCheck)

if objs.__len__() > 0:
    contructEmail(objs)
exit(0)
