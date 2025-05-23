import { Marker } from "react-map-gl/mapbox";

function DronePoint({
  coords,
}: {
  coords: { lng: number; lat: number; yaw: number };
}) {
  const yawToDeg = (coords.yaw * 180) / Math.PI;

  return (
    <>
      <Marker longitude={coords.lng} latitude={coords.lat} anchor="center">
        <img
          src="Images/dronefilled.png"
          style={{
            width: "60px",
            height: "60px",
            transformOrigin: "center center",
            transform: `rotate(${yawToDeg}deg)`,
            position: "relative",
          }}
        />
      </Marker>
    </>
  );
}
export default DronePoint;
