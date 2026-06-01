# Component Rules — linear-enterprise

## Mandatory

Every generated page MUST:
1. Be wrapped in `<PageShell>` — never render directly
2. Use `<Card>` for any content block — never raw `<div>` with border
3. Use `<SectionHeader>` at the top of each logical section
4. Use `<EmptyState>` for any empty list/table — never plain text
5. Use `<StatusBadge>` for any status indicator — never plain colored text
6. Use `<Button>` for all clickable actions — never raw `<button>`
7. Use `<Input>` for all form inputs — never raw `<input>`
8. Use `<DataTable>` for any tabular data — never raw `<table>`

## Forbidden

- `className="bg-white"` — kills dark theme
- `className="text-black"` — invisible on black bg
- `rounded-lg` / `rounded-md` — use `rounded-xl` or `rounded-2xl`
- `border-gray-*` — use `border-zinc-*`
- `shadow-md` / `shadow-lg` — no elevation shadows; use border for depth
- Any inline style with hardcoded colors
- `font-bold` — use `font-semibold`
- `text-gray-*` — use `text-zinc-*` for neutral, `text-{color}-*` for semantic

## Loading States

Every async component must render a skeleton:

```tsx
// Before data loads:
<Card padding="md">
  <div className="animate-pulse space-y-3">
    <div className="h-4 w-1/3 rounded-lg bg-zinc-800" />
    <div className="h-3 w-2/3 rounded-lg bg-zinc-800/50" />
    <div className="h-3 w-1/2 rounded-lg bg-zinc-800/50" />
  </div>
</Card>
```

## Empty States

Never: `<p>No items found</p>`

Always: `<EmptyState title="No items" description="Create your first item to get started." action={{label: "Create", onClick: ...}} />`

## Page Layout Template

```tsx
export default function FeaturePage() {
  return (
    <PageShell
      title="Feature Name"
      navItems={[
        { label: "Dashboard", icon: "dashboard", href: "/", active: false },
        { label: "Services", icon: "server", href: "/services", active: true },
      ]}
    >
      <div className="space-y-8">
        <SectionHeader
          title="Page Title"
          description="What this page does."
          actions={<Button>New Item</Button>}
        />
        
        <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
          <MetricCard title="Total" value={42} change="+12%" trend="up" />
          <MetricCard title="Active" value={18} />
          <MetricCard title="Failed" value={3} change="-2%" trend="down" />
        </div>

        <DataTable columns={columns} rows={data} />
      </div>
    </PageShell>
  );
}
```
