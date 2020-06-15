import hjson
import random
import copy
import numpy as np

'''
    terrain name -> (
        representation,
        foot movement cost,
        cavalry movement cost,
        sea cost,
        extra cost (because units can't stay on this tile)
    )
    
'''
terrain_map = {
    'neutral village': ['a'],
    'neutral barracks': ['b'],
    'neutral tower': ['c'],
    'neutral port': ['d'],
    'neutral hideout': ['V'],

    'p1 village': ['e'],
    'p1 barracks': ['f'],
    'p1 tower': ['g'],
    'p1 port': ['h'],
    'p1 hideout': ['Q'],
    'p1 stronghold': ['i'],

    'p2 village': ['j'],
    'p2 barracks': ['l'],
    'p2 tower': ['m'],
    'p2 port': ['n'],
    'p2 hideout': ['5'],
    'p2 stronghold': ['o'],

    'i forgot': ['_'],
    'plains': ['.'],
    'forest': ['@'],
    'mountain': ['^'],
    'sea': [','],
    'reef': ['%'],
    'road_1': ['-'],
    'road_2': ['='],
    'river': ['['],
    'shore': ['<'],  # might not use this
}

movement_info = {
    'neutral village': 2,
    'a': 2,
    'neutral barracks': 2,
    'b': 2,
    'neutral tower': 2,
    'c': 2,
    'neutral port': 2,
    'd': 2,
    'neutral hideout': 2,
    'V': 2,
    'p1 village': 2,
    'e': 2,
    'p1 barracks': 2,
    'f': 2,
    'p1 tower': 2,
    'g': 2,
    'p1 port': 2,
    'h': 2,
    'p1 hideout': 2,
    'Q': 2,
    'p1 stronghold': 2,
    'i': 2,
    'p2 village': 2,
    'j': 2,
    'p2 barracks': 2,
    'l': 2,
    'p2 tower': 2,
    'm': 2,
    'p2 port': 2,
    'n': 2,
    'p2 hideout': 2,
    '5': 2,
    'p2 stronghold': 2,
    'o': 2,

    'i forgot': 99,
    '_': 99,
    'plains': 3,
    '.': 3,
    'forest': 2,
    '@': 2,
    'mountain': 1,
    '^': 1,
    'sea': 0,
    ',': 0,
    'reef': 0,
    '%': 0,
    'road_1': 3,
    '-': 3,
    'road_2': 3,
    '=': 3,
    'river': 2,
    '': 2,
    'shore': 3,
    '<': 3  # might not use this
}

MAX_DIMENSION = 39
config = {}


# read the config file for settings
def load_config():
    global config
    with open('config.hjson') as f:
        config = hjson.load(f)
    if config['key'] == 0:
        config['key'] = random.randint(0, 100_000)
    random.seed(config['key'])
    enabled_terrains = [terrain_map[i] for i in list(config['terrain']) if config['terrain'][i] == 1]
    config['enabled_terrain'] = enabled_terrains


# display the map on console and store in "Generated maps/<seed name>"
def write_map(generated_map, name: str = None):
    with open('Generated maps/{}'.format(name), 'w') as f:
        for gen_row in generated_map:
            gen_row += [0] * (MAX_DIMENSION - config['width'])
            for tile in gen_row:
                f.write(str(tile))
                print(tile, end='')
            print('')
            f.write('\n')


# generate initial map to be iterated upon
def generate_initial_map():
    generated_map = [[terrain_map['sea'][0]] * config['width'] for _ in range(config['height'])]

    # deciding initial HQ/stronghold position
    max_x = np.floor(config['width'] * (1-float(config['min_starting_distance']))/2)
    max_y = np.floor(config['height'] * (1-float(config['min_starting_distance']))/2)
    hq_y = random.randint(0, max_y)
    hq_x = random.randint(0, max_x)
    mirror_y = config['height'] - hq_y - 1
    mirror_x = config['width'] - hq_x - 1

    # classic
    generated_map, successful = create_land(generated_map, hq_x, hq_y)
    while not successful:
        generated_map, successful = create_land(generated_map, hq_x, hq_y)

    # # box type
    # for i in range(config['height']):
    #     for j in range(config['width']):
    #         if hq_y <= i <= mirror_y and (j == hq_x or j == mirror_x):
    #             generated_map[i][j] = terrain_map['plains'][0]
    #         if hq_x <= j <= mirror_x and (i == hq_y or i == mirror_y):
    #             generated_map[i][j] = terrain_map['plains'][0]

    return generated_map, hq_y, hq_x


