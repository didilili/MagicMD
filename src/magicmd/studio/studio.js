const form = document.querySelector('#studio-form');
const statusStrip = document.querySelector('#status-strip');
const emptyState = document.querySelector('#empty-state');
const loadingState = document.querySelector('#loading-state');
const loadingTitle = document.querySelector('#loading-title');
const loadingDetail = document.querySelector('#loading-detail');
const resultOutput = document.querySelector('#result-output');
const publishPlanButton = document.querySelector('#publish-plan-button');
const convertButton = document.querySelector('#convert-button');
const saveConfigButton = document.querySelector('#save-config-button');
const singleModeButton = document.querySelector('#single-mode-button');
const batchModeButton = document.querySelector('#batch-mode-button');
const singleUrlField = document.querySelector('#single-url-field');
const batchUrlField = document.querySelector('#batch-url-field');
const studioToken = window.MAGICMD_STUDIO_TOKEN || '';

const state = {
  busy: false,
  mode: 'single'
};

const byteFormatter = new Intl.NumberFormat(navigator.language || 'zh-CN');

const presetDefaults = {
  default: {
    markdown: 'article.md',
    frontMatter: 'yaml',
    sourceBlock: true,
    coverImage: true,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  plain: {
    markdown: 'article.md',
    frontMatter: 'none',
    sourceBlock: false,
    coverImage: false,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  hugo: {
    markdown: 'index.md',
    frontMatter: 'yaml',
    sourceBlock: true,
    coverImage: true,
    imagePath: '{directory}/{filename}',
    videoPath: '{directory}/{filename}'
  },
  docusaurus: {
    markdown: 'index.md',
    frontMatter: 'yaml',
    sourceBlock: false,
    coverImage: true,
    imagePath: './{directory}/{filename}',
    videoPath: './{directory}/{filename}'
  }
};

function byId(id) {
  return document.querySelector(`#${id}`);
}

function valueOf(id) {
  return byId(id).value.trim();
}

function checked(id) {
  return byId(id).checked;
}

function setValue(id, value) {
  if (value !== undefined && value !== null) {
    byId(id).value = String(value);
  }
}

function setChecked(id, value) {
  if (value !== undefined && value !== null) {
    byId(id).checked = Boolean(value);
  }
}

function readForm() {
  return {
    url: valueOf('article-url'),
    batchText: byId('batch-urls').value.trim(),
    output: valueOf('output-dir') || 'output',
    config: valueOf('config-path'),
    configText: buildConfigText(),
    downloadImages: checked('download-images'),
    docx: checked('docx'),
    openFolder: checked('open-folder-toggle')
  };
}

function quoteToml(value) {
  return JSON.stringify(String(value ?? ''));
}

function buildConfigText() {
  const publishBlock = checked('publish-enabled')
    ? `
[publish.github]
repo = ${quoteToml(valueOf('publish-repo'))}
target_dir = ${quoteToml(valueOf('publish-target-dir'))}
branch = ${quoteToml(valueOf('publish-branch'))}
commit_message = ${quoteToml(valueOf('publish-commit-message'))}
create_pr = ${checked('publish-create-pr')}
overwrite = ${checked('publish-overwrite')}
`
    : '';

  return `[output]
directory = ${quoteToml(valueOf('output-dir') || 'output')}

[output.naming]
package = ${quoteToml(valueOf('config-package'))}
markdown = ${quoteToml(valueOf('config-markdown'))}
metadata = ${quoteToml(valueOf('config-metadata'))}
report = ${quoteToml(valueOf('config-report'))}
docx = "article.docx"

[ui]
language = ${quoteToml(valueOf('config-language'))}
${publishBlock}
[markdown]
preset = ${quoteToml(valueOf('config-preset'))}
front_matter = ${quoteToml(valueOf('config-front-matter'))}
include_title = true
include_source_block = ${checked('config-source-block')}
include_cover_image = ${checked('config-cover-image')}
heading_offset = ${Number(valueOf('config-heading-offset') || 0)}

[images]
download = ${checked('download-images')}
directory = "images"
filename_pattern = "img_{index:03d}.{ext}"
markdown_path = ${quoteToml(valueOf('config-image-path'))}

[videos]
download = ${checked('config-download-videos')}
directory = "videos"
filename_pattern = "video_{index:03d}.{ext}"
markdown_path = ${quoteToml(valueOf('config-video-path'))}

[docx]
enabled = ${checked('docx')}
pandoc_path = "pandoc"
reference_doc = ""
`;
}

async function fetchJson(url, options = {}, settings = {}) {
  const response = await fetch(url, options);
  const contentType = response.headers.get('Content-Type') || '';
  const payload = contentType.includes('application/json')
    ? await response.json()
    : { error: await response.text() };
  if (!response.ok || (!settings.allowFalseOk && payload.ok === false)) {
    const error = new Error(payload.error || `请求失败：${response.status}`);
    error.status = response.status;
    error.url = url;
    throw error;
  }
  return payload;
}

async function postJson(url, payload, settings = {}) {
  return fetchJson(
    url,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-MagicMD-Studio-Token': studioToken
      },
      body: JSON.stringify(payload)
    },
    settings
  );
}

