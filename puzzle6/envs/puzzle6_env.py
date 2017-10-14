import gym
from gym import error, spaces, utils
from gym.utils import seeding
import os
import sys
import random
from ctypes import *

class Puzzle6Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def __init__(self):
    print("puzzle6 inited")
    
    chessPropertiesTablePath = b"/home/mickie/course/puzzle6/data/LogicData/ChessPropertiesTable.bin"
    stageConfigPath = b"/home/mickie/course/puzzle6/data/DataConfig/StageData/Normal/stage_0061_0000.bin"
    commonPath = b"/home/mickie/course/puzzle6/data/DataConfig/"
    
    self.dll = cdll.LoadLibrary('/home/mickie/Downloads/libwe6remove.so')

    #create game instance
    self.gameInstanceRet = self.dll.we6_game_new_ctx('', 0)
    
    #start the game
    self.dll.we6_game_quick_run(self.gameInstanceRet, chessPropertiesTablePath, stageConfigPath, commonPath)
    len3 = c_int()
    print("Original:")
    print(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)
    print(len3)
    print("=========")
    
    self.episode_over = False
    self.observation_space = spaces.Box(low=-1, high=1,
                                            shape=())
    self.action_space = spaces.Tuple((spaces.Discrete(3),
                                          spaces.Box(low=0, high=100, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1),
                                          spaces.Box(low=0, high=100, shape=1),
                                          spaces.Box(low=-180, high=180, shape=1)))
  def _step(self, action):
    print("step", action)
    
    op = 0
    item_type = 4
    from_row = int(random.uniform(0, 10))
    from_col = int(random.uniform(0, 10))
    to_row = int(random.uniform(0, 10))
    to_col = int(random.uniform(0, 10))
    value1 = 0
    value2 = 0
    print("Take action.from:", from_row, from_col, ", to:", to_row, to_col)
    print(c_int(self.dll.we6_game_input_by_detail(self.gameInstanceRet, op, item_type, from_row, from_col, to_row, to_col, value1, value2)).value)
    
    print("Now board nodes:")
    len3 = c_int()
    print(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)
    print(len3)
    
    print("=========")
    
    ob = 0
    reward = 1
    return ob, reward, self.episode_over, {}
  def _reset(self):
    print("reset")
  def _render(self, mode='human', close=False):
    print("render")
