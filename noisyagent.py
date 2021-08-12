import argparse
import logging
import yaml
import time
import os

release="0.1"

def fill_disk(volume, size, rate):
  logging.debug(f'Filling {volume} with {size}M in {rate} seconds.')

  filesize = int(size/rate*1024*1024)
  logging.debug(f'Creating files {filesize}M big')

  for i in range(1,rate):
    time.sleep(1)
    with open(f'{volume}/fill_disk{i}.bin', 'wb') as fout:
         logging.debug(f"")
         fout.write(os.urandom(filesize))
         fout.flush()

if __name__ == "__main__":
  logging.basicConfig(level=logging.INFO,
                      format='%(asctime)s - %(name)s - %(levelname)s - %(funcName)s - %(message)s')
  logging.debug(f'Starting the noisy agent (v{release})')

  # 1. Arguments parsing and configuration file reading
  parser = argparse.ArgumentParser()
  parser.add_argument("config_file", help="Noisy Agent's configuration file")
  args = parser.parse_args()

  with open(args.config_file) as file:
    agent_cfg = yaml.load(file, Loader=yaml.FullLoader)

  print(f'Noisy agent v{release}\n--')
  print('This the configuration provided:')
  for conf_param in agent_cfg.keys():
    print(f'  {conf_param}: {agent_cfg[conf_param]}')

  volume = agent_cfg['data_volume']
  size = agent_cfg['volume_size']
  rate = agent_cfg['filling_rate']
  fill_disk(volume, size, rate)
