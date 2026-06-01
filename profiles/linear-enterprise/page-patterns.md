# Page Patterns — linear-enterprise

## Pattern 1: List Page (Dashboard)

```
┌────────────────────────────────────────────┐
│ TopNav: NEXUS / Services                   │
├──────────┬─────────────────────────────────┤
│ Sidebar  │ SectionHeader "Services"        │
│          │ ├ description "Manage..."        │
│          │ └ [New Service] button           │
│          │                                  │
│          │ MetricCards (3-col grid)         │
│          │ ┌──────┐ ┌──────┐ ┌──────┐      │
│          │ │Total │ │Online│ │Off   │      │
│          │ └──────┘ └──────┘ └──────┘      │
│          │                                  │
│          │ DataTable                        │
│          │ ┌──────────────────────────────┐ │
│          │ │ Name  │ IP      │ Status     │ │
│          │ │ srv-1 │ 192...  │ ● Online   │ │
│          │ └──────────────────────────────┘ │
└──────────┴─────────────────────────────────┘
```

## Pattern 2: Detail / Debug Page

```
PageShell
  SectionHeader "API Debug" + [Save] [Run]
  
  Two-column layout:
  ┌─────────────────┬──────────────────────┐
  │ Parameter Form   │ Result Panel         │
  │ (Card)           │ (Card, monospace)    │
  │                  │                      │
  │ Service: [____]  │ {                    │
  │ Method:  [____]  │   "code": 0,         │
  │ Params:          │   "data": {          │
  │   name: [___]    │     "result": 8      │
  │   value:[___]    │   }                  │
  │ [+ Add Param]    │ }                    │
  │                  │                      │
  │ [Execute]        │                      │
  └─────────────────┴──────────────────────┘
```

## Pattern 3: Test Results Page

```
PageShell
  SectionHeader "Automated Tests"
  
  Test scenario list (DataTable):
  ┌──────────────────────────────────────┐
  │ Name         │ Steps │ Last Run      │
  │ Regression   │ 12    │ 2 min ago ✅  │
  │ Smoke Test   │ 5     │ 1 hr ago  ❌  │
  └──────────────────────────────────────┘
  
  Click row → expand result details:
  ┌──────────────────────────────────────┐
  │ Step 1: POST /sum          ✅ 45ms  │
  │ Step 2: POST /multiply     ✅ 32ms  │
  │ Step 3: POST /divide       ❌ 500ms │
  │   Error: division by zero           │
  └──────────────────────────────────────┘
```

## Pattern 4: Empty State (first load)

```
PageShell
  SectionHeader "Services"
  
  EmptyState
  ┌──────────────────────────────────────┐
  │ · · · · · · · · · · · · · · · · ·  │ (micro-dots)
  │                                      │
  │         📦 (icon circle)             │
  │         No Services Yet              │
  │    Import your first service to      │
  │         get started.                 │
  │                                      │
  │         [Import Service]             │
  │                                      │
  │ · · · · · · · · · · · · · · · · ·  │
  └──────────────────────────────────────┘
```