async function loadStatus() {
  try {
    const status = await fetchJson('/api/status');
    const configText = status.config.exists ? '已找到 .magicmd.toml' : '未找到配置文件';
    const tokenText = status.github.tokenConfigured ? 'GitHub token 已就绪' : '仅可预览发布';
    statusStrip.innerHTML = `<span>${configText}</span><span>${tokenText}</span>`;
    try {
      const configPayload = await fetchJson('/api/config');
      applyConfig(configPayload.config);
    } catch (error) {
      if (isEndpointMissing(error)) {
        statusStrip.innerHTML = `
          <span>Studio 后端需要重启</span>
          <span>请在终端按 Ctrl+C 后重新运行 uv run magicmd studio</span>
        `;
        return;
      }
      throw error;
    }
  } catch (error) {
    statusStrip.textContent = error.message;
  }
}

function isEndpointMissing(error) {
  return error?.status === 404 && /not found/i.test(error.message || '');
}

function backendRestartHint() {
  return '当前浏览器已经加载新版 Studio 前端，但本地端口上还是旧版后端。请在启动 Studio 的终端按 Ctrl+C，然后重新运行 uv run magicmd studio。';
}

function applyConfig(config) {
  if (!config) return;
  setValue('output-dir', config.output?.directory);
  setValue('config-package', config.output?.naming?.package);
  setValue('config-markdown', config.output?.naming?.markdown);
  setValue('config-metadata', config.output?.naming?.metadata);
  setValue('config-report', config.output?.naming?.report);
  setValue('config-language', config.ui?.language);
  setValue('config-preset', config.markdown?.preset);
  setValue('config-front-matter', config.markdown?.front_matter);
  setValue('config-heading-offset', config.markdown?.heading_offset);
  setChecked('config-source-block', config.markdown?.include_source_block);
  setChecked('config-cover-image', config.markdown?.include_cover_image);
  setChecked('download-images', config.images?.download);
  setValue('config-image-path', config.images?.markdown_path);
  setChecked('config-download-videos', config.videos?.download);
  setValue('config-video-path', config.videos?.markdown_path);
  setChecked('docx', config.docx?.enabled);

  const github = config.publish?.github;
  if (github) {
    setValue('publish-repo', github.repo || 'owner/content');
    setValue('publish-target-dir', github.target_dir || 'content/posts');
    setValue('publish-branch', github.branch);
    setValue('publish-commit-message', github.commit_message);
    setChecked('publish-create-pr', github.create_pr);
    setChecked('publish-overwrite', github.overwrite);
    setChecked('publish-enabled', Boolean(github.repo || github.target_dir));
  }
}

