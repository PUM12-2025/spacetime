export const Map = jest.fn(() => ({
    on: jest.fn(),
    remove: jest.fn(),
    getCanvas: jest.fn(() => ({
      style: {}
    })),
    resize: jest.fn(),
  }));
  
  const mapboxgl = {
    Map,
    NavigationControl: jest.fn(),
    Marker: jest.fn(() => ({
      setLngLat: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
      remove: jest.fn().mockReturnThis(),
    })),
    Popup: jest.fn(() => ({
      setLngLat: jest.fn().mockReturnThis(),
      setHTML: jest.fn().mockReturnThis(),
      addTo: jest.fn().mockReturnThis(),
    })),
    AttributionControl: jest.fn(),
    supported: jest.fn(() => true),
    accessToken: '',
  };
  
  export default mapboxgl;
  