# Fingerprint benchmark

`python benchmarks/benchmark_fingerprint.py --size-mib 256 --repeats 3` は、一時ディレクトリに乱数を256 MiB書き込み、部分fingerprintと完全fingerprintをそれぞれ3回計測した平均をJSONで表示する。計測対象はfingerprintのみで、file生成時間やlibrary scanは含まない。既存のmedia fileは読まない。

2026-09-21の実測例（Windows、Python 3.13、256 MiB、各3回、ローカル一時ディレクトリ。storage種類は未確認）:

| 方式 | 平均時間 |
| --- | ---: |
| 部分fingerprint | 0.004298秒 |
| 完全fingerprint | 1.019911秒 |

この条件では約237倍。部分方式は既定で先頭・中央・末尾の各64 KiBだけを読むため、完全一致の証明ではない。正確な同一性確認には完全方式を選ぶ。生成直後の同じfileを繰り返し読む計測なのでOS cacheの影響が大きく、異なるstorage、file数、fileサイズ、cold cacheのlibrary全体への速度予測には使えない。実際のlibraryでの読取性能は環境ごとに別途確認する。

再現するにはrepositoryで依存を導入した後、上記コマンドを実行する。`--size-mib`と`--repeats`を変更できる。一時fileは終了時に削除されるが、指定したサイズ分の空き容量が必要。結果を共有するときはOS、Python版、storage、引数、cache条件を併記する。
