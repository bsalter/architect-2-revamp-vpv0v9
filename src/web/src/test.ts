// This file is required by karma.conf.js and loads recursively all the .spec and framework files

import 'zone.js/testing';
import { getTestBed } from '@angular/core/testing'; // @angular/core/testing ^15.0.0
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting
} from '@angular/platform-browser-dynamic/testing'; // @angular/platform-browser-dynamic/testing ^15.0.0

// First, initialize the Angular testing environment.
function initTestEnvironment() {
  getTestBed().initTestEnvironment(
    BrowserDynamicTestingModule,
    platformBrowserDynamicTesting(),
  );
}

// Declaration for CommonJS require function used to load test files
declare const require: {
  context(path: string, deep?: boolean, filter?: RegExp): {
    <T>(id: string): T;
    keys(): string[];
  };
};

// Declaration for Karma test runner global object
declare const __karma__: {
  loaded: () => void;
  start: () => void;
};

// Initialize the testing environment
initTestEnvironment();

// Configure jasmine environment with testing options
jasmine.getEnv().configure({
  random: true,
  failFast: false,
  oneFailurePerSpec: false,
  hideDisabled: false
});

// Find all test files using require.context
// This loads all files in the application matching the .spec.ts pattern recursively
const context = require.context('./', true, /\.spec\.ts$/);

// Load each test module
context.keys().forEach(context);

// Configure Karma callbacks
// Called when all tests are loaded
__karma__.loaded = function () {};
// Called to start the test execution
__karma__.start();