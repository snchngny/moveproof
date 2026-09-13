# Contribution guide

Issue、再現fixture、文書修正、code変更を歓迎します。最初に同じ内容のissueがないか確認してください。

## 開発環境

Moveproofのruntime依存はありません。Python 3.10以上で次を実行します。

```bash
python -m unittest discover -s tests -v
python -m compileall -q src tests benchmarks
```

配布物まで確認する場合:

```bash
python -m pip install build twine
python -m build
python -m twine check dist/*
```

## Pull request

- 一つの変更目的に絞る
- bug修正には失敗を再現するtestを付ける
- 公開API・JSON schema・fingerprint schemeを変える場合は互換性への影響を説明する
- benchmark結果にはOS、Python version、storage種別、file size、実行回数を記載する
- formatterだけの大規模変更を機能変更へ混ぜない

部分fingerprintは完全同一性の証明ではありません。安全性を強く見せる表現や、測定していない性能値を追加しないでください。
