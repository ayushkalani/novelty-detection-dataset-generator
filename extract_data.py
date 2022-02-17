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
# WHITELISTED_ACTIONS = ["free_mortgage", "make_sell_property_offer", "sell_property", "sell_house_hotel", "accept_sell_property_offer",
#                        "skip_turn", "concluded_actions", "mortgage_property", "improve_property", "use_get_out_of_jail_card",
#                        "pay_jail_fine", "roll_die", "buy_property", "make_trade_offer",
#                        "accept_trade_offer", "pre_roll_arbitrary_action", "out_of_turn_arbitrary_action",
#                        "post_roll_arbitrary_action", "accept_arbitrary_interaction"]

WHITELISTED_ACTIONS = {"free_mortgage":0, "make_sell_property_offer":1, "sell_property":2, "sell_house_hotel":3, "accept_sell_property_offer":4,
                       "skip_turn":5, "concluded_actions":6, "mortgage_property":7, "improve_property":8, "use_get_out_of_jail_card":9,
                       "pay_jail_fine":10, "roll_die":11, "buy_property":12, "make_trade_offer":13,
                       "accept_trade_offer":14, "pre_roll_arbitrary_action":15, "out_of_turn_arbitrary_action":16,
                       "post_roll_arbitrary_action":17, "accept_arbitrary_interaction":18}

def process_history(data, current_timestep):
    for step in data["history"]:
        if step["time_step"] == current_timestep and step["function"] in WHITELISTED_ACTIONS.keys() and step["param"]:
            # if step["param"] and step
            player_name = step["param"]["self"] if "self" in step["param"].keys() else step["param"]["player"]
            data[player_name+"."+step["function"]]=1            

            
            
def get_current_time_step(filename):
    current_timestep = re.findall("_(\d*)\.json$", filename)
    if current_timestep and current_timestep[0]:
        return int(current_timestep[0])
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
    #main_player_function = data["actions_and_params"]["function"]
    data = data["true_next_state"]
    # clean
    del data["location_sequence"]
    del data["locations"]
    del data["cards"]
    del data["die_sequence"]
    # history
    for actions in WHITELISTED_ACTIONS.keys():
        for i in range(1,5):
            data["player_"+str(i)+"."+actions] = 0 
    process_history(data, get_current_time_step(file))
    del data["history"]
    df_list.append(data)
    of.close()
    write_csv(df_list)
  write_csv(df_list)

def write_csv(write):
    df = pd.json_normalize(write)
    df.to_csv('test.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
   read_game_json()


# def OneHotEncoding(dictionary, )