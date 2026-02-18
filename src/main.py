import logging
import json


import shutil
import os

app_log_file = "app.log"
if os.path.exists(app_log_file):
  os.remove(app_log_file)
else:
  print("The file does not exist") 

logging.basicConfig(
    level=logging.DEBUG,  # Lowest level to capture
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler("app.log"),      # Logs everything to a file
        # logging.StreamHandler()             # Also prints to the console
    ]
)