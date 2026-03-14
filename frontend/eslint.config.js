import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import eslintPluginVue from 'eslint-plugin-vue';
import eslintConfigPrettier from 'eslint-config-prettier';
import globals from 'globals';

export default tseslint.config(
  // 1. Ignore build output and node_modules
  {
    ignores: ['node_modules/', 
              'dist/', 
              'build/', 
              '.output/',
              'src/schema/server_types.ts',
              '.eslintrc.cjs'],
  },
  
  // 2. Base JavaScript rules
  eslint.configs.recommended,
  
  // 3. TypeScript rules
  ...tseslint.configs.recommended,
  
  // 4. Vue rules
  ...eslintPluginVue.configs['flat/recommended'],
  
  // 5. Parse TypeScript inside Vue components
  {
    files: ['**/*.{js,ts,vue}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node
      },
      parserOptions: {
        parser: tseslint.parser,
      },
    },
    rules: {
      // Turn off the multi-word component requirement
      'vue/multi-word-component-names': 'off',
      // Optional: Turn off the strict empty object warning for your types
      '@typescript-eslint/no-empty-object-type': 'off'
    }
  },
  
  // 6. Turn off ESLint formatting rules so Prettier can handle them
  eslintConfigPrettier
);