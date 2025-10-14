# Requirements Document

## Introduction

本仕様書は、Mini-Redisプロジェクトに学習者向けの講義資料を追加するための要件を定義します。60〜90分のワークショップ形式で、asyncio/ネットワークプログラミング/Redisの内部実装を実践的に学べる教材を提供することを目的とします。

対象者は、Pythonの基本構文を理解している学習者で、asyncioによる非同期プログラミングやネットワークプロトコルの実装に興味がある技術者です。段階的な学習パスと実践的な演習を通じて、理論と実装スキルの両方を習得できる学習体験を提供します。

## Requirements

### Requirement 1: ワークショップ段階別講義資料の提供
**Objective:** 学習者として、ワークショップの各段階で必要な知識を段階的に学べる講義資料が欲しい。これにより、実装の各フェーズで必要な概念を体系的に理解できる。

#### Acceptance Criteria

1. WHEN 学習者が導入段階（5分）に進む THEN 学習資料には Redisの基本知識、デモ（PING/GET/SET/INCR/EXPIRE）、RESPの最小要素（Arrays/Bulk、CRLF終端、長さ指定）を説明するセクションを含む SHALL
2. WHEN 学習者がTCPサーバ＆コマンド呼び出し段階（15分）に進む THEN 学習資料には asyncioでのTCPサーバ構築、StreamReader/StreamWriterの使用方法、受信→解釈→コマンド実行→応答のループ実装を説明するセクションを含む SHALL
3. WHEN 学習者がメッセージの切り出し・読み取り段階（15分）に進む THEN 学習資料には ストリームから1行読む処理、Bulkの長さ指定に従った本体読み出し、RESP Arrayのパース実装を説明するセクションを含む SHALL
4. WHEN 学習者が基本コマンド実装段階（20分）に進む THEN 学習資料には PING/GET/SET/INCRの各コマンド仕様、実装方法、redis-cliでの動作確認方法を説明するセクションを含む SHALL
5. WHEN 学習者がEXPIRE発展課題段階に進む THEN 学習資料には Passive Expiry（GET/INCR/SET入口での期限確認）とActive Expiry（バックグラウンドのランダムサンプリング）の実装を説明するセクションを含む SHALL
6. WHEN 学習者がまとめと発展段階（5分）に進む THEN 学習資料には 実装した機能の振り返り、更なる発展課題（DEL/EXISTS/EXPIRETIME等）の提案を含む SHALL
7. WHEN 学習者がエラーハンドリングを実装する THEN 学習資料には 各コマンドで発生しうるエラーケースとエラーメッセージの形式を含む SHALL
8. WHERE 各段階の説明セクション THE 学習資料には その段階の目標、実装のポイント、実際のコード例、図解を含む SHALL
9. WHERE 各コマンドの説明 THE 学習資料には redis-cliでの実行例と期待される結果を含む SHALL

### Requirement 2: ハンズオン実装ガイド
**Objective:** 学習者として、段階的な実装手順と各ステップでの確認方法を知りたい。これにより、詰まることなくスムーズに実装を進められる。

#### Acceptance Criteria

1. WHEN 学習者が実装を開始する THEN ハンズオンガイドには 推奨実装順序（server.py → protocol.py → storage.py & commands.py → expiry.py）を明示する SHALL
2. WHEN 学習者が各モジュールの実装を開始する THEN ハンズオンガイドには そのモジュールの役割、実装のヒント、よくあるエラーパターンを含む SHALL
3. WHEN 学習者が実装の正確性を確認したい THEN ハンズオンガイドには 各モジュールに対応するテストコマンド（例：`pytest tests/test_protocol.py -v`）を含む SHALL
4. WHERE 各実装ステップ THE ハンズオンガイドには 期待される出力例とトラブルシューティングのヒントを含む SHALL
5. WHEN 学習者が関連ライブラリの使い方を確認したい THEN ハンズオンガイドには asyncio公式ドキュメント（StreamReader/StreamWriter）、RESP仕様、Redis公式ドキュメントへの適切なリンクを含む SHALL
6. WHEN 学習者が完成版コードを参照したい THEN ハンズオンガイドには solutions/ディレクトリの使用方法と比較学習の推奨アプローチを含む SHALL

### Requirement 3: アーキテクチャ解説資料
**Objective:** 学習者として、Mini-Redisの全体設計と各コンポーネントの役割を理解したい。これにより、なぜこの構造なのかを納得して実装できる。

#### Acceptance Criteria

1. WHEN 学習者が全体像を把握したい THEN アーキテクチャ資料には レイヤー構造図（Network → Protocol → Command → Storage）を含む SHALL
2. WHEN 学習者がモジュール間の依存関係を理解したい THEN アーキテクチャ資料には 各モジュールの責務と依存関係のダイアグラムを含む SHALL
3. WHERE データフローの説明 THE アーキテクチャ資料には クライアントリクエストから応答までの処理フローを図解する SHALL
4. WHEN 学習者が設計原則を学びたい THEN アーキテクチャ資料には レイヤー分離、単一責任、テスタビリティの原則とその理由を説明する SHALL
5. IF 学習者が将来的な拡張を考える THEN アーキテクチャ資料には 発展課題（永続化、Pub/Sub）を実装する場合の設計方針を含む SHALL
