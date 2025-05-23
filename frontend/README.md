# Spacetime Frontend

The frontend is a web application built with React.


The application uses [Mapbox](https://www.mapbox.com/) as a map library and requires a personal API key to access their maps.
Remember to update it in `src/App.tsx`

## Install the frontend

All the setup instructions assume that you are in the `frontend` directory.

### Prerequisites

- `Node.js v20` - The best way to install Node is by using
  [nvm](https://github.com/nvm-sh/nvm) (linux) or [nvm-windows](https://github.com/coreybutler/nvm-windows) (windows).

  Navigate to the frontend repository with `cd frontend` and install all
dependencies with

```bash
npm install
```

## Running the frontend

- `npm run dev` to start a hot-reloading development server.
- `npm run build` to build the project.
- `npm run test` to run the frontend tests

## Guide
In the frontend you'll find three buttons:

- `RUN` starts the projection, shows only the outline if there is so video available
- `TRACE` starts tracing the projection to the map
- `FOLLOW` puts the drone in the center of the screen and follows it