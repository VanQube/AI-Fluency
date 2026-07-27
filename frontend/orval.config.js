// Points at the backend's live /openapi.json (Section 4.8). Generated output
// is TypeScript (Orval requirement) even though the rest of this frontend is
// plain JS — see README for why. Re-run via `npm run generate:api` whenever
// the backend's routes/schemas change.
module.exports = {
  secureship: {
    input: {
      target: process.env.REACT_APP_API_BASE_URL
        ? `${process.env.REACT_APP_API_BASE_URL}/openapi.json`
        : 'http://localhost:8000/openapi.json',
    },
    output: {
      mode: 'single',
      target: 'src/api/generated/secureship.ts',
      client: 'react-query',
      baseUrl: 'http://localhost:8000',
    },
  },
};
