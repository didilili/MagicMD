module.exports = {
  plugins: ['prettier-plugin-toml'],
  printWidth: 100,
  singleQuote: true,
  trailingComma: 'none',
  overrides: [
    {
      files: ['*.json', '*.md', '*.toml'],
      options: {
        singleQuote: false
      }
    }
  ]
};
