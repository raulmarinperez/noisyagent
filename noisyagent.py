from http.server import BaseHTTPRequestHandler, HTTPServer
from event_scheduler import EventScheduler
from datetime import datetime, timedelta
from threading import Thread
from pathlib import Path
import requests
import argparse
import requests
import logging
import yaml
import json
import time
import glob
import os

release="0.3"

# Auxiliary classes
#

class NewsFeedRequestHandler(BaseHTTPRequestHandler):
  ''' Auxiliary class implementing a HTTPRequestHandler for our web server.
  '''

  def update_dates(self, news):
    ''' Function replacing all date place holders in the input parameter
        Parameters:
          news - String with the news that the web server will server
                 containing place holders to be replaced.
        Return:
          A string containing the news and the placeholder containing actual
          dates.
    '''

    # 1. Use current date as reference data and replace
    #    the 10 place holders
    dt_reference_date = datetime.now()    
    for i in range(0,10):
      date_place_holder = f"%date_{i}%"
      dt_i_date = dt_reference_date - timedelta(seconds=86400*(9-i))
      news = news.replace(date_place_holder,
                          dt_i_date.strftime("%a, %d %b %Y"))
    # 2. Return the new string
    return news
    
  def do_GET(self):
    ''' This function implements the logic to server HTTP GET request
        of our web server.
        Parameters:
          None - This function doesn't get any additional parameter
        Return:
          None - This function doesn't return anything
    '''
    # 1. Setup response code and headers
    self.send_response(200)
    self.send_header("Content-type", "application/xml")
    self.end_headers()
    # 2. Read the file containing the news from the file,
    #    replace the place holders and put it into the response.
    news = Path(self.news_file_path).read_text()    
    self.wfile.write(bytes(self.update_dates(news), "utf-8"))

class NewsFeedWebServer(Thread):
  ''' Class that will be used to run a web server in a thread concurrently 
      with the rest of the tasks.
  '''

  def __init__(self, news_file_path):
    ''' Class initialization. No additional code needed at the moment.
        Parameters:
          news_file_path - path to the file containing the XML file with the news
        Return:
          None - This function doesn't return anything
    '''
    self.news_file_path = news_file_path
    Thread.__init__(self)

  def run(self):
    ''' Method running the logic of the thread which, in our case, will
        be the web server serving news.
        Parameters:
          None - This function doesn't get any additional parameter
        Return:
          None - This function doesn't return anything
    '''
    # 1. Starting the server (bound to TCP port 8080)
    #    * News file path injected as described here: https://www.raspberrypi.org/forums/viewtopic.php?t=66940
    NewsFeedRequestHandler.news_file_path = self.news_file_path
    web_server = HTTPServer(('', 8080), NewsFeedRequestHandler)
    logging.info("Server started http://localhost:8080")
    # 2. Making the web server serve request forever until interrupted
    #    (CTRL+C is not caught when running in a thread; TBD: tear it down in a different way)
    try:
      web_server.serve_forever()
    except KeyboardInterrupt:
      pass
    # 3. Close the web server and release resources
    web_server.server_close()
    logging.info("Server stopped.")

# Auxiliary functions
#

def disk_filling(volume, size, duration):
  ''' This function creates random files in a data volume during some time
      up until certain size. This simulates a buggy process filling a disk
      after a new version has been released.
      Parameters:
        volume   - absolute path of the data volume where files will be created
        size     - size in MBs that is going to be created in total
        duration - how long (in seconds) the filling process will take
      Return:
        None - This function doesn't return anything
  '''
  logging.info(f'Filling {volume} with {size}M in {duration} seconds.')
  # 1. Size of the files that will be created and will fill up the disk incrementally
  filesize = int(size/duration*1024*1024)
  logging.debug(f'Creating files {filesize}M big')
  # 2. Main loop creating new files every second
  for i in range(1,duration):
    time.sleep(1)
    with open(f'{volume}/fill_disk{i}.bin', 'wb') as fout:
         fout.write(os.urandom(filesize))
         fout.flush()
