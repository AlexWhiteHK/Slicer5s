# Lotus V7 · Coming Soon — 预告片（v2）

Lotus AI Lab（Higan Holdings Limited 旗下）V7 系列更新的 2 分钟预告。全英文画面，用一个比喻讲完文生图模型的原理，最后落到 **Lotus Realistic V7** 与 **Lotus Anime Diffusion V7**。

- 成片：`dist/lotus-v7-teaser.mp4`（1920×1080，60 fps，H.264 + AAC，内嵌 7 个章节）
- 交互版：`index.html`（同一套时间轴，可暂停、拖动、按章节跳转）
- 配乐：原创，`tools/compose_music.py` 用 numpy 逐音合成

## 切入点

> Every block of marble holds a statue. Every field of noise holds an image.

整支片只用"雕塑家"这一个比喻：扩散模型就是在噪声里"凿"出图像。场景是一座古典画廊，一个连续镜头走完全程：

1. 黑暗中一束顶光照着底座上的大理石块；石块松散成一团噪声点云。
2. 底座铜牌上刻出一句话：*A lotus in full bloom.* ——模型的两样输入：噪声与句子。
3. 镜头转到画架：一幅古希腊陶罐画逐步溶解成噪声、再一步步复原——训练就是学会"撤销一步加噪"。
4. 回到石块：40 步，每一步去掉一点噪声，点云收拢成一朵大理石莲花。
5. 句子里的词浮出成卡片，用金线连到花心和花瓣；把 *full bloom* 翻成 *bud*，同一团噪声变成花苞，再翻回来重新盛开。
6. 侧后方展台上先堆出一个陶土小样（潜空间草模），解码器把细节还原到大雕塑上。
7. 画面被切成 18 块，飞成一圈，每一块用金线与其余所有块相连（Transformer 注意力）。
8. 痛点：朴素的句子只凿出粗坯；堆上 *masterpiece, best quality, 8k…* 才变精细；魔法词随后碎落成尘。
9. 灯光重起：Lotus V7 把质量放进模型本身。镜头上摇到拱门上方的刻字 **LOTUS V7 / REALISTIC V7 · ANIME DIFFUSION V7 / COMING SOON**。
10. 左侧展墙：Realistic V7 画作按 DiT 方式逐块去噪成片；第二幅从企鹅处向外换成雨林。
11. 右侧展墙：Anime Diffusion V7 先出线稿，再从角色面部向外上色；第二幅同样。
12. 拉回画廊正面：莲花雕塑居中，两侧挂着四幅作品，拱门上方刻着标题。

四张样张只在展墙上各出现一次；科普部分的演示全部是程序生成的内容（点云、网格、陶罐、体素、切块）。

## 文案（英文，逐章）

| 时间 | 章节 | Line |
| --- | --- | --- |
| 0:02 | — | Every block of marble holds a statue. / Every field of noise holds an image. |
| 0:12 | 01 — Noise and a sentence | An image model begins with two things: / pure noise, and a sentence. |
| 0:21 | 02 — Learning | First, it studies millions of pictures as they dissolve into noise… / …and learns to undo a single step. |
| 0:33 | 03 — Carving | Then it starts from pure noise and repeats that one step, over and over. / Each pass removes a little noise, until only the image is left. |
| 0:45 | 04 — Steering | At every step, the sentence decides what to keep. / Change a word, and the same noise becomes something else. |
| 0:54 | 05 — The sketch | Carving at full size is slow, so it first shapes a small, compressed sketch… / …then a decoder restores the detail. |
| 1:03 | 06 — The workshop | Modern models cut the picture into patches… / …and let every patch consult every other, so the whole stays coherent. |
| 1:12 | 07 — The catch | Yet most models are only as good as the prompt. / Plain words, rough work. Magic words, fine work. |
| 1:21 | Lotus V7 | Lotus V7 moves the quality into the model. / Two new models. Coming soon. |
| 1:28 | Realistic V7 | Photoreal images on a diffusion transformer. / Built for light, material and texture. / One subject. Any world. |
| 1:40 | Anime Diffusion V7 | Finished illustration from a plain sentence. / A house style — designed, not averaged. / Consistent across characters and scenes. |
| 1:51 | Coming soon | 刻字标题 + LOTUS AI LAB — A HIGAN HOLDINGS COMPANY |

