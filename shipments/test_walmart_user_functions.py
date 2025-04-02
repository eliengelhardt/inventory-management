import pyrebase
import time
from datetime import datetime, timedelta, date, timezone

# Firebase configuration
firebase_config = {
    "apiKey": "AIzaSyCoDijiYFUe5CHcS--d-EZUZAK6n6NlA-E",
    "authDomain": "walmart-api-caller.firebaseapp.com",
    "databaseURL": "https://walmart-api-caller-default-rtdb.firebaseio.com",
    "projectId": "walmart-api-caller",
    "storageBucket": "walmart-api-caller.firebasestorage.app",
    "messagingSenderId": "91738307977",
    "appId": "1:91738307977:web:d21a5ca30f1dc7248df558",
    "measurementId": "G-J5M8NPRTBJ"
}

# Initialize Firebase
firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()

# Sign into user
email = "general_user@gmail.com"
password = "pass123"
user = auth.sign_in_with_email_and_password(email, password)
auth_token = user['idToken']

# Get the database instance with the authenticated user
db = firebase.database()

# To ask for info from function
#to add a body/query parameters to request add "body" as the key
end_date_obj = datetime.today()
start_date_obj = datetime.today() - timedelta(days=31)
end_date_str = end_date_obj.strftime('%Y-%m-%d') + "T00:00:00-07:00"
start_date_str = start_date_obj.strftime('%Y-%m-%d') + "T00:00:00-07:00"
#
wpid ="3MUP9F7D1ABC"
upc ="810150881219"
gtin = "00810150881219"
ship_node_id = "ATVPDKIKX0DER"
sku = "7N-YZSA-UHN4" 
sku = "4J-B4HG-NKQ6"
next_cursor = "*"

request = {
    "api_key": "6695af7d2b581489fd4fdcfff9e98cac4aa7a0cec01a42d3194d6e0cab91abb0",
    "url": f"https://marketplace.walmartapis.com/v3/inventory",
    "body": {
                "sku": f"{sku}", 
                }
}

""""
request = {
    "api_key": "6695af7d2b581489fd4fdcfff9e98cac4aa7a0cec01a42d3194d6e0cab91abb0",
    "url": f"https://marketplace.walmartapis.com/v3/orders",
    "body": {"nextCursor": next_cursor, 
                "limit": "100", 
                "createdStartDate":start_date_str, 
                "createdEndDate": end_date_str,
                "shipNodeType": "WFSFulfilled"
                }
}
 """

""" 
request = {
    "api_key": "6695af7d2b581489fd4fdcfff9e98cac4aa7a0cec01a42d3194d6e0cab91abb0",
    "url": f"https://marketplace.walmartapis.com/v3/inventories"
    #"body": {"shipNodeType": "WFSFulfilled"
    #        }
}
"""

"""
request = {
    "api_key": "6695af7d2b581489fd4fdcfff9e98cac4aa7a0cec01a42d3194d6e0cab91abb0",
    "url": f"https://marketplace.walmartapis.com/v3/orders",
    "body": {"shipNodeType": "WFSFulfilled", 
            #"sku": sku, 
            "createdStartDate":start_date_str, 
            "createdEndDate": end_date_str
            }
}
"""


""" 
"body" : {
            "sku": f"{sku}",        
            "shipNode": ship_node_id
            # "createdStartDate":f"{start_date_str}", "createdEndDate":f"{end_date_str}"
            }
"""

try:
    result = db.child("requests").push(request, auth_token)
    result_id = result['name']
    print(f"Pushed request with ID: {result_id}")
except Exception as e:
    print(f"Error pushing request: {e}")
    result_id = None

# To get back response
time.sleep(5)
if result_id:
    try:
        responses = db.child(f"responses/{result_id}").get(auth_token).val()
        actual_response = responses['response']
        if responses is not None:
            print(f"Response found: {actual_response}")
            print(f"Response found")
        else:
            print(f"No response yet at /responses/{result_id}")

    except UnicodeEncodeError as e:
        print(f"Encoding error: {e}")

    except Exception as e:
        print(f"Error fetching response: {e}")
