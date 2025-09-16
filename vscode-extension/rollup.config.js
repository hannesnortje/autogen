const { nodeResolve } = require('@rollup/plugin-node-resolve');
const typescript = require('@rollup/plugin-typescript');

module.exports = {
  input: 'src/webview/dashboard-app.ts',
  output: {
    file: 'out/webview/dashboard-bundle.js',
    format: 'iife',
    name: 'AutoGenDashboard',
    sourcemap: true,
    intro: `
      // Webview environment polyfills
      if (typeof globalThis === 'undefined') {
        var globalThis = this;
      }
      // Prevent service worker registration in webview
      if (typeof navigator !== 'undefined') {
        Object.defineProperty(navigator, 'serviceWorker', {
          value: undefined,
          writable: false,
          configurable: false
        });
      }
    `
  },
  plugins: [
    nodeResolve({
      browser: true,
      preferBuiltins: false
    }),
    typescript({
      tsconfig: 'src/webview/tsconfig.json',
      declaration: false,
      sourceMap: true
    })
  ],
  external: [],
  onwarn(warning, warn) {
    // Suppress certain warnings
    if (warning.code === 'THIS_IS_UNDEFINED') return;
    if (warning.code === 'CIRCULAR_DEPENDENCY') return;
    // Suppress service worker related warnings
    if (warning.message && warning.message.includes('serviceWorker')) return;
    warn(warning);
  }
};
