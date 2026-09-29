# Roadmap

## 長期ミッション

Moveproofを核に、ローカルmedia libraryを失わずに移行・再編・復旧できるOSS ecosystemを作る。個別機能はOSSとして利用実績を確認し、検証済みの機能だけを統合productへ昇格する。

無料OSSは信用形成と利用者獲得の入口とする。有料化はOSSの機能制限ではなく、Immich・NAS移行後にデータを失っていないかを確認する監査レポート、移行前診断、移行後照合の成果物と作業責任に対して行う。

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

無料範囲はcore engine、CLI、基本adapterとし、利用者自身が検証できる状態を保つ。有料候補は以下の3段階とする。金額は需要検証前の価格仮説であり、提供範囲と採算を実案件で確認してから確定する。

| 仮説 | 価格 | 提供価値 |
| --- | ---: | --- |
| セルフ監査 | 9,800円 | 利用者が取得した結果から、移行前後の欠損・移動・曖昧候補を確認できる監査レポート |
| 個別監査 | 49,800円 | 環境と移行計画を確認し、実行前のrisk、必要なbackup、確認項目を個別レポート化 |
| 移行検証 | 98,000円 | 移行前診断と移行後照合を組み合わせ、差分と未解決項目を検証レポート化 |

購入対象者は、Immichの外部libraryやNASを移行・再編し、album、説明、人物、path対応などの喪失を避けたい個人管理者・小規模運用者と仮定する。media本体や秘密値を受領せずに成立する提供方法を優先する。

## 現在地

Phase 1を進行中。機能追加より、次を優先する。

1. v0.1.2を公開可能な状態へ保つ
2. Immich・NAS移行の実利用例を作り、再現条件と結果を示す
3. install、CLI実行、監査完了、相談到達を測れる導線を整える
4. 対象者へ課題、現在の回避策、価格別の購入意向を確認する

新機能は、実利用例または購入対象者の検証で既存OSSだけでは不足すると確認できた場合に追加する。最初の有料pilotが成立するまでは、GUIや自動書込、広範なmedia manager対応を先行開発しない。
