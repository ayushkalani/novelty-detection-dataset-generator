import json
import os
import logging
import re
import pandas as pd
import copy
from Novelty_utils import novelty_mapping
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("debug.log"),
        logging.StreamHandler()
    ]
)
PATH_TO_JSON = 'json/'
PLAYER_TO_IGNORE = "player_1"
PLAYER_KEYS_TO_IGNORE = ["full_color_sets_possessed", "assets", "mortgaged_assets"]
NUMBER_OF_PLAYERS = 4
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
PLAYER_STATUS_MAPPING = {"waiting_for_move": 0, 'current_move:':1, 'won': 2, 'lost':3}
# number of locations on board - 36
LOCATIONS = {'Illinois Avenue', 'Go to Jail', 'Luxury Tax', 'Go', 'B&O Railroad', 'Atlantic Avenue', 'Boardwalk', 'Marvin Gardens', 'Pacific Avenue', 'Water Works', 'Mediterranean Avenue', 'Community Chest', 'Tennessee Avenue', 'Baltic Avenue', 'North Carolina Avenue', 'Income Tax', 'Reading Railroad', 'Oriental Avenue', 'Chance', 'Indiana Avenue', 'Short Line', 'Vermont Avenue', 'Ventnor Avenue', 'Connecticut Avenue', 'In Jail/Just Visiting', 'St. Charles Place', 'Park Place', 'Electric Company', 'States Avenue', 'Virginia Avenue', 'Pennsylvania Railroad', 'St. James Place', 'Pennsylvania Avenue', 'New York Avenue', 'Free Parking', 'Kentucky Avenue'}

BOOLEAN_COLUMNS = {"has_get_out_of_jail_chance_card", "has_get_out_of_jail_community_chest_card", "currently_in_jail", "option_to_buy", "is_property_offer_outstanding", "is_trade_offer_outstanding"}

LOCATION_VECTOR = {}
PLAYER_NAME_MAPPING = {}
PLAYER_BOOLEAN_COLUMNS = set()

for i in range(1, NUMBER_OF_PLAYERS + 1):
    name = "player_" + str(i)
    for location in LOCATIONS:
        LOCATION_VECTOR[name+"." + "location" + "."+location] = 0
    for boolean_column in BOOLEAN_COLUMNS:
        PLAYER_BOOLEAN_COLUMNS.add("players"+"."+name+"." + boolean_column)
    PLAYER_NAME_MAPPING[name] = i

############## UTIL FUNCTIONS ################
def natural_sort(l): 
    convert = lambda text: int(text) if text.isdigit() else text.lower()
    alphanum_key = lambda key: [convert(c) for c in re.split('([0-9]+)', key)]
    return sorted(l, key=alphanum_key)

#############################################
        
def process_history(data, current_timestep):
    for step in data["history"]:
        function_name = step["function"]
        if function_name in novelty_mapping.keys():
            function_name = novelty_mapping[function_name]
        try:
            if step["time_step"] == current_timestep and function_name in WHITELISTED_ACTIONS.keys() and step["param"]:
                # check player first, and then self, because self can be a location too
                player_name = ""
                if  step["param"].get("player", None):
                    player_name = step["param"]["player"]
                elif  step["param"].get("self", None):
                    player_name = step["param"]["self"]
                if not player_name:
                    raise ValueError('Unable to extract Player Name')
                data[player_name+"."+step["function"]]=1
        except KeyError:
            logging.error("Keyerror while process_history %s", current_timestep)
            pass
        except ValueError:
            logging.error("ValueError while process_history %s", current_timestep)
            pass

def encode_player_assets(data):
    location = copy.deepcopy(LOCATION_VECTOR)
    try:
        for player in data["players"]:
            for asset in data["players"][player]["assets"]:
                p_asset = player + '.location.' + asset
                if p_asset in location: location[p_asset] = 1
    except KeyError:
            logging.error("Keyerror while encode_player_assets")
            pass            
    return location
    
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
    json_files = natural_sort(json_files)
    for file in json_files:
        with open(PATH_TO_JSON + file, "r", encoding='utf-8') as of: 
            logging.debug("reading file %s", file)
            data = json.load(of)
            #main_player_function = data["actions_and_params"]["function"]
            data = data["true_next_state"]
            # history
            for actions in WHITELISTED_ACTIONS.keys():
                for i in range(1, NUMBER_OF_PLAYERS + 1):
                    data["player_"+str(i)+"."+actions] = 0 
            process_history(data, get_current_time_step(file))
            player_encoded_assets = encode_player_assets(data)
            data.update(player_encoded_assets)
            # clean
            for i in range(1, NUMBER_OF_PLAYERS + 1):
                for key_to_delete in PLAYER_KEYS_TO_IGNORE:
                    data["players"]["player_"+str(i)].pop(key_to_delete, None)
            data.pop("location_sequence", None)
            data.pop("cards", None)
            data.pop("die_sequence", None)
            data.pop("history", None)
            data.pop("locations", None)
            df_list.append(data)
            break
    write_csv(df_list)

def write_csv(write):
    df = pd.json_normalize(write)
    for col in PLAYER_BOOLEAN_COLUMNS:
        if col in df.columns:
            df[col] = df[col].astype(int)
    df.to_csv('test_2.csv', index=False, encoding='utf-8')

if __name__ == "__main__":
    try:
        read_game_json()
    except OSError as err:
        print("OS error: {0}".format(err))
    except ValueError:
        logging.error("ValueError in main")
        pass    