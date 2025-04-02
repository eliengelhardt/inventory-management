import logging
from datetime import datetime, timedelta, date, timezone
import os
import pickle
import ast
import json
from collections import defaultdict
from backup_constants import ALL_PICKLE_PATH
from firebase_functions import initialize_firebase, authenticate_user, get_database, push_request, fetch_response

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')

loc_of_walmart_fba_sku_dict = ALL_PICKLE_PATH + "/walmart_fba_sku_info_for_shipments.pkl"
loc_of_supply_name_file = ALL_PICKLE_PATH + "/walmart_sku_to_parent_variation_num_dict.pkl"
market_id_USA = "ATVPDKIKX0DER"

def load_data(file_path):
    if os.path.exists(file_path):
        with open(file_path, "rb") as file:
            return pickle.load(file)
    return {}

def identify_new_skus(existing_skus, all_skus):
    new_skus = [sku for sku in all_skus if sku not in existing_skus]
    logging.debug(f"New SKUs needing data: {new_skus}")
    return new_skus

def get_sku_details(all_inventory, new_skus_need_data_for):
    result = {}
    for item in all_inventory:
        if item['sku'] in new_skus_need_data_for:
            result[item['sku']] = {
                'wpid': item['wpid'],
                'product_name': item['productName'],
                'creation_timestamp': '',
                'if_mature': ''
            }
    return result

def get_sku_of_excel(db, auth_token):
    logging.info("Start running method: get_sku_of_excel")
    try:
        walmart_fba_sku_dict = load_data(loc_of_walmart_fba_sku_dict)
        logging.debug(f"walmart_fba_sku_dict:{walmart_fba_sku_dict}")
        walmart_sku_to_par_var_dict = load_data(loc_of_supply_name_file)

        new_skus_need_data_for = identify_new_skus(walmart_fba_sku_dict, walmart_sku_to_par_var_dict)

        if new_skus_need_data_for:
            all_inventory = get_walmart_inventory_all(db, auth_token)
            new_sku_data = get_sku_details(all_inventory, new_skus_need_data_for)
            walmart_fba_sku_dict.update(new_sku_data)

        logging.debug(f"Updated SKU dictionary: {len(walmart_fba_sku_dict)}")

        return list(walmart_fba_sku_dict.keys())

    except Exception as e:
        logging.error(f"Error in get_sku_of_excel: {e}")
        return []
    finally:
        logging.info("End method: get_sku_of_excel")

def get_walmart_inventory_all(db, auth_token):
    """
    Fetches all inventory data from Walmart API for query later
    """
    logging.info("Start method: get_walmart_inventory_all")
    try:
        all_items = [] 

        response = {}
        next_cursor = "*"

        while True:

            request = {
                "api_key": "6695af7d2b581489fd4fdcfff9e98cac4aa7a0cec01a42d3194d6e0cab91abb0",
                "url": f"https://marketplace.walmartapis.com/v3/items",
                "body": {"nextCursor": next_cursor, 
                            "limit": "50", 
                            }
            }
            result_id = push_request(db, auth_token, request)
            response = fetch_response(db, auth_token, result_id)

            #data = response.json()
            # Convert string (response) to dictionary
            data = ast.literal_eval(response)

            # Save the items from the current response
            all_items.extend(data.get("ItemResponse", []))
            
            # Check if there's a nextCursor for the next page
            next_cursor = data.get("nextCursor")
            if not next_cursor:
                break

        # Save all items to a JSON file
        with open("all_items.json", "w") as f:
            json.dump(all_items, f)

        logging.debug(f"All Inventory Items Response: {response}")
        return all_items
    except Exception as e:
        logging.error(f"Error in method get_walmart_inventory_all: {e}")
    finally:
        logging.info("End method: get_walmart_inventory_all")
    

def date_to_utc_time(str):
    utc_time = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S.%fZ")
    milliseconds = (utc_time - datetime(1970, 1, 1)) // timedelta(milliseconds=1)
    return milliseconds


