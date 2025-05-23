import pytest
import numpy as np
from projection import (
    get_projection_points,
    calc_ground_point,
    deg_to_rad,
    MIN_FOV_ANGLE,
    MIN_ANGLE_TO_XY
)


def test_nominal_rotated_camera_1():
    # TC1: Standard highly rotated camera
    drone_pos = [59.0, 18.0, 100.0]
    angles = {'yaw': deg_to_rad(0.0), 'pitch': deg_to_rad(120.0), 'roll': deg_to_rad(120.0)}
    horiz_FOV = deg_to_rad(120)
    vert_FOV = deg_to_rad(120)

    cam_area, corner_offset, frame_size = get_projection_points(
        drone_pos, angles, angles, horiz_FOV, vert_FOV, earth_frame=False
    )

    # Expect four ground points, all finite
    assert isinstance(cam_area, list) and len(cam_area) == 4
    for pt in cam_area:
        assert all(np.isfinite(coord) for coord in pt)
        assert pt[2] == 0

    # corner_offset entries between 0 and 1
    assert isinstance(corner_offset, list) and len(corner_offset) == 4
    for off in corner_offset:
        assert 0 <= off[0] <= 1 and 0 <= off[1] <= 1

    # frame_size keys 'w' and 'h' in (0,1)
    assert 'w' in frame_size and 'h' in frame_size
    assert 0 <= frame_size['w'] <= 1
    assert 0 <= frame_size['h'] <= 1


def test_nominal_rotated_camera_2():
    # TC2: Standard highly rotated camera
    drone_pos = [59.0, 18.0, 100.0]
    angles = {'yaw': deg_to_rad(0.0), 'pitch': deg_to_rad(-120.0), 'roll': deg_to_rad(-120.0)}
    horiz_FOV = deg_to_rad(120)
    vert_FOV = deg_to_rad(120)

    cam_area, corner_offset, frame_size = get_projection_points(
        drone_pos, angles, angles, horiz_FOV, vert_FOV, earth_frame=False
    )

    # Expect four ground points, all finite
    assert isinstance(cam_area, list) and len(cam_area) == 4
    for pt in cam_area:
        assert all(np.isfinite(coord) for coord in pt)
        assert pt[2] == 0

    # corner_offset entries between 0 and 1
    assert isinstance(corner_offset, list) and len(corner_offset) == 4
    for off in corner_offset:
        assert 0 <= off[0] <= 1 and 0 <= off[1] <= 1

    # frame_size keys 'w' and 'h' in (0,1)
    assert 'w' in frame_size and 'h' in frame_size
    assert 0 <= frame_size['w'] <= 1
    assert 0 <= frame_size['h'] <= 1

def test_earth_frame_skips_drone_rotation():
    # TC3: earth_frame=True should produce similar valid output
    drone_pos = [59.0, 18.0, 100.0]
    angles = {'yaw': 0.5, 'pitch': 0.1, 'roll': -0.2}
    horiz_FOV = deg_to_rad(60)
    vert_FOV = deg_to_rad(40)

    cam_area, corner_offset, frame_size = get_projection_points(
        drone_pos, angles, angles, horiz_FOV, vert_FOV, earth_frame=True
    )

    # Should still get finite ground points
    assert isinstance(cam_area, list) and len(cam_area) == 4
    assert all(all(np.isfinite(coord) for coord in pt) for pt in cam_area)

    # Offsets and frame size still valid
    assert all(0 <= off[0] <= 1 and 0 <= off[1] <= 1 for off in corner_offset)
    assert 0 <= frame_size['w'] <= 1
    assert 0 <= frame_size['h'] <= 1


def test_too_narrow_FOV():
    # TC4: extremely narrow FOV should trigger verify_FOV failure
    drone_pos = [59.0, 18.0, 100.0]
    angles = {'yaw': 0, 'pitch': MIN_ANGLE_TO_XY, 'roll': 0.0}
    narrow = MIN_FOV_ANGLE / 2

    assert get_projection_points(drone_pos, angles, angles, narrow, narrow, True) == (np.inf, np.inf, np.inf)
    
def test_too_rotated_FOV():
    # TC5: rotated fov past MIN_ANGLE_TO_XY should return inf
    drone_pos = [59.0, 18.0, 100.0]
    angles = {'yaw': 0.0, 'pitch': np.pi/2, 'roll': 0.0}
    narrow = MIN_FOV_ANGLE / 2

    assert get_projection_points(drone_pos, angles, angles, narrow, narrow) == (np.inf, np.inf, np.inf)
