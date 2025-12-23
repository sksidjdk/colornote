# ColorNote - Spec-Kit 规范文档（3 章严格版）

> Template variables required:
>
> - github_owner
> - repo_name
> - default_branch
> - vercel_project_name
>
> Configuration sources:
>
> 1. project.config.json provides repo/vercel/branch values (single source of truth).
> 2. .env provides database credentials and runtime config.

---

## Constitution

**项目名称**：ColorNote - 全栈便利贴应用

**GitHub 仓库名**：`{{repo_name}}`  
**Vercel 项目名**：`{{vercel_project_name}}`

### 项目元信息（强约束）

- GitHub repository: `{{github_owner}}/{{repo_name}}`
- Default branch: `{{default_branch}}`
- Git remote (origin): `https://github.com/{{github_owner}}/{{repo_name}}.git`

**Guardrail**：实现过程中必须使用上述仓库与分支命名；禁止生成与之不一致的仓库名、远程名或默认分支。

### 项目描述与范围

**项目描述**：一个针对移动端竖屏优化的彩色便利贴单页应用（SPA），提供创建、浏览、编辑、删除笔记的核心能力，并保证在本地 `vercel dev` 与 Vercel 生产环境行为一致。

**目标用户**：需要在手机浏览器里快速记录想法、待办事项的个人用户，以竖屏使用为主。

**项目范围**：

- 包含：创建、编辑、删除便利贴；6 种预设颜色主题；列表展示与内容预览；图片上传与展示；数据持久化（云数据库 + 云存储）。
- 不包含：用户登录/账户系统；多设备同步；分享/协同编辑；富文本编辑（仅纯文本）。

### 技术栈约束原则

- 后端：必须使用 Python 3.11+，Web 框架需支持 Serverless 部署。
- 前端：必须使用现代前端框架（支持 CDN 引入），必须支持移动端响应式设计。
- 数据库：必须使用云数据库服务（MySQL 兼容），支持 JSON 字段类型。
- 存储：图片必须存储在云存储服务中，禁止将图片数据以 base64 格式存入数据库。
- 测试：必须包含端到端测试（E2E）和 API 测试框架。
- 部署：必须使用 Serverless Functions 架构，本地开发环境必须与生产环境一致。
- 开发工具：必须使用 Vercel CLI 进行本地开发与部署。

### 质量与交付红线（项目级）

- 核心 CRUD 流程必须具备端到端测试覆盖（创建、读取、更新、删除）。
- 本地 `vercel dev` 与 Vercel 生产环境行为必须一致。
- 移动端体验目标：首屏加载时间 < 2 秒，交互响应时间（点击到 UI 反馈）< 300ms（P95）。

> 注：UI 验收以可量化的布局/样式规范与端到端测试（E2E）断言为准。

---

## Specify

> 需求部分只描述"要做什么"和"如何验证做对了"，不涉及任何具体代码实现。

### 2.1 功能模块：核心笔记管理（CRUD）

#### 场景 1：创建新笔记

**用户故事**：
作为用户，我点击底部的 "+" 按钮，希望能输入标题和内容并保存，保存后立即能在列表顶部看到新笔记。

**验收标准（AC）**：

1. 点击底部 "+" 按钮后，300ms 内编辑面板自底部向上滑入，动画持续约 250ms，缓动为 ease-out。
2. 编辑面板出现时，背景区域出现半透明黑色遮罩层，opacity 为 0.5。
3. 编辑面板包含：标题输入框（placeholder 为 `"Title"`）、内容文本区域（placeholder 为 `"Write something..."`）、颜色选择器（6 色）。
4. 默认颜色为 `#FFE57F`（黄色），编辑面板背景色应用该颜色。
5. 标题：最长 30 字符；超过时禁止继续输入，并显示红色字符计数（如 `"31/30"`，等价于 Tailwind `red-500` 级别的可见红色）。
6. 内容：最长 500 字符；达到限制时禁止继续输入。
7. 点击 `"Save"` 后：200ms 内关闭编辑面板并回到列表；新笔记出现在列表顶部且字段值与输入一致。
8. 刷新页面后，新创建笔记仍存在（已持久化到 TiDB）。

