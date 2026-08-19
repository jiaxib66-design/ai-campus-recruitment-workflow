# AI 秋招岗位匹配与投递工作流

一个可公开安装的 Codex Skill，用于把零散招聘线索转成“官网核验、硬门槛检查、岗位评分、有限名额排序、申请材料辅助、投递追踪和招聘邮件待办”的隐私优先工作流。

> 本项目不代替个人判断，不承诺录用。竞争程度和“相对保底”只是在信息不完全情况下的辅助比较。

## 功能

- 从公司名、文字、CSV/JSON、截图转写或链接开始整理线索；第三方内容仅作为线索。
- 优先核验招聘官网，记录批次、截止日期、申请次数、专业/学历/语言/技术门槛、JD、来源和核验时间。
- 先检查硬性门槛，再按简历匹配、相对竞争、个人兴趣、发展前景和地域偏好评分。
- 输出“努力争取、重点投递、相对保底、不建议占用名额”，并解释共享投递名额下的取舍。
- 对照 JD 检查简历证据、辅助润色开放题、复用私有配置中的重复字段；不虚构经历。
- 用本地 CSV 维护公司、岗位、批次、投递时间、截止日期、状态和后续事项。
- 可选 163 邮箱 IMAP 只读扩展：从招聘通知中生成待确认事项；确认前不写入日历。

## 安装

需要 Python 3.10+，运行脚本不依赖第三方包。

```powershell
git clone https://github.com/jiaxib66-design/ai-campus-recruitment-workflow.git
Copy-Item -Recurse .\ai-campus-recruitment-workflow\skills\ai-campus-recruitment-workflow "$env:CODEX_HOME\skills\ai-campus-recruitment-workflow"
```

如果未设置 `CODEX_HOME`，请复制到 Codex 使用的个人 skills 目录。重启或刷新 Codex 后，可以自然语言触发：

- “用 AI 秋招投递工作流核验这家公司今年校招官网和截止日期。”
- “根据我的私有配置给这些岗位排序，只有两个投递名额。”
- “只更新投递追踪：星河科技的数据产品岗进入笔试。”
- “只用 mock 邮件提取测评截止时间，不要写日历。”

Skill 本体位于 [`skills/ai-campus-recruitment-workflow`](skills/ai-campus-recruitment-workflow)。

## 私有配置

仓库只提供虚构模板。不要把填写后的真实配置放进 Git：

```powershell
python .\skills\ai-campus-recruitment-workflow\scripts\init_user_config.py --output .\private\user-profile.json
```

编辑 `private/user-profile.json`，填写脱敏教育背景、技能、语言、城市偏好、兴趣和硬性限制。`private/`、`.env`、`*.local.json`、真实追踪表和邮件导出已加入 `.gitignore`，但提交前仍需人工检查。

模板见 [`config/user-profile.example.json`](config/user-profile.example.json)，字段说明见 [`data-schema.md`](skills/ai-campus-recruitment-workflow/references/data-schema.md)。

## 分阶段使用

### 1. 导入线索

```powershell
python .\skills\ai-campus-recruitment-workflow\scripts\import_clues.py `
  --input .\examples\clues.example.csv `
  --output .\output\clues.json `
  --observed-at 2026-08-19T00:00:00+08:00
```

输出仍是 `unverified`。让 Codex 打开官方招聘页完成核验，并记录官方 URL、抓取日期和冲突信息。截图 OCR 也必须标注可能误读。

### 2. 评分与名额排序

```powershell
python .\skills\ai-campus-recruitment-workflow\scripts\score_roles.py `
  --profile .\config\user-profile.example.json `
  --roles .\examples\roles.example.json `
  --output .\output\ranked.json
```

默认权重：简历匹配 35%、相对竞争优势 15%、兴趣 20%、发展 15%、地域 15%。先执行学历、毕业时间、专业、语言、技能、工作许可、地点和出差等硬门槛。相对竞争数据通常不完整，分类不能解释为录用概率。

### 3. 维护投递追踪

```powershell
python .\skills\ai-campus-recruitment-workflow\scripts\tracker.py init --file .\private\applications.csv
python .\skills\ai-campus-recruitment-workflow\scripts\tracker.py add --file .\private\applications.csv --company "星河科技（虚构）" --role "数据产品培训生" --cycle "2027秋招"
python .\skills\ai-campus-recruitment-workflow\scripts\tracker.py due --file .\private\applications.csv --days 7
```

### 4. 可选邮件扩展

先离线测试：

```powershell
python .\skills\ai-campus-recruitment-workflow\scripts\email_imap.py mock `
  --input .\examples\mock-emails.example.json `
  --output .\output\email-todos.json
```

真实连接 163 邮箱前，由用户在邮箱设置中启用 IMAP 并生成授权码，然后仅在当前进程环境中提供：

```powershell
$env:RECRUITMENT_IMAP_HOST = "imap.163.com"
$env:RECRUITMENT_IMAP_USER = "<your-private-mailbox>"
$env:RECRUITMENT_IMAP_AUTH_CODE = "<your-authorization-code>"
python .\skills\ai-campus-recruitment-workflow\scripts\email_imap.py fetch --output .\private\email-todos.json
```

本项目未宣称完成真实邮箱联调；仓库只验证接口与 mock。脚本以只读方式打开收件箱，不删除、不移动、不回复邮件。日期候选必须人工核验；写入任何日历前必须再次确认。

## 隐私边界与人工确认

- 禁止提交真实简历、姓名、电话、邮箱、身份证件、地址、聊天记录、投递表、Cookie、密钥或邮箱授权码。
- 不读取或复用其他项目中的个人材料；示例中的人物、公司、岗位和域名均为虚构。
- 官网无法核验的信息保持未知，不能用第三方搜索摘要替代。
- 简历和开放题只能基于用户确认的事实，不生成虚构经历或指标。
- 浏览器登录、验证码、法律声明、最终投递、邮箱访问范围和日历写入保留人工操作或明确确认。

## 测试与校验

```powershell
python -m unittest discover -s tests -v
python .\scripts\check_sensitive.py --path .
python <SKILL_CREATOR_DIR>\scripts\quick_validate.py .\skills\ai-campus-recruitment-workflow
```

## 限制

- 招聘官网结构变化快，核验需要当次访问官方页面；离线脚本不抓取网站。
- 评分依赖用户输入和证据质量，不是统计录用模型。
- 邮件自然语言日期可能缺少年份、时区或上下文，必须人工复核。
- 本工具不绕过登录、验证码、反自动化机制或招聘平台规则。

## English

AI Campus Recruitment Workflow is a privacy-first Codex Skill for verifying campus roles on official career sites, checking hard constraints, scoring and prioritizing limited application slots, reviewing resume-to-JD evidence, tracking applications locally, and optionally extracting reviewable recruiting deadlines from IMAP email. Examples are entirely fictional. Human confirmation is required for login, CAPTCHA, final submission, mailbox access, and calendar writes. “Lower competition” and “relative safety” are heuristics—not hiring guarantees.

Licensed under the [MIT License](LICENSE).