def check_error(response):
    if 'errors' in response and 'error' in response['errors']:
        for error in response['errors']['error']:
            if 'code' in error and 'CONTENT_NOT_FOUND' in error['code']:
                return True
    return False


def extract_date_from_timestamp(timestamp):
    # Parse the timestamp from ISO format and extract the date
    date = datetime.fromisoformat(timestamp).date()
    return str(date)

def convert_timestamp_to_date_with_offset(timestamp, offset_hours = -7):
    try:
        if timestamp:
            # Convert milliseconds to seconds
            timestamp = int(timestamp) / 1000
            
            # Create timezone with the specified offset
            tz = timezone(timedelta(hours=offset_hours))
            
            # Convert timestamp to date with specified timezone
            date = datetime.fromtimestamp(timestamp, tz=tz)
            
            # Return only the date as a string in the format YYYY-MM-DD
            return date.strftime('%Y-%m-%d')
        
    except Exception as e:
        logging.error(f"Error in convert_timestamp_to_date_with_offset:, {e}")

def get_start_date_with_timestamp(days_ago):
    start_date_obj = datetime.today() - timedelta(days=days_ago)
    start_date_str = start_date_obj.strftime('%Y-%m-%d') + "T00:00:00-07:00"
    return start_date_str

def get_end_date_with_timestamp():
    end_date_obj = datetime.today()
    end_date_str = end_date_obj.strftime('%Y-%m-%d') + "T00:00:00-07:00"
    return end_date_str

def generate_date_list(start_date, end_date):
    # Parse the start and end dates
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    
    # Generate the list of dates
    date_list = []
    current_date = start
    while current_date <= end:
        date_list.append(current_date.strftime("%Y-%m-%d"))
        current_date += timedelta(days=1)
    
    return date_list

def get_walmart_latest_sales(db, auth_token, days_ago):
    """
    Fetches all latest sales data from Walmart API for query later
    """
    logging.info("Start method: get_walmart_latest_sales")
    try:
        all_items = [] 

        next_cursor = "*"
        
        start_date_str = get_start_date_with_timestamp(days_ago)
        end_date_str = get_end_date_with_timestamp()
        
        while True:

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
            result_id = push_request(db, auth_token, request)
            response = fetch_response(db, auth_token, result_id)

            #data = response.json()
            # Convert string (response) to dictionary
            response_dict = ast.literal_eval(response)
            logging.info("ORDER_TYPE" +str(type(response_dict)))
            logging.info(f"ORDERS_GET: {response_dict}")
            # Extract the list of orders
            orders_json = response_dict['list']['elements']['order']

            # Save the items from the current response
            all_items.extend(orders_json)

            logging.info(f"ALL_ORDER_ITEMS {all_items}")
            # Check if there's a nextCursor for the next page
            next_cursor = response_dict.get("nextCursor")
            if not next_cursor:
                break

        # Save all items to a JSON file
        with open("all_sales.json", "w") as f:
            json.dump(all_items, f)

        logging.debug(f"All Sales Items Response: {all_items}")
        return all_items
    except Exception as e:
        logging.error(f"Error in method get_walmart_latest_sales: {e}")
    finally:
        logging.info("End method: get_walmart_latest_sales")


def combine_units_sold_for_same_order_date(input_list):
    combined_orders = {}

    for order in input_list:
        order_date = order['orderDate']
        order_lines = order['orderLines']

        if order_date not in combined_orders:
            combined_orders[order_date] = {}

        for line in order_lines:
            for sku, amount in line.items():
                if sku in combined_orders[order_date]:
                    combined_orders[order_date][sku] += amount
                else:
                    combined_orders[order_date][sku] = amount

    result = []
    for order_date, skus in combined_orders.items():
        order_lines_list = [{sku: amount} for sku, amount in skus.items()]
        result.append({'orderDate': order_date, 'orderLines': order_lines_list})

    return result


