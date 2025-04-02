import logging
import ast
import json
from firebase_functions import initialize_firebase, authenticate_user, get_database, push_request, fetch_response

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')

def get_walmart_item_inventory_for_all_ship_nodes(db, auth_token):
    """
    Fetches all inventory data from Walmart API for query later
    """
    logging.info("Start method: get_walmart_item_inventory_for_all_ship_nodes")
    try:
        all_items = [] 

        response = {}
        next_cursor = ""

        while True:

            request = {
                "api_key": "6695af7d2b581489fd4fdcfff9e98cac4aa7a0cec01a42d3194d6e0cab91abb0",
                "url": f"https://marketplace.walmartapis.com/v3/inventories",
                "body": {"nextCursor": next_cursor, 
                            "limit": "50", 
                            }
            }
            result_id = push_request(db, auth_token, request)
            response = fetch_response(db, auth_token, result_id)

            #data = response.json()
            # Convert string (response) to dictionary
            response_dict = ast.literal_eval(response)

            data_json = response_dict['elements']['inventories']
            logging.info(f"ALL_INVENTORY_ITEMS {data_json}")
            # Save the items from the current response
            all_items.extend(data_json)
            logging.info(f"ALL_INVENTORY_ITEMS {all_items}")
            # Check if there's a nextCursor for the next page

            if not "nextCursor" in response_dict['meta']:
                logging.debug("NO nextCursor")
                break
            else:
                logging.debug("Has nextCursor")

        # Save all items to a JSON file
        with open("item_inventory_for_all_ship_nodes.json", "w") as f:
            json.dump(all_items, f)

        logging.debug(f"All Inventory Items Response: {response}")
        return all_items
    except Exception as e:
        logging.error(f"Error in method get_walmart_item_inventory_for_all_ship_nodes: {e}")
    finally:
        logging.info("End method: get_walmart_item_inventory_for_all_ship_nodes")

def extract_inventory_count_per_sku(data):

    inventory_count_of_sku = {}
    for item in data:
        sku = item["sku"]
        for node in item["nodes"]:
            input_qty = node["inputQty"]["amount"]  # sum of avail_to_sell_qty and reserved_qty
            avail_to_sell_qty = node["availToSellQty"]["amount"]
            reserved_qty = node["reservedQty"]["amount"]
            #good_inventory = availToSellQty  + (reservedQty - PendingCustomerOrderQty)
            # since inventory does not expose PendingCustomerOrderQty, we will use input_qty as the good inventory
            good_inventory = input_qty
            inventory_count_of_sku[sku] = good_inventory
    return inventory_count_of_sku

def get_inventory_level_per_sku(raw_sales_data, inventory_count_of_sku, total_days_of_inventory_to_have, long_days_ago, short_term_days):
    """
     It calculates the required inventory levels based on long-term and short-term sales data, considering the total days of inventory to maintain and shipment frequency.
     """
    # Initialize inventory level dictionary
    inventory_level_per_sku = {}

    # Process each SKU
    for sku in raw_sales_data:
        cur_list = raw_sales_data[sku]  # spot 0 is oldest spot

        # Calculate long-term and short-term sales totals
        long_tot, short_tot = calculate_sales_totals(cur_list, short_term_days)

        # Calculate needed inventory
        needed_inventory = calculate_needed_inventory(long_tot, short_tot, long_days_ago, short_term_days, total_days_of_inventory_to_have)

        # Create inventory details dictionary
        inventory_details = {
            "short_term_sales": short_tot,
            "long_term_sales": long_tot,
            "total_inventory_required": needed_inventory
        }

        # Calculate the amount to ship
        need_to_ship = needed_inventory - inventory_count_of_sku.get(sku, 0)
        if need_to_ship < 0:
            need_to_ship = 0
        inventory_details["need_to_ship"] = need_to_ship

        # Update inventory level per SKU
        inventory_level_per_sku[sku] = inventory_details
    logging.info(f" inventory_level_per_sku {inventory_level_per_sku}")

# Function to calculate sales totals
def calculate_sales_totals(sales_data, short_term_days):
    long_tot = 0
    short_tot = 0
    for i in range(len(sales_data) - 1, 0, -1):
        val = sales_data[i]
        long_tot += val
        if (len(sales_data) - 1) - i < short_term_days:
            short_tot += val
    logging.info(f" long_tot : {long_tot}")
    logging.info(f" short_tot : {short_tot}")
    return long_tot, short_tot

# Function to calculate needed inventory
def calculate_needed_inventory(long_tot, short_tot, long_days_ago, short_term_days, total_days_of_inventory_to_have):
    extrapolated_short_tot = float(long_days_ago / short_term_days) * short_tot
    avg_tot = float(long_tot + extrapolated_short_tot) / 2
    needed_inventory = round(float(total_days_of_inventory_to_have / long_days_ago) * avg_tot)
    logging.info(f" needed_inventory : {needed_inventory}")
    return needed_inventory

def make_excel_temp(db, auth_token, raw_sales_data, total_days_of_inventory_to_have, long_days_ago, short_term_days):
    """ 
        if os.path.exists(loc_of_shipment_nums_excel_file):
            os.remove(loc_of_shipment_nums_excel_file)

        if os.path.exists(loc_of_check_excel_file):
            os.remove(loc_of_check_excel_file)
    """
    inventory_data = get_walmart_item_inventory_for_all_ship_nodes(db, auth_token)
    inventory_count_of_sku = extract_inventory_count_per_sku(inventory_data)
    get_inventory_level_per_sku(raw_sales_data = raw_sales_data, inventory_count_of_sku = inventory_count_of_sku, total_days_of_inventory_to_have =total_days_of_inventory_to_have, long_days_ago =long_days_ago, short_term_days = short_term_days)