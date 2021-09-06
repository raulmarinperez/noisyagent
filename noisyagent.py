from http.server import BaseHTTPRequestHandler, HTTPServer
from event_scheduler import EventScheduler
from threading import Thread
import argparse
import logging
import yaml
import time
import os

release="0.1"

# Auxiliary classes
#

class NewsFeedRequestHandler(BaseHTTPRequestHandler):
  ''' Auxiliary class implementing a HTTPRequestHandler for our web server.
  '''
  def do_GET(self):
    ''' This function implements the logic to server HTTP GET request
        of our web server.
        Parameters:
          None - This function doesn't get any additional parameter
        Return:
          None - This function doesn't return anything
    '''
    self.send_response(200)
    self.send_header("Content-type", "text/html")
    self.end_headers()
    self.wfile.write(bytes("<html><head><title>https://pythonbasics.org</title></head>", "utf-8"))
    self.wfile.write(bytes("<p>Request: %s</p>" % self.path, "utf-8"))
    self.wfile.write(bytes("<body>", "utf-8"))
    self.wfile.write(bytes("<p>This is an example web server.</p>", "utf-8"))
    self.wfile.write(bytes("</body></html>", "utf-8"))

class NewsFeedWebServer(Thread):
  ''' Class that will be used to run a web server in a thread concurrently 
      with the rest of the tasks.
  '''

  def __init__(self):
    ''' Class initialization. No additional code needed at the moment.
        Parameters:
          None - This function doesn't get any additional parameter
        Return:
          None - This function doesn't return anything
    '''
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
    web_server = HTTPServer(("localhost", 8080), NewsFeedRequestHandler)
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
  logging.debug(f'Filling {volume} with {size}M in {duration} seconds.')
  # 1. Size of the files that will be created and will fill up the disk incrementally
  filesize = int(size/duration*1024*1024)
  logging.debug(f'Creating files {filesize}M big')
  # 2. Main loop creating new files every second
  for i in range(1,duration):
    time.sleep(1)
    with open(f'{volume}/fill_disk{i}.bin', 'wb') as fout:
         fout.write(os.urandom(filesize))
         fout.flush()

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
  # 1. Get the appropiate configuration parameters based on the function
  if function_name == "disk_filling":
    (volume, size, duration) = (d_script_config['data_volume'],
                                d_script_config['volume_size'],
                                d_script_config['filling_duration'])
    event_scheduler.enter_recurring(duration, 0, disk_filling, (volume, size, duration))

def start_news_feed_service():
  ''' It starts a new thread running a web server which will be server news
      Parameters:
        None - This function doesn't get any parameter
      Return:
        None - This function doesn't return anything
  '''
  # 1. Create a new instance of the web server and set it up as a daemon service
  web_server = NewsFeedWebServer()
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
  add_event(event_scheduler, "disk_filling", d_script_config)
  #add_event(event_scheduler, "reset", d_script_config)

  # 3. Start the internal web server serving simulating the news feed service
  start_news_feed_service()

  # 4. Start the new release simulation
  # 4.1 Reset the context to start from the simulation from scratch
  #reset()
  # 4.2 Start filling up the disk
  (volume, size, duration) = (d_script_config['data_volume'],
                              d_script_config['volume_size'],
                              d_script_config['filling_duration'])
  disk_filling(volume, size, duration)
