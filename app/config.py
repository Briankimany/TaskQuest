
"""
A module to provide seeding configuration values
"""
from uuid import uuid4
from pathlib import Path
from dotenv import load_dotenv,set_key
import os 

load_dotenv()

INITIAL_TESTING_KEY= str(uuid4())

DOT_ENV_LOCATION = '.env'
TESTING_USER_ID =1
ATTRIBUTES_LIST = ['INT','STA','FCS','CHA','DSC']

TIME_PARSING_STRING =  "%H:%M"
DATE_PARSING_STRING = "%Y-%m-%d"
TIME_DATE_SEPARATOR = "T"

TEST_USER_ID = 1

app_folder =  Path(__file__).parent 
seed_folder =app_folder/'seed'
seed_data_folder = seed_folder /'data'

activites_seed_data = seed_data_folder /'activities.json'

TESTING_KEY = os.getenv("TESTING_KEY")
SUPPORT_EMAIL =os.getenv('SUPPORT_EMAIL7')

def modify_dotenv(key,value):
    set_key(DOT_ENV_LOCATION ,key ,value)

if not TESTING_KEY:
    TESTING_KEY = INITIAL_TESTING_KEY
    modify_dotenv('TESTING_KEY',INITIAL_TESTING_KEY)

if not SUPPORT_EMAIL:
    SUPPORT_EMAIL = 'support@testingdomain.com'
    modify_dotenv('SUPPORT_MAIL',SUPPORT_EMAIL)