def get_release_id(gh_repo_name, gh_personal_token):
  ''' It get the release id of release v1.9
      Parameters:
        gh_repo           - repo name to be used in the URL to send all the POST requests
        gh_personal_token - token needed to make the API calls
      Return:
        The release id of release v1.9 or -1 if there was any error.
  '''
  headers = {"Authorization": f"token {gh_personal_token}",
             "Accept": "application/vnd.github.v3+json"}
  url = f"https://api.github.com/repos/{gh_repo_name}/releases/tags/V1.9"
  release_id = -1

  # 1. Get id for release v1.9
  response = requests.get(url, headers=headers)
  logging.debug(f"response.text: {response.text}")
  if response.status_code == requests.codes.ok:
    release_id = response.json()['id']
    logging.info(f"release_id: {release_id}")
  else:
    logging.error(f"Unable to get the id of release v1.9: {response.text}")
  # 2. Return the value obtained
  return release_id
  
def delete_gh_release(release_id, gh_repo_name, gh_personal_token):
  ''' Remove release v1.9 from the Github
      Parameters:
        release_id        - the identifier needed to remove release
        gh_repo_name      - repo name to be used in the URL to send all the POST requests
        gh_personal_token - token needed to make the API calls
      Return:
        None - This function doesn't return anything
  '''
  headers = {"Authorization": f"token {gh_personal_token}",
             "Accept": "application/vnd.github.v3+json"}
  url =f"https://api.github.com/repos/{gh_repo_name}/releases/{release_id}"

  # 1. Delete the release and log the result of the operation
  #    Error code 204 (no_content) if all goes well
  response = requests.delete(url, headers=headers)
  logging.debug(f"response.text: {response.text}")
  if response.status_code == requests.codes.no_content:
    logging.info(f"release_id '{release_id}' removed!")
  else:
    logging.error(f"Error '{response.status_code}'. Unable to remove release v1.9 with id '{release_id}': {response.text}")

def publish_gh_release(gh_repo_name, gh_personal_token):
  ''' Publish release v1.9 one more time with the current date
  '''
  headers = {"Authorization": f"token {gh_personal_token}",
             "Accept": "application/vnd.github.v3+json"}
  url = f"https://api.github.com/repos/{gh_repo_name}/releases"
  data = { "tag_name" : "V1.9", 
           "name" : "V1.9", 
           "body" : "Added new logging functionality, this will help the SRE debug issues faster. Logs are now spooled to disk much faster and can the verbosity level can be customised on the fly."}

  # 1. Send the request to create the release one more time
  #    Error code 201 (created) if all goes well
  response = requests.post(url, data=json.dumps(data), headers=headers)
  logging.debug(f"response.text: {response.text}")
  if response.status_code == requests.codes.created:
    logging.info(f"Release v1.9 created one more time")
  else:
    logging.error(f"Error '{response.status_code}'. Unable to create release v1.9: {response.text}")
    
def update_gh_release(gh_repo_name, gh_personal_token):
  ''' Function making some API calls to the GH end point to refresh the release date
      Parameters:
        gh_repo_name      - repo name to be used in the URL to send all the POST requests
        gh_personal_token - token needed to make the API calls
      Return:
        None - This function doesn't return anything
  '''
  # 1. Get the identifier of release v1.9
  release_id = get_release_id(gh_repo_name, gh_personal_token)
  if release_id > -1:
    # 2. Remove release v1.9 if it was found
    delete_gh_release(release_id, gh_repo_name, gh_personal_token)
  # 3. Publish it one more time
  publish_gh_release(gh_repo_name, gh_personal_token)

def empty_data_volume(data_volume):
  ''' Remove all the contents in the data volume where the random content is
      created.
      Parameters:
        data_volume - the data volume that has to be empty
      Return:
        None - This function doesn't return anything
  '''
  files = glob.glob(f'{data_volume}/*', recursive=True)
  logging.info(f"Removing all the contents in {data_volume}")

  for f in files:
    try:
      os.remove(f)
    except OSError as e:
      logging.error(f"Error: {f} : {e.strerror}")
                
def reset(gh_repo_name, gh_personal_token, data_volume):
  ''' Resets the environment to start the simulation from scratch by:
        1. Updating the latest project release to have recent version matching
           the rest of the simulation (disk filling, ....)
        2. Removing the random data created in the data volume.
      Parameters:
        gh_repo_name      - repo name to be used in the URL to send all the POST requests
        gh_personal_token - token needed to make the API calls
        data_volume       - the data volume that has to be empty
      Return:
        None - This function doesn't return anything
  '''
  logging.info("Resetting simulation")
  # 1. Update release v1.9 of the GH repo
  update_gh_release(gh_repo_name, gh_personal_token)
  # 2. Empty the data volume to have it ready for the disk filling
  empty_data_volume(data_volume)