function applyPresetDefaults() {
  const defaults = presetDefaults[valueOf('config-preset')];
  if (!defaults) return;
  setValue('config-markdown', defaults.markdown);
  setValue('config-front-matter', defaults.frontMatter);
  setChecked('config-source-block', defaults.sourceBlock);
  setChecked('config-cover-image', defaults.coverImage);
  setValue('config-image-path', defaults.imagePath);
  setValue('config-video-path', defaults.videoPath);
}

function setMode(mode) {
  state.mode = mode;
  const isBatch = mode === 'batch';
  singleModeButton.classList.toggle('is-active', !isBatch);
  batchModeButton.classList.toggle('is-active', isBatch);
  singleUrlField.classList.toggle('is-hidden', isBatch);
  batchUrlField.classList.toggle('is-hidden', !isBatch);
  convertButton.textContent = isBatch ? '批量转换' : '转换 Markdown';
  publishPlanButton.disabled = isBatch || state.busy;
}

function setBusy(isBusy) {
  state.busy = isBusy;
  form.querySelectorAll('button, input, textarea, select').forEach((element) => {
    element.disabled = isBusy;
  });
  setMode(state.mode);
}

function showLoading(title, detail) {
  emptyState.hidden = true;
  resultOutput.hidden = true;
  loadingState.hidden = false;
  loadingTitle.textContent = title;
  loadingDetail.textContent = detail;
}

function showResult(html) {
  loadingState.hidden = true;
  emptyState.hidden = true;
  resultOutput.hidden = false;
  resultOutput.innerHTML = html;
}

function appendNotice(html) {
  resultOutput.insertAdjacentHTML('beforeend', html);
}

function escapeHtml(value) {
  return String(value ?? '')
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
}

function renderFileList(files, key = 'path') {
  if (!files?.length) {
    return '<p>没有可显示的文件。</p>';
  }
  const rows = files
    .map(
      (file) =>
        `<li>${escapeHtml(file[key])} · ${byteFormatter.format(Number(file.sizeBytes))} bytes</li>`
    )
    .join('');
  return `<ul>${rows}</ul>`;
}

function renderWarnings(warnings) {
  if (!warnings?.length) {
    return '';
  }
  const rows = warnings.map((warning) => `<li>${escapeHtml(warning)}</li>`).join('');
  return `<div class="result-block warning"><h3>需要复查</h3><ul>${rows}</ul></div>`;
}

function renderConversion(payload) {
  showResult(`
    <div class="result-block">
      <h3>${escapeHtml(payload.title)}</h3>
      <p>${escapeHtml(payload.platform)} · ${escapeHtml(payload.author || '未知作者')}</p>
      <span class="code-line">${escapeHtml(payload.packageDir || '')}</span>
      <div class="result-actions">
        <button class="secondary-action" type="button" data-open-path="${escapeHtml(payload.packageDir || '')}">
          打开输出文件夹
        </button>
      </div>
    </div>
    <div class="result-block">
      <h3>生成文件</h3>
      ${renderFileList(payload.files)}
    </div>
    ${renderWarnings(payload.warnings)}
  `);
}

function renderBatch(payload) {
  const rows = payload.items
    .map((item) => {
      if (item.ok) {
        return `<li><strong>${escapeHtml(item.title)}</strong><br><span>${escapeHtml(item.packageDir)}</span></li>`;
      }
      return `<li><strong>${escapeHtml(item.url)}</strong><br><span>${escapeHtml(item.error)}</span></li>`;
    })
    .join('');
  showResult(`
    <div class="result-block">
      <h3>批量转换完成</h3>
      <p>共 ${payload.summary.total} 条，成功 ${payload.summary.success} 条，失败 ${payload.summary.failed} 条。</p>
      <div class="result-actions">
        <button class="secondary-action" type="button" data-open-path="${escapeHtml(valueOf('output-dir') || 'output')}">
          打开输出目录
        </button>
      </div>
    </div>
    <div class="result-block">
      <h3>转换结果</h3>
      <ul>${rows}</ul>
    </div>
  `);
}

