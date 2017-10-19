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

    self.rowsum = 3
    self.colsum = 3
    self.chesssum = self.rowsum * self.colsum
    self.directsum = 6
    self.halfdirectsum = int(self.directsum / 1)
    self.colorsum = 5

    #action id to real actions(x, y, position)
    action_count = self.rowsum * self.colsum * self.halfdirectsum
    self.action_list = []
    for x in range(self.rowsum):
      for y in range(self.colsum):
        for a in range(self.halfdirectsum):
          action_item = (x, y, a)
          self.action_list.append(action_item)
    #len self.action_list 243

    self.gameInstanceRet = None;
    self.episode_over = False
    high = np.zeros(self.chesssum) + 1.0
    self.observation_space = spaces.Box(np.zeros(self.chesssum), high)
    #self.observation_space = np.zeros(81)
    self.action_space = spaces.Discrete(len(self.action_list))


    #color dictionary
    yellow = self.get_color(255, 255, 128)
    red = self.get_color(255, 0, 0)
    brown = self.get_color(128, 64, 0)
    green = self.get_color(0, 255, 0)
    blue = self.get_color(0, 0, 255)
    purple = self.get_color(128, 128, 255)
    white = self.get_color(192, 192, 192)
    self.color_dict = {'color(0)': yellow, 'color(1)': red, 'color(2)': brown, 'color(3)': green, 'color(4)': blue, 'color(5)': purple, 'color(6)': white, 'color(7)': None, 'color(8)': None, 'color(9)': None}
    self.color_num_dict = {'color(0)': 1, 'color(1)': 2, 'color(2)': 3, 'color(3)': 4, 'color(4)': 5,
                       'color(5)': 6, 'color(6)': 7, 'color(7)': 0, 'color(8)': 0, 'color(9)': 0}
    self.to_direction_dict = {0: (-1,1), 1: (0,1), 2: (1,0), 3: (-1,0), 4: (0,-1), 5: (-1,-1), 6: (0,0), 7: (0,0), 8: (0,0)}
    #graphic
    self.viewer = None

    #statics
    self.failure_count = 0
    self.train_count = 0


    self.reset()

  def _step(self, action):
    print("step", action)
    action_item = self.action_list[action] #turbo

    from_row = action_item[0]
    from_col = action_item[1]
    to_direction = action_item[2]

    item_type = 4
    #delta
    delta = self.to_direction_dict[to_direction]
    #print("from_row:", from_row, ", from_col:", from_col, " to_direction:", to_direction, " delta:", delta)
    to_row = from_row + delta[0]
    to_col = from_col + delta[1]
    value1 = 0
    value2 = 0
    op = 0
    #print("Take action ", self.train_count, " from:", from_row, from_col, ", to:", to_row, to_col)
    #get the result from that action
    r = int(c_int(self.dll.we6_game_input_by_detail(self.gameInstanceRet, op, item_type, from_row, from_col, to_row, to_col, value1, value2)).value)

    len3 = c_int()
    self.data_stream = str(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)

    #print(self.data_stream)
    #print(len3)



    ob = self.get_state()

    #print(ob)
    reward = 0
    if r == 0:
      reward = 1
    else:
      reward = -10000

    if reward > 0:
      print("Success after ", self.failure_count, " failures ! \nTrain: ", self.train_count)
      self.failure_count = 0
    else:
      self.failure_count = self.failure_count + 1

    if self.failure_count > 100:
      self.episode_over = True

    self.train_count = self.train_count + 1

    #print("action:", action, "reward:", reward)
    return ob, reward, self.episode_over, {}
  def _reset(self):
    print("reset")

    self.episode_over = False
    self.train_count = 0

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
    len3 = c_int()
    print("get nodes data")
    self.data_stream = str(c_char_p(self.dll.we6_board_nodes_data(self.gameInstanceRet, byref(len3))).value)
    state = self.get_state()
    print("Original:")
    print(state)
    print(len3)
    print("=========")

    return state
  def get_chess(self, w, h):
    l,r,t,b = -w/2, w/2, h/2, -h/2
    pole = rendering.FilledPolygon([(l,b), (l,t), (r,t), (r,b)])
    axleoffset = h/4.0
    pole.trans = rendering.Transform(translation=(0, axleoffset))
    pole.add_attr(pole.trans)
    self.viewer.add_geom(pole)
    return pole

  def get_state(self):
    ob = np.zeros(self.chesssum)

    max_color_num = 0
    if self.data_stream != '':
      stream_list = self.data_stream.replace("b'", "").split(',')
      for current_data_stream in stream_list:  # 0|0|color(9)
        # current data
        if current_data_stream != "'":
          # print(current_data_stream)
          current_data_stream_list = current_data_stream.split('|')
          chess_position_x = int(current_data_stream_list[1])
          chess_position_y = int(current_data_stream_list[0])
          if chess_position_x >= self.colsum:
            continue
          if chess_position_y >= self.rowsum:
            continue
          chess_color_str = current_data_stream_list[2]
          # color
          chess_color_num = self.color_num_dict[chess_color_str]
          index = chess_position_x * self.rowsum + chess_position_y
          #print("index:", index, ",chess_position_x:", chess_position_x, ",chess_position_y", chess_position_y)
          ob[index] = chess_color_num
          # print(index, chess_color_str, ob[index])
          if chess_color_num > max_color_num:
            max_color_num = chess_color_num
    ob = ob / max_color_num
    return ob

  def _render(self, mode='human', close=False):
    print("render")
    if close:
        if self.viewer is not None:
            self.viewer.close()
            self.viewer = None
            return
    print(1)
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
    print(len(self.data_stream))
    if self.data_stream != '':
      stream_list = self.data_stream.replace("b'", "").split(',')
      if self.viewer == None:
          self.viewer = rendering.Viewer(screen_width, screen_height)
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
          chess_color_num = self.color_num_dict[chess_color_str]
          #print(chess_color)
          if chess_color != None:
            if chesses.get(chess_position_x * self.rowsum + chess_position_y) == None:
              #not exists
              pole = self.get_chess(30, 30)
              chesses[chess_position_x * self.rowsum + chess_position_y] = pole
            else:
              #exists
              pole = chesses[chess_position_x * self.rowsum + chess_position_y]
            pole.set_color(chess_color[0], chess_color[1], chess_color[2])
            x = start_position_x + (chess_width + chess_bargin) * chess_position_x
            y = screen_height - (start_position_y + chess_position_x % 2 * 15 + (chess_height + chess_bargin) * chess_position_y)
            pole.trans.set_translation(x, y)
            pole.color_num = chess_color_num

    if self.viewer != None:
      return self.viewer.render(return_rgb_array=mode == 'rgb_array')
