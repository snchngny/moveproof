# Security policy

## 対象version

公開後は最新releaseを対象にsecurity修正を行います。未公開の`0.1.0`はAPI・schemaが変わる可能性があります。

## 報告方法

公開repositoryのGitHub Private Vulnerability Reportingから報告してください。公開前はsecurity連絡先をまだ設けていないため、秘密情報をissueへ書かないでください。

通常のbugや、攻撃者が関与しないfingerprint衝突の相談はissueで扱います。次はsecurity上の重要事項です。

- 意図的なfingerprint衝突により別fileを同一と誤認させられる
- scan対象外へのpath traversalやsymlink追跡
- 読取中のfile差替えを検出できない
- 配布物やrelease workflowの改ざん

部分fingerprintは信頼できるローカルcollectionの高速な候補識別用です。敵対的入力や完全一致の証明には`full=True`またはCLIの`--full`を使用してください。
