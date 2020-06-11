import hjson
import random
import copy

'''
    terrain name -> (
        representation,
        foot movement cost,
        cavalry movement cost,
        sea cost,
        extra cost (because units can't stay on this tile)
    )
    
'''
terrain_stats = {
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
    'road': ['-'],
    'river': ['['],
    'shore': ['<'],  # might not use this
}

MAX_DIMENSION = 39
config_data = {}


# read the config file for settings
def load_config():
    global config_data
    with open('config.hjson') as f:
        config_data = hjson.load(f)
    if config_data['key'] == 0:
        config_data['key'] = random.randint(0, 100_000)
    random.seed(config_data['key'])
    enabled_terrains = [terrain_stats[i] for i in list(config_data['terrain']) if config_data['terrain'][i] == 1]
    config_data['enabled_terrain'] = enabled_terrains


# display the map on console and store in "Generated maps/<seed name>"
def write_map(generated_map, name: str = None):
    with open('Generated maps/{}'.format(name), 'w') as f:
        for gen_row in generated_map:
            gen_row += [0] * (MAX_DIMENSION - config_data['width'])
            for tile in gen_row:
                f.write(str(tile))
                print(tile, end='')
            print('')
            f.write('\n')


# generate initial map to be iterated upon
def generate_initial_map():
    generated_map = [[terrain_stats['sea'][0]] * config_data['width'] for _ in range(config_data['height'])]

    # deciding initial HQ/stronghold position
    hq_x = random.randint(0, int(config_data['width'] / 3))
    hq_y = int(config_data['height'] / 2) - hq_x
    if hq_y < 0:
        hq_y *= -1
    hq_y = random.randint(0, min(config_data['height'], hq_y))
    generated_map[hq_y][hq_x] = terrain_stats['p1 stronghold'][0]
    generated_map[config_data['height'] - hq_y - 1][config_data['width'] - hq_x - 1] = terrain_stats['p2 stronghold'][0]

    # for i in range(config_data['height']):
    #     for j in range(config_data['width']):
    #         generated_map[i][j] = random.sample(config_data['enabled_terrain'], 1)[0][0]
    #         generated_map[config_data['height'] - i - 1][config_data['width'] - j - 1] = generated_map[i][j]
    generated_map, successful = create_land(generated_map, hq_x, hq_y)
    while not successful:
        generated_map, successful = create_land(generated_map, hq_x, hq_y)

    generated_map = add_land(generated_map)
    return generated_map


def generate_tile_info(generated_map, y, x):
    tile_info = [y, x, [], 0]
    if x + 1 < config_data['width'] and generated_map[y][x + 1] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append('e')
    if x - 1 > 0 and generated_map[y][x - 1] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append('w')
    if y + 1 < config_data['height'] and generated_map[y + 1][x] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append('s')
    if y - 1 > 0 and generated_map[y - 1][x] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append('n')
    return tile_info


