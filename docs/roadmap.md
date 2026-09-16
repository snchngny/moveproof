# Roadmap

## 長期ミッション

Moveproofを核に、ローカルmedia libraryを失わずに移行・再編・復旧できるOSS ecosystemを作る。個別機能はOSSとして利用実績を確認し、検証済みの機能だけを統合productへ昇格する。

## 原則

- 同じ利用者、データ、workflowを共有する機能だけを開発する
- 新しいrepositoryは、単独利用者と独立versioningが必要になってから分離する
- fileやDBを変更する前に、dry-run、根拠、影響、backup、undoを示す
- GitHub Sponsorsはcommunity支援、有料productとsupportは継続的な開発費として役割を分ける

## Phase 1: 安全な識別・検証

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

無料範囲はcore engine、CLI、基本adapterとする。有料候補はGUI、定期監視、大規模library高速化、team監査、専用integration、優先supportとする。

## 現在地

Phase 1を進行中。次の優先順位はlibrary guardの利用検証、実環境benchmark、最初のintegration要望の収集とする。
