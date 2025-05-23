import type { Config } from 'jest';

const config: Config = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
  globals: {
    'ts-jest': {
      tsconfig: 'tsconfig.app.json', // <-- Explicitly use this
    },
  },
  moduleNameMapper: {
    '^react-map-gl/mapbox$': '<rootDir>/src/__mocks__/react-map-gl-mapbox.tsx',
    '^mapbox-gl$': '<rootDir>/src/__mocks__/mapbox-gl.ts',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy'
  },
  
  transform: {
  '^.+\\.(ts|tsx)$': ['ts-jest', {
    tsconfig: './tsconfig.app.json',
  }],
},
};

export default config;