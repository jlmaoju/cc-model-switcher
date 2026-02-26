# CC Model Switcher

一个简洁的 GUI 工具，用于快速切换 [Claude Code](https://docs.anthropic.com/en/docs/claude-code) 的 API 配置。

[English](README_EN.md)

<p align="center">
  <img src="screenshot.png" alt="CC Model Switcher 截图" width="700">
</p>

## 功能特点

- **多配置管理** — 保存并切换多个 API 配置
- **自定义命名** — 随意命名你的配置
- **安全存储** — API Key 本地存储，默认隐藏显示
- **自动备份** — 应用前自动备份原有设置
- **跨平台** — 支持 Windows、macOS、Linux
- **深色主题** — 现代简约的黑白灰界面

## 安装

**环境要求：** Python 3.8+ 以及 tkinter

```bash
# 克隆仓库
git clone https://github.com/jlmaoju/cc-model-switcher.git
cd cc-model-switcher

# 运行
python api_switcher.py
```

Windows 用户可以直接双击 `run.bat` 运行。

## 使用方法

首次运行会自动创建一个示例配置，你可以编辑它或创建新的配置。

1. 点击 **+** 创建新配置
2. 填写配置信息：
   - **Name** — 配置名称
   - **Base URL** — API 端点地址
   - **API Key** — 你的 API 密钥
   - **Model Mappings** — 可选的模型名称映射
3. 点击 **Apply** 保存并应用配置
4. **重启 Claude Code** 使配置生效

## 工作原理

CC Model Switcher 会修改 Claude Code 的配置文件 `~/.claude/settings.json`：

```json
{
  "env": {
    "ANTHROPIC_BASE_URL": "https://api.example.com",
    "ANTHROPIC_AUTH_TOKEN": "your-api-key",
    "API_TIMEOUT_MS": "3000000",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "model-name",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "model-name",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "model-name"
  }
}
```

你的配置保存在脚本同目录下的 `saved_configs.json` 文件中。

## 安全说明

- API Key 存储在本地的 `saved_configs.json` 文件中
- 该文件已加入 `.gitignore`，不会被提交到仓库
- 请妥善保管此文件，不要分享给他人
- 每次应用配置前会自动备份原有的 `settings.json`

## 许可证

[MIT](LICENSE)

## 贡献

欢迎提交 Issue 和 Pull Request。