#### 场景 2：笔记列表展示

**用户故事**：
作为用户，我希望看到所有笔记按时间倒序排列，并且在移动端有良好的阅读体验。

**验收标准（AC）**：

1. 页面加载完成时向后端请求笔记列表数据，并在 500ms 内完成渲染（不含冷启动极端情况；冷启动见 2.4）。
2. 笔记按 `created_at` 降序排列（最新在顶部）。
3. 每个笔记卡片展示：
   - 标题：完整展示，字体大小 16px，字体粗细 600（或等效视觉粗体）。
   - 内容预览：字体大小 14px；基于视口宽度 375px 的布局下最多显示 3 行；超出使用省略号截断。
   - 背景色：使用该笔记的 `color` 字段值。
4. 卡片间垂直间距 16px；页面左右内边距 20px。
5. 点击任意卡片：300ms 内打开编辑面板，并自动填充该笔记当前标题、内容、颜色。
6. 空状态：无笔记时显示居中文案 `"No notes yet. Create your first note."`，字体大小 14px，颜色 `#9CA3AF`。
7. 列表滚动流畅；在目标设备上无明显卡顿。

#### 场景 3：编辑现有笔记

**用户故事**：
作为用户，我点击一个已有笔记，希望可以修改标题、内容或颜色，并保存修改。

**验收标准（AC）**：

1. 点击卡片后打开编辑面板，动画与遮罩行为与"创建新笔记"一致。
2. 编辑面板默认填充该笔记最新数据（title/content/color）。
3. 用户可修改标题（≤30）、内容（≤500）、颜色（6 色之一）。
4. 切换颜色后编辑面板背景立即更新；颜色选择器明确展示当前选中状态（例如边框高亮或对勾）。
5. 点击 `"Save"` 后：200ms 内关闭编辑面板；列表卡片内容、颜色立即更新；`updated_at` 刷新为当前时间。
6. 刷新页面后修改仍存在；通过 API 获取数据应反映最新值。

#### 场景 4：删除笔记

**用户故事**：
作为用户，我希望能够删除不再需要的笔记，并且删除操作是明确且可确认的。

**验收标准（AC）**：

1. 编辑面板右上角提供红色 `"Delete"` 操作入口（按钮或图标按钮均可，但需可访问并可点击）。
2. 点击 `"Delete"` 弹出确认对话框：
   - 文案为 `"Are you sure you want to delete this note?"`；
   - 按钮为 `"Cancel"` 与 `"Delete"`。
3. 点击 `"Cancel"`：关闭对话框，返回编辑面板，数据不变。
4. 点击确认 `"Delete"`：200ms 内关闭对话框与编辑面板；列表中对应卡片移除（允许淡出动画）；数据库记录物理删除。
5. 刷新页面后该笔记不再出现；通过 API 查询该 id 不应返回记录。

#### 场景 5：颜色主题选择

**预设颜色**：

1. `#FFE57F`（Yellow）
2. `#FFB3BA`（Pink）
3. `#BAE1FF`（Blue）
4. `#BAFFC9`（Green）
5. `#E0BBE4`（Purple）
6. `#FFDAC1`（Orange）

**验收标准（AC）**：

1. 新建与编辑面板内均提供颜色选择器；每个颜色按钮可点击区域 ≥ 44×44 px。
2. 点击颜色立即更新编辑面板背景色，并可清晰识别选中状态。
3. 保存后列表卡片背景色与所选颜色一致，刷新页面后保持一致。

#### 场景 6：图片上传与展示

**用户故事**：
作为用户，我希望能够在笔记中上传图片，并在列表中看到图片预览。

**验收标准（AC）**：

