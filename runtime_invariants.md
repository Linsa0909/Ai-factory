# AI Runtime Invariants

这些不变量是所有测试和 Runtime 行为的硬约束。任何违反都是 Bug。

---

## 1. 状态一致性不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| SI-01 | `graph.tasks == persisted.tasks` — 内存中的 task 集合必须与 `task_graph.json` 完全一致，不允许不同步 | save 后立即 load 并 compare |
| SI-02 | 任何 `transition()` 调用必须同步更新 `status_history`，不允许跳过 | test_invalid_transition_does_not_mutate |
| SI-03 | `PASSED` 或 `READY` 到达时 `failure_reason` 必须被清空 | test_failure_reason_cleared_on_recovery |
| SI-04 | 非法 transition 必须抛 `InvalidTransition` 且不修改 task 任何字段 | test_invalid_transition_does_not_mutate |

## 2. Snapshot 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| SN-01 | `snapshot_before` 必须在 `create()` 后立即获得有效值（非空字符串） | test_create_produces_commit |
| SN-02 | rollback 必须恢复文件内容到 snapshot 状态（含删除 untracked 文件） | test_rollback_restores + test_rollback_removes_untracked |
| SN-03 | rollback 到不存在的 snapshot_id 必须抛 `FileNotFoundError` | test_error_on_missing_snapshot |
| SN-04 | workspace 不是 git repo 时 create 必须立即报错 | test_error_on_non_git_workspace |

## 3. DAG 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| DG-01 | `depends_on` 不允许自引用 | test_self_dependency_rejected |
| DG-02 | `depends_on` 不允许循环（A→B→A、A→B→C→A） | test_simple_cycle_rejected, test_three_node_cycle_rejected |
| DG-03 | `depends_on` 不允许引用不存在的 task_id | test_dangling_dependency_rejected |
| DG-04 | `invalidate_downstream` 只标记直接依赖者（单级），不递归级联 | test_invalidation_on_stale_propagates_only_one_level |
| DG-05 | `invalidate_downstream` 在 target 不在允许 STALE 的状态时静默跳过，绝不能崩溃 | test_invalidation_skips_running_task |

## 4. FSM 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| FS-01 | `PASSED` 只能通过 `STALE` 出口（DAG invalidation），不能转其他状态 | test_cannot_transition_from_terminal_passed |
| FS-02 | `CANCELLED` 完全终端，不允许任何 exit | test_cannot_transition_from_terminal_cancelled |
| FS-03 | 回退方向不允许（如 RUNNING→PASSED 后不允许再 RUNNING） | test_cannot_re_run_passed_task |
| FS-04 | 修复链路必须按序走完，不允许跳步（FAILED→FIXING 必须经 WAITING_RETRY） | test_cannot_skip_states_in_fix_chain |
| FS-05 | 任何未注册的 TaskStatus 必须 `RuntimeError` 大声报错，不允许静默 | test_unregistered_status_fails_loudly |

## 5. Store 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| ST-01 | 文件缺失或损坏时 `load_graph()` 返回 `[]` 绝不崩溃 | test_load_graph_returns_empty |
| ST-02 | `save_graph()` 必须原子写入（先写 .tmp 再 replace），不允许半写入 | test_atomic_write |
| ST-03 | 损坏的 JSON 中 `status` 字段非法时返回 `[]`（ValueError 捕获） | (需新增 test_corrupted_status_value) |
| ST-04 | telemetry 追加写入（"a" mode），不丢失历史数据 | test_telemetry_appends_jsonl |

## 6. Scope 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| SC-01 | AI 永远不能修改 `SCOPE_FORBIDDEN` 中的路径 | test_forbidden_file_violated |
| SC-02 | AI 修改超出 `SCOPE_ALLOWED` 的路径必须被拒绝 | test_out_of_scope_file_violated |
| SC-03 | forbidden 检查优先级高于 allowed | test_multiple_files_mixed |

## 7. FixLoop 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| FL-01 | retry_count 必须单调递增，不允许重复或递减 | (需 P0 实现后验证) |
| FL-02 | 同一错误重复出现 `STOP_CONDITIONS.same_error_repeated` 次后必须停止 | test_same_error_repeated_raises |
| FL-03 | diff size 超过上次 2x（entropy 上升）必须停止 | test_diff_entropy_rising |
| FL-04 | scope violation 立即停止，不允许继续 | test_scope_violation_immediate |
| FL-05 | fix 失败后必须 escalate 到 HUMAN_REQUIRED，不允许无限循环 | (需 P0 实现后验证) |

## 8. Event 不变量

| ID | 规则 | 验证方式 |
|----|------|---------|
| EV-01 | 任何 `TASK_STARTED` 最终必须匹配一个终端事件（PASSED / FAILED / HUMAN_REQUIRED） | (需 Runtime 集成后验证) |
| EV-02 | EventBus 订阅者崩溃不影响其他订阅者和生产者 | (需 P1 验证) |
| EV-03 | `next_event()` 在没有事件时阻塞等待，不返回 None | (当前设计保证) |

---

## 验证优先级

| 阶段 | 验证的不变量 |
|------|------------|
| P0 (当前) | SI-01~04, SN-01~04, DG-01~05, FS-01~05, ST-01~04, SC-01~03, FL-02~04, EV-01 |
| P1 | FL-01/05, EV-02, 并发不变量 |
| P2 | 跨 Feature 不变量, Episodic Memory 一致性 |
