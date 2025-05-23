import Map, { Source, Layer, LayerProps } from "react-map-gl/mapbox";
import "mapbox-gl/dist/mapbox-gl.css";
import {
  ChangeEvent,
  SetStateAction,
  useEffect,
  useRef,
  useState,
} from "react";
import "./App.css";
import DronePoint from "./components/DronePoint";

/**
 * An imageSourceItem is a single frame of the projected video flow.
 * It is used to draw the traced trail.
 */
interface ImageSourceItem {
  id: string;
  url: string;
  coordinates: [
    [number, number],
    [number, number],
    [number, number],
    [number, number]
  ]; // Top-left, top-right, bottom-right, bottom-left
}

/**
 * Layer for the ImageSourceItems.
 */
const rasterLayer = (id: string): LayerProps => ({
  id: `raster-${id}`,
  type: "raster",
  source: id,
  paint: { "raster-fade-duration": 0 },
  beforeId: "projLayer",
});

function App() {
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const [coords, setCoords] = useState<
    [[number, number], [number, number], [number, number], [number, number]]
  >([
    [13, 58],
    [14.5, 58],
    [14.5, 57],
    [13, 57],
  ]);

  /**
   * GeoJSON polygon used for drawing the outline for the projection.
   */
  const polygon: GeoJSON.Feature<GeoJSON.Polygon> = {
    type: "Feature",
    properties: {},
    geometry: {
      type: "Polygon",
      coordinates: [[...coords, coords[0]]],
    },
  };

  /**
   * Layer for projection outline.
   */
  const polyStyle: mapboxgl.Layer = {
    id: "polygon-layer",
    type: "line",
    paint: {
      "line-color": "red",
      "line-width": 3,
    },
  };

  /**
   * Drone position and rotation
   */
  const [dronePos, setDronePos] = useState<{
    lng: number;
    lat: number;
    yaw: number;
  }>({ lng: 11.77, lat: 57.5, yaw: 0 });

  /**
   * Map view state.
   * Used for following the drone automatically.
   */
  const [viewState, setViewState] = useState({
    longitude: 11.781,
    latitude: 57.66,
    zoom: 12,
  });

  /**
   * Array for projection trail.
   * Gets mapped to JSX.
   */
  const [sources, setSources] = useState<ImageSourceItem[]>([]);

  /**
   * Data about how the video should be drawn onto the canvas.
   * Contains offsets and scalars for both x and y.
   */
  const [frameData, setFrameData] = useState<{
    x: number;
    y: number;
    w: number;
    h: number;
  }>({ x: 0, y: 0, w: 1, h: 1 });

  const [running, setRunning] = useState(false);

  const [tracing, setTracing] = useState(false);

  const [tracking, setTracking] = useState(false);

  const latestCoordsRef = useRef(coords);

  const latestFrameDataRef = useRef(frameData);

  const projectingRef = useRef(false);

  const trackingRef = useRef(false);

  const zoomRef = useRef(8);

  useEffect(() => {
    latestFrameDataRef.current = frameData;
  }, [frameData]);


  useEffect(() => {
    latestCoordsRef.current = coords;
  }, [coords]);

  useEffect(() => {
    zoomRef.current = viewState.zoom;
  }, [viewState]);

  useEffect(() => {
    trackingRef.current = tracking;
  }, [tracking]);

  /**
   * Asks the client to select a window, screen or app to capture.
   * Used to get the MAVCesium video to the frontend.
   */
  async function getVideo() {
    try {
      const stream = await navigator.mediaDevices.getDisplayMedia({
        video: true,
      });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (error) {
      console.error("Error accessing webcam", error);
    }
  }

  /**
   * Initialises the canvas that is drawn onto the Mapbox map.
   * Uses frame data from the backend to transform the image.
   */
  useEffect(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");

    if (video && canvas && context) {
      const drawFrame = () => {
        const fData = latestFrameDataRef.current;

        if (video.readyState === video.HAVE_ENOUGH_DATA && fData) {
          canvas.width = video.videoWidth * fData.w;
          canvas.height = video.videoHeight * fData.h;

          context.drawImage(
            video,
            fData.x * video.videoWidth,
            video.videoHeight * fData.y,
            canvas.width,
            canvas.height,
            0,
            0,
            canvas.width,
            canvas.height
          );
        }
        requestAnimationFrame(drawFrame);
      };
      drawFrame();
    }
  }, []);

  /**
   * Takes a snapshot of the projected video and saves it to sources along
   * with the current coordinates and an ID for later use.
   * Limits amount of concurrent sources to 30 to save memory and data getting old.
   */
  const snapVid = () => {
    const canvas = canvasRef.current;
    const context = canvas?.getContext("2d");

    if (canvas && context) {
      const imageDataUrl = canvas.toDataURL("image/png");
      const newimgsrc: ImageSourceItem = {
        id: `source-${Date.now()}`,
        coordinates: latestCoordsRef.current,
        url: imageDataUrl,
      };
      setSources((sources) => {
        const newSources = [...sources, newimgsrc];
        if (newSources.length > 30) {
          return newSources.slice(1);
        }
        return newSources;
      });
    }
  };

  /**
   * Toggles an interval to save projections with snapvid.
   */
  useEffect(() => {
    if (!tracing) return;
    const intervalId = setInterval(() => {
      snapVid();
    }, 3000);

    return () => clearInterval(intervalId);
  }, [tracing]);

  /**
   * Opens a websocket to connect to the backend sniffer.
   * Updates telemetry and the map view if following is toggled.
   */
  useEffect(() => {
    const socket = new WebSocket("ws://localhost:8777");

    socket.onmessage = (event) => {
      const json = JSON.parse(event.data);
      projectingRef.current = json.has_projection;

      setDronePos({ lng: json.lon, lat: json.lat, yaw: json.yaw });

      if (trackingRef.current) {
        setViewState({
          longitude: json.lon,
          latitude: json.lat,
          zoom: zoomRef.current,
        });
      }

      if (projectingRef.current) {
        const corners: [
          [number, number],
          [number, number],
          [number, number],
          [number, number]
        ] = [
          [json.corner1.lon, json.corner1.lat],
          [json.corner0.lon, json.corner0.lat],
          [json.corner3.lon, json.corner3.lat],
          [json.corner2.lon, json.corner2.lat],
        ];

        setCoords(corners);
        setFrameData({
          x: json.corner1.offset.x,
          y: json.corner1.offset.y,
          w: json.frame_size.w,
          h: json.frame_size.h,
        });
      }
    };
  }, []);


  const handleRunningToggle = (e: ChangeEvent<HTMLInputElement>) => {
    setRunning(e.target.checked);
  };

  const handleTrailToggle = (e: ChangeEvent<HTMLInputElement>) => {
    setTracing(e.target.checked);
  };

  const handleTrackToggle = (e: ChangeEvent<HTMLInputElement>) => {
    setTracking(e.target.checked);
  };


  /**
   * JSX for the application.
   * It contains 2 main components: btncontainer and the Mapbox map.
   * 
   * btncontainer holds buttons for user interaction.
   * 
   * The Mapbox map has the interactive map along with the projected video,
   * an outline for the projection, the traced video trail as well as a drone icon.
   * 
   * The projected video and the trail both make use of CanvasSource    
   * from Mapbox GL JS to be drawn on the map.
   * 
   * The outline is drawn as a GeoJSON polygon. 
   * 
   * The drone icon is a rotating mapbox marker.
   */
  return (
    <div className="mapcontainer">
      <video ref={videoRef} autoPlay hidden></video>
      <canvas id="vidCanvas" ref={canvasRef} hidden></canvas>

      <div className="btnContainer">
        <button onClick={getVideo}>getVideo</button>
      </div>

      <div className="uidiv">
        <label className="atoggle">
          <input
            type="checkbox"
            checked={running}
            onChange={(e) => handleRunningToggle(e)}
          ></input>
          <span className="togglestyle">RUN</span>
        </label>
        <label className="atoggle">
          <input
            type="checkbox"
            checked={tracing}
            onChange={(e) => handleTrailToggle(e)}
          ></input>
          <span className="togglestyle">TRACE</span>
        </label>
        <label className="atoggle">
          <input
            type="checkbox"
            checked={tracking}
            onChange={(e) => handleTrackToggle(e)}
          ></input>
          <span className="togglestyle">FOLLOW</span>
        </label>
      </div>

      <Map
        mapboxAccessToken="YOUR ACCESS TOKEN"
        {...viewState}
        onMove={(evt: {
          viewState: SetStateAction<{
            longitude: number;
            latitude: number;
            zoom: number;
          }>;
        }) => {
          setViewState(evt.viewState);
          setTracking(false);
        }}
        style={{ width: "100%", height: "100%" }}
        mapStyle="mapbox://styles/fredrikfalkman/clr0p93p5018401o94gvydtuw"
      >
        {running && projectingRef.current ? (
          <>
            <Source
              id="projCanvas"
              type="canvas"
              canvas="vidCanvas"
              coordinates={coords}
              animate
            >
              <Layer
                id="projLayer"
                type="raster"
                source="projCanvas"
                paint={{ "raster-fade-duration": 0 }}
                beforeId="polygon-layer"
              />
            </Source>

            <Source id="polygon" type="geojson" data={polygon}>
              <Layer {...(polyStyle as any)} />
            </Source>

            {sources.map((source) => (
              <Source
                key={source.id}
                id={source.id}
                type="image"
                url={source.url}
                coordinates={source.coordinates}
              >
                <Layer {...rasterLayer(source.id)} />
              </Source>
            ))}
          </>
        ) : null}

        <DronePoint coords={dronePos} />
      </Map>
    </div>
  );
}

export default App;
