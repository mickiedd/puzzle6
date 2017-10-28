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
  def is_border(self, row, col, direction):
    if col >= self.colsum - 1 and (direction == 0 or direction == 1):
      return True
    if row >= self.rowsum - 1 and ((direction == 1 and col % 2 == 1) or direction == 2):
      return True
    if row <= 0 and direction == 0 and col % 2 == 0:
      return True
    return False
  def endcode_color(self, color_num):
    return int(float(color_num) / 10.0 * 255.0)
  def decode_color(self, color_num):
    return int(float(color_num) / 250.0 * 10.0)
  def get_color(self, r, g, b):
    return (r / 255, g / 255, b / 255)
  def grid2position(self, row, col):
    x = self.start_position_x + (self.chess_width + self.chess_bargin) * col
    y = self.screen_height - (self.start_position_y + col % 2 * 15 + (self.chess_height + self.chess_bargin) * row)
    return (x, y)
  def get_chess(self, w, h):
    l,r,t,b = -w/2, w/2, h/2, -h/2
    pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
    axleoffset = h/4.0
    pole.trans = rendering.Transform(translation=(0, axleoffset))
    pole.add_attr(pole.trans)
    self.viewer.add_geom(pole)
    return pole
  def fetch_stream_data(self):
    len = c_int()
    p = c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len)))
    self.data_stream = str(p.value)
    # free pointer
    self.dll.we6_free_data(self.gameInstanceRet, p, len)
  def get_state(self):
    ob = np.zeros((self.rowsum, self.colsum, self.colorsum), dtype=c_uint8)
    max_color_num = 0
    if self.data_stream != '':
      stream_list = self.data_stream.replace("b'", "").split(',')
      for current_data_stream in stream_list:  # 0|0|color(9)
        # current data
        if current_data_stream != "'":
          current_data_stream_list = current_data_stream.split('|')
          chess_position_x = int(current_data_stream_list[0])
          chess_position_y = int(current_data_stream_list[1])
          if chess_position_x >= self.colsum:
            continue
          if chess_position_y >= self.rowsum:
            continue
          chess_color_str = current_data_stream_list[2]
          # color
          chess_color_num = self.color_num_dict[chess_color_str]
          ob[chess_position_x][chess_position_y][chess_color_num] = 1
          if chess_color_num > max_color_num:
            max_color_num = chess_color_num
    return ob
  def __init__(self):
    print("puzzle6 inited")
    self.rowsum = 8
    self.colsum = 8
    self.chesssum = self.rowsum * self.colsum
    self.directsum = 6
    self.halfdirectsum = int(self.directsum / 2)
    self.colorsum = 8
    self.chesses = {}
    self.from_grid = (0, 0)
    self.to_grid = (0, 0)
    self.start_position_x = 100
    self.start_position_y = 100
    self.screen_width = 600
    self.screen_height = 600
    self.chess_width = 30
    self.chess_height = 30
    self.chess_bargin = 5
    self.current_state = None
    self.last_time_reward = 0.0
    self.action_list = []
    for x in range(self.rowsum):
      for y in range(self.colsum):
        for a in range(self.halfdirectsum):
          if not self.is_border(x, y, a):
            action_item = (x, y, a)
            self.action_list.append(action_item)
    self.gameInstanceRet = None;
    self.episode_over = False
    self.observation_space = spaces.Box(low=0, high=255, shape=(self.rowsum, self.colsum, self.colorsum))
    self.action_space = spaces.Discrete(len(self.action_list))
    #color dictionary
    yellow = self.get_color(255, 255, 128)
    red = self.get_color(255, 0, 0)
    brown = self.get_color(128, 64, 0)
    green = self.get_color(0, 255, 0)
    blue = self.get_color(0, 0, 255)
    purple = self.get_color(128, 128, 255)
    white = self.get_color(192, 192, 192)
    self.color_dict = {'color(-1)': None, 'color(0)': yellow, 'color(1)': red, 'color(2)': brown, 'color(3)': green, 'color(4)': blue, 'color(5)': purple, 'color(6)': white, 'color(7)': None, 'color(8)': None, 'color(9)': None}
    self.color_num_dict = {'color(-1)': 0, 'color(0)': 1, 'color(1)': 2, 'color(2)': 3, 'color(3)': 4, 'color(4)': 5,
                       'color(5)': 6, 'color(6)': 7, 'color(7)': 0, 'color(8)': 0, 'color(9)': 0}
    self.to_direction_dict1 = {0: (-1, 1), 1: (0, 1), 2: (1, 0), 3: (0, -1), 4: (-1, -1), 5: (-1, 0), 6: (0, 0), 7: (0, 0), 8: (0, 0)}
    self.to_direction_dict2 = {0: (0, 1), 1: (1, 1), 2: (1, 0), 3: (1, -1), 4: (0, -1), 5: (-1, 0), 6: (0, 0), 7: (0, 0), 8: (0, 0)}
    #graphic
    self.viewer = None
    #statics
    self.failure_count = 0
    self.train_count = 0
    # score for one episode
    self.reward_count = 0
    self.reset()

  def _step(self, action):
    self.current_state = self.get_state()
    action_item = self.action_list[action] #turbo

    from_row = action_item[0]
    from_col = action_item[1]
    to_direction = action_item[2]

    item_type = 4
    #delta
    if from_col % 2 == 1:
      delta = self.to_direction_dict2[to_direction]
    else:
      delta = self.to_direction_dict1[to_direction]
    to_row = from_row + delta[0]
    to_col = from_col + delta[1]
    self.from_grid = (from_row, from_col)
    self.to_grid = (to_row, to_col)
    value1 = 0
    value2 = 0
    op = 0


    #print("Take action ", self.train_count, " from:", from_row, from_col, ", to:", to_row, to_col)
    #get the result from that action
    r = int(c_int(self.dll.we6_game_input_by_detail(self.gameInstanceRet, op, item_type, self.from_grid[0], self.from_grid[1], self.to_grid[0], self.to_grid[1], value1, value2)).value)
    #self.dll.we6_check_dead_game()
    is_dead_game = int(c_int(self.dll.we6_is_dead_game()).value)
    #fetch next screen data
    self.fetch_stream_data()

    reward = 0 # - self.last_time_reward
    if r == 0:
      reward = 1
    if reward > 0:
      reward = 1

    self.last_time_reward = r

    self.reward_count = self.reward_count + reward
    self.train_count = self.train_count + 1

    if reward > 0:
      #print("Success after ", self.failure_count, " failures ! \nTrain: ", self.train_count)
      self.failure_count = 0
    else:
      self.failure_count = self.failure_count + 1

    if self.train_count >= 5000 or is_dead_game > 0:
      #print("Reward count for", self.train_count, " train:", self.reward_count)
      self.episode_over = True

    return self.current_state, reward, self.episode_over, {"reward_count": self.reward_count}
  def _reset(self):
    print("\nreset")

    self.episode_over = False
    self.train_count = 0
    self.reward_count = 0
    self.last_time_reward = 0.0

    #data
    self.data_stream = ""

    chessPropertiesTablePath = b"/home/mickie/course/puzzle6/data/LogicData/ChessPropertiesTable.bin"
    stageConfigPath = b"/home/mickie/Downloads/stage_0002_0000.bin"
    commonPath = b"/home/mickie/course/puzzle6/data/DataConfig/"

    self.dll = cdll.LoadLibrary('/home/mickie/Downloads/libwe6remove.so')

    # create game instance
    # release old one first
    if self.gameInstanceRet != None:
      print("release old one first.")
      self.dll.we6_game_delete_ctx(self.gameInstanceRet)

    print("create new game instance.")
    self.gameInstanceRet = self.dll.we6_game_new_ctx('', 0)

    # start the game
    print("start the game")
    self.dll.we6_game_quick_run(self.gameInstanceRet, chessPropertiesTablePath, stageConfigPath, commonPath)
    #self.dll.we6_check_dead_game()
    self.fetch_stream_data()
    state = self.get_state()

    return state

  def _render(self, mode='human', close=False):
    if close:
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
            return


    if self.viewer == None:
      self.viewer = rendering.Viewer(self.screen_width, self.screen_height)
    if self.current_state != None:
      for i in range(len(self.current_state)):
        for j in range(len(self.current_state[i])):
          single_state = self.current_state[i][j]
          #print(single_state)
          chess_position_x = i
          chess_position_y = j
          for k in range(self.colorsum):
            if single_state[k] > 0:
              chess_color_num = k
          chess_color_str = "color(" + str(chess_color_num - 1) + ")"
          #print(chess_position_x, chess_position_y, chess_color_str)
          # color
          chess_color = self.color_dict[chess_color_str]
          if chess_color != None:
            if self.chesses.get(chess_position_x * self.rowsum + chess_position_y) == None:
              # not exists
              pole = self.get_chess(self.chess_width, self.chess_height)
              self.chesses[chess_position_x * self.rowsum + chess_position_y] = pole
            else:
              # exists
              pole = self.chesses[chess_position_x * self.rowsum + chess_position_y]
            pole.set_color(chess_color[0], chess_color[1], chess_color[2])
            position = self.grid2position(chess_position_x, chess_position_y)
            x = position[0]
            y = position[1]
            pole.trans.set_translation(x, y)
            pole.color_num = chess_color_num
    from_position = self.grid2position(self.from_grid[0], self.from_grid[1])
    to_position = self.grid2position(self.to_grid[0], self.to_grid[1])
    self.viewer.draw_line(from_position, to_position)

    if self.viewer != None:
      return self.viewer.render(return_rgb_array=mode == 'rgb_array')
