# create_spirob_usd.py - Complete system assembly
import omni
from pxr import UsdGeom, Usd, UsdPhysics, UsdShade, Sdf, Gf, UsdUtils
import omni.usd
import omni.kit.commands
import numpy as np

class SpiRobUSDCreator:
    def __init__(self):
        self.stage = omni.usd.get_context().new_stage()
        self.setup_scene()
        
    def setup_scene(self):
        """Initialize the USD stage with physics scene."""
        # Set up axis and units
        UsdGeom.SetStageUpAxis(self.stage, UsdGeom.Tokens.z)
        UsdGeom.SetStageMetersPerUnit(self.stage, 1.0)
        
        # Create physics scene
        scene = UsdPhysics.Scene.Define(self.stage, "/physicsScene")
        scene.CreateGravityDirectionAttr().Set(Gf.Vec3f(0.0, 0.0, -1.0))
        scene.CreateGravityMagnitudeAttr().Set(9.81)
        
        # Physics solver settings
        scene.CreateEnableSceneQuerySupportAttr().Set(True)
        
    def create_spirob_assembly(self):
        """Create the complete SpiRob assembly."""
        
        # Root assembly
        spirob_root = UsdGeom.Xform.Define(self.stage, "/SpiRob")
        
        # Create components
        self.create_base_frame()
        self.create_motor_assemblies()
        self.create_spirob_body()
        self.create_cables()
        self.setup_joints()
        self.create_materials()
        
        print("SpiRob assembly created successfully!")
        
    def create_base_frame(self):
        """Create the fixed base structure."""
        base_prim = self.import_stl_as_rigid_body(
            stl_path="cleaned_base_frame.stl",
            prim_path="/SpiRob/BaseFrame",
            position=(0, 0, 0),
            is_kinematic=True,  # Fixed to world
            mass=10.0
        )
        
    def create_motor_assemblies(self):
        """Create left and right motor assemblies with spools."""
        
        # Motor mount positions (adjust based on your design)
        motor_positions = {
            "left": (-0.4, 0, 0.8),   # Left motor position  
            "right": (0.4, 0, 0.8)    # Right motor position
        }
        
        for side in ["left", "right"]:
            # Motor mount (fixed)
            mount_prim = self.import_stl_as_rigid_body(
                stl_path=f"cleaned_{side}_motor_mount.stl",
                prim_path=f"/SpiRob/{side.title()}MotorMount",
                position=motor_positions[side],
                is_kinematic=True,
                mass=1.0
            )
            
            # Spool (rotates with motor)
            spool_prim = self.import_stl_as_rigid_body(
                stl_path=f"cleaned_{side}_spool.stl", 
                prim_path=f"/SpiRob/{side.title()}Spool",
                position=motor_positions[side],
                is_kinematic=False,  # Will be controlled by joint
                mass=0.1
            )
            
    def create_spirob_body(self):
        """Create the main SpiRob body (the suspended part)."""
        
        # Starting position (center, suspended)
        start_pos = (0, 0, 0.3)
        
        spirob_prim = self.import_stl_as_rigid_body(
            stl_path="cleaned_spirob_body.stl",
            prim_path="/SpiRob/SpiRobBody", 
            position=start_pos,
            is_kinematic=False,
            mass=0.050  # 50g as specified
        )
        
        # Add contact sensor for collision detection
        self.add_contact_sensor("/SpiRob/SpiRobBody")
        
    def import_stl_as_rigid_body(self, stl_path, prim_path, position, is_kinematic=False, mass=1.0):
        """Import STL and set up as rigid body with physics."""
        
        # Import STL mesh
        success = omni.kit.commands.execute(
            "CreateMeshFromFile",
            mesh_path=stl_path,
            prim_path=prim_path
        )
        
        if not success:
            print(f"Failed to import {stl_path}")
            return None
            
        # Get the prim
        prim = self.stage.GetPrimAtPath(prim_path)
        
        # Set position
        xform = UsdGeom.Xformable(prim)
        xform.AddTranslateOp().Set(Gf.Vec3d(*position))
        
        # Add rigid body physics
        rigid_body_api = UsdPhysics.RigidBodyAPI.Apply(prim)
        
        if is_kinematic:
            rigid_body_api.CreateKinematicEnabledAttr(True)
        
        # Set mass properties
        mass_api = UsdPhysics.MassAPI.Apply(prim)
        mass_api.CreateMassAttr(mass)
        
        # Add collision
        collision_api = UsdPhysics.CollisionAPI.Apply(prim)
        
        return prim
        
    def create_cables(self):
        """Create cable simulation using deformable bodies or constraints."""
        
        # For Isaac Lab, we'll use distance joints to simulate cables
        # More advanced: Use FEM deformable bodies
        
        cable_length = 0.6  # Initial cable length (meters)
        
        # Left cable constraint
        left_cable = self.create_cable_constraint(
            name="LeftCable",
            body1_path="/SpiRob/LeftSpool",
            body2_path="/SpiRob/SpiRobBody", 
            attachment1=(0, 0, -0.05),  # Bottom of spool
            attachment2=(-0.02, 0, 0.05),  # Left side of spirob body
            rest_length=cable_length
        )
        
        # Right cable constraint  
        right_cable = self.create_cable_constraint(
            name="RightCable",
            body1_path="/SpiRob/RightSpool",
            body2_path="/SpiRob/SpiRobBody",
            attachment1=(0, 0, -0.05),  # Bottom of spool
            attachment2=(0.02, 0, 0.05),  # Right side of spirob body
            rest_length=cable_length
        )
        
    def create_cable_constraint(self, name, body1_path, body2_path, attachment1, attachment2, rest_length):
        """Create a distance joint to simulate cable behavior."""
        
        # Create distance joint
        joint_path = f"/SpiRob/{name}Joint"
        distance_joint = UsdPhysics.DistanceJoint.Define(self.stage, joint_path)
        
        # Set joint properties
        distance_joint.CreateBody0Rel().SetTargets([body1_path])
        distance_joint.CreateBody1Rel().SetTargets([body2_path])
        
        # Local attachment points
        distance_joint.CreateLocalPos0Attr().Set(Gf.Vec3f(*attachment1))
        distance_joint.CreateLocalPos1Attr().Set(Gf.Vec3f(*attachment2))
        
        # Distance constraint
        distance_joint.CreateRestLengthAttr().Set(rest_length)
        distance_joint.CreateMinDistanceAttr().Set(0.1)  # Minimum cable length
        distance_joint.CreateMaxDistanceAttr().Set(2.0)  # Maximum cable length
        
        # Stiffness and damping
        distance_joint.CreateStiffnessAttr().Set(10000.0)  # High stiffness for cable
        distance_joint.CreateDampingAttr().Set(100.0)     # Some damping
        
        return distance_joint
        
    def setup_joints(self):
        """Create revolute joints for motor control."""
        
        for side in ["Left", "Right"]:
            # Create revolute joint for spool rotation
            joint_path = f"/SpiRob/{side}MotorJoint"
            revolute_joint = UsdPhysics.RevoluteJoint.Define(self.stage, joint_path)
            
            # Connect spool to motor mount
            revolute_joint.CreateBody0Rel().SetTargets([f"/SpiRob/{side}MotorMount"])
            revolute_joint.CreateBody1Rel().SetTargets([f"/SpiRob/{side}Spool"])
            
            # Joint axis (Z-axis rotation)
            revolute_joint.CreateAxisAttr().Set("Z")
            
            # Joint limits (unlimited rotation)
            revolute_joint.CreateLowerLimitAttr().Set(-1000000)  # Many rotations
            revolute_joint.CreateUpperLimitAttr().Set(1000000)
            
            # Motor drive properties
            drive_api = UsdPhysics.DriveAPI.Apply(revolute_joint.GetPrim(), "angular")
            drive_api.CreateTypeAttr().Set("force")  # Velocity control
            drive_api.CreateMaxForceAttr().Set(10.0)  # Max motor torque (Nm)
            drive_api.CreateStiffnessAttr().Set(0)    # No position stiffness
            drive_api.CreateDampingAttr().Set(0.1)    # Small damping
            
    def create_materials(self):
        """Create physics materials for different components."""
        
        # Metal material (for spools and mounts)
        metal_material = UsdShade.Material.Define(self.stage, "/SpiRob/Materials/MetalMaterial")
        metal_physics = UsdPhysics.MaterialAPI.Apply(metal_material.GetPrim())
        metal_physics.CreateStaticFrictionAttr(0.8)
        metal_physics.CreateDynamicFrictionAttr(0.6)
        metal_physics.CreateRestitutionAttr(0.1)
        
        # Plastic material (for spirob body)
        plastic_material = UsdShade.Material.Define(self.stage, "/SpiRob/Materials/PlasticMaterial")
        plastic_physics = UsdPhysics.MaterialAPI.Apply(plastic_material.GetPrim())
        plastic_physics.CreateStaticFrictionAttr(0.6)
        plastic_physics.CreateDynamicFrictionAttr(0.4)
        plastic_physics.CreateRestitutionAttr(0.3)
        
        # Apply materials to components
        self.apply_material_to_prim("/SpiRob/SpiRobBody", plastic_material)
        for side in ["Left", "Right"]:
            self.apply_material_to_prim(f"/SpiRob/{side}Spool", metal_material)
            self.apply_material_to_prim(f"/SpiRob/{side}MotorMount", metal_material)
            
    def apply_material_to_prim(self, prim_path, material):
        """Apply physics material to a prim."""
        prim = self.stage.GetPrimAtPath(prim_path)
        if prim:
            binding_api = UsdShade.MaterialBindingAPI.Apply(prim)
            binding_api.Bind(material)
            
    def add_contact_sensor(self, prim_path):
        """Add contact sensor for collision detection."""
        # This will be handled in the Isaac Lab environment configuration
        pass
        
    def save_usd(self, output_path="spirob_complete.usd"):
        """Save the complete USD assembly."""
        self.stage.GetRootLayer().Export(output_path)
        print(f"USD assembly saved to {output_path}")

# Create the complete SpiRob assembly
if __name__ == "__main__":
    creator = SpiRobUSDCreator()
    creator.create_spirob_assembly()
    creator.save_usd("spirob_complete.usd")