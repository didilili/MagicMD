const containsChinese = (value) => /[\u3400-\u9fff]/u.test(value ?? '');

module.exports = {
  extends: ['@commitlint/config-conventional'],
  defaultIgnores: false,
  plugins: [
    {
      rules: {
        'subject-contains-chinese': ({ subject }) => [
          containsChinese(subject),
          '提交主题必须包含中文'
        ],
        'body-contains-chinese': ({ body }) => [
          containsChinese(body),
          '提交正文不能为空且必须包含中文'
        ]
      }
    }
  ],
  rules: {
    'body-empty': [2, 'never'],
    'body-leading-blank': [2, 'always'],
    'subject-contains-chinese': [2, 'always'],
    'body-contains-chinese': [2, 'always']
  }
};
