
"""
A module to provide seeding configuration values
"""
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv,set_key
import os 
import logging

app_folder =  Path(__file__).parent 

DOT_ENV_LOCATION = str((app_folder.parent /'.env').absolute())

load_dotenv(DOT_ENV_LOCATION)   

INITIAL_TESTING_KEY= str(uuid4())

ATTRIBUTES_LIST = ['INT','STA','FCS','CHA','DSC']

TIME_PARSING_STRING =  "%H:%M"
DATE_PARSING_STRING = "%Y-%m-%d"
TIME_DATE_SEPARATOR = "T"

TEST_USER_ID = 2

seed_folder =app_folder/'seed'
seed_data_folder = seed_folder /'data'

activites_seed_data = seed_data_folder /'activities.json'

TESTING_KEY = os.getenv("TESTING_KEY")
SUPPORT_EMAIL =os.getenv('SUPPORT_EMAIL')

def modify_dotenv(key,value):
    set_key(DOT_ENV_LOCATION ,key ,value)

if not TESTING_KEY:
    TESTING_KEY = INITIAL_TESTING_KEY
    modify_dotenv('TESTING_KEY',INITIAL_TESTING_KEY)
    load_dotenv(DOT_ENV_LOCATION)

if not SUPPORT_EMAIL:
    SUPPORT_EMAIL = 'support@testingdomain.com'
    modify_dotenv('SUPPORT_MAIL',SUPPORT_EMAIL)
  

## assistant config
assistant_config_folder = seed_data_folder /'assistant'
if not assistant_config_folder.exists():
    assistant_config_folder.mkdir(parents=True ,exist_ok=True)


if hasattr(logging,os.getenv('LOGGING_LEVEL','DEBUG')):
    LOGGING_LEVEL = getattr(logging,os.getenv('LOGGING_LEVEL','DEBUG'))
else:
    LOGGING_LEVEL = logging.DEBUG
