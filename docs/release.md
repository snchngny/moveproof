# Release手順

PyPI API tokenは保存せず、GitHub ActionsとPyPI Trusted Publishingを使う。

## 初回だけ行う設定

1. GitHub repositoryをpublicで作成し、`main`をpush
2. GitHubのPrivate Vulnerability Reportingを有効化
3. GitHub Environment `pypi`を作り、manual approvalを必須化
4. PyPIのpending publisherへ次を登録
   - PyPI project: `moveproof`
   - Owner: `senooy-dot`
   - Repository: `moveproof`
   - Workflow: `release.yml`
   - Environment: `pypi`

## Releaseごとの手順

1. `CHANGELOG.md`の`未公開`をrelease日へ変更
2. `pyproject.toml`のversionとrelease tag `vMAJOR.MINOR.PATCH`を一致させる
3. test、`compileall`、build、`twine check`を実行
4. 変更を`main`へcommit、push
5. GitHub Releaseをdraftで作り、差分と既知の制約を確認
6. Releaseを公開
7. `pypi` Environmentの実行内容とartifactを確認して承認
8. PyPIのversion、metadata、provenance、`pip install moveproof`を確認

Release公開をtriggerにbuild Jobが配布物を一度だけ生成し、権限を分離したpublish Jobが同じartifactをPyPIへ送る。tagとpackage versionが違う場合は公開前に失敗する。

参考: [PyPAのTrusted Publishing手順](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
