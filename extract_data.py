from asyncore import file_wrapper
import json
import os, sys
import logging
import re
import pandas as pd

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH_TO_JSON = 'json/'
PLAYER_TO_IGNORE = "player_1"

PLAYER_KEYS_TO_IGNORE = ["full_color_sets_possessed"]
WHITELISTED_ACTIONS = ["free_mortgage", "make_sell_property_offer", "sell_property", "sell_house_hotel", "accept_sell_property_offer",
                       "skip_turn", "concluded_actions", "mortgage_property", "improve_property", "use_get_out_of_jail_card",
                       "pay_jail_fine", "roll_die", "buy_property", "make_trade_offer",
                       "accept_trade_offer", "pre_roll_arbitrary_action", "out_of_turn_arbitrary_action",
                       "post_roll_arbitrary_action", "accept_arbitrary_interaction"]

def process_history(history, current_timestep):
    for step in history:
        if step["time_step"] == current_timestep and step["function"] in WHITELISTED_ACTIONS:
            return 7
            
            
def get_current_time_step(filename):
    current_timestep = re.findall("_(\d*)\.json$", filename)
    if current_timestep and current_timestep[0]:
        return current_timestep[0]
    else:
        raise ValueError('Not able to detect timestep of the json, check the regex') # json_msg_1_5228.json
    

def read_game_json():
  file_prefix = "json_msg_"
  json_files = [pos_json for pos_json in os.listdir(
      PATH_TO_JSON) if pos_json.startswith(file_prefix) and pos_json.endswith('.json')]
  df_list = []
  for file in json_files:
    of = open(PATH_TO_JSON + file, "r", encoding='utf-8')
    logging.debug("reading file %s", file)
    data = json.load(of)
    main_player_function = data["actions_and_params"]["function"]
    data = data["true_next_state"]
    # clean
    del data["location_sequence"]
    del data["locations"]
    del data["cards"]
    del data["die_sequence"]
    # history
    process_history(data["history"], get_current_time_step(file))
    df_list.append(data)
    of.close()
  write_csv(df_list)

def write_csv(write):
    df = pd.json_normalize(write)
    df.to_csv('test.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
   read_game_json()