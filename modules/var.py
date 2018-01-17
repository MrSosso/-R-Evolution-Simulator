import os
import pygame as pyg
from . import genes as gns

SIMULATIONS_PATH = os.path.join(os.getcwd(), "simulations")

# simulation

DEFAULT_SIM_VARIABLES = {'dimension': {'width': 60, 'height': 45},
                         'chunk_dim': 10,
                         'max_lifetime': 10000,
                         'initial_creatures': {
                             'herbivors': 400,
                             'carnivors': 100
                         },
                         'chunks_vars': {'growth_coeff': 0.0003,
                                         'foodmax_max': 100,
                                         'temperature_max': 100,
                                         },
                         'creatures_vars': {'view_ray': 3,
                                            'en_dec_coeff': 0.02,
                                            'eat_coeff': 0.005,
                                            'en_inc_coeff': 1.5,
                                            'average_age': 1000,
                                            'dev_age_prob': 500,
                                            'temp_death_prob_coeff': 100,
                                            'genes_lim': {'agility': (10, 60),
                                                          'bigness': (20, 80),
                                                          'fertility': (150, 250),
                                                          'num_control': (0, 100)
                                                          },
                                            'mutation_coeff': 0.05,
                                            'fertility_energy_coeff': 50000,
                                            'reprod_energy_dec_coeff': 0.8,
                                            'predator_eat_coeff': 0.5,
                                            },
                         'analysis': {'tick_interval': 100,
                                      'percentile_parts': 4,
                                      'parts': 8,
                                      'rounding': 4}
                         }

CHUNK_ATTRS = ('temperature', 'foodmax')

CREATURES_GENES = {'agility': gns.Agility, 'bigness': gns.Bigness, 'fertility': gns.Fertility,
                   'num_control': gns.NumControl, 'temp_resist': gns.TempResist, 'mndl_control': gns.MendelControl}
CREATURES_SECONDARY_GENES = {'speed': gns.Speed}

# files

DIRECTORIES = ['data', 'images', 'analysis']

FILE_SEPARATORS = (';', '/', ',', '|', '§')

FILE_EXTENSIONS = {'numeric_analysis': 'rsan',
                   'spreading_analysis': 'rsas',
                   'demographic_analysis': 'rsad',
                   'chunks_attribute': 'rsca',
                   'creatures_data': 'rscr',
                   'chunks_data': 'rsch',
                   'simulation_data': 'rssd'}

TO_RECORD = {
    'simulation': {'name': None, 'dimension': {'width': None, 'height': None}, 'lifetime': None,
                   'initial_creatures': {
                       'herbivors': None,
                       'carnivors': None
                   }, 'chunk_dim': None, 'tick_count': None,
                   'chunks_vars': {'growth_coeff': None,
                                   'foodmax_max': None,
                                   'temperature_max': None,
                                   },
                   'creatures_vars': {'view_ray': None,
                                      'en_dec_coeff': None,
                                      'eat_coeff': None,
                                      'en_inc_coeff': None,
                                      'average_age': None,
                                      'dev_age_prob': None,
                                      'temp_death_prob_coeff': None,
                                      'genes_lim': {'agility': None,
                                                    'bigness': None,
                                                    'fertility': None,
                                                    'num_control': None
                                                    },
                                      'mutation_coeff': None,
                                      'fertility_energy_coeff': None,
                                      'reprod_energy_dec_coeff': None,
                                      'predator_eat_coeff': None
                                      },
                   'analysis': {'tick_interval': None,
                                'percentile_parts': None,
                                'parts': None,
                                'rounding': None},
                   'ID_count': None},
    'creature': {'ID': None, 'birth_tick': None, 'parents_ID': None, 'sex': None, 'diet': None,
                 'genes': {'agility': None,
                           'bigness': None,
                           'fertility': None,
                           'num_control': None,
                           'temp_resist': None,
                           'mndl_control': None,
                           'speed': None
                           },
                 'death_tick': None, 'death_cause': None, 'tick_history': 1},
    'chunk': {'coord': None, 'foodmax': None, 'growth_rate': None, 'temperature': None, 'food_history': 1}}

# graphics

DEFAULT_CREATURES_COLORS = {'none': pyg.Color(255, 255, 255, 255),
                            'sex': (pyg.Color(255, 255, 0, 255), pyg.Color(0, 255, 255, 255)),
                            'temp_resist': {'c': pyg.Color(255, 0, 0, 255),
                                            'l': pyg.Color(0, 0, 255, 255),
                                            'N': pyg.Color(127, 127, 127, 255),
                                            'n': pyg.Color(255, 255, 255, 255)},
                            'mndl_control': {'A': pyg.Color(255, 0, 255, 255),
                                             'a': pyg.Color(255, 191, 255, 255), }
                            }

DEFAULT_CREATURES_DIMS = {'none': 7,
                          'agility': 1 / 5,
                          'bigness': 1 / 7,
                          'num_control': 1 / 9,
                          'speed': 5}

DEFAULT_CREATURES_BORDER = {'color': pyg.Color(0, 0, 0, 255), 'width': 1}