1. 编辑面板中提供图片上传入口（按钮或图标按钮，可点击区域 ≥ 44×44 px）。
2. 点击上传入口后，打开设备文件选择器，仅允许选择图片格式（如 jpg、png、gif、webp）。
3. 选择图片后，300ms 内在编辑面板中显示图片预览（缩略图形式，最大宽度 200px，保持宽高比）。
4. 图片上传过程中显示加载状态（如进度条或 spinner）。
5. 上传成功后，图片预览下方显示图片文件名（字体大小 12px，颜色 `#6B7280`）。
6. 每个笔记最多支持上传 3 张图片；达到上限时，上传入口禁用或提示"最多 3 张图片"。
7. 单张图片大小限制为 5MB；超过限制时，显示错误提示"图片大小不能超过 5MB"。
8. 点击 `"Save"` 后：图片上传到 Vercel Blob，笔记保存到 TiDB，图片 URL 存储在数据库中。
9. 列表卡片中：如果笔记包含图片，在内容预览下方显示第一张图片的缩略图（最大宽度 100px，保持宽高比，圆角 8px）。
10. 点击列表卡片中的图片：在编辑面板中打开该笔记，显示所有上传的图片。
11. 编辑笔记时：可以删除已上传的图片（提供删除按钮，点击后立即从预览中移除）。
12. 删除笔记时：笔记关联的所有图片从 Vercel Blob 中删除。
13. 刷新页面后，所有图片仍能正常显示（通过 Vercel Blob URL 访问）。

### 2.2 移动端适配要求

**目标设备**：

- iPhone 15 Pro（393×852）作为基准设备。
- iPhone 15 Pro Max（430×932）及主流 Android 机型（视口宽度 360–412 px）作为兼容目标。

**验收标准（AC）**：

1. 页面 `<head>` 包含 viewport meta：`width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no`。
2. 布局基于宽度 375px 设计；最大内容宽度 ≤ 480px；超出部分水平居中。
3. 所有可点击控件最小可点击区域 ≥ 44×44 px。
4. 竖屏为主要支持模式；横屏无需专门优化，可提示或保持可用。
5. 在目标设备上：列表滚动顺畅；按钮点击有明显视觉反馈（如颜色加深或阴影变化）。

### 2.3 部署与环境一致性要求

**部署平台**：Vercel Serverless Functions。

**验收标准（AC）**：

1. 本地开发必须使用 `vercel dev` 启动（禁止使用 `flask run` 作为日常入口）。
2. 每次 PR 或推送触发 GitHub Actions：运行单元/API/E2E 测试；测试通过后部署到 Vercel 生产环境。
3. 最终功能验证必须在 Vercel 生产环境进行，确保生产环境行为符合所有验收标准。
4. 不允许出现"本地可用、生产不可用"的行为差异。

### 2.4 冷启动与性能要求（Serverless）

**验收标准（AC）**：

1. 针对 Vercel Serverless 冷启动：允许首个请求更高延迟，但必须在 UI 上提供明确加载反馈（如 skeleton 或 loading 状态）。
2. 非冷启动情况下：主要交互（打开编辑面板、保存后回到列表、删除后列表更新）UI 反馈 < 300ms（P95）。

---

## Plan

> Plan 只描述"怎么做"，不重复 AC；所有可验收口径必须留在 Specify。

### 3.1 开发前置校验（Preflight）

Preflight 必须先读取 project.config.json，并使用其中的值进行 Git/Vercel 相关校验。

在开始任何业务代码实现之前，必须先完成以下校验；任意一项失败则停止实现并报告错误原因与修复建议：

1. Git 元信息校验：

   - 当前仓库 remote `origin` 必须为 `https://github.com/{{github_owner}}/{{repo_name}}.git`；
   - 默认分支必须为 `{{default_branch}}`；
   - 本地仓库名与宪章中声明一致。

2. 环境变量校验：

   - 必须能读取到 `.env` 中的 DB\_\* 变量；
   - `DB_DATABASE` 与 `DB_TEST_DATABASE` 均非空且不相同。
   - 必须能读取到 `BLOB_READ_WRITE_TOKEN`（用于 Vercel Blob 存储，图片必须存储在 Blob 中，不能使用 base64 存入数据库）。
   - 如果本地 `.env` 文件中没有 `BLOB_READ_WRITE_TOKEN`，必须使用 Vercel CLI 工具获取：
     - 运行 `vercel env pull .env.local` 从 Vercel 项目拉取环境变量
     - 或运行 `vercel env pull .env` 直接更新 `.env` 文件
     - 确保从 Vercel Dashboard 中已配置该环境变量（如未配置，需先在 Dashboard 中配置）

