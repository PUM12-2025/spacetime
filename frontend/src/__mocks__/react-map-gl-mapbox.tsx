// __mocks__/react-map-gl-mapbox.ts
import React from 'react';

const Map = ({ children }: { children?: React.ReactNode }) => <div data-testid="mock-map">{children}</div>;

const Source = ({ children }: { children?: React.ReactNode }) => <div data-testid="mock-source">{children}</div>;
const Layer = () => <div data-testid="mock-layer" />;
type LayerProps = Record<string, unknown>;

export type { Source, Layer, LayerProps };
export default Map;