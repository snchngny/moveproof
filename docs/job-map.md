# Jobマップ

Moveproofは永続DBを持たず、各CLI実行を一つのJobとして扱う。Job IDや実行履歴の永続化は組込先が担う。

| Job種別 | Trigger | 状態遷移 | 入力 | 出力 | Undo |
| --- | --- | --- | --- | --- | --- |
| `snapshot.create` | CLIまたはPython API | `started -> completed / failed` | root、fingerprint方式 | version付きsnapshot JSON | 不要。読取専用 |
| `snapshot.compare` | CLIまたはPython API | `started -> completed / failed` | before、after | change set JSON | 不要。読取専用 |

## ステータス別

| 状態 | 対象Job |
| --- | --- |
| `started` | `snapshot.create`、`snapshot.compare` |
| `completed` | `snapshot.create`、`snapshot.compare` |
| `failed` | `snapshot.create`、`snapshot.compare` |

## Trigger別

| Trigger | 対象Job |
| --- | --- |
| CLI | `snapshot.create`、`snapshot.compare` |
| Python API | `snapshot.create`、`snapshot.compare` |

