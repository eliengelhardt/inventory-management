import requests
import pickle
from backup_constants import ALL_PICKLE_PATH



# needs to change Walmart credentials
loc_of_cred_file = ALL_PICKLE_PATH + "/aws_cred.pkl"
cred_dict = pickle.load(open(loc_of_cred_file, "rb"))

CLIENT_ID = cred_dict["CLIENT_ID"]
CLIENT_SECRET = cred_dict["CLIENT_SECRET"]
ACCESS_TOKEN = "" 