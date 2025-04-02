from backup_inventory import before_run
from backup_constants import ALL_PICKLE_PATH, ALL_PICKLE_PATH_COPY
from fetch_recent_sales_data import get_sku_of_excel, sales_for_skus, get_walmart_inventory_all, get_walmart_latest_sales, load_data
from shipment_calculations import make_excel_temp   
from firebase_functions import initialize_firebase, authenticate_user, get_database
import logging
import time

logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')

def main():
    start_time = time.time()
    logging.info("Starting Walmart Inventory Management System")

    # Guide link:
    # https://docs.google.com/document/d/1NvqlAJ-V3I3n31Smr9MuI5eZgGHGrGdme5CjzDQW4CM/edit?usp=sharing.

    # 1) Inventory Backup: 
    # Copy current inventory files before making any modifications. 
    before_run(ALL_PICKLE_PATH, ALL_PICKLE_PATH_COPY)

    firebase = initialize_firebase()
    auth_token = authenticate_user(firebase, "general_user@gmail.com", "pass123")
    db = get_database(firebase)

    # 2) Sales Data Retrieval: 
    # Use the Walmart API to fetch recent(since last shipment) sales data.
    # 3)  Inventory Status: 
    # Retrieve current Walmart inventory levels and track inventory currently being shipped. 
    long_days_ago = 32

    skus_of_excel = get_sku_of_excel(db, auth_token)    
    print(skus_of_excel)

    latest_sales = get_walmart_latest_sales(db, auth_token, long_days_ago)  
    raw_sales_data = sales_for_skus(skus_of_excel, latest_sales, long_days_ago)
    print(raw_sales_data)

    days_of_inventory_to_always_have_at_walmart = 60
    shipment_frequency_days = 14
    short_term_days = 8
    total_days_of_inventory_to_have = days_of_inventory_to_always_have_at_walmart + shipment_frequency_days
    make_excel_temp(db = db, auth_token = auth_token, raw_sales_data = raw_sales_data, total_days_of_inventory_to_have = total_days_of_inventory_to_have, long_days_ago = long_days_ago, short_term_days=short_term_days)

    end_time = time.time()
    elapsed_time = end_time - start_time
    logging.info(f"Run completed in {elapsed_time:.2f} seconds")    

if __name__ == "__main__":
    main()