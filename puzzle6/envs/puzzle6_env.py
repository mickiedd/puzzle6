import gym
from gym import error, spaces, utils
from gym.utils import seeding
import os
import sys
import random
from ctypes import *
import math
from gym.envs.classic_control import rendering
import numpy as np



class Puzzle6Env(gym.Env):
  metadata = {'render.modes': ['human']}

  def get_color(self, r, g, b):
    return (r / 255, g / 255, b / 255)

  def __init__(self):

    print("puzzle6 inited")

    chessPropertiesTablePath = b"/home/mickie/course/puzzle6/data/LogicData/ChessPropertiesTable.bin"
    stageConfigPath = b"/home/mickie/course/puzzle6/data/DataConfig/StageData/Normal/stage_0003_0000.bin"
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
    self.observation_space = np.zeros(810)
    self.action_space = spaces.Discrete(729)

    #data
    self.data_stream = ""

    #color dictionary
    yellow = self.get_color(255, 255, 128)
    red = self.get_color(255, 0, 0)
    brown = self.get_color(128, 64, 0)
    green = self.get_color(0, 255, 0)
    blue = self.get_color(0, 0, 255)
    purple = self.get_color(128, 128, 255)
    white = self.get_color(192, 192, 192)
    self.color_dict = {'color(0)': yellow, 'color(1)': red, 'color(2)': brown, 'color(3)': green, 'color(4)': blue, 'color(5)': purple, 'color(6)': white, 'color(7)': None, 'color(8)': None, 'color(9)': None}
    self.to_direction_dict = {0: (0,-1), 1: (0,1), 2: (1,0), 3: (-1,0), 4: (-1,1), 5: (-1,-1), 6: (0,0), 7: (0,0), 8: (0,0)}
    #graphic
    self.viewer = None
    # Angle at which to fail the episode
    self.theta_threshold_radians = 12 * 2 * math.pi / 360
    self.x_threshold = 2.4
    self.state = None

  def _step(self, action):
    print("step", action)
    # 729=>900 728=>888
    to_direction = int(action % 9)
    from_col = int(action / 9 % 9)
    from_row = int(action / 81)
    item_type = 4
    #delta
    delta = self.to_direction_dict[to_direction]
    print("from_row:", from_row, ", from_col:", from_col, " to_direction:", to_direction, " delta:", delta)
    to_row = from_row + delta[0]
    to_col = from_col + delta[1]
    value1 = 0
    value2 = 0
    op = 0
    print("Take action.from:", from_row, from_col, ", to:", to_row, to_col)
    r = int(c_int(self.dll.we6_game_input_by_detail(self.gameInstanceRet, op, item_type, from_row, from_col, to_row, to_col, value1, value2)).value)

    print("Now board nodes:")
    len3 = c_int()
    self.data_stream = str(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)

    #print(data_stream)
    #print(len3)


    ob = np.zeros(810)
    reward = 0
    if r == 0:
      reward = 1
    print("action:", action, "reward:", reward)
    return ob, reward, self.episode_over, {}
  def _reset(self):
    print("reset")
    self.observation_space = np.zeros(810)
    return self.observation_space
  def get_chess(self, w, h):
    l,r,t,b = -w/2, w/2, h/2, -h/2
    pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
    axleoffset = h/4.0
    pole.trans = rendering.Transform(translation=(0, axleoffset))
    pole.add_attr(pole.trans)
    self.viewer.add_geom(pole)
    return pole

  def _render(self, mode='human', close=False):
    print("render")
    if close:
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
            return

    #start position x
    start_position_x = 100
    #start position y
    start_position_y = 100

    screen_width = 600
    screen_height = 600
    chess_width = 30
    chess_height = 30
    chess_bargin = 5

    chesses = {}

    #print(self.data_stream)
    if self.data_stream != '':
      stream_list = self.data_stream.replace("b'", "").split(',')
      #chesses_count = self.data_stream.count(',')
      #i_count = j_count = int(math.sqrt(chesses_count))
      if self.viewer == None:
          self.viewer = rendering.Viewer(screen_width, screen_height)
      print('subrender')
      for current_data_stream in stream_list: #0|0|color(9)
        #current data
        if current_data_stream != "'":
          #print(current_data_stream)
          current_data_stream_list = current_data_stream.split('|')
          chess_position_x = int(current_data_stream_list[1])
          chess_position_y = int(current_data_stream_list[0])
          chess_color_str = current_data_stream_list[2]
          #color
          chess_color = self.color_dict[chess_color_str]
          #print(chess_color)
          if chess_color != None:
            if chesses.get(chess_position_x * 9 + chess_position_y) == None:
              #not exists
              pole = self.get_chess(30, 30)
              chesses[chess_position_x * 9 + chess_position_y] = pole
            else:
              #exists
              pole = chesses[chess_position_x * 9 + chess_position_y]
            pole.set_color(chess_color[0], chess_color[1], chess_color[2])
            x = start_position_x + (chess_width + chess_bargin) * chess_position_x
            y = start_position_y + chess_position_x % 2 * 15 + (chess_height + chess_bargin) * chess_position_y
            pole.trans.set_translation(x, y)

    if self.viewer != None:
      return self.viewer.render(return_rgb_array=mode == 'rgb_array')
