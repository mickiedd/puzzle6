import numpy as np
import gym

from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten, Convolution2D, Permute, Reshape
from keras.layers import Dropout, MaxPooling2D
from keras.optimizers import Adam
import keras.backend as K

from rl.agents.dqn import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory
from rl.policy import LinearAnnealedPolicy, BoltzmannQPolicy, EpsGreedyQPolicy

from rl.core import Processor
from puzzle6.envs import puzzle6_env

class Puzzle6Processor(Processor):
    def process_observation(self, observation):
        processed_observation = np.array(observation)
        return processed_observation.astype('uint8')  # saves storage in experience memory

    def process_state_batch(self, batch):
        return batch

    def process_reward(self, reward):
        return reward

ENV_NAME = 'puzzle6-v0'


# Get the environment and extract the number of actions.
env = gym.make(ENV_NAME)
np.random.seed(123)
env.seed(123)
nb_actions = env.action_space.n
input_shape = env.observation_space.shape
print("nb_actions:", nb_actions)

# Next, we build a very simple model.
model = Sequential()
filter = 512
model.add(Reshape(input_shape, input_shape=(1,) + input_shape))
model.add(Convolution2D(input_shape=input_shape, kernel_size=(3,3), filters=filter, padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(2, 2))
model.add(Convolution2D(input_shape=(None, 4, 4, filter), kernel_size=(3,3), filters=filter, padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(2, 2))
model.add(Convolution2D(input_shape=(None, 2, 2, filter), kernel_size=(3,3), filters=filter, padding='same'))
model.add(Activation('relu'))
model.add(MaxPooling2D(2, 2))
model.add(Flatten())
model.add(Dense(256))
model.add(Activation('relu'))
model.add(Dropout(0.5))
model.add(Dense(nb_actions))
model.add(Activation('softmax'))
print(model.summary())

# Finally, we configure and compile our agent. You can use every built-in Keras optimizer and
# even the metrics!
memory = SequentialMemory(limit=1000, window_length=1)
#policy = LinearAnnealedPolicy(EpsGreedyQPolicy(), attr='eps', value_max=1., value_min=.1, value_test=.05, nb_steps=1000000)
policy = BoltzmannQPolicy()
dqn = DQNAgent(model=model, nb_actions=nb_actions, memory=memory, nb_steps_warmup=1000,
               target_model_update=1e-5, policy=policy, processor=Puzzle6Processor())
dqn.compile(Adam(lr=1e-5), metrics=['mae'])

# Okay, now it's time to learn something! We visualize the training here for show, but this
# slows down training quite a lot. You can always safely abort the training prematurely using
# Ctrl + C.
dqn.fit(env, nb_steps=80000000, visualize=False, verbose=2)

# After training is done, we save the final weights.
dqn.save_weights('dqn_{}_weights.h5f'.format(ENV_NAME), overwrite=True)

# Finally, evaluate our algorithm for 5 episodes.
dqn.test(env, nb_episodes=5000, visualize=True)