3. 数据库连通性与权限校验：

   - 能连接 TiDB（DB_HOST/DB_PORT/DB_USERNAME/DB_PASSWORD）；
   - `DB_DATABASE` 与 `DB_TEST_DATABASE` 均可访问；
   - 在 `DB_TEST_DATABASE` 中具备创建/删除表权限（用于测试隔离）。

4. Vercel 本地一致性校验：

   - 本地开发与测试必须使用 `vercel dev` 启动。
   - 确保已安装 Vercel CLI：`npm i -g vercel` 或通过其他方式安装。
   - 必须配置 `BLOB_READ_WRITE_TOKEN` 环境变量：
     - **如果本地 `.env` 文件中没有该变量**：必须使用 Vercel CLI 工具获取：
       - 运行 `vercel env pull .env.local` 或 `vercel env pull .env` 从 Vercel 项目拉取环境变量
       - 确保 Vercel 项目中已配置该环境变量（如未配置，需先在 Vercel Dashboard 中配置）
     - **如果 Vercel 项目中也没有配置**：必须在 Vercel Dashboard 中配置该环境变量，然后使用 CLI 拉取
   - 由于 TiDB 性能限制，图片必须存储在 Vercel Blob 中，禁止使用 base64 数据存入数据库。`BLOB_READ_WRITE_TOKEN` 是必须的，不允许跳过或使用 fallback。

### 3.2 技术栈选型

**后端技术栈**：

- Python 3.11
- Flask 3.0（Web 框架）
- SQLAlchemy（ORM）

**前端技术栈**：

- Vue.js 3（通过 CDN 引入）
- Tailwind CSS（通过 CDN 引入）

**数据库与存储**：

- TiDB Cloud（MySQL 兼容的云数据库）
- Vercel Blob（云存储服务，用于图片存储）

**测试框架**：

- Playwright（E2E 测试）
- pytest（API/单元测试）

**部署与工具**：

- Vercel Serverless Functions（部署平台）
- Vercel CLI（本地开发与部署工具）

### 3.3 架构设计

**架构模式**：

- Flask 单体应用（Monolith）。
- 服务端返回基础 HTML（含 Vue 挂载点）+ Vue 客户端渲染与交互（CSR）。

**前后端组织**：

- 后端：`app/`，使用 Blueprints 管理主页面与 API。
- 前端：`app/templates/index.html` 输出 DOM 框架；静态资源在 `app/static/js/app.js`、`app/static/css/custom.css`。
- Vue 3 与 Tailwind CSS 通过 CDN 引入。

**路由设计**：

- `GET /`：返回主页面 HTML。
- `GET /api/notes`：获取列表。
- `POST /api/notes`：创建（支持图片上传）。
- `PUT /api/notes/<id>`：更新（支持图片上传和删除）。
- `DELETE /api/notes/<id>`：删除（同时删除关联的图片）。
- `POST /api/notes/<id>/images`：上传图片到指定笔记（可选，也可在创建/更新时一并上传）。

### 3.4 数据模型与持久化（TiDB + ORM）

**表名**：`notes`。

| 字段名     | 类型     | 约束                         | 说明          |
| ---------- | -------- | ---------------------------- | ------------- |
| id         | 整数     | 主键，自增                   | 唯一标识      |
| title      | 字符串   | ≤30，非空                    | 标题          |
| content    | 文本     | ≤500，非空                   | 内容          |
| color      | 字符串   | 长度 7，非空，默认 `#FFE57F` | HEX 颜色      |
| image_urls | JSON     | 可为空，最多 3 个 URL        | 图片 URL 数组 |
| created_at | 日期时间 | 默认 `NOW()`                 | 创建时间      |
| updated_at | 日期时间 | 默认 `NOW()`，更新自动刷新   | 更新时间      |

**图片存储**：

- 图片必须存储在 Vercel Blob 中，数据库仅存储图片 URL（由于 TiDB 性能限制，禁止将图片数据以 base64 格式存入数据库）。
- `image_urls` 字段为 JSON 数组，格式：`["https://xxx.vercel-storage.com/image1.jpg", ...]`。
- 每个笔记最多存储 3 个图片 URL。

