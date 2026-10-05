# Roadmap

## 長期ミッション

Moveproofを核に、ローカルmedia libraryを失わずに移行・再編・復旧できるOSS ecosystemを作る。個別機能はOSSとして利用実績を確認し、検証済みの機能だけを統合productへ昇格する。

この文書は公開OSSの改善方針を扱う。統合productの販売条件や開発順序は約束しない。

## 原則

- 同じ利用者、データ、workflowを共有する機能だけを開発する
- 新しいrepositoryは、単独利用者と独立versioningが必要になってから分離する
- fileやDBを変更する前に、dry-run、根拠、影響、backup、undoを示す
- GitHub Sponsorsはcommunity支援、有料productとsupportは継続的な開発費として役割を分ける

## Phase 1: 安全な識別・検証

- file内容を読まず拡張子・件数・容量・大分類を把握するread-only inventory
- version付きfingerprintとsnapshot
- rename、move、copy、変更、欠損の検出
- path reconciliation plan
- mount変更の検出
- 不完全scanと大量消失を止めるlibrary guard

昇格条件:

- 外部利用者から再現可能な利用例が集まる
- 誤判定を防ぐtestとmachine-readableな結果がある
- 破壊的変更を行わず、組込先が判断できる

## Phase 2: Integration OSS

実際の要望が確認できた順に、以下をpluginまたはadapterとして追加する。

- Immichなどmedia manager向けの読取・移行plan adapter
- CSV、SQLite、filesystem間のpath mapping
- incremental scanとfingerprint cache
- backup manifestと復旧検証

別repositoryへ分離する条件:

- Moveproof本体とは別のrelease周期が必要
- 単独で利用・test・説明できる
- 依存先固有の変更がcoreへ波及する

## Phase 3: 統合product

local-firstのdesktopまたはlocal web appで以下を一つの操作flowにする。

1. 旧libraryと新libraryをscan
2. 移動、欠損、重複、metadata不整合を可視化
3. 変更planと根拠を確認
4. backupを作成
5. 適用して結果を検証
6. 必要ならundo

上記は連携先が構成できる操作flowの例であり、Moveproofが提供済みの機能ではない。Moveproof本体はファイルやDBの書換、backup、undoを実行しない。統合productの価格・販売対象・提供範囲は未確定で、このOSSの利用条件とは分けて扱う。

## 現在地

Phase 1を進行中。機能追加より、次を優先する。

1. v0.1.2を公開可能な状態へ保つ
2. Immich・NAS移行の実利用例を作り、再現条件と結果を示す
3. install、CLI実行、監査完了、相談到達を測れる導線を整える
4. 利用者へ課題、現在の回避策、既存機能の不足を確認する

新機能は、実利用例で既存OSSだけでは不足すると確認できた場合に追加する。統合productのGUI開発時期や販売検証は、このOSSのroadmapで制約しない。未合意のmetadata規格や書込仕様を提供済みとして扱わない。
