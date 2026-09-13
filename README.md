# Moveproof

大きなローカルファイルを毎回すべて読まずに識別し、変更・改名・移動・コピーを検出するゼロ依存のPythonライブラリです。

[English README](README.en.md)

## 使いどころ

- 音源、動画、写真などのローカル索引で、パスが変わってもタグや履歴を引き継ぐ
- バックアップやメディア管理ツールで、追加・削除・移動を区別する
- 部分フィンガープリントの形式をversion付きで保存し、将来の方式変更を安全に扱う

## インストール

```bash
pip install moveproof
```

## Python API

```python
from pathlib import Path
from moveproof import compare_snapshots, create_snapshot

before = create_snapshot(Path("media"))
# ファイルを移動・追加する
after = create_snapshot(Path("media"))

changes = compare_snapshots(before, after)
for change in changes.changes:
    print(change.kind, change.old_path, change.new_path)
```

## CLI

```bash
moveproof snapshot media --output before.json
moveproof snapshot media --output after.json
moveproof compare before.json after.json
```

対象をrelative pathのglobで絞れます。excludeはincludeより優先され、指定条件はsnapshotへ保存されます。異なる条件のsnapshot比較は誤判定を避けるため拒否されます。

```bash
moveproof snapshot media --include "*.wav" --include "*.aiff" --exclude "archive/*" -o audio.json
```

通常は一件でも読取に失敗するとsnapshot作成を中止します。長時間scanの診断結果を残したい場合は`--record-errors`を使います。この場合はissue付きsnapshotを書き、CLIは終了code 1を返します。不完全なsnapshot同士の比較は誤った削除判定を避けるため既定で拒否され、内容を理解したうえで`--allow-incomplete`を指定できます。

snapshot JSONは同じdirectoryの一時fileへ書いてから置換するため、書込失敗で既存snapshotを途中状態へ壊しません。

`snapshot`は既定で64 KiB以下のファイルを全読込し、それより大きいファイルは先頭・中央・末尾を読みます。ファイルサイズもdigestへ含めます。読取中にファイルが変化した場合は記録せず、エラーとして扱います。

snapshotにはsampling幅も保存され、異なる方式・幅のsnapshotを誤って比較すると明示的に失敗します。

部分フィンガープリントは暗号学的な完全同一性の証明ではありません。意図的な衝突が問題になる用途や、内容の完全一致を保証する用途では`--full`を使ってください。

## 開発

```bash
python -m unittest discover -s tests -v
python -m build
python benchmarks/benchmark_fingerprint.py --size-mib 256
```

benchmarkは同じfileを繰り返し読むため、OS cache、storage、sparse file対応の影響を受けます。結果を掲載するときは環境と実行条件を併記してください。

変更提案は[Contribution guide](CONTRIBUTING.md)、脆弱性報告は[Security policy](SECURITY.md)を確認してください。

保守者向けの公開手順は[Release手順](docs/release.md)にあります。

## License

MIT
