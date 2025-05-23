import time
import asyncio
import websockets
import json
from scipy.spatial.transform import Rotation as R
import numpy as np
"""
---- mavlink_sniffer ----
A tool for sending MavLink data from a chosen port to a chosen local websocket

Arguments:
-p: port to sniff
-w: websocket port
-m: message type to filter by
-f: reads .tlog file instead
"""

from argparse import ArgumentParser
from pymavlink import mavutil

from projection import deg_to_rad, get_projection_points

def unpack_mavlink_flags(bitmap: int) -> dict:
    gimbal_flags = [
        "GIMBAL_DEVICE_FLAGS_RETRACT",
        "GIMBAL_DEVICE_FLAGS_NEUTRAL",
        "GIMBAL_DEVICE_FLAGS_ROLL_LOCK",
        "GIMBAL_DEVICE_FLAGS_PITCH_LOCK",
        "GIMBAL_DEVICE_FLAGS_YAW_LOCK",
        "GIMBAL_DEVICE_FLAGS_YAW_IN_VEHICLE_FRAME",
        "GIMBAL_DEVICE_FLAGS_YAW_IN_EARTH_FRAME",
        "GIMBAL_DEVICE_FLAGS_ACCEPTS_YAW_IN_EARTH_FRAME",
        "GIMBAL_DEVICE_FLAGS_RC_EXCLUSIVE",
        "GIMBAL_DEVICE_FLAGS_RC_MIXED"
    ]
    flags = {}
    flag_values = [bool(int(x)) for x in "{0:b}".format(int(bitmap))[::-1]]
    for i, flag in enumerate(gimbal_flags):
        if i < len(flag_values):
            flags[flag] = flag_values[i]
        else:
            flags[flag] = False
    return flags

parser = ArgumentParser(description=__doc__)
parser.add_argument("-p", "--port", type=int,
                     help="port to sniff (default: 5762)", default=5762)
parser.add_argument("-w", "--websocket-port", type=int,
                     help="websocket port (default: 8777)", default=8777)
parser.add_argument("-m", "--messages", nargs='+',
                     help="mavlink message to filter by", default=["GLOBAL_POSITION_INT", "ATTITUDE", "GIMBAL_DEVICE_ATTITUDE_STATUS", "CAMERA_FOV_STATUS"])
parser.add_argument("-f", "--filepath", dest="path",
                    help="filepath to .tlog file ", default=None)
args = parser.parse_args()

async def main():

    if args.path:
        async with websockets.serve(filereader, 'localhost', args.websocket_port):
            await asyncio.Future()

    async with websockets.serve(tcpsniffer, 'localhost', args.websocket_port):
        await asyncio.Future()

async def tcpsniffer(ws):
    msrc = mavutil.mavlink_connection('tcp:localhost:{}'.format(args.port), planner_format=False,
                                    notimestamps=True,
                                robust_parsing=True)
    
    #Set standard values
    drone_pos = np.array([0.0,0.0,1.0])

    drone_angles = {}
    drone_angles['yaw'] = 0
    drone_angles['pitch'] = 0
    drone_angles['roll'] = 0

    cam_angles = {}
    cam_angles['yaw'] = 0
    cam_angles['pitch'] = 0
    cam_angles['roll'] = 0
    earth_frame = False

    #Standard value taken from MAVCesiums mount view
    horiFOV = deg_to_rad(109.17181489731475)
    vertFOV = deg_to_rad(122.60000000000001)

    while True:
        dont_send = False
        l = msrc.recv_match(type=args.messages, blocking=False)
        if l is not None:
            l_last_timestamp = 0
            if  l.get_type() != 'BAD_DATA':
                l_timestamp = getattr(l, '_timestamp', None)
                if not l_timestamp:
                    l_timestamp = l_last_timestamp
                l_last_timestamp = l_timestamp

            d = l.to_dict()
            data = {}
            if d["mavpackettype"] == "GLOBAL_POSITION_INT":
                drone_pos[0] = d["lat"]/(10**7)
                drone_pos[1] = d["lon"]/(10**7)
                drone_pos[2] = d["relative_alt"]/(10**3)
            elif d["mavpackettype"] == "ATTITUDE":
                drone_angles['yaw'] = d["yaw"]
                drone_angles['pitch'] = d["pitch"]
                drone_angles['roll'] = d["roll"]
            elif d["mavpackettype"] == "GIMBAL_DEVICE_ATTITUDE_STATUS":
                r = R.from_quat(d["q"], scalar_first = True)
                cam_rotation = r.as_euler('zyx', degrees=False)
                cam_angles['yaw'] = cam_rotation[0]
                cam_angles['pitch'] = cam_rotation[1]
                cam_angles['roll'] = cam_rotation[2]
                gimbal_flags = unpack_mavlink_flags(d["flags"])
                if gimbal_flags["GIMBAL_DEVICE_FLAGS_YAW_IN_VEHICLE_FRAME"]:
                    earth_frame = False
                elif d["GIMBAL_DEVICE_FLAGS_YAW_IN_EARTH_FRAME"]:
                    earth_frame = True
                elif d["GIMBAL_DEVICE_FLAGS_YAW_LOCK"]:
                    earth_frame = True
                else:
                    earth_frame = False
            elif d["mavpackettype"] == "CAMERA_FOV_STATUS":
                horiFOV = deg_to_rad(d["hfov"])
                vertFOV = deg_to_rad(d["vfov"])


            data["yaw"] = drone_angles['yaw']
            data["lat"] = drone_pos[0]
            data["lon"] = drone_pos[1]
                
            fov_coords, corner_offset, frame_size = get_projection_points(drone_pos, drone_angles, cam_angles, horiFOV, vertFOV, earth_frame)
            data["has_projection"] = False
            if not fov_coords == np.inf:
                data["has_projection"] = True
                for i, corner in enumerate(fov_coords):
                    dict_corner = {"lat": float(corner[0]), "lon": float(corner[1]), "offset": {"x": float(corner_offset[i][0]), "y": float(corner_offset[i][1])}} 
                    data[f"corner{i}"] = dict_corner  
                    
                data["frame_size"] = frame_size

            if not dont_send:    
                await ws.send(json.dumps(data))
            await asyncio.sleep(0.01)
        else:
            await asyncio.sleep(0.001)

async def filereader(ws):
    mlog = mavutil.mavlink_connection(args.path)
    while True:
        l = mlog.recv_match(blocking=True, type=args.messages)
        if l is not None:
            l_last_timestamp = 0
            if  l.get_type() != 'BAD_DATA':
                l_timestamp = getattr(l, '_timestamp', None)
                if not l_timestamp:
                    l_timestamp = l_last_timestamp
                l_last_timestamp = l_timestamp
            d = l.to_dict()
            d.update({'timestamp': time.strftime("%Y-%m-%d %H:%M:%S",
                                time.localtime(l._timestamp))})
            await ws.send(json.dumps(d))
            await asyncio.sleep(1)


if __name__ == "__main__":
    asyncio.run(main())