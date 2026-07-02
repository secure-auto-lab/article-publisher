---
title: "Cloudflareの530を追ったら真犯人はWSLの sleep infinity だった｜多層障害デバッグ全記録"
description: "本番サイトがダウン。Cloudflare 530(error 1033)に見えた障害は、実は5層に積み重なった根本原因の連鎖だった。表面の症状に振り回されずに真因へ辿り着いた、systematic debuggingの全記録。"
pubDate: "2026-07-03"
updatedDate: "2026-07-03"
category: "dev-tips"
tags: ["WSL", "Cloudflare", "Docker", "cloudflared", "トラブルシューティング"]
author: "Secure Auto Lab"
---

# Cloudflareの530を追ったら、真犯人はWSLの `sleep infinity` だった

---

## 🎯 この記事で得られること

> **この記事を読むと、「表面のエラーに騙されず、多層に積み重なった障害の真因まで辿り着く」思考プロセスが手に入ります。**
>
> - ✅ Cloudflare Tunnel の `530 (error 1033)` を、origin側から体系的に切り分ける手順
> - ✅ WSL2 が数十秒ごとに落ちる「p9io poweroffループ」の正体と対処（`microsoft/WSL #13435`）
> - ✅ 「ローカルでは正常」なのにダッシュボードでは「停止」になるトンネルの謎の解き方
> - ✅ `docker` が遅い・コンテナが勝手に再起動する時に最初に疑うべきポイント

---

## 😰 あなたもこんな「多層障害」に溺れたことはありませんか？

- 「エラーメッセージを直しても直しても、別の場所から次のエラーが出てくる…」
- 「ログでは『正常に接続しました』と出ているのに、ユーザーには繋がらない…」
- 「原因を1つ潰すたびに、実はその下にもう1つ原因が隠れていた…」

**私はこの日、まさにこの沼に何時間も沈みました。**

きっかけは、たった一言の報告でした。

> 「本番サイトに繋がらないです。Cloudflare tunnelに繋がっていません」

Cloudflareが `530` を返している。ここから、**5層に積み重なった根本原因を1枚ずつ剥がしていく**長い旅が始まりました。

---

## 📖 私のストーリー：530という「氷山の一角」

### Before：たった1つの症状、5つの真因

インフラ構成はこうです。

- **Windows + WSL2 (Ubuntu) 上の Docker** に約25個のコンテナ
- `cloudflared` トンネルで外部公開（本番サイト → nginx LB → Next.js Blue/Green → ClickHouse）
- ポート開放なし、すべて Cloudflare Tunnel 経由

症状は「サイトが `530`」。普通なら「トンネル（cloudflared）を再起動すれば直る」——実際、過去のインシデントでは `docker restart` 一発で復旧していました。

ところが今回は、その一手が**まったく効かない**。そこから、症状の下に隠れた真因が次々と顔を出します。

| 層 | 見えた症状 | 実際の原因 |
|----|-----------|-----------|
| 1 | `docker ps` が `HCS_E_CONNECTION_TIMEOUT` | **WSLディストロ全体がハング** |
| 2 | WSLが60〜90秒ごとに電源断 | **p9ioバグの poweroffループ**（`#13435`） |
| 3 | 530が断続的に続く | ClickHouseの **ghost attachment** / nginxの **stale upstream** |
| 4 | トンネルは`/ready`で4本healthyなのに `1033` | **Cloudflare側ではレプリカ0・停止** |
| 5 | トンネルが30〜60秒ごとにSIGTERMで死ぬ | **keepaliveの `sleep infinity` が消えていた** ← 真犯人 |

**「1つの530」の下に、これだけの原因が積み重なっていたのです。**

### 転機：`wsl --update` を打つ、あの一瞬

第2層まで剥がした時点で、真因はWSL2の既知バグ `p9io.cpp:258 (AcceptAsync)` だと分かりました。`docker.service` 起動の約15秒後に `systemd-logind: The system will power off now!` が発火し、VM全体が数十秒周期で電源断していたのです。

`/etc/wsl.conf` で `automount=false` にして9P境界を削ると、ループは85%減りました。でも完全には止まらない。

そこでユーザーから、思いがけない一言が飛んできます。