def get_script_config(config_filename):
  ''' This function add all the configuration parameters of the script into a dictionary.
      Parameters:
        config_filename - filename of the file containing the script configuration
      Return:
        A dictionary all the configuration parameters available in the configuration file.
  '''
  logging.debug(f'config_filename = {config_filename}')
  d_script_config = {}
  # 1. Open the configuration file
  with open(args.config_file) as file:
    d_script_config = yaml.load(file, Loader=yaml.FullLoader)

  # 2. Log the configuration for troubleshooting purposes

  for conf_param in d_script_config.keys():
    logging.info(f'  {conf_param}: {d_script_config[conf_param]}')

  # 3. Return the dictionary
  return d_script_config

def start_event_scheduler():
  ''' It creates an EventScheduler instance, starts it up and return a reference.
      Parameters:
        None - This function doesn't get any parameter
      Return:
        It returns a EventScheduler instance already started
  '''
  # 1. Create an EventScheduler instance and start it up
  event_scheduler = EventScheduler()
  event_scheduler.start()
  # 2. Return the started instance
  return event_scheduler

def add_event(event_scheduler, function_name, d_script_config):
  ''' It adds a new event to the event scheduler based on the input parameters.
      Parameters:
        event_scheduler - a reference to a started EventScheduler instance
        function_name   - a string with the name of the function to schedule
        d_script_config - the dictionary containing the configuration of the script
      Return:
        None - This function doesn't return anything
  '''
  simulation_duration = d_script_config['simulation_duration']
  # 1. Get the appropiate configuration parameters based on the function
  if function_name == "disk_filling":
    (volume, size, duration) = (d_script_config['data_volume'],
                                d_script_config['volume_size'],
                                d_script_config['filling_duration'])
    event_scheduler.enter_recurring(simulation_duration, 0, disk_filling, (volume, size, duration))
  elif function_name == "reset":
    (repo_name, personal_token, volume) = (d_script_config['gh_repo_name'],
                                           d_script_config['gh_personal_token'],
                                           d_script_config['data_volume'])
    # reset should happen before anything else (triggered at 90% of the simulation duration)
    event_scheduler.enter_recurring(simulation_duration*0.9, 0, reset, (repo_name, personal_token, volume))

def start_news_feed_service(news_file_path):
  ''' It starts a new thread running a web server which will be server news
      Parameters:
        news_file_path - path to the file containing the XML file with the news
      Return:
        None - This function doesn't return anything
  '''
  # 1. Create a new instance of the web server and set it up as a daemon service
  web_server = NewsFeedWebServer(news_file_path)
  web_server.daemon = True
  # 2. Start the web server
  web_server.start()  

# Main application
#

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
  logging.info(f'Starting the noisy agent (v{release})')

  # 1. Arguments parsing and getting the configuration of the script
  parser = argparse.ArgumentParser()
  parser.add_argument("config_file", help="Noisy Agent's configuration file")
  args = parser.parse_args()

  d_script_config = get_script_config(args.config_file)
  
  # 2. Starting the scheduler and adding tasks
  event_scheduler = start_event_scheduler()
  add_event(event_scheduler, "reset", d_script_config)
  add_event(event_scheduler, "disk_filling", d_script_config)

  # 3. Start the internal web server serving simulating the news feed service
  start_news_feed_service(d_script_config['news_file_path'])

  # 4. Start the new release simulation
  # 4.1 Reset the context to start from the simulation from scratch
  (repo_name, personal_token, volume) = (d_script_config['gh_repo_name'],
                                         d_script_config['gh_personal_token'],
                                         d_script_config['data_volume'])
  reset(repo_name, personal_token, volume)
  # 4.2 Start filling up the disk
  (volume, size, duration) = (d_script_config['data_volume'],
                              d_script_config['volume_size'],
                              d_script_config['filling_duration'])
  disk_filling(volume, size, duration)