function renderPublishPlan(payload) {
  showResult(`
    <div class="result-block">
      <h3>发布计划</h3>
      <p>${escapeHtml(payload.repo)} → ${escapeHtml(payload.targetDir)}</p>
      <span class="code-line">${escapeHtml(payload.branch)}</span>
    </div>
    <div class="result-block">
      <h3>提交信息</h3>
      <p>${escapeHtml(payload.commitMessage)}</p>
    </div>
    <div class="result-block">
      <h3>将写入的文件</h3>
      ${renderFileList(payload.files, 'targetPath')}
    </div>
  `);
}

function renderError(error) {
  showResult(`
    <div class="result-block error">
      <h3>操作没有完成</h3>
      <p>${escapeHtml(error.message)}</p>
    </div>
  `);
}

async function openGeneratedPath(path) {
  if (!path) return;
  try {
    await postJson('/api/open-path', { path });
  } catch (error) {
    if (isEndpointMissing(error)) {
      if (resultOutput.querySelector('[data-runtime-warning="studio-restart"]')) {
        return;
      }
      appendNotice(`
        <div class="result-block warning" data-runtime-warning="studio-restart">
          <h3>当前 Studio 后端不支持自动打开目录</h3>
          <p>${escapeHtml(backendRestartHint())}</p>
        </div>
      `);
      return;
    }
    appendNotice(`
      <div class="result-block warning">
        <h3>无法自动打开目录</h3>
        <p>${escapeHtml(error.message)}</p>
      </div>
    `);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (state.busy) return;
  const formPayload = readForm();
  setBusy(true);
  try {
    if (state.mode === 'batch') {
      showLoading('正在批量转换', '正在逐条抓取文章、写入内容包并汇总结果。');
      const payload = await postJson('/api/batch', formPayload, { allowFalseOk: true });
      renderBatch(payload);
      if (formPayload.openFolder) {
        await openGeneratedPath(formPayload.output);
      }
      return;
    }

    showLoading('正在转换', '正在抓取文章、清理正文并写入内容包。');
    const payload = await postJson('/api/convert', formPayload);
    renderConversion(payload);
    if (formPayload.openFolder) {
      await openGeneratedPath(payload.packageDir);
    }
  } catch (error) {
    renderError(error);
  } finally {
    setBusy(false);
  }
});

publishPlanButton.addEventListener('click', async () => {
  if (state.busy) return;
  if (state.mode === 'batch') {
    renderError(new Error('发布预览目前针对单篇文章，请切回单篇模式。'));
    return;
  }
  setBusy(true);
  try {
    showLoading('正在生成发布计划', '正在转换文章并计算会写入 GitHub 的文件列表。');
    const payload = await postJson('/api/publish/plan', readForm());
    renderPublishPlan(payload);
  } catch (error) {
    renderError(error);
  } finally {
    setBusy(false);
  }
});

saveConfigButton.addEventListener('click', async () => {
  if (state.busy) return;
  setBusy(true);
  try {
    showLoading('正在保存配置', '正在把当前界面设置写入 .magicmd.toml。');
    const payload = await postJson('/api/config/save', {
      path: valueOf('config-path') || '.magicmd.toml',
      configText: buildConfigText()
    });
    showResult(`
      <div class="result-block">
        <h3>配置已保存</h3>
        <span class="code-line">${escapeHtml(payload.path)}</span>
      </div>
    `);
    await loadStatus();
  } catch (error) {
    renderError(error);
  } finally {
    setBusy(false);
  }
});

singleModeButton.addEventListener('click', () => setMode('single'));
batchModeButton.addEventListener('click', () => setMode('batch'));
byId('config-preset').addEventListener('change', applyPresetDefaults);
resultOutput.addEventListener('click', (event) => {
  const button = event.target.closest('[data-open-path]');
  if (button) {
    openGeneratedPath(button.dataset.openPath);
  }
});

setMode('single');
loadStatus();
