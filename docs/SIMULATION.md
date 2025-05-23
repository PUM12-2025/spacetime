# SIMULATION
To simulate video synced to drone telemetry we used ArduPilot combined with screen recording a MAVCesium window,
and this requires quite a lot of setup.

## ArduPilot
To use ArduPilot without MissionPlanner you need a Linux/Ubuntu machine.
Then simply follow this [guide](https://ardupilot.org/dev/docs/building-setup-linux.html#building-setup-linux).
The ArduPilot repo contains a file called `BUILD.md` that will help with configuring the simulation. 

In this project, we used the `SITL` board and the `ArduPlane` vehicle and this guide will not cover anything else.

### WSL
Windows users can use WSL to install a Linux distribution for ArduPilot.
First, follow [this](https://learn.microsoft.com/en-us/windows/wsl/install) for WSL, the official guides use Ubuntu and so have we.

## MAVCesium
MAVCesium is untested on Windows but we've gotten it to work on Windows 11, do as you like.
MAVCesium is a submodule in the [MAVProxy](https://github.com/ArduPilot/MAVProxy) repo so start with cloning that to the same machine that everything else is installed on.
If you already have MAVProxy cloned you can use
```
git submodule update --init –recursive 
```
to get the module.

NOTE: Don't forget to install the Python requirements!

NOTE: ArduPilot already contains MAVProxy but we did not find a way to get MAVCesium to work there.

## Running everything
🙏 Bless this mess 🙏
### ArduPilot
Navigate to your cloned ArduPilot repo and run
```
sim_vehicle.py --map --console -v ArduPlane
```
and you should get a map and a console window opened.

The terminal you started ArduPilot is now used to control the drone, type
```
mode takeoff
arm throttle
```
and your plane should start moving on the map and loiter around the starting point. Check the console so everything looks right.

For more info about the arguments see the official [guide](https://ardupilot.org/dev/docs/using-sitl-for-ardupilot-testing.html#using-sitl-for-ardupilot-testing) to using SITL
You can for example add a location to the `locations.txt` file in `Tools/autotest` and add `-L <Name of location>` to start the simulation somewhere else.

### MAVCesium
Now to start MAVCesium, navigate to the MAVProxy repo and then enter `MAVProxy/modules/mavproxy_cesium/app`. Note that `MAVCesium` here is a directory in the repo for maximum confusion.

Then finally run
```
python ./cesium_web_server.py
```
following the link you should now see a 3D plane flying according to the ArduPilot simulation.

NOTE: MAVCesium won't start if it can't connect to `tcp:127.0.0.1:5763` unless changing the code manually, so make sure that the port is free and that ArduPilot is running.

### Screen recording

Once everything is running it's time to get the screen recording started.

Simply click the `getVideo` button in the top right and you will be prompted to select which window to record.

TIP: Put MAVCesium in its own window to make this easier, depending on browser and perhaps OS the window may also need to remain visible.


## Gimbal
To get ArduPilot to start sending MAVLink messages relating to the gimbal requires some additional work.

For starters, ArduPilot's [guide](https://ardupilot.org/dev/docs/adding_simulated_devices.html) is outdated and makes controlling the mounts yaw impossible. Instead write
```
param set MNT1_TYPE 1

param set SERVO6_FUNCTION 6 

param set SERVO7_FUNCTION 7 

param set SERVO8_FUNCTION 8 
``` 
into ArduPilot. Then restart ArduPilot with the `-M` flag and it should start sending gembal related MAVLink data.

A problem now is that the gimbal also takes up a port. Telemetry is streamed on ports 5762 and 5763 and is used by MAVCesium and the gimbal. To solve this we need to add a new port to ArduPilot.

To enable a new port you need to start running ArduPilot with the argument
```
-A "--serial5=tcp:<port number>"
```
and then in ArduPilot run
```
param set SERIAL5_PROTOCOL 2
```

this will connect serial5 to the port of your choice and tell the autopilot to stream MAVLink data to it.

NOTE: Don't forget to change the sniffer's port using `-p` as well!

