# Spacetime Backend

The backend is written in Python and consists of two files.`mavlink_sniffer.py` and `projection.py`.
It's tested for python 3.x found [here](https://www.python.org/downloads/)

## Setup
The setup assumes you're in the `backend` folder.

Install Python using the link above and run 
```bash
pip install -r requirements.txt
```
to install the requirements.

Then simply run 
```bash
python3 mavlink_sniffer.py
```
with your arguments of choice.

## MAVLink sniffer
The sniffer uses [pymavlink](https://github.com/ArduPilot/pymavlink) to receive MAVLink data from a chosen port or read from a `.tlog` file. It then sends the processed message through a websocket.
When reading from file the messages will be sent over the websocket with 1~ sec intervals to mimic simulations.

IMPORTANT: It cannot sniff and read from a file at the same time. 

### Arguments
- `-h` Displays help
- `-p` Select the port to listen to (default: 5762)
- `-w` Select the websocket port (default: 8777)
- `-m` Select the MAVLink messages to filter by
- `-f` Enter filepath for `.tlog`file and swap to file reading mode

## The projection

### ⚠️🚨!! Math Alert !! ⚠️🚨

#### Known data
- `drone_pos`: the position of the drone, latitude, longitude and altitude, denoted from now on as d<sub>lat</sub>, d<sub>lon</sub> and d<sub>alt</sub>.

- `drone_angles`: Newton angles describing the rotation of the drone around x- (roll), y- (pitch) and z-axis (yaw), denoted from now on as d<sub>roll</sub>, d<sub>pitch</sub> and d<sub>yaw</sub>.

- `cam_angles`: Newton angles describing the rotation of the camera gimbal around x- (roll), y- (pitch) and z-axis (yaw), denoted from now on as c<sub>roll</sub>, c<sub>pitch</sub> and c<sub>yaw</sub>.

- `horiFOV`: the angle describing the horizontal field of view (FOV) of the camera, denoted from now on as f<sub>x</sub>.

- `vertFOV`: the angle describing the vertical FOV of the camera, denoted from now on as f<sub>y</sub>.

- `earth_frame`: bool deciding if the camera rotation is described in the frame of the drone or the
earth.

- `MIN_ANGLE_TO_XY`: describes the minimum allowed angle between FOV corners and the x-y plane (negative value to ensure only vectors with negative z values, downwards), in radians, denoted from now on as ϴ<sub>xy</sub>.

- `MIN_FOV_ANGLE`: minimum allowed angle between sides of the FOV, in radians, denoted from now on as ϴ<sub>fov</sub>.

#### 1. Calculating the FOV:
Assumed: 0 rotation of camera means pointing along positive x. 
Each vertical side of the FOV has an absolute angle of f<sub>x</sub>/2 from the x-axis and each horizontal side of the FOV has an absolute angle of f<sub>y</sub>/2 from the x-axis along the x-z plane. Define vectors representing the corners of FOV as follows:
 - v̄<sub>fov0</sub> = (1, tan(f<sub>x</sub> / 2), tan(f<sub>y</sub> / 2))
 - v̄<sub>fov1</sub> = (1, tan(-fx / 2), tan(f<sub>y</sub> / 2))
 - v̄<sub>fov2</sub> = (1, tan(-f<sub>x</sub> / 2), tan(-f<sub>y</sub> / 2))
 - v̄<sub>fov3</sub> = (1, tan(f<sub>x</sub> / 2), tan(-f<sub>y</sub> / 2))

The angles to a specific corner will be denoted as f<sub>xn</sub> and f<sub>yn</sub> from now on, where n is the corresponding corner number.

#### 2. Rotating FOV:
Rotate each vector using rotation matrices built with c<sub>roll</sub>, c<sub>pitch</sub> and c<sub>yaw</sub> [(wiki)](https://en.wikipedia.org/wiki/Rotation_matrix#In_three_dimensions), applied in the order of zyx. If the rotation is described in the frame of the drone, apply d<sub>roll</sub>, d<sub>pitch</sub> and d<sub>yaw</sub> as well.
 - v̄<sub>rot_fov0</sub> = R<sub>zyx</sub>⋅v̄<sub>fov0</sub>
 - v̄<sub>rot_fov1</sub> = R<sub>zyx</sub>⋅v̄<sub>fov1</sub>
 - v̄<sub>rot_fov2</sub> = R<sub>zyx</sub>⋅v̄<sub>fov2</sub>
 - v̄<sub>rot_fov3</sub> = R<sub>zyx</sub>⋅v̄<sub>fov3</sub>

If ϴ > ϴ<sub>xy</sub> for all ϴ, defined by 
 ϴ = π/2 - arcos((n̄⋅v̄)/((||n̄||)(||v̄||))) 
where n̄ is the normal vector of the xy plane (0,0,1) and v̄ ∈ {v̄<sub>rot_fov0</sub>, v̄<sub>rot_fov1</sub>, v̄<sub>rot_fov2</sub>, v̄<sub>rot_fov3</sub>}, then abort (if all FOV corners are too close or above x-y plane then abort)

#### 3. FOV reduction
If ϴ > ϴ<sub>xy</sub>for one to three ϴ, defined by 
 ϴ = π/2 - arcos((n̄⋅v̄)/((||n̄||)(||v̄||))) 
where n̄ is the normal vector of the xy plane (0,0,1) and v̄ ∈ {v̄_rot_fov0, v̄<sub>rot_fov1</sub>, v̄<sub>rot_fov2</sub>, v̄<sub>rot_fov3</sub>} then the FOV is reduced.

Reduce the corner, denoted as c<sub>h</sub>from now on, with the highest ϴ's f<sub>x</sub>and f<sub>y</sub>based on its neighbouring corners denoted.
If both or neither neighbours ϴ > ϴ<sub>xy</sub>:
 Reduce the f<sub>x<sub>n</sub></sub> and f<sub>y<sub>n</sub></sub> for n = c<sub>h</sub>and the corresponding angle of the neighbours by i.

If only one neighbour ϴ > ϴ<sub>xy</sub>:
 Reduce the f<sub>x<sub>n</sub></sub> or f<sub>y<sub>n</sub></sub> corresponding to the side connecting by c<sub>h</sub>and the neighbour by i.

If f < ϴ<sub>fov</sub>for any f ∈ {f<sub>x</sub>, f<sub>y</sub>} then abort. 
Calculate new v̄<sub>rot_fov0</sub>, v̄<sub>rot_fov1</sub>, v̄<sub>rot_fov2</sub>and v̄_rot_fov3. Redo reduction until c<sub>hs</sub>ϴ ≤ ϴ<sub>xy</sub>.

##### Example of new corner vectors if both or neither neighbours ϴ > ϴ<sub>xy</sub>:
 - v̄<sub>fov0</sub>= (1, tan(f<sub>x</sub>/ 2), tan((f<sub>y</sub>/ 2) - i))
 - v̄<sub>fov1</sub>= (1, tan((-f<sub>x</sub>/ 2) - i), tan((f<sub>y</sub>/ 2) - i))
 - v̄<sub>fov2</sub>= (1, tan((-f<sub>x</sub>/ 2) - i), tan(-f<sub>y</sub>/ 2))
 - v̄<sub>fov3</sub>= (1, tan(f<sub>x</sub>/ 2), tan(-f<sub>y</sub>/ 2))

##### Example of new corner vectors if one of the neighbours ϴ > ϴ<sub>xy</sub>:
 - v̄<sub>fov0</sub>= (1, tan(f<sub>x</sub>/ 2), tan((f<sub>y</sub>/ 2) - i))
 - v̄<sub>fov1</sub>= (1, tan(-f<sub>x</sub>/ 2), tan((f<sub>y</sub>/ 2) - i))
 - v̄<sub>fov2</sub>= (1, tan(-f<sub>x</sub>/ 2), tan(-f<sub>y</sub>/ 2))
 - v̄<sub>fov3</sub>= (1, tan(f<sub>x</sub>/ 2), tan(-f<sub>y</sub>/ 2))

#### Calculate the intersection between FOV vectors and the x-y plane
Calculate the ratio between the altitude of the drone and the z component of each FOV vector and multiply the vector by it, add the drone height to calculate the meter offset from the drone's position to each corner, denoted as o<sub>c<sub>n</sub></sub> where n corresponds to the corner number.

A = d<sub>alt</sub>/-v̄<sub>rot_fov0<sub>z</sub></sub> 
 o<sub>c<sub>0</sub></sub> = v̄<sub>rot_fov0</sub>⋅A + (0, 0, d<sub>alt</sub>)

#### Use offset of corner and drone coordinates to calculate new coordinates
Uses library pyproj's function geod.fwd and World Geodetic System 84. For further reading see: https://pyproj4.github.io/pyproj/stable/api/geod.html

#### Calculate frame size and corner offset
Calculate the proportional offset of the FOV using the original f<sub>x</sub>and f</sub>y</sub>compared to the reduced f<sub>x</sub>/2 and f<sub>y</sub>/2 of each corner, denoted from now on as f<sub>r<sub>x<sub>n</sub></sub></sub> and f<sub>r<sub>y<sub>n</sub></sub></sub> where n corresponds to the corner number.
 Convert the angles to length, using distance from the lens of 1 for ease. 
 X offset for corner 0 denoted from now on as o<sub>x<sub>0</sub></sub>.
 Example:
 - o<sub>x<sub>0</sub></sub> = |tan(f<sub>x<sub>0</sub></sub>) - tan(f<sub>r<sub>x<sub>0</sub></sub></sub>)|/(2⋅|tan(f<sub>x<sub>0</sub></sub>)|)
 - o<sub>y<sub>0</sub></sub> = |tan(f<sub>y<sub>0</sub></sub>) - tan(f<sub>r<sub>y<sub>0</sub></sub></sub>)|/(2⋅|tan(f<sub>y<sub>0</sub></sub>)|)

Calculate the proportional size of the reduced FOV based on the offset of corners 0, 1 and 3, denoted as f<sub>s<sub>x</sub></sub> and f<sub>s<sub>y</sub></sub>:
 - f<sub>s<sub>x</sub></sub> = 1 - o<sub>x<sub>1</sub></sub> - o<sub>x<sub>0</sub></sub>
 - f<sub>s<sub>y</sub></sub> = 1 - o<sub>y<sub>3</sub></sub> - o<sub>y<sub>0</sub></sub> 
