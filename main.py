import redis
import random

r = redis.Redis()

space_def = {
    "chests": 0,
    "monsters": 0
}

# a function that adds random spots that will have encounters
def pop_encounters(rows, cols):
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


def check_encounters(last_bit):
    if r.json().get(f"encounters:{last_bit}"):
        print("you found something!")

# a function that checks if a player is on an edge and therefore cannot move in a certain direction
def check_edge(last_bit, rows, cols):
    movement_options = {
        "left": 1,
        "right": 1,
        "down": 1,
        "up": 1
    }
    if last_bit % cols == 0:
        movement_options["left"] = 0
    if last_bit % cols == cols - 1:
        movement_options["right"] = 0
    if 0 <= last_bit < cols:
        movement_options["down"] = 0
    if rows*cols - rows + 1 <= last_bit <= rows * cols:
        movement_options["up"] = 0
        
    return movement_options

def move_char(last_bit, rows, cols):
    opts = check_edge(last_bit, rows, cols)
    opts_list = [k for k,v in opts.items() if v == 1]
    mv = "diaganol"
    while mv not in opts_list:
        print("Your options are: ")
        print(opts_list)
        mv = input("Which way would you like to move?")
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

    return last_bit


def main():
    r.delete("map_game")
    name = input("what's your characters name?")
    rows = int(input("how wide should the map be?"))
    cols = int(input("how tall should the map be?"))

    map_entrance = random.randrange(0,cols)
    print("entrance: ", map_entrance)
    map_exit = random.randrange(rows*cols - rows + 1, rows*cols)
    print("exit: ", map_exit)
    last_bit = map_entrance

    pop_encounters(rows, cols)
    r.setbit("map_game", map_entrance, 1)
    while last_bit != map_exit:
        last_bit = move_char(last_bit, rows, cols)
        check_encounters(last_bit)
    print("you escaped!")
    return None




if __name__ == "__main__":
    main()
