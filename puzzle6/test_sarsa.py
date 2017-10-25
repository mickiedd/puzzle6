import numpy as np
import gym

from PIL import Image
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, Convolution2D, Permute
from keras.layers import Dropout, MaxPooling2D
from keras.optimizers import Adam

import keras.backend as K
from rl.core import Processor

from rl.agents import SARSAAgent
from rl.policy import BoltzmannQPolicy

from puzzle6.envs import puzzle6_env

class AtariProcessor(Processor):
    def process_observation(self, observation):
        assert observation.ndim == 3  # (height, width, channel)
        img = Image.fromarray(observation)
        img = img.resize(INPUT_SHAPE).convert('L')  # resize and convert to grayscale
        processed_observation = np.array(img)
        assert processed_observation.shape == INPUT_SHAPE
        return processed_observation.astype('uint8')  # saves storage in experience memory

    def process_state_batch(self, batch):
        # We could perform this processing step in `process_observation`. In this case, however,
        # we would need to store a `float32` array instead, which is 4x more memory intensive than
        # an `uint8` array. This matters if we store 1M observations.
        processed_batch = batch.astype('float32') / 255.
        return processed_batch

    def process_reward(self, reward):
        return np.clip(reward, -1.0, 1.0)

ENV_NAME = 'puzzle6-v0'

# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n
INPUT_SHAPE = (env.observation_space.shape[0],env.observation_space.shape[1])
WINDOW_LENGTH = 1

# Next, we build a very simple model.
input_shape = (WINDOW_LENGTH,) + INPUT_SHAPE
model = Sequential()
if K.image_dim_ordering() == 'tf':
    # (width, height, channels)
    model.add(Permute((2, 3, 1), input_shape=input_shape))
elif K.image_dim_ordering() == 'th':
    # (channels, width, height)
    model.add(Permute((1, 2, 3), input_shape=input_shape))
else:
    raise RuntimeError('Unknown image_dim_ordering.')
model.add(Convolution2D(input_shape=input_shape, kernel_size=(3,3), filters=32, padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(2, 2))
model.add(Convolution2D(input_shape=(None, 4, 4, 32), kernel_size=(3,3), filters=32, padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(2, 2))
model.add(Convolution2D(input_shape=(None, 2, 2, 32), kernel_size=(3,3), filters=32, padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(2, 2))
model.add(Flatten())
model.add(Dense(512))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_actions))
model.add(Activation('softmax'))
print(model.summary())

# SARSA does not require a memory.
policy = BoltzmannQPolicy()
processor = AtariProcessor()
sarsa = SARSAAgent(model=model, nb_actions=nb_actions, nb_steps_warmup=10, policy=policy, processor=processor, train_interval=4)
sarsa.compile(Adam(lr=1e-5), metrics=['mae'])

# Okay, now it's time to learn something! We visualize the training here for show, but this
# slows down training quite a lot. You can always safely abort the training prematurely using
# Ctrl + C.
sarsa.fit(env, nb_steps=50000000, visualize=False, verbose=2)

# After training is done, we save the final weights.
sarsa.save_weights('sarsa_{}_weights.h5f'.format(ENV_NAME), overwrite=True)

# Finally, evaluate our algorithm for 5 episodes.
sarsa.test(env, nb_episodes=5, visualize=True)
