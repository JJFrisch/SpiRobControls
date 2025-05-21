import mujoco
import numpy as np
import gymnasium as gym
from gymnasium import spaces
import os
import time

class SpiRobEnv(gym.Env):
    """
    SpiRob 3-cable robot environment for object manipulation tasks.
    This environment simulates a cable-driven parallel robot with 3 cables.
    """
    
    def __init__(self, task="pick", render_mode=None):
        super().__init__()
        
        # Load the model from XML
        self.model_path = "spirob_3cable.xml"  # Update this path as needed
        self.model = mujoco.MjModel.from_xml_path(self.model_path)
        self.data = mujoco.MjData(self.model)
        
        # Set up rendering
        self.render_mode = render_mode
        if self.render_mode == "human":
            self.viewer = mujoco.Renderer(self.model)
        
        # Task selection (pick or catch)
        self.task = task
        
        # Define action space: control signals for the 3 motors
        # Actions control the velocity of each motor (-1 to 1 normalized)
        self.action_space = spaces.Box(
            low=-1.0, high=1.0, shape=(3,), dtype=np.float32
        )
        
        # Define observation space
        # [ee_pos (3), ee_vel(3), cable_lengths(3), cable_velocities(3), target_pos(3), target_vel(3)]
        self.observation_space = spaces.Box(
            low=-np.inf, high=np.inf, shape=(18,), dtype=np.float32
        )
        
        # Workspace limits
        self.workspace_bounds = {
            "x": (-0.4, 0.4),
            "y": (-0.4, 0.4),
            "z": (0.1, 1.2)
        }
        
        # Reset the environment
        self.reset()
    
    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        
        # Reset MuJoCo simulation
        mujoco.mj_resetData(self.model, self.data)
        
        # Initialize end effector at a stable position
        ee_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "end_effector")
        self.data.qpos[0:3] = np.array([0.0, 0.0, 0.8])  # x, y, z position
        self.data.qpos[3:7] = np.array([1.0, 0.0, 0.0, 0.0])  # quaternion orientation
        
        # Randomize target object position for pick task
        target_body_id = mujoco.mj_name2id(self.model, mujoco.mjtObj.mjOBJ_BODY, "target")
        if self.task == "pick":
            # Place the object on the ground with random x,y position
            x = self.np_random.uniform(-0.3, 0.3)
            y = self.np_random.uniform(-0.3, 0.3)
            self.data.qpos[7:10] = np.array([x, y, 0.03])  # x, y, z position (slightly above ground)
            self.data.qpos[10:14] = np.array([1.0, 0.0, 0.0, 0.0])  # quaternion orientation
        elif self.task == "catch":
            # For catch task, we'll spawn the object in the air with a velocity
            x = self.np_random.uniform(-0.5, 0.5)
            y = self.np_random.uniform(-0.5, 0.5)
            z = self.np_random.uniform(0.8, 1.2)
            self.data.qpos[7:10] = np.array([x, y, z])
            self.data.qvel[6:9] = np.array([
                self.np_random.uniform(-0.5, 0.5),
                self.np_random.uniform(-0.5, 0.5),
                self.np_random.uniform(-1.5, -0.5)  # Falling downward
            ])
        
        # Run a few steps to stabilize the simulation
        for _ in range(100):
            mujoco.mj_step(self.model, self.data)
        
        # Get observation
        observation = self._get_obs()
        info = self._get_info()
        
        return observation, info
    
    def step(self, action):
        # Set control signals to motors based on action
        self.data.ctrl[:] = action
        
        # Step the simulation
        for _ in range(5):  # Multiple steps for stability
            mujoco.mj_step(self.model, self.data)
        
        # Get observation, reward and check if done
        observation = self._get_obs()
        reward = self._compute_reward()
        terminated = self._is_terminated()
        truncated = False  # Could be based on step count
        info = self._get_info()
        
        return observation, reward, terminated, truncated, info
    
    def _get_obs(self):
        """Get the current observation state."""
        ee_pos = self.data.qpos[0:3].copy()  # End-effector position
        ee_vel = self.data.qvel[0:3].copy()  # End-effector velocity
        
        # Cable lengths and velocities
        cable_lengths = np.array([
            self.data.sensordata[0],
            self.data.sensordata[1],
            self.data.sensordata[2]
        ])
        
        cable_velocities = np.array([
            self.data.sensordata[3],
            self.data.sensordata[4],
            self.data.sensordata[5]
        ])
        
        # Target object position and velocity
        target_pos = self.data.qpos[7:10].copy()
        target_vel = self.data.qvel[6:9].copy()
        
        # Concatenate all observations
        obs = np.concatenate([
            ee_pos, ee_vel, 
            cable_lengths, cable_velocities,
            target_pos, target_vel
        ])
        
        return obs
    
    def _compute_reward(self):
        """Compute the reward based on the task."""
        ee_pos = self.data.qpos[0:3]
        target_pos = self.data.qpos[7:10]
        
        # Distance between end-effector and target
        distance = np.linalg.norm(ee_pos - target_pos)
        
        # Base reward is negative distance (closer is better)
        reward = -distance
        
        # Check if the object is picked/caught
        if distance < 0.08:  # If end-effector is close to the object
            reward += 10.0  # Bonus for being close
            
            # Additional bonus if the object is lifted (for pick task)
            if self.task == "pick" and target_pos[2] > 0.1:
                reward += 20.0 * target_pos[2]  # Reward proportional to height
        
        # Penalize if end-effector is outside the valid workspace
        if not self._is_in_workspace(ee_pos):
            reward -= 5.0
        
        return reward
    
    def _is_terminated(self):
        """Check if the episode should terminate."""
        ee_pos = self.data.qpos[0:3]
        target_pos = self.data.qpos[7:10]
        
        # Success condition: object lifted to a certain height (for pick task)
        if self.task == "pick" and target_pos[2] > 0.3:
            return True
        
        # Success condition for catch task: caught the object before it hits the ground
        if self.task == "catch":
            distance = np.linalg.norm(ee_pos - target_pos)
            if distance < 0.08 and target_pos[2] > 0.1:
                return True
            # Failed catch (object hit the ground)
            if target_pos[2] < 0.03:
                return True
        
        # Terminate if outside workspace
        if not self._is_in_workspace(ee_pos):
            return True
        
        return False
    
    def _is_in_workspace(self, position):
        """Check if a position is within the valid workspace."""
        x, y, z = position
        bounds = self.workspace_bounds
        
        return (bounds["x"][0] <= x <= bounds["x"][1] and
                bounds["y"][0] <= y <= bounds["y"][1] and
                bounds["z"][0] <= z <= bounds["z"][1])
    
    def _get_info(self):
        """Return additional information for debugging."""
        ee_pos = self.data.qpos[0:3]
        target_pos = self.data.qpos[7:10]
        distance = np.linalg.norm(ee_pos - target_pos)
        
        return {
            "distance": distance,
            "target_height": target_pos[2],
            "ee_position": ee_pos
        }
    
    def render(self):
        """Render the environment."""
        if self.render_mode == "human":
            # Update camera
            self.viewer.update_scene(self.data)
            img = self.viewer.render()
            return img
        return None
    
    def close(self):
        """Clean up resources."""
        pass

# Example usage
if __name__ == "__main__":
    env = SpiRobEnv(task="pick", render_mode="human")
    obs, info = env.reset()
    
    for _ in range(1000):
        action = env.action_space.sample()  # Random action
        obs, reward, terminated, truncated, info = env.step(action)
        env.render()
        
        if terminated or truncated:
            obs, info = env.reset()
    
    env.close()