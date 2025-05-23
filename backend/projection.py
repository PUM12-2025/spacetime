import numpy as np
from pyproj import Geod

# Minimum elevation angle (radians) above which a corner is considered 'too high' relative to the XY-plane
MIN_ANGLE_TO_XY = -np.pi/18  # -10 degrees
# Minimum field-of-view angular separation (radians) between adjacent corners
MIN_FOV_ANGLE = np.pi/45    # 4 degrees
# Approximate mean Earth radius in meters (used if needed for other computations)
R_EARTH = 6371001

def dist_to_degs_new(drone_pos, points):
    """
    Convert planar offsets (dx, dy) in meters from the drone to latitude/longitude.

    Args:
        drone_pos: [lat, lon, alt] of drone in degrees/meters.
        points: list of [dy, dx, dz] offsets in meters relative to drone_pos.

    Returns:
        new_points: list of [lat, lon, 0] ground coordinates in degrees.
    """
    new_points = []
    # Initialize geodetic converter on the WGS84 ellipsoid
    geod = Geod(ellps="WGS84")
    for dy, dx, dz in points:
        # First, move from original lat/lon by north-south offset (bearing 0 or 180)
        lon1, lat1, _ = geod.fwd(
            drone_pos[1], drone_pos[0],           # start lon, lat
            0 if dy >= 0 else 180,                # heading north if dy>=0 else south
            abs(dy)                               # distance moved
        )
        # Then, move by east-west offset (bearing 90 or 270)
        lon2, lat2, _ = geod.fwd(
            lon1, lat1,                           # intermediate lon, lat
            90 if dx >= 0 else 270,               # heading east if dx>=0 else west
            abs(dx)                               # distance moved
        )
        # Append final lat/lon, ignore altitude (ground = 0)
        new_points.append([lat2, lon2, 0])
    return new_points


def calc_ground_point(drone_pos, vect):
    """
    Calculate where a direction vector from the drone intersects the ground plane z=0.

    Args:
        drone_pos: numpy array [x, y, z] of drone in meters.
        vect: numpy array [vx, vy, vz] direction vector in meters.

    Returns:
        Intersection point as numpy array [x, y, 0] if vect[2]<0, else infinity.
    """
    # If pointing upwards or perfectly horizontal, no ground intersection
    if vect[2] >= 0:
        return np.inf
    # Solve for t such that drone_z + t * vz = 0 => t = -drone_z / vz
    A = drone_pos[2] / (-vect[2])
    # Compute intersection: origin + A * vect
    return vect * A + drone_pos
    

def angle_to_xy(vect):
    """
    Compute elevation angle of vect above the XY-plane.

    Args:
        vect: numpy array [vx, vy, vz].

    Returns:
        Elevation angle in radians relative to horizontal (pi/2 - angle with vertical axis).
    """
    # Zero vector has undefined angle
    if np.linalg.norm(vect) == 0:
        return np.inf
    # Angle from vector to up-axis [0,0,1]
    return np.pi/2 - angle_between(np.array([0, 0, 1]), vect)


def unit_vector(vector):
    """
    Normalize a vector to unit length.

    Args:
        vector: numpy array.

    Returns:
        Unit vector, or 0 if zero-length.
    """
    norm = np.linalg.norm(vector)
    if norm == 0:
        return 0
    return vector / norm


def angle_between(v1, v2):
    """
    Compute the angle between two vectors using the dot product formula.

    Args:
        v1, v2: numpy arrays.

    Returns:
        Angle in radians, clipped to [0, pi], or inf if inputs invalid.
    """
    if type(v1) != np.ndarray or type(v2) != np.ndarray:
        return np.inf
    # Normalize both
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    # Compute arccos of dot, with clipping to avoid numerical issues
    return np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))


