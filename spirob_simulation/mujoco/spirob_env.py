import numpy as np
import mujoco
import gymnasium as gym
from gymnasium import spaces
import os
import yaml

class SpiRobEnv(gym.Env):
    """
    MuJoCo environment for the 3-cable SpiRob robot.
    """
    
    def __init__(self, config_path='config.yaml'):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Set up the simulation
        model_path = os.path.join(os.path.dirname(__file__), 'models', 'spirob.xml')
        self.model = mujoco.MjModel.from_xml_path(model_path)
        self.data = mujoco.MjData(self.model)
        
        # Define action and observation spaces
        # Action: Change in cable lengths (3 values, one for each motor)
        self.action_space = spaces.Box(
            low=np.array([-0.01, -0.01, -0.01]),  # Min change in cable length
            high=np.array([0.01, 0.01, 0.01]),    # Max change in cable length
            dtype=np.float32
        )
        
        # Observation: Cable lengths, end effector position/orientation, target object position
        # [cable1_len, cable2_len, cable3_len, 
        #  ee_pos_x, ee_pos_y, ee_pos_z, ee_quat_w, ee_quat_x, ee_quat_y, ee_quat_z,
        #  obj_pos_x, obj_pos_y, obj_pos_z]
        self.observation_space = spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(13,),
            dtype=np.float32
        )
        
        # Task parameters
        self.max_episode_steps = self.config.get('max_episode_steps', 500)
        self.current_step = 0
        
        # For tracking the object being manipulated
        self.target_position = np.array([0.0, 0.0, 0.1])  # Default target position
        
    def step(self, action):
        """Execute action and return next state, reward, done, and info."""
        self.current_step += 1
        
        # Apply action (change in cable lengths)
        for i in range(3):
            # Get current cable length from sensor
            current_length = self.data.sensor(f"cable{i+1}_length").data[0]
            # Apply change (clipped to valid range)
            target_length = np.clip(
                current_length + action[i],
                self.model.tendon(f"cable{i+1}").range[0],  # Min length
                self.model.tendon(f"cable{i+1}").range[1]   # Max length
            )
            # Set actuator control
            self.data.ctrl[i] = target_length
        
        # Step the simulation
        for _ in range(self.config.get('substeps', 10)):
            mujoco.mj_step(self.model, self.data)
        
        # Get observation
        obs = self._get_obs()
        
        # Calculate reward
        reward = self._compute_reward(obs)
        
        # Check if episode is done
        done = self._is_done(obs)
        
        # Additional info
        info = {
            'is_success': self._is_success(obs),
            'cable_tensions': np.array([
                self.data.sensor("cable1_force").data[0],
                self.data.sensor("cable2_force").data[0],
                self.data.sensor("cable3_force").data[0]
            ])
        }
        
        return obs, reward, done, info
    
    def reset(self):
        """Reset the environment to initial state."""
        self.current_step = 0
        
        # Reset simulation
        mujoco.mj_resetData(self.model, self.data)
        
        # Randomize object position (if enabled)
        if self.config.get('randomize_object', True):
            obj_pos = np.random.uniform(
                low=np.array([-0.1, -0.1, 0.02]),
                high=np.array([0.1, 0.1, 0.1])
            )
            obj_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "target_object")
            self.data.qpos[obj_body_id*7:obj_body_id*7+3] = obj_pos
            
            # Update target position
            self.target_position = obj_pos.copy()
        
        # Initialize end effector position
        ee_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "end_effector")
        self.data.qpos[ee_body_id*7:ee_body_id*7+3] = np.array([0.0, 0.0, 0.15])  # Initial position
        
        # Step simulation a few times to stabilize
        for _ in range(100):
            mujoco.mj_step(self.model, self.data)
        
        return self._get_obs()
    
    def _get_obs(self):
        """Get the current observation state."""
        # Cable lengths
        cable_lengths = np.array([
            self.data.sensor("cable1_length").data[0],
            self.data.sensor("cable2_length").data[0],
            self.data.sensor("cable3_length").data[0]
        ])
        
        # End effector position and orientation
        ee_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "end_effector")
        ee_pos = self.data.qpos[ee_body_id*7:ee_body_id*7+3]
        ee_quat = self.data.qpos[ee_body_id*7+3:ee_body_id*7+7]
        
        # Object position
        obj_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "target_object")
        obj_pos = self.data.qpos[obj_body_id*7:obj_body_id*7+3]
        
        # Combine all observations
        obs = np.concatenate([cable_lengths, ee_pos, ee_quat, obj_pos])
        return obs
    
    def _compute_reward(self, obs):
        """Compute the reward based on current state."""
        # Extract relevant parts of the observation
        ee_pos = obs[3:6]
        obj_pos = obs[10:13]
        
        # Distance between end effector and object
        distance = np.linalg.norm(ee_pos - obj_pos)
        
        # Base reward is negative distance (closer is better)
        distance_reward = -distance * self.config.get('distance_reward_scale', 10.0)
        
        # Check if object is grasped (end effector close to object)
        grasped = distance < self.config.get('grasp_threshold', 0.03)
        grasp_reward = self.config.get('grasp_reward', 10.0) if grasped else 0.0
        
        # Check if object is lifted (if grasped)
        lifted = grasped and obj_pos[2] > self.config.get('lift_height', 0.08)
        lift_reward = self.config.get('lift_reward', 50.0) if lifted else 0.0
        
        # Penalty for excessive cable tension
        cable_tensions = np.array([
            self.data.sensor("cable1_force").data[0],
            self.data.sensor("cable2_force").data[0],
            self.data.sensor("cable3_force").data[0]
        ])
        max_tension = self.config.get('max_tension', 40.0)
        tension_penalty = sum(max(0, tension - max_tension) for tension in cable_tensions) * \
                          self.config.get('tension_penalty', 0.1)
        
        # Time penalty to encourage efficiency
        time_penalty = self.config.get('time_penalty', 0.1)
        
        # Total reward
        reward = distance_reward + grasp_reward + lift_reward - tension_penalty - time_penalty
        
        return reward
    
    def _is_success(self, obs):
        """Check if the task is successful."""
        # Extract object position
        obj_pos = obs[10:13]
        ee_pos = obs[3:6]
        
        # Check if end effector is close to object (grasped)
        distance = np.linalg.norm(ee_pos - obj_pos)
        grasped = distance < self.config.get('grasp_threshold', 0.03)
        
        # Success if object is grasped and lifted above threshold
        return grasped and obj_pos[2] > self.config.get('lift_height', 0.08)
    
    def _is_done(self, obs):
        """Check if episode is done."""
        # Done if max steps reached or success
        return self.current_step >= self.max_episode_steps or self._is_success(obs)
    
    def render(self, mode='human'):
        """Render the environment."""
        # Note: This is a placeholder. For proper rendering, 
        # you'll need to set up mujoco_py viewer or custom visualization
        pass
    
    def close(self):
        """Cleanup resources."""
        pass