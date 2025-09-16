const { nodeResolve } = require('@rollup/plugin-node-resolve');
const typescript = require('@rollup/plugin-typescript');

module.exports = {
  input: 'src/webview/panels/dashboard.ts',
  output: {
    file: 'out/webview/dashboard.js',
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
    warn(warning);
  }
};