画面标注（小号无衬线）：NOISE、SENTENCE、TRAINING、STEP 01–40 / 40、LATENT SKETCH · 1/8 SCALE、DECODER、PATCH → TOKEN、ATTENTION。

## 视觉

- **伪 3D**：自写透视相机（Hermite 曲线插值关键帧，连续一镜到底）。建筑、底座、体素在 2D 画布上投影并做近裁剪；雕塑是 3.8 万个带 z-buffer 的点加实体网格；画框、画架、立柱、刻字用 CSS `matrix3d` 贴在同一相机下，浏览器负责遮挡排序。
- **配色**：象牙、石色、墨色为主；陶土色 `#c4633f` 与黄铜 `#b08d57` 只作点缀（章节标签、金线、铜牌、刻字 COMING SOON）。
- **字体**：Cormorant Garamond（正文衬线）、Cinzel（罗马碑刻）、Instrument Sans（标签）、IBM Plex Mono（计数）。
- **质感**：顶光光束与浮尘、地面光斑、壁龛纵深、线脚、静态胶片颗粒、暗角；开场从黑暗中逐渐亮灯，第 07 章结尾暗下再重新亮起。

## 配乐

80 BPM，D 大调，40 小节正好 120 秒，每个章节落在小节线上。

| 时间 | 内容 |
| --- | --- |
| 0–12 s | 大提琴长音、稀疏钢琴；石块松散时的碎粒声 |
| 12–21 s | 铭牌逐字刻出（金属刻字声） |
| 21–33 s | 竖琴式拨弦；加噪时噪声上扬，复原时倒放 |
| 33–45 s | 40 声"凿击"沿音阶上行，成形时钟音和弦 |
| 45–54 s | 钢琴旋律；翻卡气声；花苞时和声转暗，盛开时回到大调 |
| 54–63 s | 体素落定的木质轻敲；解码器上扬微光 |
| 63–72 s | 脉冲节拍进入，金线像玻璃叮声 |
| 72–81 s | 不协和铺底与魔法词刻字声；碎落成尘；约 1.5 秒的呼吸 |
| 81–111 s | 主题完整进入（钢琴旋律、低音、轻鼓）；Anime 段钟音八度叠奏 |
| 111–120 s | 回到 Dmaj9，开场动机收尾 |

## 构建

```sh
python3 -m http.server 8123 --bind 127.0.0.1 &
pip install numpy scipy pillow fonttools pyloudnorm imageio-ffmpeg
python3 tools/fetch_fonts.py                              # 改动文案后需重跑
python3 tools/compose_music.py "$FFMPEG"                  # dist/music.wav, assets/music.m4a
NODE_PATH=$(npm root -g) node tools/render.cjs stills 46.5,90   # 单帧检查
FFMPEG=$FFMPEG NODE_PATH=$(npm root -g) node tools/render.cjs video --fps 60 --workers 4
python3 tools/mux.py "$FFMPEG"                            # → dist/lotus-v7-teaser.mp4
```

## 史实与表述

科普内容对应的真实机制：扩散模型的前向加噪与逐步去噪（DDPM, 2020）、文本条件引导（CLIP / classifier-free guidance）、潜空间扩散（Latent Diffusion, 下采样因子 8）、Diffusion Transformer（DiT：切块成 token、全局注意力）。产品描述只取自 Lotus AI Lab 官网文案（`AutoHandling2027/lotus/index.html`）：Realistic V7 基于 diffusion transformer，专注光线与材质；Anime Diffusion V7 强调更高的下限与自有画风。片中不引用任何基准数字。

## 素材

`assets/img/` 中四张图为模型样张：`anime-*` 由 Lotus Anime Diffusion V7 生成，`realistic-*` 由 Lotus Realistic V7 生成。
