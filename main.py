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
        de = defaultdict(list, self.inventory)
        for i, j in chest.items():
            de[i].extend(j)
        self.inventory = de
        self.update_strongest_weapon()


class game_board:
    def __init__(self, debug=False, rows=20, cols=20):
        self.rows = rows
        self.cols = cols
        self.exit = random.randrange(self.rows*self.cols - self.rows + 1, self.rows*self.cols)
        r.set("map_exit", self.exit)
        if not debug:
            self.pop_encounters()
        else:
            self.pop_test_encounters()

    # a function that adds random spots that will have encounters
    def pop_encounters(self):
        num_encounters = random.randrange(int(self.rows*self.cols / 3), int(self.rows*self.cols))
        while num_encounters != 0:
            encounter_bit = random.randrange(0, self.rows*self.cols)
            encounter_type = random.choice(["chests", "monsters"])
            x = {"chests": {"weapons": [],"potions": []}, "monsters": []}
            if space_info := r.json().get(f"encounters:{encounter_bit}"):
                x = space_info
            if encounter_type == "chests":
                item_type = random.choice(["weapons", "potions"])
                x["chests"][item_type].append(random.randrange(5,15))
            else: 
                if len(x["monsters"]) >= 4:
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

            r.json().set(f"encounters:{encounter_bit}", "$", x)

            num_encounters -= 1


    def pop_test_encounters(self):
        encounter_bit = random.randrange(0, self.rows*self.cols)
        print("encounter :", encounter_bit)
        encounter_type = "chests"
        x = {"chests": {"weapons": [],"potions": []}, "monsters": 0}
        x[encounter_type] += 1
        r.json().set(f"encounters:{encounter_bit}", "$", x)


def check_encounters():
    if enc := r.json().get(f"encounters:{player.location}"):
        while len(enc["monsters"]) > 0:
            print("you found a monster!")
            # every time you fight a monster, you have the choice to run away
            fight_monster(enc["monsters"].pop())
            r.json().set(f"encounters:{player.location}", "$", enc)
        while enc["chests"]["potions"] or enc["chests"]["weapons"]:
            print("you found a chest!")
            loot_chest(enc)
            enc["chests"] = {}
            r.json().set(f"encounters:{player.location}", "$", enc)

# modify this so that monsters on higher rows have more health
def fight_monster(monster):
    print(f"the monster has {monster['health']} health")
    print(f"the monster does {monster['damage']} damage")
    while monster["health"] > 0 and player.health > 0:
        fight = input("fight the monster? (y or n)")
        if fight == "n":
            print("run away!")
            move_char()
            break
        if fight == "y":
            player.health -= monster["damage"]
            print(f"you have {player.health} health left!")
            if player.health > 0:
                if player.strongest_weapon < 0:
                    print("you're punching a monster!")
                    monster["health"] -= player.damage
                else:
                    print("you can use your weapon!")
                    monster["health"] -= player.strongest_weapon

    if monster["health"] <= 0:
        print("you defeated the monster!")
    if player.health <= 0:
        print("the monster defeated you :( ")
        exit()

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
        mv = input("Which way would you like to move?")
    last_bit = player.location
    if mv == "potion":
        print(player.inventory["potions"])
        potion_choice = int(input("enter the index of the potion you want to use"))
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

    if r.getbit("map_game", last_bit) == 1:
        print("you've been here before!")
    else:
        r.setbit("map_game", last_bit, 1)

    player.location = last_bit

def reset_game():
    r.delete("map_game")
    old_encounters = r.scan(0, "encounters:*", 10000)
    for k in old_encounters[1]:
        r.delete(k)

def main():
    reset_game()
    player_name = input("what's your characters name?")
    global player 
    player = player_def()
    player.name = player_name
    global game
    if len(sys.argv) > 1:
        debug=True
        rows = input("how many rows?")
        cols = input("how many cols?")
        game = game_board(debug, rows, cols)
    else:
        game = game_board()

    map_entrance = random.randrange(0,game.cols-1)
    print("entrance: ", map_entrance)
    logging.debug("exit: ", game.exit)
    player.location = map_entrance
    r.setbit("map_game", map_entrance, 1)
    # check encounters at entrance
    while player.location != game.exit and player.health > 0:
        check_encounters()
        move_char()
    if player.health > 0:
        print("you escaped!")
    else:
        print("you remained in the map forever :( ")
    return None



if __name__ == "__main__":
    main()
