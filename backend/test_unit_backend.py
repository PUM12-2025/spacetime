from projection import *
import numpy as np
import pytest
from pytest_mock import mocker

def test_dist_to_degs_new(mocker):
    mock_geod = mocker.patch("projection.Geod")
    instance = mock_geod.return_value
    instance.fwd.side_effect = [
        (10.1, 59.1, 0),
        (10.2, 59.2, 0),
        (10.3, 59.3, 0),
        (10.4, 59.4, 0),
    ]
    drone_pos = [59.0, 10.0, 100]
    points = [[1000, 1000, 0], [0,0,0]]
    result = dist_to_degs_new(drone_pos, points)
    assert isinstance(result, list)
    assert len(result) == 2
    assert len(result[0]) == 3
    assert result == [[59.2, 10.2, 0], [59.4, 10.4, 0]]

def test_negative_calc_ground_point():
    drone_pos = np.array([0,0,2])
    vect = np.array([1,1,0])
    result = calc_ground_point(drone_pos, vect)
    assert  result == np.inf

def test_positive_calc_ground_point():
    drone_pos = np.array([0,0,2])
    vect = np.array([1,1,-1])
    result = calc_ground_point(drone_pos, vect)
    assert isinstance(result, np.ndarray)
    assert result[2] == 0

def test_negative_angle_to_xy():
    vect = np.array([0,0,0])
    result = angle_to_xy(vect)
    assert result == np.inf


def test_positive_angle_to_xy():
    vect = np.array([0,0,1])
    result = angle_to_xy(vect)
    assert result == np.pi/2
    vect = np.array([0,1,0])
    result = angle_to_xy(vect)
    assert result == 0
    vect = np.array([0,0,-1])
    result = angle_to_xy(vect)
    assert result == -np.pi/2

def test_negtive_unit_vector():
    vect = np.array([0,0,0])
    assert unit_vector(vect) == 0

def test_positive_unit_vector():
    vect = np.array([0,0,2])
    result = unit_vector(vect)
    assert np.array_equal(np.array([0,0,1]), result)

def test_negative_angle_between():
    vect1 = np.array([0,0,2])
    vect2 = 1
    result = angle_between(vect1, vect2)
    assert result == np.inf
    vect1 = 1
    vect2 = np.array([0,0,1])
    result = angle_between(vect1, vect2)
    assert result == np.inf


def test_angle_between():
    vect1 = np.array([0,0,2])
    vect2 = np.array([0,0,1])
    result = angle_between(vect1, vect2)
    assert result == 0
    vect1 = np.array([0,1,0])
    vect2 = np.array([0,0,1])
    result = angle_between(vect1, vect2)
    assert result == np.pi/2


def test_positive_FOV_angle_big_enough():
    angles = [[MIN_FOV_ANGLE/2, -MIN_FOV_ANGLE/2],
              [-MIN_FOV_ANGLE/2, -MIN_FOV_ANGLE/2],
              [-MIN_FOV_ANGLE/2, MIN_FOV_ANGLE/2],
              [MIN_FOV_ANGLE/2, MIN_FOV_ANGLE/2]]
    result = FOV_angle_big_enough(angles)
    assert result

def test_negative_FOV_angle_big_enough():
    MIN_FOV_ANGLE/2
    angles = [[MIN_FOV_ANGLE/3, -MIN_FOV_ANGLE/3],
              [-MIN_FOV_ANGLE/3, -MIN_FOV_ANGLE/3],
              [-MIN_FOV_ANGLE/3, MIN_FOV_ANGLE/3],
              [MIN_FOV_ANGLE/3, MIN_FOV_ANGLE/3]]
    result = FOV_angle_big_enough(angles)
    assert not result
    
def test_calc_frame_size_no_reduction():
    angles = [np.array([np.pi/12, np.pi/12]),
              np.array([-np.pi/12, np.pi/12]),
              np.array([-np.pi/12, -np.pi/12]),
              np.array([np.pi/12, -np.pi/12])]
    result_offset, result_size = calc_frame_size(np.pi/6, np.pi/6, angles)
    assert np.all(result_offset) == 0
    assert result_size["h"] == 1 and  result_size["w"] == 1

def test_calc_frame_size_reduction():
    angles = [np.array([np.arctan(0.25), np.arctan(0.25)]),
              np.array([-np.arctan(0.25), np.arctan(0.25)]),
              np.array([-np.arctan(0.25), -np.arctan(0.25)]),
              np.array([np.arctan(0.25), -np.arctan(0.25)])]
    result_offset, result_size = calc_frame_size(np.arctan(0.5)*2, np.arctan(0.5)*2, angles)
    for offset in result_offset:
        assert np.isclose(offset[0], 0.25) and np.isclose(offset[1], 0.25)
    assert np.isclose(result_size["h"], 0.5)
    assert np.isclose(result_size["w"], 0.5)

def test_deg_to_rad():
    result = deg_to_rad(90)
    assert result == np.pi/2
    
def test_rad_to_deg():
    result = rad_to_deg(np.pi/2)
    assert result == 90
    
def test_rotate_vect():
    angles = {"yaw":0, "pitch":0, "roll":np.pi/2}
    vect = np.array([0,0,1])
    result = rotate_vect(vect, angles)
    assert np.allclose(result, [0, 1, 0])