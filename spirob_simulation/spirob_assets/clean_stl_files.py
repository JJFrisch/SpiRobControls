"""
clean_stl_files.py - Pre-processes raw SolidWorks STL exports for physics sim.

Cleans, validates, scales (mm -> m), and simplifies each mesh so it is
suitable for MuJoCo or Isaac Sim. Output files are written alongside the
inputs with a 'cleaned_' prefix.

Dependencies: trimesh, numpy
    pip install trimesh numpy
"""
# mesh_cleaner.py
import trimesh
import numpy as np
import os

def clean_stl_file(input_path, output_path):
    """Clean and validate STL file for physics simulation."""
    
    # Load mesh
    mesh = trimesh.load(input_path)
    
    print(f"Processing {input_path}:")
    print(f"  Original: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    
    # Basic cleaning
    mesh.remove_duplicate_faces()
    mesh.remove_degenerate_faces()
    mesh.remove_unreferenced_vertices()
    
    # Fill holes (if small)
    mesh.fill_holes()
    
    # Fix normals
    mesh.fix_normals()
    
    # Check if watertight
    if not mesh.is_watertight:
        print(f"  WARNING: {input_path} is not watertight!")
        # Attempt to make watertight
        mesh = mesh.convex_hull  # Last resort - use convex hull
    
    # Scale check (assume input is in mm, convert to meters)
    if mesh.bounds.ptp().max() > 10:  # Likely in mm
        mesh.apply_scale(0.001)  # Convert mm to meters
        print(f"  Scaled from mm to meters")
    
    # Simplify if too complex
    if len(mesh.faces) > 10000:
        mesh = mesh.simplify_quadric_decimation(5000)
        print(f"  Simplified to {len(mesh.faces)} faces")
    
    print(f"  Final: {len(mesh.vertices)} vertices, {len(mesh.faces)} faces")
    print(f"  Bounds: {mesh.bounds}")
    print(f"  Volume: {mesh.volume:.6f} m³")
    
    # Export cleaned mesh
    mesh.export(output_path)
    return mesh

# Clean all STL files
stl_files = [
    "spirob_body.stl",
    "left_spool.stl",
    "right_spool.stl",        # previously commented out -- add file to meshes/ to enable
    "left_motor_mount.stl",
    "right_motor_mount.stl",  # previously commented out -- add file to meshes/ to enable
    "base_frame.stl"
]

if __name__ == "__main__":
    import os
    for stl_file in stl_files:
        if os.path.exists(stl_file):
            clean_stl_file(stl_file, f"cleaned_{stl_file}")
        else:
            print(f"Skipping {stl_file} (file not found)")