def FOV_angle_big_enough(angles):
    """
    Ensure all adjacent FOV corner angles remain separated by at least MIN_FOV_ANGLE.

    Args:
        angles: list of four [hori, vert] angle pairs in radians.

    Returns:
        True if all angular differences >= MIN_FOV_ANGLE, else False.
    """
    for j in range(len(angles)):
        # Compare each corner j with next corner (j+1 mod 4) on same axis
        diff = np.abs(angles[j][j % 2] - angles[(j + 1) % 4][j % 2])
        if diff < MIN_FOV_ANGLE:
            return False
    return True


def get_highest_corner_index(corners):
    """
    Find the corner vector with the largest elevation angle (most 'upward').

    Args:
        corners: list of 4 direction vectors [1, tan(h), tan(v)].

    Returns:
        Index of corner with max elevation.
    """
    highest_corner_index = 0
    highest_angle = -np.inf
    for i, corner in enumerate(corners):
        if angle_to_xy(corner) >= highest_angle:
            highest_angle = angle_to_xy(corner)
            highest_corner_index = i
    return highest_corner_index


def both_or_neither_neighbouring_corners_too_high(corners, i):
    """
    Check if both neighbours of corner i are either both above MIN_ANGLE_TO_XY or both below.
    This determines symmetric adjustment strategy.

    Args:
        corners: list of 4 vectors.
        i: index of current corner.

    Returns:
        True if neighbours are both too high or both too low.
    """
    both = (angle_to_xy(corners[(i - 1) % 4]) >= MIN_ANGLE_TO_XY and 
            angle_to_xy(corners[(i + 1) % 4]) >= MIN_ANGLE_TO_XY)
    neither = (angle_to_xy(corners[(i - 1) % 4]) < MIN_ANGLE_TO_XY and 
            angle_to_xy(corners[(i + 1) % 4]) < MIN_ANGLE_TO_XY)
    return both or neither
            

def verify_FOV(corners, rotated_corners, start_angles, drone_angles, cam_angles, earth_frame=False):
    """
    Iteratively adjust corner angles so no corner remains above min elevation, preserving FOV separation.

    Args:
        corners: original corner direction vectors.
        rotated_corners: corners after rotation by camera/drone angles.
        start_angles: list of [hori, vert] initial angles.
        drone_angles, cam_angles: dicts with 'yaw','pitch','roll'.
        earth_frame: if True, skip drone rotation.

    Returns:
        (rotated_corners, angles) if successful, else (inf, inf) if FOV separation fails.
    """
    # Copy starting angles and record initial sign of each for consistent step direction
    angles = start_angles.copy()
    signs = [np.sign(angle) for angle in angles]
    # Find the corner pointing highest above horizontal
    i = get_highest_corner_index(rotated_corners)
    # While this corner is still above threshold, adjust
    while angle_to_xy(rotated_corners[i]) >= MIN_ANGLE_TO_XY:
        if both_or_neither_neighbouring_corners_too_high(rotated_corners, i):
            # Adjust both adjacent corners symmetrically
            index_down = i % 2
            index_up = (i + 1) % 2

            # Step the corner i downwards by 3 degrees in appropriate axis
            angles[i] -= deg_to_rad(signs[i]) * 3
            # Propagate same component change to neighbors
            angles[(i-1) % 4][index_down] = angles[i][index_down]
            angles[(i+1) % 4][index_up]   = angles[i][index_up]

            # Update direction vectors
            corners[i]         = np.append(1, np.tan(angles[i]))
            corners[(i-1)%4]   = np.append(1, np.tan(angles[(i-1)%4]))
            corners[(i+1)%4]   = np.append(1, np.tan(angles[(i+1)%4]))
        else:
            # Only one neighbour is too high: adjust that plane axis for both
            if angle_to_xy(rotated_corners[(i - 1) % 4]) >= MIN_ANGLE_TO_XY:
                i_diff = -1
                index_common = i % 2
            elif angle_to_xy(rotated_corners[(i + 1) % 4]) >= MIN_ANGLE_TO_XY:
                i_diff = 1
                index_common = (i + 1) % 2

            # Lower selected axis by 3 degrees for corner i and its high neighbour
            angles[i][index_common] -= deg_to_rad(signs[i][[index_common]])*3
            angles[(i+i_diff) % 4][index_common] = angles[i][index_common]

            # Update vectors for this pair
            corners[i] = np.append(1, np.tan(angles[i]))
            corners[(i+i_diff) % 4] = np.append(1, np.tan(angles[i+i_diff]))

        # If FOV angular separation violated, return failure
        if not FOV_angle_big_enough(angles):
            return np.inf, np.inf

        # Recompute rotated corners after adjusting angles
        rotated_corners = rotate_FOV(corners, drone_angles, cam_angles, earth_frame)
    # Return final valid rotated corners and their angles
    return rotated_corners, angles


