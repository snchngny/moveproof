# Moveproof

[![PyPI](https://img.shields.io/pypi/v/moveproof.svg)](https://pypi.org/project/moveproof/)
[![CI](https://github.com/snchngny/moveproof/actions/workflows/ci.yml/badge.svg)](https://github.com/snchngny/moveproof/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/moveproof.svg)](https://pypi.org/project/moveproof/)

大きなローカルファイルを毎回すべて読まずに識別し、変更・改名・移動・コピーを検出するゼロ依存のPythonライブラリです。

[English README](README.en.md)

## 使いどころ

- 音源、動画、写真などのローカル索引で、パスが変わってもタグや履歴を引き継ぐ
- バックアップやメディア管理ツールで、追加・削除・移動を区別する
- 部分フィンガープリントの形式をversion付きで保存し、将来の方式変更を安全に扱う

## 似たツールとの違い

| 必要なこと | 適したツール |
| --- | --- |
| 実行中のファイル操作をリアルタイムに監視する | [watchdog](https://python-watchdog.readthedocs.io/) |
| JSON manifestを作り、追加・変更・削除を比較する | [file-watchman](https://pypi.org/project/file-watchman/) |
| `rsync`前にinodeを使って改名・移動を反映する | [irsync](https://pypi.org/project/irsync/) |
| オフライン期間を挟む2つのsnapshotから、内容fingerprintで移動・改名・copyを分類し、安全なdry-run planを作る | **Moveproof** |

Moveproofはファイル監視、同期、重複削除を行いません。ローカルlibraryのpathが変わった後も、既存のタグ、履歴、DB recordを安全に引き継ぐための識別・比較層です。

## インストール

```bash
python -m pip install moveproof
```

インストール後に`moveproof --help`が表示されれば準備完了です。

リポジトリを取得済みなら、[一時フォルダだけを使う移動検出デモ](examples/media_library_move.py)を実行できます。自分のファイルやDBは変更しません。

Immichの[外部ライブラリ公式説明](https://docs.immich.app/features/libraries/)は、ファイルを移動すると再スキャンで新しいassetとして扱われ、Immich内だけにあるalbum、説明などのmetadataが失われると警告しています。移動・改名前後の対応確認には、[既存ツール比較、移動前後の監査手順、asset ID照合の試作](docs/immich-external-library.md)を参照してください。Moveproofは再スキャン前に旧パスと新パスの候補を示しますが、Immichのmetadata自体は保護・復旧しません。

```bash
python examples/media_library_move.py
```

`samples/kick.wav`から`archive/kick.wav`への移動と`safe_to_apply: true`が表示されます。この値は候補の曖昧さがないことを示すだけで、DBへの適用やbackupを実行するものではありません。

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

DBやmedia indexのpathを安全に引き継ぐ前に、移動候補だけのdry-run planを作れます。自動適用可能なplanには完全fingerprintのsnapshotが必要です。曖昧な候補、変更、copy、追加、削除が一件でも残る場合は`unresolved_changes`と`safe_to_apply: false`を出力し、終了code 1で自動適用を止めます。このcommand自体はfileやDBを変更しません。

```bash
moveproof snapshot media --full --output before.json
# fileを移動・改名する
moveproof snapshot media --full --output after.json
moveproof reconcile before.json after.json --output plan.json
```

`--allow-sampled`や`--allow-incomplete`は候補確認用のadvisory planを作れますが、完全一致を保証できないため`safe_to_apply`はtrueになりません。

自動処理の前にbaselineと現在のlibraryを比較し、不完全なscan、空のmount、大量のfile消失を検出できます。既定ではbaselineの10%を超えるfileが見つからない場合に終了code 1で後続処理を止めます。移動・改名は消失として数えません。このcommandもfileやDBを変更しません。

```bash
moveproof snapshot media --output baseline.json
moveproof guard baseline.json media --output guard.json
moveproof guard baseline.json media --max-missing-ratio 0.02
```

libraryのmount先やroot directoryだけを変更した場合は、完全fingerprint、relative path、file集合がすべて一致すると`root_move`を出力します。DBを直接変更せず、旧rootから新rootへの置換計画を事前確認できます。

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

benchmarkは一時fileに乱数を書き込んでから計測します。既存の写真・動画には触れません。同じfileを繰り返し読むため、OS cacheやstorageの影響を受けます。再現条件と実測例は[benchmark](docs/benchmark.md)を参照してください。

変更提案は[Contribution guide](CONTRIBUTING.md)、脆弱性報告は[Security policy](SECURITY.md)を確認してください。

保守者向けの公開手順は[Release手順](docs/release.md)にあります。

OSSから統合productまでの開発順序は[Roadmap](docs/roadmap.md)にあります。

## 開発を支援

音源・写真・動画libraryの移行で使う場合は、ファイル数・容量・組込先を添えて[利用例を報告](https://github.com/snchngny/moveproof/issues/new?template=feature.yml)してください。互換性テストとOSSの継続開発は[GitHub Sponsors](https://github.com/sponsors/snchngny)から支援できます。支援は機能の納期や個別supportを保証しません。

## License

MIT
