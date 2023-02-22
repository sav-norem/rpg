import redis
import random
from abc import ABC, abstractmethod
from collections import defaultdict

r = redis.Redis()


# Game Constants
MIN_CHEST_ITEMS = 1
MAX_CHEST_ITEMS = 4
MONSTER_HEALTH = 3
MONSTER_DAMAGE = 1
PLAYER_HEALTH = 20
PLAYER_DAMAGE = 2
TILE_TYPES = {
    "CHESTS": 0,
    "MONSTERS": 0
}

def init_weapons(num_weapons)
    random.seed(random.randrange(5,15))
    weapons = []
    x = 0
    while x < num_weapons
        damage = random.randrange(5,15)
        weapon_type = random.choice(["sword", "mace", "dagger"])
        weapons.append({"type": weapon_type, "damage": damage})
        x += 1

class Inventory:
    def __init__(self):
        self.weapons = []
        self.potions = []

class Player:
    def __init__(self, name):
        self.health = 20
        self.damage = 2
        self.inventory = Inventory()
        self.name = name
        self.location = 0

    @property
    def strongest_weapon:
        self.strongest_weapon = -1

    def fight_monster(self):
        monster = Monster()
        # also randomize monster damage
        monster.health = random.randrange(1,5)
        while monster.health > 0:
            fight = input("fight the monster? (y or n)")
            if fight == "n":
                print("run away!")
                move_char()
                break
            if fight == "y":        
                self.health -= monster.damage 
                if self.health > 0:
                    if self.strongest_weapon < 0:
                        print("you're punching a monster!")
                        monster.health -= player.damage
                    else:
                        print("you can use your weapon!")
                        print(type(self.inventory.weapons[0]))
                        monster.health -= self.strongest_weapon

        if monster.health <= 0:
            print("you defeated the monster!")
            return

        if self.health <= 0:
            print("the monster defeated you :( ")
            raise Exception("Died")

    def loot_chest(self, chest):
        # player.inventory.update(chest.items)
        de = defaultdict(list, player.inventory)
        for i, j in chest.items.items():
            de[i].extend(j)
        player.inventory = de
            
        # player.update_strongest_weapon



class Monster:
    def __init__(self):
        self.health = MONSTER_HEALTH
        self.damage = MONSTER_DAMAGE

class Chest():
    def __init__(self, num_items):
        self.items = Inventory()
        for range(0, num_items):
            item_type = random.choice(["weapons", "potions"])
            # item_type = "potions"
            if item_type == "potions":
                self.items.potions.append(random.randrange(5,15))
            else:
                self.items.weapons.append(random.choice(weapons))



def check_encounters():
    if enc := r.json().get(f"encounters:{player.location}"):
        while enc["monsters"] > 0:
            print("you found a monster!")
            fight_monster()
            enc["monsters"] -= 1
            r.json().set(f"encounters:{player.location}", "$", enc)
        while enc["chests"] > 0:
            print("you found a chest!")
            num_items = random.randrange(MIN_CHEST_ITEMS, MAX_CHEST_ITEMS)
            chest = Chest(num_items)
            player.loot_chest(chest)
            enc["chests"] -= 1
            r.json().set(f"encounters:{player.location}", "$", enc)




    
# a function that adds random spots that will have encounters

def pop_test_encounters():
    encounter_bit = random.randrange(0, rows*cols)
    print("encounter :", encounter_bit)
    encounter_type = "chests"
    space_def[encounter_type] += 1
    r.json().set(f"encounters:{encounter_bit}", "$", space_def)


class Map():
    def __init__(self, r, rows, cols)
        self.r = r
        self.rows = rows
        self.cols = cols)
        self.entrance = random.randrange(0, cols-1)
        self.exit = random.randrange(rows*cols - rows + 1, rows*cols)
    # a function that checks if a player is on an edge and therefore cannot move in a certain direction

    def move(self, player):
        opts = self.check_edge(player)
        opts_list = [k for k,v in opts.items() if v == 1]
        mv = "diagonal"
        while mv not in opts_list:
            print("Your options are: ")
            print(opts_list)
            mv = input("Which way would you like to move?")
        last_bit = player.location
        if mv == "left":
            last_bit -= 1
        elif mv == "right":
            last_bit += 1
        elif mv == "up":
            last_bit += cols
        elif mv == "down":
            last_bit -= cols
        else:
            print("how on earth did you get here")

        print(last_bit)

        if r.getbit("map_game", last_bit) == 1:
            print("you've been here before!")
        else:
            r.setbit("map_game", last_bit, 1)

        self.location = last_bit

    def check_edge(self, player):
        movement_options = {
            "left": 1,
            "right": 1,
            "down": 1,
            "up": 1
        }
        last_bit = player.location
        if last_bit % cols == 0:
            movement_options["left"] = 0
        if last_bit % cols == cols - 1:
            movement_options["right"] = 0
        if 0 <= last_bit < cols:
            movement_options["down"] = 0
        if rows*cols - rows <= last_bit:
            movement_options["up"] = 0
        
    return movement_options


    def check_encounter(self, player):
        if enc := self.r.json().get(f"encounters:{player.location}"):
            for range(0, enc["monsters"]):
                print("you found a monster!")
                try:
                    player.fight_monster()
                except Exception as e:
                    print(e)
                    exit
                self.r.json().set(f"encounters:{player.location}", "$", enc)

            for range(0, enc["chests"])
                print("you found a chest!")
                player.loot_chest()
                self.r.json().set(f"encounters:{player.location}", "$", enc)

    def populate_tiles():
        num_encounters = random.randrange(
            int(self.rows*self.cols / 5),
            int(self.rows*self.cols / 2)
        )

        for range(0, num_encounters):
            encounter_bit = random.randrange(0, self.rows * self.cols)
            print("encounter :", encounter_bit)
            tile_type = random.choice(["chests", "monsters"])
            try:
                tile_info = r.json().get(f"encounters:{encounter_bit}")
                tile_info[tile_type] += 1
                r.json().set(f"encounters:{encounter_bit}", "$", tile_info)
            except:
                TILE_TYPES[tile_type] += 1
                r.json().set(f"encounters:{encounter_bit}", "$", TILE_TYPES)

def init_game():
    r.delete("map_game")

def main():
    player_name = input("what's your characters name?")
    player = Player(player_name)

    rows = int(input("how wide should the map be?"))
    cols = int(input("how tall should the map be?"))
    map = generate_map(rows, cols)
    print("entrance: ", map.entrance)
    print("exit: ", map.exit)
    
    player.location = map.entrance
    map.populate_tiles()
    # pop_test_encounters()
    r.setbit("map_game", map.entrance, 1)
    
    while player.location != map_exit and player.health > 0:
        if player.inventory.potions:
            use_potion = input("would you like to use a potion? (y or n)")
            if use_potion == "y":
                print(player.inventory.potions)
                potion_choice = int(input("enter the index of the potion you want to use"))
                player.health += player.inventory.potions.pop(potion_choice)
                print(player.health)
        map.move(player)
        map.check_encounter(player)
    if player.health > 0:
        print("you escaped!")
    else:
        print("you remained in the map forever :( ")

if __name__ == "__main__":
    main()