def rotate_FOV(corners, drone_angles, cam_angles, earth_frame=False):
    """
    Apply camera and optionally drone rotations to FOV corner vectors.

    Args:
        corners: list of 4 direction vectors.
        drone_angles, cam_angles: dicts of Euler angles.
        earth_frame: skip drone rotation if True.

    Returns:
        List of rotated vectors if all below MIN_ANGLE_TO_XY, else inf.
    """
    # First apply camera rotation to each corner
    rotated_corners = [rotate_vect(corner, cam_angles) for corner in corners]
    # Then apply drone rotation if using drone frame
    if not earth_frame:
        rotated_corners = [rotate_vect(corner, drone_angles) for corner in rotated_corners]
    # Early exit: if any corner is now below threshold, return early for verify_FOV loop
    for corner in rotated_corners:
        if angle_to_xy(corner) < MIN_ANGLE_TO_XY:
            return rotated_corners
    # If all still above threshold, indicate failure
    return np.inf


def calc_frame_size(vertFOV, horiFOV, angles):
    """
    Compute relative cropping offsets and resulting frame size after angle adjustments.

    Args:
        vertFOV, horiFOV: full FOV in radians.
        angles: adjusted angles for each corner.

    Returns:
        corner_offset: fractional offsets per corner [x_frac, y_frac].
        frame_size: dict with keys "w","h" as final coverage ratios.
    """
    # Define starting half-angles for 4 corners
    start_angles = [
        np.array([horiFOV/2,  vertFOV/2]),
        np.array([-horiFOV/2, vertFOV/2]),
        np.array([-horiFOV/2,-vertFOV/2]),
        np.array([horiFOV/2, -vertFOV/2])
    ]
    corner_offset = []
    # For each corner, compute ratio of reduction in tan() distance
    for i, corner_angle in enumerate(angles):
        start_dist   = np.tan(start_angles[i])
        reduced_dist = np.tan(corner_angle)
        # Fractional offset along each axis (half distance - reduced distance / full half-dist)
        corner_offset.append([(np.abs(start_dist[0] - reduced_dist[0]))/(2*np.abs(start_dist[0])), 
                              (np.abs(start_dist[1] - reduced_dist[1]))/(2*np.abs(start_dist[1]))])
    # Compute remaining width and height after cropping both sides
    frame_size = {}
    frame_size["w"] = float(1 - corner_offset[1][0] - corner_offset[0][0])
    frame_size["h"] = float(1 - corner_offset[3][1] - corner_offset[0][1])
    return corner_offset, frame_size


def compute_FOV_corners(vertFOV, horiFOV, drone_angles, cam_angles, earth_frame=False):
    """
    Initialize FOV corner vectors and perform rotations and angle corrections.

    Args:
        vertFOV, horiFOV: full field of view in radians.
        drone_angles, cam_angles: rotation dicts.
        earth_frame: disable drone rotation if True.

    Returns:
        rotated_corners: final direction vectors or inf if invalid.
        angles: final per-corner angles.
    """
    # Set up the 4 extreme corner angles (horiz left/right, vert up/down)
    angles = [
        np.array([horiFOV/2,  vertFOV/2]),
        np.array([-horiFOV/2, vertFOV/2]),
        np.array([-horiFOV/2,-vertFOV/2]),
        np.array([horiFOV/2, -vertFOV/2])
    ]
    # Convert half-angle pairs to 3D direction vectors [1, tan(h), tan(v)]
    corners = [np.append(1, np.tan(angle)) for angle in angles]
    # Apply rotations
    rotated_corners = rotate_FOV(corners, drone_angles, cam_angles, earth_frame)
    # If initial rotation is valid, refine angles to ensure no corner is too high
    if not rotated_corners == np.inf:
        rotated_corners, angles = verify_FOV(corners, rotated_corners, angles,
                                             drone_angles, cam_angles, earth_frame)
    return rotated_corners, angles