def generate_tile_info(generated_map, y, x):
    tile_info = [y, x, [], 0]
    if x + 1 < config['width'] and generated_map[y][x + 1] == terrain_map['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([0, 1])
    if x - 1 > 0 and generated_map[y][x - 1] == terrain_map['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([0, -1])
    if y + 1 < config['height'] and generated_map[y + 1][x] == terrain_map['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([1, 0])
    if y - 1 > 0 and generated_map[y - 1][x] == terrain_map['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([-1, 0])
    return tile_info


def add_land(generated_map):
    target_land_count = int(config['height'] * config['width'] * float(config['land_ratio']))
    current_land_count = 0

    # generating a set of land tiless
    land_tiles = []
    for y in range(int(config['height'] / 2)):
        for x in range(config['width']):
            if generated_map[y][x] == terrain_map['plains'][0]:
                current_land_count += 1
                land_tiles.append(generate_tile_info(generated_map, y, x))
                if land_tiles[-1][3] == 0:
                    del land_tiles[-1]

    while current_land_count < target_land_count:
        while True:
            if len(land_tiles) == 0:
                return generated_map
            target_tile_index = random.randint(0, len(land_tiles) - 1)
            target_tile_info = land_tiles[target_tile_index]
            if target_tile_info[3] == 1 and random.uniform(0, 1) > 0:
                append_direction = random.sample(target_tile_info[2], 1)[0]
            elif target_tile_info[3] == 2 and random.uniform(0, 1) > .2:
                append_direction = random.sample(target_tile_info[2], 1)[0]
            elif target_tile_info[3] == 3 and random.uniform(0, 1) > .8:
                append_direction = random.sample(target_tile_info[2], 1)[0]
            elif target_tile_info[3] == 4 and random.uniform(0, 1) > 1:
                append_direction = random.sample(target_tile_info[2], 1)[0]
            else:
                continue
            break
        y = target_tile_info[0] + append_direction[0]
        x = target_tile_info[1] + append_direction[1]
        mirror_y = config['height'] - y - 1
        mirror_x = config['width'] - x - 1
        if generated_map[y][x] == terrain_map['sea'][0]:
            current_land_count += 2
        generated_map[y][x] = terrain_map['plains'][0]
        generated_map[mirror_y][mirror_x] = terrain_map['plains'][0]
        land_tiles.append(
            generate_tile_info(
                generated_map,
                y,
                x
            )
        )
        if land_tiles[-1][3] == 0:
            del land_tiles[-1]
        land_tiles[target_tile_index][2].remove(append_direction)
        land_tiles[target_tile_index][3] -= 1
        if land_tiles[target_tile_index][3] == 0:
            del land_tiles[target_tile_index]
    return generated_map


def create_land(generated_map, hq_x, hq_y):
    map_backup = copy.deepcopy(generated_map)
    x = hq_x
    y = hq_y
    while True:
        generated_map[y][x] = terrain_map['road_1'][0]
        generated_map[config['height'] - y - 1][config['width'] - x - 1] = terrain_map['road_2'][0]
        next_square = []
        if x + 1 < config['width']:
            if generated_map[y][x + 1] == terrain_map['road_2'][0]:
                break
            if generated_map[y][x + 1] == terrain_map['sea'][0]:
                next_square.append([y, x + 1])
        if x - 1 > 0:
            if generated_map[y][x - 1] == terrain_map['road_2'][0]:
                break
            if generated_map[y][x - 1] == terrain_map['sea'][0]:
                next_square.append([y, x - 1])
        if y + 1 < config['height']:
            if generated_map[y + 1][x] == terrain_map['road_2'][0]:
                break
            if generated_map[y + 1][x] == terrain_map['sea'][0]:
                next_square.append([y + 1, x])
        if y - 1 > 0:
            if generated_map[y - 1][x] == terrain_map['road_2'][0]:
                break
            if generated_map[y - 1][x] == terrain_map['sea'][0]:
                next_square.append([y - 1, x])
        if len(next_square) == 0:
            return map_backup, False
        y, x = random.sample(next_square, 1)[0]
    for i in range(config['height']):
        for j in range(config['width']):
            if generated_map[i][j] == terrain_map['road_1'][0] or generated_map[i][j] == \
                    terrain_map['road_2'][0]:
                generated_map[i][j] = terrain_map['plains'][0]
    return generated_map, True


def remove_lone_sea(generated_map):
    for y in range(config['height']):
        for x in range(config['width']):
            if generated_map[y][x] == terrain_map['sea'][0] and generate_tile_info(generated_map, y, x)[3] == 0:
                generated_map[y][x] = terrain_map['plains'][0]
    return generated_map


def place_buildings(generated_map, hq_y, hq_x):
    # placing strongholds
    generated_map[hq_y][hq_x] = terrain_map['p1 stronghold'][0]
    generated_map[config['height'] - hq_y - 1][config['width'] - hq_x - 1] = terrain_map['p2 stronghold'][0]

    # placing barracks and towers
    # TODO

    # placing villages
    # TODO

    return generated_map


def calculate_openness(generated_map):
    openness = np.array([[0] * config['width'] for _ in range(config['height'])])
    for y in range(config['height']):
        for x in range(config['width']):
            if generated_map[y][x] == terrain_map['sea'][0]:
                continue
            for i in range(config['height']):
                for j in range(config['width']):
                    distance = abs(y - i) + abs(x - j)
                    if distance == 0:
                        continue
                    openness[y][x] += movement_info[generated_map[i][j]] / distance
    # calculate average movement
    mov_values = []
    for i in openness.flatten():
        if i != 0:
            mov_values.append(i)
    avg_openness = np.average(mov_values)

    # normalize
    openness = (openness / np.sum(openness)) ** 2
    return openness, avg_openness


def calculate_movement(generated_map, max_move: int = 5):
    movement = np.array([[0] * config['width'] for _ in range(config['height'])])
    for y in range(config['height']):
        for x in range(config['width']):
            if generated_map[y][x] == terrain_map['sea'][0]:
                continue
            for i in range(y - max_move, y + max_move + 1):
                if i < 0 or i >= config['height']:
                    continue
                for j in range(x - max_move, x + max_move + 1):
                    if j < 0 or j >= config['width']:
                        continue
                    distance = abs(y - i) + abs(x - j)
                    if distance == 0:
                        continue
                    movement[y][x] += movement_info[generated_map[i][j]] / distance
    # calculate average movement
    mov_values = []
    for i in movement.flatten():
        if i != 0:
            mov_values.append(i)
    avg_movement = np.average(mov_values)

    # normalize
    movement = (movement / np.sum(movement)) ** 2
    return movement, avg_movement


def weighted_sample_2d(matrix: np.ndarray, count: int = 1):
    matrix = matrix.flatten()
    matrix = matrix / sum(matrix)
    sample = np.random.choice(range(len(matrix)), count, p=matrix)
    if count == 1:
        y = int(np.floor(sample[0] / config['width']))
        x = int(sample[0] % config['width'])
    else:
        y = []
        x = []
        for i in range(count):
            y.append(int(np.floor(sample[i] / config['width'])))
            x.append(int(sample[i] % config['width']))
    return y, x


def place_terrain(generated_map):
    while True:
        mov_matrix, movement = calculate_openness(generated_map)
        y, x = weighted_sample_2d(mov_matrix)
        if generated_map[y][x] == terrain_map['plains'][0]:
            if random.uniform(0, 1) > .3:
                generated_map[y][x] = terrain_map['forest'][0]
                generated_map[config['height'] - y - 1][config['width'] - x - 1] = terrain_map['forest'][0]
            else:
                generated_map[y][x] = terrain_map['mountain'][0]
                generated_map[config['height'] - y - 1][config['width'] - x - 1] = terrain_map['mountain'][0]
        if movement < config['openness']:
            break
    return generated_map


def place_terrain_fast(generated_map):
    mountain_count = int(float(config['mountain_ratio']) * config['width'] * config['height'] * float(config['land_ratio']))
    forest_count = int(float(config['forest_ratio']) * config['width'] * config['height'] * float(config['land_ratio']))

    # adding mountains
    mov_matrix, _ = calculate_movement(generated_map)
    y, x = weighted_sample_2d(mov_matrix, mountain_count)
    for i in range(len(x)):
        if generated_map[y[i]][x[i]] == terrain_map['plains'][0]:
            generated_map[y[i]][x[i]] = terrain_map['mountain'][0]
            generated_map[config['height'] - y[i] - 1][config['width'] - x[i] - 1] = terrain_map['mountain'][0]

    # adding mountains
    mov_matrix, _ = calculate_movement(generated_map)
    y, x = weighted_sample_2d(mov_matrix, forest_count)
    for i in range(len(x)):
        if generated_map[y[i]][x[i]] == terrain_map['plains'][0]:
            generated_map[y[i]][x[i]] = terrain_map['forest'][0]
            generated_map[config['height'] - y[i] - 1][config['width'] - x[i] - 1] = terrain_map['forest'][0]
    return generated_map


if __name__ == '__main__':
    load_config()

    # creating land
    generated_map, hq_y, hq_x = generate_initial_map()
    generated_map = add_land(generated_map)

    # various checks
    if config['remove_lone_sea'] == 1:
        generated_map = remove_lone_sea(generated_map)

    # placing buildings
    generated_map = place_buildings(generated_map, hq_y, hq_x)

    # placing trees and mountains
    generated_map = place_terrain_fast(generated_map)

    # storing map
    write_map(generated_map, config['key'])

    # debug stuff
    map_movement, _ = calculate_movement(generated_map)
    for row in map_movement:
        for val in row:
            print(round(val, 3), end=',')
        print('')
    print('\n\n')
