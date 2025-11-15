module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true, // Added node for configuration file itself
  },
  extends: [
    'eslint:recommended',
    'plugin:vue/vue3-essential', // Use Vue 3 rules
  ],
  parserOptions: {
    ecmaVersion: 'latest',
    sourceType: 'module',
  },
  plugins: [
    'vue', // Tell ESLint to use the Vue plugin
  ],
  rules: {
    // You can add your own custom rules here later
    'vue/multi-word-component-names': 'off', // Disables the rule requiring multi-word component names
  },
};