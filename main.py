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
config = {}


# read the config file for settings
def load_config():
    global config
    with open('config.hjson') as f:
        config = hjson.load(f)
    if config['key'] == 0:
        config['key'] = random.randint(0, 100_000)
    random.seed(config['key'])
    enabled_terrains = [terrain_stats[i] for i in list(config['terrain']) if config['terrain'][i] == 1]
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
    generated_map = [[terrain_stats['sea'][0]] * config['width'] for _ in range(config['height'])]

    # deciding initial HQ/stronghold position
    hq_x = random.randint(0, int(config['width'] / 3))
    hq_y = int(config['height'] / 2) - hq_x
    if hq_y < 0:
        hq_y *= -1
    hq_y = random.randint(0, min(config['height'], hq_y))
    generated_map[hq_y][hq_x] = terrain_stats['p1 stronghold'][0]
    generated_map[config['height'] - hq_y - 1][config['width'] - hq_x - 1] = terrain_stats['p2 stronghold'][0]

    generated_map, successful = create_land(generated_map, hq_x, hq_y)
    while not successful:
        generated_map, successful = create_land(generated_map, hq_x, hq_y)

    return generated_map


def generate_tile_info(generated_map, y, x):
    tile_info = [y, x, [], 0]
    if x + 1 < config['width'] and generated_map[y][x + 1] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([0, 1])
    if x - 1 > 0 and generated_map[y][x - 1] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([0, -1])
    if y + 1 < config['height'] and generated_map[y + 1][x] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([1, 0])
    if y - 1 > 0 and generated_map[y - 1][x] == terrain_stats['sea'][0]:
        tile_info[3] += 1
        tile_info[2].append([-1, 0])
    return tile_info


def add_land(generated_map):
    target_land_count = int(config['height'] * config['width'] * float(config['land_ratio'])/2)
    current_land_count = 0

    # generating a set of land tiless
    land_tiles = []
    for y in range(int(config['height'] / 2)):
        for x in range(config['width']):
            if generated_map[y][x] == terrain_stats['plains'][0]:
                current_land_count += 1
                land_tiles.append(generate_tile_info(generated_map, y, x))
                if land_tiles[-1][3] == 0:
                    del land_tiles[-1]

    for i in range(int((target_land_count - current_land_count))):
        while True:
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
        generated_map[y][x] = terrain_stats['plains'][0]
        generated_map[mirror_y][mirror_x] = terrain_stats['plains'][0]
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
        generated_map[y][x] = terrain_stats['p1 stronghold'][0]
        generated_map[config['height'] - y - 1][config['width'] - x - 1] = terrain_stats['p2 stronghold'][0]
        next_square = []
        if x + 1 < config['width']:
            if generated_map[y][x + 1] == terrain_stats['p2 stronghold'][0]:
                break
            if generated_map[y][x + 1] == terrain_stats['sea'][0]:
                next_square.append([y, x + 1])
        if x - 1 > 0:
            if generated_map[y][x - 1] == terrain_stats['p2 stronghold'][0]:
                break
            if generated_map[y][x - 1] == terrain_stats['sea'][0]:
                next_square.append([y, x - 1])
        if y + 1 < config['height']:
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
    for i in range(config['height']):
        for j in range(config['width']):
            if generated_map[i][j] == terrain_stats['p1 stronghold'][0] or generated_map[i][j] == \
                    terrain_stats['p2 stronghold'][0]:
                generated_map[i][j] = terrain_stats['plains'][0]
    return generated_map, True


def remove_lone_sea(generated_map):
    for y in range(config['height']):
        for x in range(config['width']):
            if generated_map[y][x] == terrain_stats['sea'][0] and generate_tile_info(generated_map, y, x)[3] == 0:
                generated_map[y][x] = terrain_stats['plains'][0]
    return generated_map


if __name__ == '__main__':
    load_config()
    generated_map = generate_initial_map()
    generated_map = add_land(generated_map)
    if config['remove_lone_sea'] == 1:
        generated_map = remove_lone_sea(generated_map)
    write_map(generated_map, config['key'])
