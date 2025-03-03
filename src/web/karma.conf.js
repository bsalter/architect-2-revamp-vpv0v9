// Karma configuration file, see link for more information
// https://karma-runner.github.io/1.0/config/configuration-file.html

module.exports = function (config) {
  config.set({
    // base path that will be used to resolve all patterns (eg. files, exclude)
    basePath: '',

    // frameworks to use
    // available frameworks: https://www.npmjs.com/search?q=keywords:karma-adapter
    frameworks: ['jasmine', '@angular-devkit/build-angular'],

    // list of files / patterns to load in the browser
    files: [
      // The test.ts file serves as entry point for all our tests
    ],

    // plugins required for running the karma tests
    plugins: [
      require('karma-jasmine'), // karma-jasmine ^5.1.0
      require('karma-chrome-launcher'), // karma-chrome-launcher ^3.2.0
      require('karma-firefox-launcher'), // karma-firefox-launcher ^2.1.2
      require('karma-jasmine-html-reporter'), // karma-jasmine-html-reporter ^2.1.0
      require('karma-coverage'), // karma-coverage ^2.2.1
      require('karma-junit-reporter'), // karma-junit-reporter ^2.0.1
      require('@angular-devkit/build-angular/plugins/karma') // @angular-devkit/build-angular ^16.2.0
    ],

    // client configuration
    client: {
      clearContext: false, // leave Jasmine Spec Runner output visible in browser
      jasmine: {
        // Jasmine configuration options
        random: true,
        failFast: false,
        timeoutInterval: 30000
      }
    },

    // list of files / patterns to exclude
    exclude: [],

    // preprocess matching files before serving them to the browser
    // available preprocessors: https://www.npmjs.com/search?q=keywords:karma-preprocessor
    preprocessors: {},

    // test results reporter to use
    // possible values: 'dots', 'progress'
    // available reporters: https://www.npmjs.com/search?q=keywords:karma-reporter
    reporters: ['progress', 'kjhtml', 'coverage', 'junit'],

    junitReporter: {
      outputFile: 'test-results.xml',
      useBrowserName: false
    },

    // web server port
    port: 9876,

    // enable / disable colors in the output (reporters and logs)
    colors: true,

    // level of logging
    // possible values: config.LOG_DISABLE || config.LOG_ERROR || config.LOG_WARN || config.LOG_INFO || config.LOG_DEBUG
    logLevel: config.LOG_INFO,

    // enable / disable watching file and executing tests whenever any file changes
    autoWatch: true,

    // start these browsers
    // available browser launchers: https://www.npmjs.com/search?q=keywords:karma-launcher
    browsers: ['Chrome', 'ChromeHeadless', 'Firefox'],

    // Custom launcher for CI environments
    customLaunchers: {
      ChromeHeadlessCI: {
        base: 'ChromeHeadless',
        flags: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage']
      }
    },

    // Continuous Integration mode
    // if true, Karma captures browsers, runs the tests and exits
    singleRun: false,

    // Concurrency level
    // how many browser instances should be started simultaneously
    concurrency: Infinity,

    // Coverage reporter configuration
    coverageReporter: {
      dir: 'coverage',
      reporters: [
        { type: 'html', subdir: 'html' },
        { type: 'lcov', subdir: 'lcov' },
        { type: 'text-summary' }
      ],
      // enforce minimum coverage thresholds
      check: {
        global: {
          statements: 85,
          lines: 85,
          branches: 75,
          functions: 90
        }
      }
    },

    // Performance tuning settings for browser disconnect issues
    browserDisconnectTimeout: 10000,
    browserDisconnectTolerance: 3,
    browserNoActivityTimeout: 60000,
    captureTimeout: 120000,

    // Use webpack for processing files
    // This setting allows TypeScript files to be processed correctly
    webpack: {
      mode: 'development',
      devtool: 'inline-source-map'
    },

    // Disable webpack's file watching feature for Karma's auto-watch feature
    webpackMiddleware: {
      stats: 'errors-only'
    },

    // Fail on empty test suites
    failOnEmptyTestSuite: true,

    // Explicitly set up the Angular devkit to use the tsconfig.spec.json file
    ngHmr: false,
    angularCli: {
      environment: 'dev',
      codeCoverage: true,
      sourcemaps: true,
      tsConfig: './tsconfig.spec.json'
    }
  });

  // Setup for CI environments
  if (process.env.CI) {
    config.set({
      browsers: ['ChromeHeadlessCI'],
      autoWatch: false,
      singleRun: true,
      reporters: ['junit', 'coverage'],
      // Adjust settings for CI environment
      client: {
        jasmine: {
          random: false // Disable random test order in CI for reproducible builds
        }
      }
    });
  }
};