> 「WSL containerdにすれば改善しますか？」

調べると、`microsoft/WSL #13435` は **WSLプラットフォームの更新で修正される種類**のバグでした。そして——**その修正を含む新ビルドが、まさにその日にリリースされていた**のです。

```powershell
wsl --update --pre-release   # 2.7.10 → 2.9.3（#13435修正込み）
```

**VMは3時間以上、一度も落ちなくなりました。** ここで「勝った」と思いました。……が、まだ第4層・第5層が残っていたのです。

### After：ダッシュボードが「正常・レプリカ1」に変わった瞬間

最終的に真犯人を仕留めた後の変化がこれです。

| 項目 | 復旧前 | 復旧後 |
|------|--------|--------|
| Cloudflareトンネル ステータス | 🔴 停止 | 🟢 **正常** |
| アクティブなレプリカ | **0** | **1** |
| 本番サイト HTTPステータス | `530 (1033)` | **`200`** |
| ランキングページ | 真っ白 | **569KB / 正常表示** |

`Start-ScheduledTask WSLKeepAlive` ——**たったこの1行**で、数時間の沼が晴れました。

---

## 💭 なぜ「トンネルの再起動」では直らなかったのか

このインシデントで最も大きな学びは、**「動いている証拠」を鵜呑みにしなかったこと**でした。

### `/ready = 4 connections` という"嘘"

`cloudflared` のメトリクスエンドポイントはこう言っていました。

```json
{"status":200,"readyConnections":4,"connectorId":"..."}
```

「4本のコネクションがready」。ローカルのログにも `Registered tunnel connection connIndex=0..3` と、成功が並んでいます。普通ならここで「トンネルは正常。原因は別だ」と判断してしまいます。

**でも、Cloudflareのダッシュボードは正反対のことを言っていました。**

- ステータス: **停止**
- アクティブなレプリカ: **0**

ローカルの「正常です」と、edge側の「停止しています」。この**矛盾こそが真実への扉**でした。片方の指標だけを信じていたら、永遠に origin側を疑い続けて迷宮入りしていたはずです。

### ユーザーの「ClickHouseが怪しい」を、あえて否定した

途中でこんな報告も来ました。

> 「ClickHouseと接続できていないようです。ページは開くがランキングが表示されない。IPが変わっていないか確認してください」

もっともらしい仮説です。実際、ghost attachment（コンテナがネットワークから外れてDNSで引けなくなる）は過去に起きていました。

でも、**推測で動かず証拠を取りに行きました**。

- ClickHouseのIP → `172.21.0.10` のまま、**変わっていない**
- コンテナのhealth → `healthy`
- origin（nginx LB経由）で `/ja` を叩く → **ランキングデータを含む56KBを正常に描画**

つまり、**ClickHouseもoriginも無実**。「ページは開くがランキングが出ない」の正体は、CHではなく **Cloudflareトンネルの530**——ページの枠だけがCDNキャッシュで開き、データ取得がトンネル経由で失敗していたのです。

**もっともらしい仮説ほど、証拠で殺す。** これが遠回りに見えて最短でした。

### 決め手：「なぜCloudflareはレプリカ0と言うのか」を問い直す

「cloudflaredは繋がっている。でもCloudflareは繋がっていないと言う」——この矛盾を放置せず、**cloudflaredのログを"時系列"で読み直した**のが決定打でした。

そこに、犯人の指紋がありました。

```text
15:06:12 INF Registered tunnel connection connIndex=2 ...
15:06:13 INF Registered tunnel connection connIndex=3 ...
15:06:44 INF Initiating graceful shutdown due to signal terminated ...  ← 31秒後にSIGTERM
15:07:21 INF Registered tunnel connection connIndex=0 ...                ← また登録
15:07:29 INF Initiating graceful shutdown due to signal terminated ...  ← また8秒後にSIGTERM
```

**登録 → 30〜60秒後にSIGTERM → 再登録** の無限ループ。トンネルは「繋がっては殺され」を繰り返していて、Cloudflareが安定したレプリカとしてカウントできる瞬間が一度も無かった。だから edge は `1033` を返し続けていたのです。

---

## 🔧 具体的な調査と修正の全手順

### 全体像：症状から真因へ剥がしていく流れ

