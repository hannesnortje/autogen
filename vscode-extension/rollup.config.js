const { nodeResolve } = require('@rollup/plugin-node-resolve');
const typescript = require('@rollup/plugin-typescript');

module.exports = {
  input: 'src/webview/dashboard-app.ts',
  output: {
    file: 'out/webview/dashboard-bundle.js',
    format: 'iife',
    name: 'AutoGenDashboard',
    sourcemap: true
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
    warn(warning);
  }
};
