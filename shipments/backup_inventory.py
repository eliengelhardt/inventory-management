import os
import pickle
import shutil
import logging

# Configure logging
logging.basicConfig(filename='app.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s', filemode='a')

def create_directory(path):
    logging.info(f"Running method: create_directory for path {path}")
    if not os.path.exists(path):
        try:
            os.makedirs(path)
            logging.info(f"Directory created: {path}")
        except OSError as e:
            logging.error(f"Error creating directory {path}: {e}")
            exit()

def load_pickle_files(path):
    try:
        all_files = os.listdir(path)
        if all_files:
            for name in all_files:
                if name != ".DS_Store":
                    try:
                        with open(os.path.join(path, name), "rb") as file:
                            pickle.load(file)
                    except pickle.UnpicklingError:
                        logging.error(f"Error: pickle file {name} corrupted")
                        return False
            return True
    except Exception as e:
        logging.error(f"Error in load_pickle_files: {e}")    

def copy_files(src_folder, dest_folder):
    # Ensure the destination folder exists
    if not os.path.exists(dest_folder):
        os.makedirs(dest_folder)
    
    # Iterate over all files in the source folder
    for item in os.listdir(src_folder):
        src_path = os.path.join(src_folder, item)
        dest_path = os.path.join(dest_folder, item)
        
        # Copy files only (not directories)
        if os.path.isfile(src_path):
            if not os.path.exists(dest_path):
                shutil.copy2(src_path, dest_path)
            else:
                shutil.copy2(src_path, dest_path)
              
        
def before_run(all_pickle_path, all_pickle_path_copy):
    logging.info(f"Running inventory backup...")

    #create_directory(all_pickle_path)
    #create_directory(all_pickle_path_copy)

    if not load_pickle_files(all_pickle_path):
        logging.error("Error: pickle files corrupted before run")
        exit()

    try:
        copy_files(all_pickle_path, all_pickle_path_copy)
    except Exception as e:
        logging.error(f"Error in deleting path {all_pickle_path_copy}")

    if not load_pickle_files(all_pickle_path_copy):
        logging.error("Error: copied pickle files corrupted before run")
        exit()
    
    logging.info(f"Completed inventory backup.")