```text
[530] サイト不通
  │
  ├─ WSL自体が応答なし (HCS_E_CONNECTION_TIMEOUT)
  │    → wsl --shutdown で復帰（が、ループ継続）
  │
  ├─ p9io poweroffループ (docker起動15秒後にpower off)
  │    → /etc/wsl.conf automount=false（85%減）
  │    → wsl --update --pre-release（2.9.3でVM安定）
  │
  ├─ ClickHouse ghost attachment / nginx stale upstream
  │    → docker network connect / nginx -s reload
  │
  └─ nexus-tunnel が30-60秒ごとにSIGTERM
       → 原因: keepalive(sleep infinity)喪失
       → Start-ScheduledTask WSLKeepAlive で復旧 → 200
```

### Step 1: WSLが「Running」でも死んでいることを見抜く

`wsl --list` は `Running` と表示するのに、中のコマンドが返らない。まずはここを疑います。

```bash
# 25秒待って返らなければ rc=124（ハング確定）
timeout 25 wsl.exe -d Ubuntu -e bash -lc 'echo ALIVE' ; echo "rc=$?"
```

`rc=124` ならディストロがハング。`wsl --shutdown` で一度クリーンにします。

### Step 2: p9io poweroffループを特定する

ジャーナルに「docker.service起動 → 約15秒後にpower off」のパターンが出ていれば `#13435`。

```bash
# 直近のpoweroff回数とp9ioエラーを数える
sudo journalctl --since '-20 min' | grep -cE 'power off now'
sudo journalctl --since '-20 min' | grep -cE 'AcceptAsync|p9io'
```

`p9io.cpp:258 (AcceptAsync) Operation canceled` が連発していれば確定です。

### Step 3: 9P境界を削り、WSLを更新する

`/etc/wsl.conf` でWindowsドライブの自動マウント（9P）を切ると、クラッシュ面が激減します。

```ini
[boot]
systemd=true

[automount]
enabled = false
mountFsTab = false
```

そして本命の修正はプラットフォーム更新です。

```powershell
wsl --update --pre-release   # #13435 修正を含む新ビルドへ
wsl --shutdown               # 適用
```

### Step 4: 「ローカルは正常、edgeは停止」の矛盾を確認する

`cloudflared` の `/ready` と、Cloudflareダッシュボードの**両方**を見ます。

```bash
# ローカル側（同一Dockerネットワークの別コンテナから）
docker exec nexus-lb sh -c "wget -qO- http://nexus-tunnel:2000/ready"
# → {"status":200,"readyConnections":4} でも安心しない
```

ダッシュボード（Networks → Tunnels）で **アクティブなレプリカ / ステータス**を確認。ここが `0 / 停止` なら、**ローカルの"ready"は信用してはいけません**。

### Step 5: 真犯人 —— SIGTERMループとkeepalive喪失

トンネルログに `graceful shutdown due to signal terminated` が周期的に出ていたら、コンテナが外部からSIGTERMされ続けています。今回の犯人は、WSLディストロを保持し続ける `sleep infinity` プロセスの消失でした。

```bash
# keepalive(sleep infinity)が生きているか
ps -ef | grep '[s]leep infinity'    # 0個なら黒
```

WSLは、ディストロを保持するプロセスが無いと数十秒周期でpoweroffを試み、その巻き添えで `docker.service` が停止し、トンネルがSIGTERMで死にます。復旧は、既存のkeepaliveタスクを起動するだけ。

```powershell
Start-ScheduledTask -TaskName 'WSLKeepAlive'
Start-ScheduledTask -TaskName 'WSL2-KeepAlive'
```

keepaliveが入ればループが止まり、ループが止まればkeepaliveも死ななくなる（**自己安定**）。トンネルが数分安定すると、Cloudflareがレプリカを認識し、`530` は `200` に変わります。

---

## 🧱 壁にぶつかった瞬間と乗り越え方

一番苦しかったのは、**「WSLを更新してVMは安定したのに、530が消えない」**局面でした。

第2層（p9io）を倒し、VMは3時間以上落ちなくなった。ここで9割方「勝った」と思っていました。なのに、外からアクセスすると相変わらず `530`。origin側は完璧に健全——ランキングも描画できている。なのに繋がらない。

