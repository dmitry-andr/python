"""
home automation script
emailing is built on google apis

Installation steps:
1) Enter value for SERVICE_EMAIL_SEND_TO - email execution result is sent to
2) Enter value for SERVICE_EMAIL_FOR_INCOMING_COMMANDS - email configured to recieve command emails
   this email is used to get credentials.json in google developer console
3) run init_gmail_authorization.py to pass oauth2 and generate token json
4) current main file can be executed as python program or added as cronjob for execution on schedue

montioring_data_manager.py - utility to read temperature data using sensors connected to raspberry pi
servomotor_driver.py - raspberry pi driver to rotate servomotor pushing button of air conditioner remote control
"""

# [START gmail_send_message]
import base64
import os
import numpy as np
import sys
from subprocess import call
import monitoring_data_manager
import init_gmail_authorization
import tas_file_util
import servomotor_driver
from email.message import EmailMessage


from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from bs4 import BeautifulSoup

PRINT_INCOMING_EMAIL_DATA = False
PRINT_DEVELOPMENT_DEBUG_DATA = False

SERVICE_EMAIL_SEND_TO = "d*k@gmail.com"
SERVICE_EMAIL_FOR_INCOMING_COMMANDS = "a*25@gmail.com"

# If modifying these scopes, delete the file token.json.
#SCOPES = ["https://www.googleapis.com/auth/gmail.readonly", "https://www.googleapis.com/auth/gmail.compose"]
MESSAGE_SUMMARY_ELEMENT_SEPARATOR = '#element_separator#'
ACTION_MESSAGE_SUBJECT_TEMPLATE = 'tas home automation action'
NO_MESSAGES_ENTRY = 'no_messages_recieved'
TIMESTAMPS_FILE = 'action_timestamps_list.txt'
ACTION_TO_PERFORM_SEND_COMMANDS_LIST = 'sendcommandslist'
ACTION_TO_PERFORM_SEND_REPORT = 'sendreport'
ACTION_TO_PERFORM_TOOGLE_ACTUATOR = 'toogleactuator'
ACTION_TO_PERFORM_SHUTDOWN_PI = 'shutdownpi'
REPLY_MESSAGE_SUBJECT = 'tas home action completed : '
SYSTEM_START_PARAM= 'home_automation_script_system_start'



def gmail_send_message(recipient, subject, body):
  """Create and send an email message
  Print the returned  message id
  Returns: Message object, including message id

  Load pre-authorized user credentials from the environment.
  TODO(developer) - See https://developers.google.com/identity
  for guides on implementing OAuth2 for the application.
  """
  creds = Credentials.from_authorized_user_file(tas_file_util.resolve_absolute_path_of_executables() + "token.json", init_gmail_authorization.SCOPES)

  try:
    service = build("gmail", "v1", credentials=creds)
    message = EmailMessage()

    message.set_content(body)
    
    send_to = SERVICE_EMAIL_SEND_TO
    if recipient is not None and recipient != SERVICE_EMAIL_SEND_TO :
      send_to += ',' + recipient
    message["To"] = send_to
    message["From"] = SERVICE_EMAIL_FOR_INCOMING_COMMANDS
    message["Subject"] = REPLY_MESSAGE_SUBJECT + subject

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    # pylint: disable=E1101
    send_message = (
        service.users()
        .messages()
        .send(userId="me", body=create_message)
        .execute()
    )
    print(f'Message Id: {send_message["id"]}')
  except HttpError as error:
    print(f"An error occurred: {error}")
    send_message = None
  return send_message


def gmail_read_messages():
  creds = Credentials.from_authorized_user_file(tas_file_util.resolve_absolute_path_of_executables() + "token.json", init_gmail_authorization.SCOPES)
  try:
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().list(userId='me', labelIds=['INBOX']).execute()
    messages = results.get('messages',[]);
    if not messages:
      messages_summary = [NO_MESSAGES_ENTRY]
      print('No new messages.')
    else:
      messages_summary = [''] * len(messages)
      msg_index = 0
      for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()                
        email_data = msg['payload']
        subject = ""
        sender = ""
        for header in email_data["headers"]:
          if header["name"] == "Subject":
            subject = header["value"]
          if header["name"] == "From":
            sender = header["value"]
            
        #print(f"-{sender}, {subject}, {messages}")
        # The Body of the message is in Encrypted format. So, we have to decode it.
        # Get the data and decode it with base 64 decoder.
        parts = email_data.get('parts')[0]
        data = parts['body']['data']
        data = data.replace("-","+").replace("_","/")
        decoded_data = base64.b64decode(data)

        # Now, the data obtained is in lxml. So, we will parse 
        # it with BeautifulSoup library
        soup = BeautifulSoup(decoded_data , "lxml")
        body = soup.body()
        if PRINT_INCOMING_EMAIL_DATA :
          print("Subject: ", subject)
          print("From: ", sender)
          print("Message: ", body)
          print('********************** \n')
        msg_summary = str(sender) + MESSAGE_SUMMARY_ELEMENT_SEPARATOR + str(subject) + MESSAGE_SUMMARY_ELEMENT_SEPARATOR + str(body) + MESSAGE_SUMMARY_ELEMENT_SEPARATOR + message['id']
        messages_summary[msg_index] = msg_summary
        msg_index += 1
      print(str(msg_index) + ' - Messages recieved')
  except HttpError as error:
    print(f"An error occurred: {error}")
  return messages_summary

def trash_message(msg_id):
  creds = Credentials.from_authorized_user_file(tas_file_util.resolve_absolute_path_of_executables() + "token.json", init_gmail_authorization.SCOPES)
  try:
    service = build("gmail", "v1", credentials=creds)
    results = service.users().messages().trash(userId="me", id=msg_id).execute()
  except HttpError as error:
    print(f"An error occurred: {error}")