def deg_to_rad(deg):
    """Convert degrees to radians."""
    return deg/180 * np.pi


def rad_to_deg(rad):
    """Convert radians to degrees."""
    return rad * 180 / np.pi

# Rotation matrices from Wikipedia: https://en.wikipedia.org/wiki/Rotation_matrix#In_three_dimensions 
# Yaw (Z), Pitch (Y), Roll (X)
def rotate_vect(vect, angles):
    """
    Rotate a vector by Euler angles (yaw, pitch, roll).

    Args:
        vect: numpy array [x, y, z].
        angles: dict with keys 'yaw','pitch','roll' in radians.

    Returns:
        Rotated vector as numpy array.
    """
    vect = vect.copy()
    # Z-axis (yaw) rotation
    Rz = np.array([
        [ np.cos(angles['yaw']), -np.sin(angles['yaw']), 0],
        [ np.sin(angles['yaw']),  np.cos(angles['yaw']), 0],
        [                  0,                   0, 1]
    ])
    # Y-axis (pitch) rotation (negative for camera convention)
    Ry = np.array([
        [ np.cos(-angles['pitch']), 0, np.sin(-angles['pitch'])],
        [                       0, 1,                      0],
        [-np.sin(-angles['pitch']), 0, np.cos(-angles['pitch'])]
    ])
    # X-axis (roll) rotation (negative for camera convention)
    Rx = np.array([
        [1,                   0,                    0],
        [0, np.cos(-angles['roll']), -np.sin(-angles['roll'])],
        [0, np.sin(-angles['roll']),  np.cos(-angles['roll'])]
    ])
    # Combined rotation: Rz * Ry * Rx
    Rzy  = np.dot(Rz, Ry)
    Rzyx = np.dot(Rzy, Rx)
    # Apply to input vector
    return np.dot(Rzyx, vect)


def get_projection_points(drone_pos, drone_angles, cam_angles, horiFOV, vertFOV, earth_frame = False):
    """
    Compute ground projection of camera FOV corners given drone state.

    Args:
        drone_pos: [lat, lon, alt] of drone.
        drone_angles, cam_angles: dicts of Euler angles.
        horiFOV, vertFOV: FOV angles in radians.

    Returns:
        camArea: list of lat/lon ground corner positions.
        corner_offset: fractional cropping offsets.
        frame_size: dict with final image coverage ratios.
        Or (inf,inf,inf) on failure.
    """
    # Compute rotated direction vectors and final corner angles
    FOV_vects, FOV_angles = compute_FOV_corners(horiFOV, vertFOV, drone_angles, cam_angles, earth_frame)
    
    # if fov too high, return (np.inf, np.inf, np.inf)
    if FOV_vects == np.inf:
        return np.inf, np.inf, np.inf
    # compute fractional cropping offsets and image coverage ratios.
    corner_offset, frame_size = calc_frame_size(horiFOV, vertFOV, FOV_angles)

    #calculate grpund points relative to drone and then in lat, lon
    origin_drone_pos = np.array([0.0,0.0, drone_pos[2]])
    fov_points_relative_drone = [calc_ground_point(origin_drone_pos, vect) for vect in FOV_vects]
    fov_coords = dist_to_degs_new(drone_pos, fov_points_relative_drone)
    return fov_coords, corner_offset, frame_size