**实现要求**：

- 使用 SQLAlchemy ORM 定义模型 `Note`；时间字段通过 ORM 或数据库机制自动维护。
- 使用 `NoteRepository` 作为数据库访问边界，对外提供 create/get_all/update/delete 四类能力。
- 内部使用 SQLAlchemy Session 事务管理，异常时回滚并返回统一错误格式。

### 3.5 API 合同与校验逻辑

- `GET /api/notes`：按 `created_at` 降序返回，包含 `image_urls` 字段。
- `POST /api/notes`：接收 `{title, content, color, images}`（images 为文件数组），进行字段校验后：
  - 将图片上传到 Vercel Blob（使用 `@vercel/blob` Python SDK 或 REST API）
  - 获取图片 URL 数组
  - 创建笔记并返回完整对象（含 id、时间戳、image_urls）
- `PUT /api/notes/<id>`：接收 `{title, content, color, images, deleted_image_urls}`，进行字段校验后：
  - 上传新图片到 Vercel Blob
  - 从 Vercel Blob 删除 `deleted_image_urls` 中的图片
  - 更新笔记并返回更新后的对象（updated_at 刷新）
- `DELETE /api/notes/<id>`：
  - 从 Vercel Blob 删除该笔记关联的所有图片
  - 物理删除数据库记录
  - 返回 `{success: true}`
- 错误格式统一：`{"error": "错误描述"}`。

**图片上传实现要求**：

- 使用 Vercel Blob 存储服务，通过 `BLOB_READ_WRITE_TOKEN` 环境变量进行认证。
- **强制要求**：由于 TiDB 性能限制，图片必须存储在 Vercel Blob 中，禁止将图片数据以 base64 格式存入数据库。
- **环境变量配置要求**：`BLOB_READ_WRITE_TOKEN` 必须配置，不允许 fallback。如果本地 `.env` 文件中没有该变量：
  - 必须使用 Vercel CLI 工具获取：运行 `vercel env pull .env.local` 或 `vercel env pull .env`
  - 如果 Vercel 项目中未配置，必须在 Vercel Dashboard 中先配置该环境变量，然后使用 CLI 拉取
- 图片上传实现方式（二选一）：
  1. **使用 Vercel CLI**：通过 `vercel blob put <file>` 命令上传，获取返回的 URL。
  2. **使用 Python SDK**：安装 `vercel-blob` Python 包（如果可用），或使用 Vercel Blob REST API。
- 图片路径格式：`notes/{note_id}/{timestamp}_{filename}`，确保唯一性。
- 图片访问权限：`public`，允许通过 URL 直接访问。
- 单张图片大小限制：5MB，上传前进行校验。
- 每个笔记最多 3 张图片，创建/更新时进行校验。
- 图片删除：使用 `vercel blob rm <url>` 命令或相应的 API 删除。
- 所有 Vercel Blob 操作必须通过 Vercel CLI 或官方 API 完成，禁止使用第三方工具。

### 3.6 测试落地方案（目录、隔离、断言）

**测试目录结构**：

- `tests/api/test_api_routes.py`：API 行为与校验（pytest）。
- `tests/e2e/*.py`：Playwright E2E 覆盖 CRUD 与关键样式断言。
- `tests/conftest.py`：统一 fixtures（启动 `vercel dev`、等待就绪、测试数据清理）。

**数据库隔离**：

- 测试必须使用独立 TiDB 数据库或独立 schema。
- 每个测试用例清理其创建的数据，保证可重复执行。

**E2E 断言策略（实现侧）**：

- UI 层：元素存在/可见/可点击/关键样式可被选择器断言。
- 数据层：关键操作后通过 API 校验数据状态与字段值。

### 3.7 运行方式与 CI/CD

- 本地开发与测试统一入口：`vercel dev`。
- CI（GitHub Actions）：先跑 pytest（单元/API），再跑本地 `vercel dev` 下 E2E；测试通过后部署到 Vercel 生产环境。
- **最终验证**：所有功能验证必须在 Vercel 生产环境进行，确保生产环境行为符合所有验收标准。
