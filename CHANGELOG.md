# 変更履歴

このprojectは[Semantic Versioning](https://semver.org/)に従う。

## 0.1.0 - 未公開

### 追加

- version付きの部分・全byte fingerprint
- directory snapshotのJSON保存と読込
- 読取失敗をsnapshotへ残す任意のerror policy
- 既存fileを途中状態へ壊さないatomic snapshot保存
- include/exclude globと比較時のfilter互換性検査
- 変更、移動、copy、追加、削除、曖昧な重複の分類
- Python APIとCLI
- path更新前に安全な移動候補と曖昧な競合を分離するreconciliation plan API・CLI
- Windows、macOS、Linux向けCI

### 安全性

- fingerprint読取中のfile変更を検出
- 異なるfingerprint方式・sampling幅のsnapshot比較を拒否
- symlinkを既定で追跡しない
- 不完全なsnapshot比較を既定で拒否