def add_land(generated_map):
    target_land_count = int(config_data['height'] * config_data['width'] * float(config_data['land_ratio']))
    current_land_count = 0

    # generating a set of land tiles
    land_tiles = []
    for y in range(config_data['height']):
        for x in range(config_data['width']):
            if generated_map[y][x] == terrain_stats['plains'][0]:
                current_land_count += 1
                land_tiles.append(generate_tile_info(generated_map, y, x))
                if land_tiles[-1][3] == 4:
                    del land_tiles[-1]

    for i in range(int((target_land_count - current_land_count)/2)):
        while True:
            target_tile_index = random.randint(0, len(land_tiles)-1)
            target_tile = land_tiles[target_tile_index]
            if target_tile[3] == 1 and random.uniform(0, 1) > 0:
                append_direction = random.sample(target_tile[2], 1)[0]
            elif target_tile[3] == 2 and random.uniform(0, 1) > .2:
                append_direction = random.sample(target_tile[2], 1)[0]
            elif target_tile[3] == 3 and random.uniform(0, 1) > .8:
                append_direction = random.sample(target_tile[2], 1)[0]
            elif target_tile[3] == 4 and random.uniform(0, 1) > 1:
                append_direction = random.sample(target_tile[2], 1)[0]
            else:
                continue
            if append_direction == 'n':
                land_tiles[target_tile_index][2].remove('n')
                land_tiles[target_tile_index][3] -= 1
                if land_tiles[target_tile_index][3] == 4:
                    del land_tiles[target_tile_index]

                generated_map[target_tile[0] - 1][target_tile[1]] = terrain_stats['plains'][0]
                land_tiles.append(generate_tile_info(generated_map, target_tile[0] - 1, target_tile[1]))
                if land_tiles[-1][3] == 4:
                    del land_tiles[-1]
            if append_direction == 's':
                land_tiles[target_tile_index][2].remove('s')
                land_tiles[target_tile_index][3] -= 1
                if land_tiles[target_tile_index][3] == 4:
                    del land_tiles[target_tile_index]

                generated_map[target_tile[0] + 1][target_tile[1]] = terrain_stats['plains'][0]
                land_tiles.append(generate_tile_info(generated_map, target_tile[0] + 1, target_tile[1]))
                if land_tiles[-1][3] == 4:
                    del land_tiles[-1]
            if append_direction == 'e':
                land_tiles[target_tile_index][2].remove('e')
                land_tiles[target_tile_index][3] -= 1
                if land_tiles[target_tile_index][3] == 4:
                    del land_tiles[target_tile_index]

                generated_map[target_tile[0]][target_tile[1] + 1] = terrain_stats['plains'][0]
                land_tiles.append(generate_tile_info(generated_map, target_tile[0], target_tile[1] + 1))
                if land_tiles[-1][3] == 4:
                    del land_tiles[-1]
            if append_direction == 'w':
                land_tiles[target_tile_index][2].remove('w')
                land_tiles[target_tile_index][3] -= 1
                if land_tiles[target_tile_index][3] == 4:
                    del land_tiles[target_tile_index]

                generated_map[target_tile[0]][target_tile[1] - 1] = terrain_stats['plains'][0]
                land_tiles.append(generate_tile_info(generated_map, target_tile[0], target_tile[1] - 1))
                if land_tiles[-1][3] == 4:
                    del land_tiles[-1]
            break
    return generated_map


def create_land(generated_map, hq_x, hq_y):
    map_backup = copy.deepcopy(generated_map)
    x = hq_x
    y = hq_y
    while True:
        generated_map[y][x] = terrain_stats['p1 stronghold'][0]
        generated_map[config_data['height'] - y - 1][config_data['width'] - x - 1] = terrain_stats['p2 stronghold'][0]
        next_square = []
        if x + 1 < config_data['width']:
            if generated_map[y][x + 1] == terrain_stats['p2 stronghold'][0]:
                break
            if generated_map[y][x + 1] == terrain_stats['sea'][0]:
                next_square.append([y, x + 1])
        if x - 1 > 0:
            if generated_map[y][x - 1] == terrain_stats['p2 stronghold'][0]:
                break
            if generated_map[y][x - 1] == terrain_stats['sea'][0]:
                next_square.append([y, x - 1])
        if y + 1 < config_data['height']:
            if generated_map[y + 1][x] == terrain_stats['p2 stronghold'][0]:
                break
            if generated_map[y + 1][x] == terrain_stats['sea'][0]:
                next_square.append([y + 1, x])
        if y - 1 > 0:
            if generated_map[y - 1][x] == terrain_stats['p2 stronghold'][0]:
                break
            if generated_map[y - 1][x] == terrain_stats['sea'][0]:
                next_square.append([y - 1, x])
        if len(next_square) == 0:
            return map_backup, False
        y, x = random.sample(next_square, 1)[0]
    for i in range(config_data['height']):
        for j in range(config_data['width']):
            if generated_map[i][j] == terrain_stats['p1 stronghold'][0] or generated_map[i][j] == \
                    terrain_stats['p2 stronghold'][0]:
                generated_map[i][j] = terrain_stats['plains'][0]
    return generated_map, True


if __name__ == '__main__':
    load_config()
    generated_map = generate_initial_map()
    write_map(generated_map, config_data['key'])
