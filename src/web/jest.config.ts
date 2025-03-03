import type { JestConfigWithTsJest } from 'jest-preset-angular/build/types'; // jest-preset-angular@13.1.1

const jestConfig: JestConfigWithTsJest = {
  // Use the jest-preset-angular preset which includes necessary configurations for Angular
  preset: 'jest-preset-angular',
  
  // Specify the test environment
  testEnvironment: 'jsdom',
  
  // Setup files to run after the Jest environment is set up
  setupFilesAfterEnv: ['<rootDir>/src/setup-jest.ts'],
  
  // Map module paths to their locations
  moduleNameMapper: {
    '^@app/(.*)$': '<rootDir>/src/app/$1',
    '^@environments/(.*)$': '<rootDir>/src/environments/$1',
    '^@shared/(.*)$': '<rootDir>/src/app/shared/$1',
    '^@core/(.*)$': '<rootDir>/src/app/core/$1',
    '^@services/(.*)$': '<rootDir>/src/app/services/$1',
    '^@models/(.*)$': '<rootDir>/src/app/models/$1',
    '^@utils/(.*)$': '<rootDir>/src/app/utils/$1'
  },
  
  // Specify file extensions to be treated as modules
  moduleFileExtensions: ['ts', 'html', 'js', 'json', 'mjs'],
  
  // Transform files with TypeScript
  transform: {
    '^.+\\.(ts|js|mjs|html|svg)$': [
      'jest-preset-angular',
      {
        tsconfig: '<rootDir>/tsconfig.spec.json',
        stringifyContentPathRegex: '\\.(html|svg)$',
        isolatedModules: true
      }
    ]
  },
  
  // Don't transform node_modules except for specific packages if needed
  transformIgnorePatterns: [
    'node_modules/(?!(@angular|rxjs|date-fns)/)'
  ],
  
  // Paths to ignore for testing
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/dist/',
    '<rootDir>/e2e/',
    '<rootDir>/src/test.ts'
  ],
  
  // Enable coverage collection
  collectCoverage: true,
  
  // Specify where to output coverage reports
  coverageDirectory: '<rootDir>/coverage/jest',
  
  // Coverage report formats
  coverageReporters: ['json', 'lcov', 'text', 'clover', 'html'],
  
  // Set threshold requirements per the specifications
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 95,
      lines: 85,
      statements: 85
    },
    './src/app/services/': {
      branches: 80,
      functions: 95,
      lines: 90,
      statements: 90
    },
    './src/app/utils/': {
      branches: 80,
      functions: 95,
      lines: 90,
      statements: 90
    }
  },
  
  // Global configuration for tests
  globals: {
    'ts-jest': {
      tsconfig: '<rootDir>/tsconfig.spec.json',
      stringifyContentPathRegex: '\\.(html|svg)$',
      isolatedModules: true
    }
  }
};

export default jestConfig;