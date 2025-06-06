# advanced_cable_physics.py - Deformable cable implementation

def create_deformable_cable(stage, start_pos, end_pos, segments=20):
    """Create a deformable cable using soft body physics."""
    
    cable_length = np.linalg.norm(np.array(end_pos) - np.array(start_pos))
    segment_length = cable_length / segments
    
    # Create cable segments
    cable_prims = []
    
    for i in range(segments):
        # Position along cable
        t = i / (segments - 1)
        pos = np.array(start_pos) + t * (np.array(end_pos) - np.array(start_pos))
        
        # Create cable segment
        segment_path = f"/SpiRob/Cable/Segment_{i:02d}"
        segment = UsdGeom.Capsule.Define(stage, segment_path)
        segment.CreateRadiusAttr(0.0005)  # 0.5mm radius
        segment.CreateHeightAttr(segment_length)
        
        # Position segment
        xform = UsdGeom.Xformable(segment)
        xform.AddTranslateOp().Set(Gf.Vec3d(*pos))
        
        # Add physics
        rigid_body = UsdPhysics.RigidBodyAPI.Apply(segment.GetPrim())
        mass_api = UsdPhysics.MassAPI.Apply(segment.GetPrim())
        mass_api.CreateMassAttr(0.001 / segments)  # 1g total cable mass
        
        # Add collision
        UsdPhysics.CollisionAPI.Apply(segment.GetPrim())
        
        cable_prims.append(segment)
        
        # Connect segments with joints
        if i > 0:
            create_cable_joint(stage, f"/SpiRob/Cable/Segment_{i-1:02d}", 
                             segment_path, segment_length)
    
    return cable_prims

def create_cable_joint(stage, body1_path, body2_path, segment_length):
    """Create joint between cable segments."""
    
    joint_path = f"{body2_path}_Joint"
    spherical_joint = UsdPhysics.SphericalJoint.Define(stage, joint_path)
    
    # Connect bodies
    spherical_joint.CreateBody0Rel().SetTargets([body1_path])
    spherical_joint.CreateBody1Rel().SetTargets([body2_path])
    
    # Joint limits (allow some swing but not too much)
    spherical_joint.CreateConeAngle0LimitAttr().Set(30.0)  # degrees
    spherical_joint.CreateConeAngle1LimitAttr().Set(30.0)
    
    # Joint stiffness
    for axis in ["X", "Y", "Z"]:
        drive_api = UsdPhysics.DriveAPI.Apply(spherical_joint.GetPrim(), axis.lower())
        drive_api.CreateStiffnessAttr().Set(1000.0)
        drive_api.CreateDampingAttr().Set(10.0)