import os
import random
import re
import tweepy
import json
import time
import sqlite3

def create_array(array_unclean):
    return [cap_string_length(entry.strip()) 
        for entry in array_unclean if len(entry) > 12]

def cap_string_length(string):
    return string if len(string) < 160 else string[0:160]

def check_creds():
    try:
        cred_file = open("/home/bot/cred.json")
        cred_data = json.load(cred_file)
        auth = tweepy.OAuthHandler(cred_data['consumer_token'],
            cred_data['consumer_secret'])
        auth.set_access_token(cred_data['access_token'],
            cred_data['access_token_secret'])
        cred_file.close()
        return auth
    except IOError:
        consumer_token = input("Enter consmer token: ")
        consumer_secret = input("Enter consumer secret: ")
        auth = tweepy.OAuthHandler(consumer_token, consumer_secret)
        redirect_url = auth.get_authorization_url()
        print("Get verifier from: " + redirect_url)
        verifier = input("Input verifier: ")
        try:
            auth.get_access_token(verifier)
            cred_file = open("/home/bot/cred.json", 'w')
            json.dump({'consumer_token': consumer_token, 
                'consumer_secret' : consumer_secret,
                'access_token' : auth.access_token, 
                'access_token_secret' : auth.access_token_secret}, cred_file)
            cred_file.close()
            check_creds()
        except tweepy.TweepError:
            print("Try again. Get verifier from: " + redirect_url)
            check_creds()

def check_db(message):
    try:
        db_file = open(DB_FILE)
        db = sqlite3.connect(DB_FILE)
        found = db.cursor().execute("SELECT * from used where text=?", [message]).fetchone()
        if found:
            return True
        else:
            return False
    except FileNotFoundError:
        db = sqlite3.connect(DB_FILE)
        with open("/home/bot/schema.sql") as f:
            db.cursor().executescript(f.read())
        check_db(message)

def add_to_db(message):
    db = sqlite3.connect(DB_FILE)
    db.cursor().execute("INSERT INTO used(text) values (?)", [message])
    db.commit()

def generate_message(file_data):
    stripped_content = file_data
    regex = re.compile("(?!\.).+?\.|(?! ).+?\.|(?!\.).+?\?|(?! ).+?\?|(?!\.).+?:|(?! ).+\.|(?!\.).+?\n|(?! ).+?\n")
    groups = regex.findall(stripped_content)
    array_clean = create_array(groups)
    match_no = random.randrange(len(array_clean))
    db_match = check_db(array_clean[match_no])
    if not db_match:
        return array_clean[match_no]
    else:
        generate_message(file_name)

DIRECTORY = "/home/bot/files/"
DB_FILE = "/home/bot/sql.db"

if __name__ == "__main__":
    credentials = check_creds()
    api = tweepy.API(credentials)
    while True:
        file_list = os.listdir(DIRECTORY)
        file_choice = random.randrange(len(DIRECTORY))
        file_name = file_list[file_choice]
        try:
            file_content = open(DIRECTORY + file_name).read()
            message = generate_message(file_content)
            try:
                api.update_status(status=message)
                add_to_db(message)
                time.sleep(900)
            except tweepy.error.TweepError as e:
                print(message + "not sent, error: " + e)
        except UnicodeDecodeError:
            print(file_name + " not valid")
