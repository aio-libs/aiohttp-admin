module.exports = {
  clearMocks: true,
  collectCoverageFrom: ["src/**", "tests/**"],
  errorOnDeprecated: true,
  maxWorkers: 1,
  resetMocks: true,
  restoreMocks: true,
  setupFilesAfterEnv: ["<rootDir>/tests/setupTests.js"],
  testEnvironment: "jsdom",
  testEnvironmentOptions: {"url": "http://localhost:8080", "pretendToBeVisual": true},
  verbose: true,

  globals: {
    "ts-jest": {
       isolatedModules: true
    }
  }
};