正直、心が折れかけました。「もう自分の手の届く範囲（origin側）に原因は無いのでは」と、一度は "Cloudflare側の問題です" と結論づけかけたほどです。

### 発見した突破口

諦める前に、もう一度だけ**「自分の操作ログ」を疑いました**。

思い返せば、この日わたしは調査のために `wsl --shutdown` を何度も打っていた。そして、ディストロを保持する keepalive タスクは **Windowsのブート時にしか起動しない**設計だった。

「——もしかして、私自身の `wsl --shutdown` が、keepaliveを殺し続けていたのでは？」

`ps -ef | grep 'sleep infinity'` の結果は **`0`**。ビンゴでした。真犯人は、外部の障害ではなく、**調査の過程で自分が作り出していた**のです。

### この失敗から学んだこと

**「動いている証拠」も「自分は無実だという前提」も、両方疑う。** 表面のエラーコード（530）は、5つ下の階層で起きている出来事の"影"に過ぎませんでした。

---

## 🎓 この経験から得た3つの教訓

### 教訓1：メトリクスは「どちらの視点か」を必ず確認する

`cloudflared /ready = 4本healthy` は嘘ではありません。**ローカルから見た真実**です。一方、Cloudflareダッシュボードの「レプリカ0」も真実——**edgeから見た真実**。障害は往々にして、この2つの視点が食い違う場所に潜んでいます。片方だけを信じた瞬間、迷宮が始まります。

### 教訓2：もっともらしい仮説ほど、証拠で殺す

「ClickHouseが原因では」という仮説は自然でした。でも推測で再起動をかけていたら、無実のCHをいじって状態をさらに悪化させていたはず。**IPを見る、healthを見る、originを直接叩く**——事実を1つずつ確認したから、CHを容疑者リストから外して真犯人に集中できました。

### 教訓3：障害の"共犯者"は、自分の操作かもしれない

今回の最深部の原因は、外部バグではなく **「調査のための `wsl --shutdown` が keepalive を殺していた」**という自作自演でした。ログを読むとき、監視対象だけでなく**自分がその日打ったコマンドの副作用**も時系列に並べる。これが真因発見の決定打になりました。

---

## 💡 実践Tips・よくあるエラーと解決法

<!-- qiita-section -->

WSL2 + Docker + cloudflared 構成で「サイトが落ちた」時に、上から順に叩くと切り分けが速いコマンド集です。

### Tips 1: WSLが「Running」でも死んでいるか判定する

`wsl --list` の表示は当てになりません。中で1コマンド叩いて、返らなければハングです。

```bash
timeout 25 wsl.exe -d Ubuntu -e bash -lc 'echo ALIVE' ; echo "rc=$?"
# rc=124 → ハング。wsl --shutdown でクリーン再起動
```

### Tips 2: WSLの p9io poweroffループ（microsoft/WSL #13435）

`docker.service` 起動の直後に `systemd-logind: The system will power off now!` が周期的に出るのが特徴。

```bash
# 直近20分のpoweroff回数（多発していればループ）
sudo journalctl --since '-20 min' | grep -cE 'power off now'
# p9ioエラー
sudo journalctl --since '-20 min' | grep -E 'AcceptAsync|p9io' | tail
```

対処は「9P境界を削る」＋「WSL更新」の合わせ技。

```ini
# /etc/wsl.conf … Windowsドライブの自動マウント(9P)を無効化
[automount]
enabled = false
mountFsTab = false
```

```powershell
wsl --update --pre-release   # #13435修正を含む新ビルドへ
wsl --shutdown
```

### Tips 3: cloudflared が「ローカルはready、edgeは停止」

トンネルの `/ready` が正常でも、Cloudflareダッシュボードで **アクティブなレプリカ=0 / ステータス=停止** なら、コンテナが**周期的にSIGTERMされている**可能性大。ログの時系列を見る。

```bash
# 登録直後にSIGTERMが出ていないか
docker logs nexus-tunnel --since 10m 2>&1 \
  | grep -E 'Registered|graceful shutdown|signal terminated'
```

`Registered → 数十秒後に graceful shutdown due to signal terminated` の反復が見えたら、外部からコンテナが殺され続けている。

