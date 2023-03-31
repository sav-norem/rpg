import redis
import random
from collections import defaultdict
import logging
import sys

r = redis.Redis(decode_responses=True)

MAX_HEALTH = 30
MAX_MONSTERS = 4

class player_def:
    def __init__(self):
        self.health = 20
        self.damage = 5
        self.inventory = {
            "weapons": [],
            "potions": []
        }
        self.name = ''
        self.location = 0
        self.strongest_weapon = -1

    def update_strongest_weapon(self):
        if self.inventory["weapons"]:
            self.strongest_weapon = max(self.inventory["weapons"])

    def open_chest(self, chest: dict):
        r.xadd(stream_name, {"message": f"{player.name} found a chest!"})
        de = defaultdict(list, self.inventory)
        for i, j in chest.items():
            de[i].extend(j)
        self.inventory = de
        self.update_strongest_weapon()


class game_board:
    def __init__(self, name, rows=20, cols=20):
        self.name = name
        self.rows = rows
        self.cols = cols
        self.exit = random.randrange(self.rows*self.cols - self.rows + 1, self.rows*self.cols)
        # map_exit not tied to specific game board
        r.set("map_exit", self.exit)
        if r.bitcount(map_name) == 0:
            self.pop_encounters()

    # a function that adds random spots that will have encounters
    def pop_encounters(self):
        num_encounters = random.randrange(int(self.rows*self.cols / 3), int(self.rows*self.cols))
        while num_encounters != 0:
            encounter_bit = random.randrange(0, self.rows*self.cols)
            encounter_type = random.choice(["chests", "monsters"])
            x = {"chests": {"weapons": [],"potions": []}, "monsters": [], "letters": []}
            if space_info := r.json().get(f"encounters:{encounter_bit}"):
                x = space_info
            if encounter_type == "chests":
                item_type = random.choice(["weapons", "potions"])
                x["chests"][item_type].append(random.randrange(5,15))
            else: 
                if len(x["monsters"]) == 4:
                    break
                else:
                    monster_modifier = (encounter_bit // self.rows) / self.rows
                    base_damage = random.randrange(5,10)
                    base_health = random.randrange(5,10)
                    monster = {}
                    # (5 + 5 * (1/20)) - > obviously not a whole number
                    monster["damage"] = base_damage + (base_damage * monster_modifier)
                    monster["health"] = base_health + (base_health * monster_modifier)
                    x["monsters"].append(monster)

            r.json().set(f"{self.name}:encounters:{encounter_bit}", "$", x)
            r.expire(f"{self.name}:encounters:{encounter_bit}", 604800)

            num_encounters -= 1

    # this is a function to use for debugging only
    def pop_test_encounters(self):
        encounter_bit = random.randrange(0, self.rows*self.cols)
        print("encounter :", encounter_bit)
        encounter_type = "chests"
        x = {"chests": {"weapons": [],"potions": []}, "monsters": 0}
        x[encounter_type] += 1
        r.json().set(f"{self.name}:encounters:{encounter_bit}", "$", x)

def player_death():
    print("you remained in the map forever :( ")
    r.incr(player_count, -1)
    if int(r.get(player_count)) == 0:
        map_del = input("delete map? y or n\n")
        if map_del == 'y':
            r.delete(map_name)
            old_encounters = r.scan(0, f"{map_name}:encounters:*", 10000)
            for k in old_encounters[1]:
                r.delete(k)
        r.delete(stream_name)
        r.delete(player_count)

def check_encounters():
    if enc := r.json().get(f"{map_name}:encounters:{player.location}"):
        while len(enc["monsters"]) > 0:
            print("you found a monster!")
            # every time you fight a monster, you have the choice to run away
            fight_monster(enc["monsters"].pop())
            r.json().set(f"{map_name}:encounters:{player.location}", "$", enc)
        while enc["chests"]["potions"] or enc["chests"]["weapons"]:
            print("you found a chest!")
            loot_chest(enc)
            enc["chests"]["potions"] = []
            enc["chests"]["weapons"] = []
            r.json().set(f"{map_name}:encounters:{player.location}", "$", enc)

# modify this so that monsters on higher rows have more health
def fight_monster(monster):
    print(f"the monster has {monster['health']} health")
    print(f"the monster does {monster['damage']} damage")
    # could move the input to before the check?
    fight = input("fight the monster? (y or n)\n")  
    if fight == "y":
        while monster["health"] > 0 and player.health > 0:
            player.health -= monster["damage"]
            print(f"you have {player.health} health left!")
            if player.health > 0:
                if player.strongest_weapon < 0:
                    print("you're punching a monster!")
                    monster["health"] -= player.damage
                else:
                    print("you can use your weapon!")
                    monster["health"] -= player.strongest_weapon
    else:
        print("run away!")
        move_char()

    if monster["health"] <= 0:
        # print("you defeated the monster!")
        r.xadd(stream_name, {"message": f"{player.name} defeated a monster!"})
    elif player.health <= 0:
        # print("the monster defeated you :( ")
        r.xadd(stream_name, {"message": f"{player.name} got defeated by a monster :("})
        player_death()

def loot_chest(enc):
    print(enc["chests"])
    player.open_chest(enc["chests"])
    
# a function that checks if a player is on an edge and therefore cannot move in a certain direction
def check_edge():
    movement_options = {
        "left": 1,
        "right": 1,
        "down": 1,
        "up": 1
    }
    last_bit = player.location
    if last_bit % game.cols == 0:
        movement_options["left"] = 0
    if last_bit % game.cols == game.cols - 1:
        movement_options["right"] = 0
    if 0 <= last_bit < game.cols:
        movement_options["down"] = 0
    if game.rows*game.cols - game.rows <= last_bit:
        movement_options["up"] = 0
        
    return movement_options

def move_char():
    opts = check_edge()
    opts_list = [k for k,v in opts.items() if v == 1]
    if player.inventory["potions"]:
        opts_list.append("potion")
    mv = "diaganol"
    while mv not in opts_list:
        print("Your options are: ")
        print(opts_list)
        mv = input("Which way would you like to move?\n")
    last_bit = player.location
    if mv == "potion":
        print(player.inventory["potions"])
        potion_choice = int(input("enter the index of the potion you want to use\n"))
        if (new_health := player.health + player.inventory["potions"][potion_choice]) > 30:
            logging.info(new_health)
            player.health = MAX_HEALTH
        else:
            logging.info(new_health)
            player.health = new_health
        player.inventory["potions"].pop(potion_choice)
        print(player.health)
    elif mv == "left":
        last_bit -= 1
    elif mv == "right":
        last_bit += 1
    elif mv == "up":
        last_bit += game.cols
    elif mv == "down":
        last_bit -= game.cols
    else:
        print("how on earth did you get here")

    print(last_bit)
    r.setbit(map_name, last_bit, 1)

    player.location = last_bit

def main():
    # reset_game()
    global map_name
    map_name = input("do you have a map name to play? if no, press enter\n")
    if not map_name:
        x = r.get("map_count")
        map_name = f"map_game_{x}"
        r.incr("map_count", 1)
        r.expire(map_name, 604800)
    global stream_name
    stream_name = f"stream:{map_name}"
    LAST_STREAM_ID = 0
    player_name = input("what's your characters name?\n")
    global player_count
    player_count = f"{map_name}:player_count"
    r.incr(player_count, 1)
    global player
    player = player_def()
    player.name = player_name
    global game
    game = game_board(map_name)

    map_entrance = random.randrange(0,game.cols-1)
    print("entrance: ", map_entrance)
    player.location = map_entrance
    r.setbit(map_name, map_entrance, 1)
    # check encounters at entrance
    check_encounters()
    while player.location != game.exit and player.health > 0:
        # check for a message on the stream
        move_char()
        check_encounters()
        try:
            # currently shows last message still
            # cannot ignore first message
            # could check length > 1 and then skip first message?
            m = r.xrange(stream_name, LAST_STREAM_ID, "+")
            if len(m) > 1:
                m = m[1:]
            for message in m:
                print(message[1]["message"])
            LAST_STREAM_ID = m[-1][0]
        except:
            continue
    if player.health > 0:
        print("you escaped!")
        r.incr(player_count, -1)
        # add a check for if another person is in the map?
        player_death()
    return None



if __name__ == "__main__":
    try:
        main()
    except:
        r.incr(player_count, -1)
