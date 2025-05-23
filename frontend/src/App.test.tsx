import { render, screen, fireEvent } from '@testing-library/react';
import App from './App';


jest.mock('mapbox-gl/dist/mapbox-gl', () => ({
  Map: () => ({})
}));

jest.mock('react-map-gl/mapbox', () => ({
  __esModule: true,
  default: ({ children }: any) => <div>{children}</div>, // Mocking Map
  Source: ({ children }: any) => <div>{children}</div>,
  Layer: () => <div>Mocked Layer</div>,
}));

jest.mock('./components/DronePoint', () => ({
  __esModule: true, // important if DronePoint uses export default
  default: () => <div>Mocked DronePoint</div>,
}));

test('renders App and DronePoint', () => {
  render(<App />);


  // Check if DronePoint renders
  expect(screen.getByText('Mocked DronePoint')).toBeInTheDocument();
});

test('TRACE toggle updates state', () => {
  render(<App />);
  expect(screen.getByText('TRACE')).toBeInTheDocument();
  const runCheckbox = screen.getByLabelText('TRACE') as HTMLInputElement;
  expect(runCheckbox.checked).toBe(false);
  fireEvent.click(runCheckbox);
  expect(runCheckbox.checked).toBe(true);
});


test('RUN toggle updates state', () => {
  render(<App />);
  expect(screen.getByText('RUN')).toBeInTheDocument();
  const runCheckbox = screen.getByLabelText('RUN') as HTMLInputElement;
  expect(runCheckbox.checked).toBe(false);
  fireEvent.click(runCheckbox);
  expect(runCheckbox.checked).toBe(true);
});

test('FOLLOW toggle updates state', () => {
  render(<App />);
  expect(screen.getByText('FOLLOW')).toBeInTheDocument();
  const trackingCheckbox = screen.getByLabelText('FOLLOW') as HTMLInputElement;
  expect(trackingCheckbox.checked).toBe(false);
  fireEvent.click(trackingCheckbox);
  expect(trackingCheckbox.checked).toBe(true);
});

