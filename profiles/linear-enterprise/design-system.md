# Design System — linear-enterprise

> 风格: Linear.app × Vercel × Raycast
> 主题: Dark Only
> 字体: Geist / Inter

---

## Color Palette

| Token | Value | Usage |
|-------|-------|-------|
| `background` | `#000000` | 全局背景 |
| `card` | `rgba(24,24,27,0.5)` | 卡片底色 |
| `border` | `#27272a` | 默认边框 |
| `border-hover` | `#3f3f46` | 悬停边框 |
| `foreground` | `#fafafa` | 主文字 |
| `muted` | `#71717a` | 次要文字 |
| `accent` | `#6366f1` | 强调色 (indigo) |

## Typography

- 字体: **Geist** (Vercel) 或 **Inter**
- 标题: `font-semibold` + `tracking-tight`
- 正文: `text-sm` / `text-xs`
- 代码: `JetBrains Mono`, `font-mono`

```css
h1: text-2xl font-semibold tracking-tight
h2: text-xl font-semibold tracking-tight
h3: text-sm font-medium
body: text-sm text-zinc-100
muted: text-xs text-zinc-500
```

## Border & Radius

- 卡片: `rounded-2xl`, border 1px zinc-800
- 按钮/输入框: `rounded-xl`
- 标签: `rounded-full`
- 内部元素: `rounded-lg`

规则: **只用 border 表达深度，不用 shadow。阴影只在 hover 时出。**

## Spacing

- 页面: `p-8`, gap `space-y-8`
- 卡片: `p-6`, gap `space-y-4`
- 组件间: `gap-3`
- 表单: `gap-2`

## Interactions

| 元素 | Hover | Active |
|------|-------|--------|
| Button (primary) | `scale-[1.01]`, inset shadow | `scale-[0.99]` |
| Card | `border-zinc-700`, `scale-[1.01]` | — |
| Input | `border-zinc-700` | `border-indigo-500`, `ring-2 ring-indigo-500/20` |
| Sidebar item | `bg-zinc-900/50` | `bg-zinc-900` |
| Table row | `bg-zinc-900/50` | — |

## Glow Effect

在关键操作区（生成按钮、搜索框、modal 触发区）添加：

```css
background: radial-gradient(
  circle at center,
  rgba(99, 102, 241, 0.08) 0%,
  transparent 70%
);
```

## Micro-dots Background

空状态和装饰区：

```css
background-image: radial-gradient(#27272a 1px, transparent 1px);
background-size: 16px 16px;
opacity: 0.2;
```

## Icons

- **Lucide React** — 唯一图标库
- 尺寸: `h-4 w-4` (默认), `h-5 w-5` (大)
- 颜色: `text-zinc-400` (默认), `text-zinc-500` (次要)

## Loading States

不使用 spinner（除按钮内）。使用骨架屏：

1. 页面: `<Skeleton variant="page" />`
2. 卡片: `<Skeleton variant="card" />`
3. 指标: `<Skeleton variant="metric" />`
4. 表格行: `<Skeleton variant="table-row" />`

## Empty States

永远不要纯文字。使用带 micro-dots 背景的 `<EmptyState>`:

- 图标圆圈 + 标题 + 描述 + 行动按钮
- 图标颜色: `text-zinc-500`
- 图标背景: `bg-zinc-900 border border-zinc-800`

## Forbidden

- `bg-white` → 破坏暗色主题
- `text-black` → 在黑色背景上看不见
- `rounded-lg/md` → 使用 `rounded-xl/2xl`
- `shadow-md/lg` → 用 border 替代阴影表达层次
- `font-bold` → 使用 `font-semibold`
- `text-gray-*` → 使用 `text-zinc-*`
- `border-gray-*` → 使用 `border-zinc-*`
- Material UI / Antd / Bootstrap → 任何第三方组件库禁止

## Page Composition Rule

```
PageShell
  ├── TopNav (必须)
  ├── Sidebar (必须)
  └── content
       ├── SectionHeader (必须)
       ├── MetricCards (可选)
       ├── Card / DataTable (主要内容)
       └── EmptyState (数据为空)
```

## Component Dependency Map

```
PageShell
├── TopNav
├── Sidebar
└── content
     ├── SectionHeader
     │   └── Button
     ├── MetricCard → Card
     ├── DataTable → EmptyState
     ├── Card
     ├── Dialog → Button
     ├── Tabs
     ├── Select
     ├── Input
     ├── ActivityFeed → Card → EmptyState
     ├── CommandPalette
     ├── Toast → ToastContainer
     ├── Skeleton
     ├── StatusBadge
     └── Tooltip
```
