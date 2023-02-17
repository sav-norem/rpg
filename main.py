import redis
import random

r = redis.Redis()

space_def = {
    "chests": 0,
    "monsters": 0
}

weapons = []
x = 0
while x < 4:
    damage = random.randrange(5,15)
    weapon_type = random.choice(["sword", "mace", "dagger"])
    weapons.append({"type": weapon_type, "damage": damage})
    x += 1

class player_def:
    def __init__(self):
        self.health = 20
        self.damage = 2
        self.inventory = []
        self.name = ''
        self.location = 0

class monster_def:
    def __init__(self):
        self.health = 3
        self.damage = 1

class chest_def:
    def __init__(self):
        self.items = []

# a function that adds random spots that will have encounters
def pop_encounters():
    num_encounters = random.randrange(0, int(rows*cols / 4))
    while num_encounters != 0:
        encounter_bit = random.randrange(0, rows*cols)
        print("encounter :", encounter_bit)
        encounter_type = random.choice(["chests", "monsters"])
        try:
            space_info = r.json().get(f"encounters:{encounter_bit}")
            space_info[encounter_type] += 1
            r.json().set(f"encounters:{encounter_bit}", "$", space_info)
        except:
            space_def[encounter_type] += 1
            r.json().set(f"encounters:{encounter_bit}", "$", space_def)

        num_encounters -= 1


def pop_test_encounters():
    encounter_bit = random.randrange(0, rows*cols)
    print("encounter :", encounter_bit)
    encounter_type = "monsters"
    space_def[encounter_type] += 1
    r.json().set(f"encounters:{encounter_bit}", "$", space_def)


def check_encounters():
    if enc := r.json().get(f"encounters:{player.location}"):
        while enc["monsters"] > 0:
            print("you found a monster!")
            fight_monster()
            enc["monsters"] -= 1
            r.json().set(f"encounters:{player.location}", "$", enc)
        if enc["chests"] > 0:
            print("you found a chest!")
            loot_chest()


def fight_monster():
    monster = monster_def()
    monster.health = random.randrange(1,5)
    while monster.health > 0:
        fight = input("fight the monster? (y or n)")
        if fight == "n":
            print("run away!")
            move_char()
            break
        if fight == "y":        
            player.health -= monster.damage 
            if player.health > 0:
                if not player.inventory:
                    print("you're punching a monster!")
                    monster.health -= player.damage
                else:
                    print("you can use your weapon!")
                    monster.health -= player.inventory[0]["damage"]

    if monster.health <= 0:
        print("you defeated the monster!")
    if player.health <= 0:
        print("the monster defeated you :( ")
        exit()

def loot_chest():
    chest = chest_def()
    chest.items.append(random.choice(weapons))
    choice = input(f'do you want to take the {chest.items[0]["type"]} that does {chest.items[0]["damage"]} damage? (y or n)')
    if choice == "y":
        player.inventory.append(chest.items[0])

# a function that checks if a player is on an edge and therefore cannot move in a certain direction
def check_edge():
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

def move_char():
    opts = check_edge()
    opts_list = [k for k,v in opts.items() if v == 1]
    mv = "diaganol"
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

    player.location = last_bit


def main():
    r.delete("map_game")
    player_name = input("what's your characters name?")
    global player 
    player = player_def()
    player.name = player_name
    global rows, cols
    rows = int(input("how wide should the map be?"))
    cols = int(input("how tall should the map be?"))

    map_entrance = random.randrange(0,cols-1)
    print("entrance: ", map_entrance)
    map_exit = random.randrange(rows*cols - rows + 1, rows*cols)
    print("exit: ", map_exit)
    player.location = map_entrance

    pop_encounters()
    # pop_test_encounters()
    r.setbit("map_game", map_entrance, 1)
    while player.location != map_exit and player.health > 0:
        move_char()
        check_encounters()
    if player.health > 0:
        print("you escaped!")
    else:
        print("you remained in the map forever :( ")
    return None



if __name__ == "__main__":
    main()
