import hjson
import numpy as np
import random

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
    'road': ['='],
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
    generated_map = [[terrain_stats['plains'][0]] * config_data['width'] for _ in range(config_data['height'])]
    for i in range(config_data['height']):
        for j in range(config_data['width']):
            generated_map[i][j] = terrain_stats[random.sample(list(terrain_stats)[18:26], 1)[0]][0]
    return generated_map


if __name__ == '__main__':
    load_config()
    generated_map = generate_initial_map()
    generated_map[2][4] = 'Q'
    write_map(generated_map, config_data['key'])