def find_not_processed_messages(messages_list):
  not_processed_messages = []
  for message in messages_list:
    if(message.find(NO_MESSAGES_ENTRY) < 0 and is_action_subject(get_subject_part_of_msg_summary(message)) and not is_timestamp_exist_in_file(get_timestamp_from_subject(get_subject_part_of_msg_summary(message)))):
      not_processed_messages.append(message)
      add_timestamp_in_file(get_timestamp_from_subject(get_subject_part_of_msg_summary(message))) 
  return not_processed_messages

def get_sender_part_of_msg_summary(message_summary):
  return message_summary.split(MESSAGE_SUMMARY_ELEMENT_SEPARATOR)[0].split('<')[1].replace(">", "")

def get_subject_part_of_msg_summary(message_summary):
  return message_summary.split(MESSAGE_SUMMARY_ELEMENT_SEPARATOR)[1]

def get_timestamp_from_subject(subject):
  return subject.split('-')[1].strip()

def get_body_part_of_msg_summary(message_summary):
  return message_summary.split(MESSAGE_SUMMARY_ELEMENT_SEPARATOR)[2]

def get_message_id_of_msg_summary(message_summary):
  return message_summary.split(MESSAGE_SUMMARY_ELEMENT_SEPARATOR)[3]

def is_action_subject(subject):
  return subject.find(ACTION_MESSAGE_SUBJECT_TEMPLATE) >= 0

def is_report_action_in_body(body):
  return body.find(ACTION_TO_PERFORM_SEND_REPORT) >= 0

def is_toogle_action_in_body(body):
  return body.find(ACTION_TO_PERFORM_TOOGLE_ACTUATOR) >= 0

def is_shutdownpi_action_in_body(body):
  return body.find(ACTION_TO_PERFORM_SHUTDOWN_PI) >= 0

def is_send_commands_list_action_in_body(body):
  return body.find(ACTION_TO_PERFORM_SEND_COMMANDS_LIST) >= 0

def is_timestamp_exist_in_file(timestamp):
  if len(timestamp) == 0:
    return True #for empty timestamps treat them as already processed to avoid multiple times excution
  timestamps_processed = get_timestamps_from_file()
  if len(timestamps_processed) > 0:
    for timestamp_in_file in timestamps_processed:
      if timestamp == timestamp_in_file:
        return True
  return False

def get_timestamps_from_file():
  if os.path.exists(TIMESTAMPS_FILE):
      file = open(TIMESTAMPS_FILE, "r+")
      lines = []
      for line in file.readlines():
        lines.append(line.replace('\n', ''))
      return lines
  else:
    return []

def add_timestamp_in_file(timestamp):
  if os.path.exists(TIMESTAMPS_FILE):
      file = open(TIMESTAMPS_FILE, "a")
      file.write(str(timestamp) + "\n")
      file.close()
  else:
    with open(TIMESTAMPS_FILE, 'w') as file:
        file.write(str(timestamp) + "\n")

def process_message_action(not_processed_messages):
  for message in not_processed_messages:
    body = get_body_part_of_msg_summary(message)
    if is_report_action_in_body(body):
      gmail_send_message(get_sender_part_of_msg_summary(message), ACTION_TO_PERFORM_SEND_REPORT, monitoring_data_manager.get_temperature_summary())
    if is_shutdownpi_action_in_body(body):
      gmail_send_message(get_sender_part_of_msg_summary(message), ACTION_TO_PERFORM_SHUTDOWN_PI, 'Shutting down raspberrypi in 1 minute. \n\nCurrent state listed below \n' + monitoring_data_manager.get_temperature_summary())
      call("sudo shutdown --poweroff", shell=True)
    if is_toogle_action_in_body(body):
      servomotor_driver.rotate_to_angle_in_pulse_width_and_return(6.56)
      gmail_send_message(get_sender_part_of_msg_summary(message), ACTION_TO_PERFORM_TOOGLE_ACTUATOR, '\n\nCurrent state listed below \n' + monitoring_data_manager.get_temperature_summary())
    if is_send_commands_list_action_in_body(body):
      commands_list = ACTION_TO_PERFORM_SEND_COMMANDS_LIST + '\n'
      commands_list += ACTION_TO_PERFORM_SEND_REPORT + '\n'
      commands_list += ACTION_TO_PERFORM_TOOGLE_ACTUATOR + '\n'
      commands_list += ACTION_TO_PERFORM_SHUTDOWN_PI + '\n'
      gmail_send_message(get_sender_part_of_msg_summary(message), ACTION_TO_PERFORM_SEND_COMMANDS_LIST, commands_list + '\n\nCurrent state listed below \n' + monitoring_data_manager.get_temperature_summary())
    trash_message(get_message_id_of_msg_summary(message))

def main():
  """
  This function serves as the entry point of the program.
  """
  if len(sys.argv) > 1:
    param_value = sys.argv[1]
    if param_value == SYSTEM_START_PARAM:
      gmail_send_message(None, SYSTEM_START_PARAM, monitoring_data_manager.get_temperature_summary())
  messages_summary = gmail_read_messages()
  not_processed_messages = find_not_processed_messages(messages_summary)
  process_message_action(not_processed_messages)
  
  if PRINT_DEVELOPMENT_DEBUG_DATA:
    print(tas_file_util.resolve_absolute_path_of_executables())
    print(str(len(not_processed_messages)) + ' - to process')
    print(monitoring_data_manager.get_temperature_summary())
    
    
if __name__ == "__main__":
  main()