def initialize_sku_units_sold(sku_list, days_ago):
    # Initialize the dictionary with 0 values for each SKU for the specified number of days
    sku_units_sold = {sku: [0] * days_ago for sku in sku_list}
    return sku_units_sold

def generate_temp_list_from_latest_sales(latest_sales):

    # Initialize the result dictionary
    result = []

    # Iterate over each order in latest_sales
    for order in latest_sales:

        # Extract the order date by converting the timestamp to date with format (yyyy-MM-DD)
        order_date = convert_timestamp_to_date_with_offset(order['orderDate'])
        
        # Extract the order lines
        order_lines = order['orderLines']['orderLine']
        
        # Initialize the list for order lines
        order_lines_list = []
        
        # Iterate over each order line
        for line in order_lines:
            sku = line['item']['sku']
            amount = int(line['orderLineQuantity']['amount'])
            order_lines_list.append({sku: amount})
        
        # Add the order date and order lines to the result list
        result.append({'orderDate': order_date, 'orderLines': order_lines_list})
        logging.debug(f"result_X: {result}")
    return result

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def update_combined_list_with_date_index(combined_list, dates_list):
    # Create a dictionary to map dates to their indices
    date_to_index = {date: index for index, date in enumerate(dates_list)}

    # Update the combined list with the orderDateIndex field
    for order in combined_list:
        order_date = order['orderDate']
        if order_date in date_to_index:
            order['orderDateIndex'] = date_to_index[order_date]

    return combined_list

def update_dict_with_unit_sold_data(order_list, sku_dict):
    for order in order_list:
        order_date_index = order['orderDateIndex']
        order_lines = order['orderLines']
        
        for line in order_lines:
            for sku, amount in line.items():
                if sku in sku_dict:
                    sku_dict[sku][order_date_index] += amount

    return sku_dict


def sales_for_skus(skus_of_excel, latest_sales, days_ago):
    try:
        logging.info("Start method: sales_for_skus")

        # initialize return variable
        result = {}
        # Initialize the return variable sku_units_sold_per_day by inserting 0 unit sold for each days
        sku_units_sold_per_day_dict = initialize_sku_units_sold(skus_of_excel, days_ago + 1) # add 1 for the day
        logging.debug(f"sku_units_sold_per_day {sku_units_sold_per_day_dict}")

        # generates date list and we will use the index to use when updating the index of sku_units_sold_per_day
        start_date_str = get_start_date_with_timestamp(days_ago)
        end_date_str = get_end_date_with_timestamp()
        logging.debug(f"start_date_str {start_date_str}")
        logging.debug(f"end_date_str {end_date_str}")

        start_date_str = extract_date_from_timestamp(start_date_str)
        end_date_str = extract_date_from_timestamp(end_date_str)
        logging.debug(f"start_date_str {start_date_str}")
        logging.debug(f"end_date_str {end_date_str}")

        dates_list = generate_date_list(start_date_str, end_date_str)
        logging.debug(f"dates_list {dates_list}")

        # generate dictionary from latest sales, getting the SKU and Units sold per Order Date

        #latest_sales = read_json_file("all_sales.json")
        if latest_sales:
            temp_list = generate_temp_list_from_latest_sales(latest_sales)
            combined_list = combine_units_sold_for_same_order_date(temp_list)
            update_combined_list = update_combined_list_with_date_index(combined_list, dates_list)
            logging.debug(f" update_combined_list : {update_combined_list}")
            
            result = update_dict_with_unit_sold_data(update_combined_list, sku_units_sold_per_day_dict)
            logging.debug(f" result : {result}")

            # Save all items to a JSON file
            with open("sales_for_skus.json", "w") as f:
                json.dump(result, f)           
        else:
            logging.warning("No data retrieved for latest_sales")
        return result
    except Exception as e:
        logging.error(f"Error in method sales_for_skus: {e}")
        return None
    finally:
        logging.info("End method: sales_for_skus")