### Tips 4: WSLディストロが数十秒周期で落ちる → keepaliveを確認

`wsl --shutdown` を繰り返した後などに起きがち。ディストロを保持する `sleep infinity` が消えると、WSLが idle poweroff を繰り返し、Docker→トンネルが巻き添えで落ちる。

```bash
# keepaliveが生きているか（0個なら黒）
ps -ef | grep '[s]leep infinity'
```

```powershell
# 既存のkeepaliveタスクを起動して復旧（Windows側）
Start-ScheduledTask -TaskName 'WSLKeepAlive'
Get-Process wsl | Measure-Object   # プロセスが増えれば保持できている
```

keepaliveを入れるとpoweroffループが止まり、Cloudflareがレプリカを再認識して `530→200` に戻ります。

### Tips 5: ClickHouse ghost attachment（DNSで引けない）

コンテナがネットワークから外れて、固定IPを失いDNS解決できなくなる現象。

```bash
# CHがネットワークに正しいIPで居るか
docker inspect nexus-clickhouse \
  --format '{{range $k,$v := .NetworkSettings.Networks}}{{$k}}({{$v.IPAddress}}){{end}}'
# 空 or 想定外IPなら ghost。再接続する:
docker network disconnect -f nexus-network nexus-clickhouse
docker network connect --ip 172.21.0.10 nexus-network nexus-clickhouse
docker compose restart nexus-aggregator nexus-web-blue nexus-web-green
```

<!-- /qiita-section -->

---

## ❓ よくある質問（FAQ）

### Q1: `wsl --update` が効かないと聞きましたが？

A: バグ修正がまだそのビルドに載っていない時期だと効きません。今回は `--pre-release` で当日リリースの新ビルド（2.9.3）を掴んだのが効きました。**更新前に、その修正がどのバージョンで入ったかを確認**するのが確実です。

### Q2: `automount=false` にするとWSLから `/mnt/c` が使えなくなりませんか？

A: なります。ただしコンテナのバインドマウントが `/mnt/c` に依存していないなら実害は小さいです（プロジェクトをext4側に置いていれば問題なし）。必要な時だけ `\\wsl$` 経由で参照するか、設定を戻します。

### Q3: keepaliveって普段は意識しなくていいのでは？

A: 通常のPC再起動ならブート時にkeepaliveタスクが自動起動するので不要です。**問題になるのは「手動で `wsl --shutdown` を何度も打った後」**。この時だけは手動でkeepaliveを起動し直してください。

---

## 📝 まとめ：今日からできるアクションプラン

多層障害を最短で解くための順番です。

1. **表面のエラーを"影"だと疑う**: 530は結果。原因は数階層下にあると仮定する
2. **メトリクスは視点を確認**: 「ローカルからの正常」と「相手からの正常」は別物
3. **仮説は証拠で殺す**: IP・health・直接叩き、で容疑者を1つずつ外す
4. **自分の操作ログも時系列に並べる**: 真犯人は自分の副作用かもしれない

> 📌 まずは、あなたの障害の「1つ下の階層」を見に行ってください。
> ログを"時系列で"読むだけで、見えていなかった真因が浮かびます。

---

## 🙏 おわりに：伝えたかったこと

最後まで読んでいただき、ありがとうございました。

この日、私は何度も「もう自分の手の届く範囲に原因は無い」と思いました。Cloudflareのせいにして終わりにしかけた瞬間もありました。

でも、あと一歩だけログを疑い、あと一つだけ「自分は無実か？」を疑ったら、真犯人は驚くほどシンプルな `sleep infinity` の消失でした。

**障害対応は、犯人探しではなく"層を剥がす"作業です。** 表面の派手なエラーに気を取られず、1枚ずつ、静かに剥がしていく。その先に、たった1行で解決する真因が待っています。

同じように多層障害の沼で溺れている誰かの、浮き輪になれたら嬉しいです。

質問や「うちではこうだった」という体験談があれば、ぜひコメントやSNSで教えてください。すべて読みます。

**あなたのデバッグを、心から応援しています。**

---

**この記事が役に立ったら、ぜひシェアをお願いします！**
あなたのシェアが、同じ沼にいる誰かの助けになります。