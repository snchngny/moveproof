# Immich外部ライブラリでファイルを移動したときの読取専用監査

Immichの[外部ライブラリの公式説明](https://docs.immich.app/features/libraries/)は、ファイルを移動すると再スキャン時に新しいassetとして扱われ、Immich内だけにあるアルバムや説明などのmetadataが失われると警告している（2026-09-22確認）。[移動検出の要望](https://github.com/immich-app/immich/discussions/16394)でも、同じ内容のファイルが複数ある場合に旧assetを一意に特定できない問題が議論されている。

Moveproofができるのは、移動前後のファイル内容を照合し、旧パスと新パスの対応候補や曖昧さを読取専用で示すことまで。**Immichのasset IDやmetadataを保持・復旧する機能ではない。** `safe_to_apply: true`もMoveproofのファイル対応が一意という意味であり、Immichへ適用して安全という意味ではない。ImmichのAPIやDBには接続・書込しない。

## 移動前後を確認する

写真・動画のbackupを別に確保したうえで、移動前に完全fingerprintのsnapshotを作る。JSONは外部ライブラリの外に保存する。以下のパスは自分の環境に置き換える。

```bash
python -m pip install moveproof
moveproof snapshot /path/to/photos --full --output /path/to/audit/before.json
```

ファイルを移動した後、同じrootと条件で再度snapshotを作り、対応候補を出力する。Moveproofはこの操作で写真・動画やImmichのデータを書き換えない。

```bash
moveproof snapshot /path/to/photos --full --output /path/to/audit/after.json
moveproof reconcile /path/to/audit/before.json /path/to/audit/after.json --output /path/to/audit/plan.json
```

`plan.json`の`moves`が旧パスと新パスの候補、`unresolved_changes`が追加・削除・内容変更・copyの件数、`conflicts`が曖昧な候補。未解決または曖昧な候補があれば終了code 1になる。完全fingerprintでも同一内容の複数ファイルは個別の履歴を区別できないため、自動対応しない。事前snapshotがない場合は、この手順で移動前の状態を復元できない。

Immich側は自動watchや定期scanが有効なことがある。Moveproofで計画を作っても、Immichの再スキャンによるmetadata消失を止められない。既に失われたmetadataの復旧も保証しない。Immich運用を変更する前に、Immichの[backup手順](https://docs.immich.app/administration/backup-and-restore/)と現在のscan設定を確認する。

## Immichのasset IDと照合する試作

移動前、かつImmichが旧パスのassetを検索できる間なら、repository同梱の試作で`plan.json`の旧パスをImmichのasset IDに対応付けられる。Immichの[検索API](https://docs.immich.app/api/)へ検索リクエストだけを送り、`libraryId`とコンテナ内のrootを確認する。APIやDBへの更新は一切しない。実サーバーでの動作は未検証で、APIの変更や閲覧権限によって結果が欠ける可能性がある。

```bash
# IMMICH_API_KEYを環境変数に設定する。値をcommand行や共有logに残さない。
python examples/immich_asset_audit.py \
  --api-url https://your-immich.example/api \
  --library-id YOUR_LIBRARY_ID \
  --immich-root /mnt/photos \
  --plan /path/to/audit/plan.json \
  --output /path/to/audit/asset-audit.json
```

`--immich-root`はImmichコンテナ内の外部ライブラリのパスで、Moveproofのsnapshot rootと同じファイル集合を指す。`matched`は旧パスにasset IDが一つ、`ambiguous`は複数、`missing`は見つからない状態。`matched`でもImmichのmetadata保持や更新が安全だとは意味しない。API keyは環境変数からだけ読み、結果fileには含めない。結果にはasset IDとパスが含まれるためprivateに保管し、既存fileは上書きしない。通信先はHTTPS（localhostのみHTTP可）とし、必要な検索権限だけを持つAPI keyを使う。スクリプトはGitHubからrepositoryを取得して実行するもので、PyPI wheelには含まれない。

この用途で不足する情報（asset ID、アルバム、重複の扱いなど）があれば、個人情報やmediaを添付せずに[利用例を知らせてほしい](https://github.com/snchngny/moveproof/issues/new?template=feature.yml)。
