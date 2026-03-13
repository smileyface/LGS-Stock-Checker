import eslint from '@eslint/js';
import tseslint from 'typescript-eslint';
import eslintPluginVue from 'eslint-plugin-vue';
import eslintConfigPrettier from 'eslint-config-prettier';

export default tseslint.config(
  // 1. Ignore build output and node_modules
  {
    ignores: ['node_modules/', 'dist/', 'build/', '.output/'],
  },
  
  // 2. Base JavaScript rules
  eslint.configs.recommended,
  
  // 3. TypeScript rules
  ...tseslint.configs.recommended,
  
  // 4. Vue rules
  ...eslintPluginVue.configs['flat/recommended'],
  
  // 5. Parse TypeScript inside Vue components
  {
    files: ['*.vue', '**/*.vue'],
    languageOptions: {
      parserOptions: {
        parser: tseslint.parser,
      },
    },
  },
  
  // 6. Turn off ESLint formatting rules so Prettier can handle them
  eslintConfigPrettier
);