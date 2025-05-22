# spirob_motor_control.py - Motor control specifics for 28BYJ-48 steppers

class SpiRobMotorConfig:
    """Configuration for 28BYJ-48 stepper motors."""
    
    # Motor specifications
    STEPS_PER_REVOLUTION = 2048  # 28BYJ-48 with gear reduction
    MAX_SPEED_RPM = 15          # Maximum speed in RPM
    HOLDING_TORQUE = 0.34       # Holding torque in Nm
    
    # Spool specifications  
    SPOOL_RADIUS = 12.5      # 15mm radius in meters
    CABLE_DIAMETER = 0.5      # 1mm cable diameter
    
    # Derived parameters
    MAX_ANGULAR_VELOCITY = (MAX_SPEED_RPM * 2 * 3.14159) / 60  # rad/s
    CABLE_LENGTH_PER_REV = 2 * 3.14159 * SPOOL_RADIUS          # meters
    CABLE_SPEED_PER_RPM = CABLE_LENGTH_PER_REV * (MAX_SPEED_RPM / 60)  # m/s

# Updated environment configuration for motors
@configclass
class SpiRobEnvCfg(ManagerBasedRLEnvCfg):
    """Updated configuration with proper motor control."""
    
    # ... (previous configuration)
    
    # SpiRob with detailed motor configuration
    spirob: ArticulationCfg = ArticulationCfg(
        prim_path="{ENV_REGEX_NS}/SpiRob",
        spawn=sim_utils.UsdFileCfg(
            usd_path="spirob_complete.usd",
            rigid_props=sim_utils.RigidBodyPropertiesCfg(
                disable_gravity=False,
                linear_damping=0.02,     # Small air resistance
                angular_damping=0.05,    # Rotational damping
                max_linear_velocity=10.0,
                max_angular_velocity=100.0,
            ),
            articulation_props=sim_utils.ArticulationRootPropertiesCfg(
                enabled_self_collisions=False,  # Disable for performance
                solver_position_iteration_count=8,
                solver_velocity_iteration_count=4,
            ),
        ),
        init_state=ArticulationCfg.InitialStateCfg(
            pos=(0.0, 0.0, 0.5),
            joint_pos={
                "LeftMotorJoint": 0.0,   # Initial spool positions
                "RightMotorJoint": 0.0,
            },
            joint_vel={
                ".*": 0.0,
            },
        ),
        actuators={
            # Stepper motor actuators
            "left_motor": sim_utils.DCMotorCfg(
                joint_names_expr=["LeftMotorJoint"],
                effort_limit=SpiRobMotorConfig.HOLDING_TORQUE,
                velocity_limit=SpiRobMotorConfig.MAX_ANGULAR_VELOCITY,
                stiffness=0.0,      # Pure velocity control
                damping=0.05,       # Small damping
                armature=0.001,     # Motor inertia
            ),
            "right_motor": sim_utils.DCMotorCfg(
                joint_names_expr=["RightMotorJoint"], 
                effort_limit=SpiRobMotorConfig.HOLDING_TORQUE,
                velocity_limit=SpiRobMotorConfig.MAX_ANGULAR_VELOCITY,
                stiffness=0.0,
                damping=0.05,
                armature=0.001,
            ),
        },
    )