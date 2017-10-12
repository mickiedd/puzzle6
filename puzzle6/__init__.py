from gym.envs.registration import register

register(
    id='puzzle6-v0',
    entry_point='puzzle6.envs:Puzzle6Env',
)
register(
    id='puzzle6-extrahard-v0',
    entry_point='puzzle6.envs:Puzzle6ExtraHardEnv',
)
