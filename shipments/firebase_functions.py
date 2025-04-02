import pyrebase
import logging
import time
# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')

def initialize_firebase():
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
    firebase = pyrebase.initialize_app(firebase_config)
    logging.info("Firebase initialized")
    return firebase

def authenticate_user(firebase, email, password):
    auth = firebase.auth()
    retries = 3
    for attempt in range(retries):
        try:
            user = auth.sign_in_with_email_and_password(email, password)
            logging.info("User authenticated")
            return user['idToken']
        except Exception as e:
            logging.error(f"Authentication failed: {e}")
            if attempt < retries - 1:
                logging.info("Retrying...")
                time.sleep(2)  # Wait for 2 seconds before retrying
            else:
                logging.error(f"All retries failed {e}")


def get_database(firebase):
    logging.info("Database instance obtained")
    return firebase.database()

def push_request(db, auth_token, request):
    retries = 3
    for attempt in range(retries):
        try:
            result = db.child("requests").push(request, auth_token)
            result_id = result['name']
            logging.info(f"Pushed request with ID: {result_id}")
            return result_id
        except Exception as e:
            logging.error(f"Error pushing request: {e}")
            if attempt < retries - 1:
                logging.info("Retrying...")
                time.sleep(5)  # Wait for 2 seconds before retrying
            else:
                logging.error("All retries failed")
                return None

def fetch_response(db, auth_token, result_id):
    retries = 3
    for attempt in range(retries):
        time.sleep(20)  # Wait for 5 seconds before each attempt
        if result_id:
            try:
                actual_response = {}
                responses = db.child(f"responses/{result_id}").get(auth_token).val()
                if responses is not None:
                    actual_response = responses['response']
                    logging.info(f"Response found: {actual_response}")
                    return actual_response
                else:
                    logging.info(f"No response yet at /responses/{result_id}")
                    if attempt < retries - 1:
                        logging.info("Retrying...")
                    else:
                        logging.error("All retries failed")
                        return None
            except Exception as e:
                logging.error(f"Error fetching response: {e}")
                if attempt < retries - 1:
                    logging.info("Retrying...")
                else:
                    logging.error("All retries failed")
                    return None
    return None