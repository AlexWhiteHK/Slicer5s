# Lotus V7 · Coming Soon — 预告片

Lotus AI Lab（Higan Holdings Limited 旗下）V7 系列更新的 2 分钟预告：以时间线科普文生图模型从 2014 到 2026 的演进，最后落到 **Lotus Realistic V7** 与 **Lotus Anime Diffusion V7** 两条产品线。

- 成片：`dist/lotus-v7-teaser.mp4`（1920×1080，60 fps，H.264 + AAC 256k，内嵌 6 个章节标记）
- 交互版：`index.html`（同一套时间轴，可暂停、拖动、按章节跳转）
- 配乐：原创，由 `tools/compose_music.py` 用 numpy 逐音合成，无第三方素材

## 叙事

全片只有一条线索：一句提示词 `a penguin running across water`。

它在开场由一个朱色圆点展开成输入框，随后在十二年里被一代代模型"读"：先是噪声与色块，再是 32×32、64×64 的像素，然后是扩散、潜空间、Transformer。画面里始终是同一只企鹅，清晰度随时代提高。到 2025 年，提示词被堆满 `masterpiece, best quality, 8k…`，这是全片唯一的冲突点。之后一切停下、回到最初那句朴素的提示词，输入框左侧的星形图标升起、化成莲花，引出 V7。

Realistic V7 用 DiT 逐块去噪的方式第一次把这只企鹅完整呈现，再从企鹅所在位置向外"换一个世界"（沙漠 → 雨林，两张图的主体位置完全重合）。Anime Diffusion V7 从"质量在哪里"的示意曲线出发，曲线上的点展开成插画卡片，线稿先画出、颜色从角色面部向外晕开。结尾四张作品收拢进莲花，落版 Coming Soon。

## 分镜与文案

小节线每 3 秒一条（80 BPM），所有场景切换都落在小节线上。

| 时间 | 章节 | 画面 | 中文 | English |
| --- | --- | --- | --- | --- |
| 0:00 | 序章 | 朱色圆点 → 输入框，打字 | 每一张图，都从一句话开始。 | Every image begins with a sentence. |
| 0:07 | | 输入框移向右上，时间轴展开 | 教会机器读懂它，用了十二年。 | Teaching a machine to read it took twelve years. |
| 0:12 | 2014 · GAN | 噪声争吵成一团色块；生成器 ⇄ 判别器 | 生成对抗网络登场：一个网络负责画，另一个负责挑错。 | GANs arrive: one network draws, another points out what is wrong. |
| 0:18 | 2015–16 · alignDRAW / T2I GAN | 词语落进画面，32×32 → 64×64 像素 | 第一次，机器照着一句话作画。只有几十个像素见方，勉强看出轮廓。 | For the first time, pictures from a caption… |
| 0:24 | 2020 · DDPM | 前向加噪 x₀→x₁₀₀₀，再反向去噪；公式与五帧示意 | 扩散模型：先学会把一张图一点点变成噪声，再学会把这条路一步一步走回来。 | Diffusion: learn how an image dissolves into noise, then walk the path back. |
| 0:33 | 2021 · CLIP / DALL·E | 提示词中的词连线到画面区域；文字与图像向量对齐 | CLIP 把文字和图像放进同一个空间，模型开始真正听懂描述。 | CLIP places words and pictures in one space. |
| 0:39 | 2022 · Latent / Stable Diffusion | 编码到 1/8 潜空间去噪再解码；卡片裂成社区变体马赛克 | 在压缩后的潜空间里去噪…权重开源，二次元模型也由此兴起。 | Denoise in a compressed latent space… Open weights. |
| 0:48 | 2023 · DiT | 切块 16×7，块飞成 token 序列，注意力弧线 | Transformer 接手去噪：每一块都是一个 token。 | Transformers take over denoising. |
| 0:54 | 2024 · MMDiT / Rectified Flow | 提示词的词变成文字 token 并入序列；参数量级条 10⁸→10¹⁰ | 文字与图像并入同一条序列，参数从数亿走向百亿。 | Text and image share one sequence… |
| 1:00 | 2025 · 提示词工程 | 输入框被 40 个质量词条撑满、溢出 | 模型越来越强，好图却依然藏在提示词里。 | The good images still hid inside the prompt. |
| 1:09 | 转折 | 全部停下，词条飘散；输入框回到开场位置 | 如果，质量本就该属于模型？ | What if the quality belonged to the model? |
| 1:15 | | 星形图标升起，绽放为莲花；时间轴走到 2026 · V7 | | |
| 1:18 | V7 | Lotus V7 / 更高的下限 / 两个产品标签 / 即将推出 | 更高的下限。 | A higher floor. |
| 1:22 | Realistic V7 | "Realistic V7" 标签展开成画卡（container transform），DiT 逐块去噪到成片 | 基于 Diffusion Transformer 的照片级写实模型。 | Photoreal generation on a diffusion transformer. |
| 1:27 | | 缓推镜头，光线 / 材质 / 倒影标注 | 把能力花在光线、材质与每一处细节上。 | Capacity spent on light, material and every detail. |
| 1:30 | | 从企鹅位置向外晕开，沙漠 → 雨林 | 同一个主角，任意一个世界。 | One subject. Any world. |
| 1:36 | Anime Diffusion V7 | "质量在哪里"示意曲线（明确标注为示意） | 朴素的提示词，也能得到完成度很高的插画。 | Plain prompts, finished illustration. |
| 1:40 | | 曲线上的点展开成画卡：线稿 → 从面部向外上色 | 画风由实验室设计，而不是数据的平均值。 | A look designed in the lab, not an average of the data. |
| 1:45 | | 第二张作品并排入场，樱花瓣 | 换一个角色、一个场景，风格依旧稳定。 | New character, new scene. The same steady hand. |
| 1:51 | 即将推出 | 四张作品画廊横移，收拢进莲花 | 一个实验室，两条图像产品线。 | One lab. Two lines of image models. |
| 1:55 | | 落版：Lotus V7 · Realistic V7 · Anime Diffusion V7 · 即将推出 · Lotus AI Lab / A Higan Holdings company / lotuslab.ai | | |

历史段画面右下角常驻"示意动画，非模型输出"；Anime 曲线标注"示意图，非实测数据"，与官网 lotus 页面的表述一致。

## 可打断

- 成片内嵌章节（0:00 / 0:12 / 1:06 / 1:18 / 1:36 / 1:51），播放器可直接跳转。每个章节起点都是音乐小节线上的静止构图，可以从这些时间点直接剪成独立短片。
- `index.html` 交互版：空格暂停 / 继续，← → 跳章节，点击进度条任意定位；`?t=90` 从指定秒开始。

## 视觉规范

- 底色 `#f7f6f2`（纸色），四个柔和色团随章节变换色调（历史偏冷、Realistic 偏沙色、Anime 偏樱粉）。
- 强调色为 Lotus 的朱 `#d4553f`；莲花五瓣使用柔化的 Google 四色 + 朱色，multiply 叠色。
- 字体：Google Sans Flex（标题 / 界面）、Noto Sans SC（中文）、Source Serif 4 Italic（英文副句）、Google Sans Code（技术标注）。`tools/fetch_fonts.py` 只下载实际用到的字形。
- 动效：Material 3 emphasized 曲线（`cubic-bezier(.05,.7,.1,1)`）、container transform（标签 → 卡片、曲线点 → 卡片）、shared-axis 章节过渡；文字按字 / 按词带模糊淡入；全片叠加轻微颗粒以避免渐变色带。

## 配乐

80 BPM，D 大调，40 小节正好 120 秒。毡化钢琴、合成铺底 pad、FM 钟音、sub bass、轻底鼓与沙锤，全部为加法 / FM 合成，最后过卷积混响（合成脉冲响应）、总线压缩与软限幅，整体响度约 −15.7 LUFS。

| 小节 | 时间 | 内容 |
| --- | --- | --- |
| 1–4 | 0–12 s | Dmaj9 → Bm9 → Gmaj9 → Asus4，稀疏钢琴；打字声、发送音效 |
| 5–20 | 12–60 s | Gmaj9 → D/F# → Em9 → A7sus4 循环；琶音从四分音符逐步加密到八分，每个年份节点一声低音 + 钟音，2021 起加钟音副旋律，2022 起加底鼓 |
| 21–23 | 60–69 s | 十六分琶音与 40 个词条弹出音叠加，噪声上升，拥挤感到顶 |
| 24 | 69 s | 一切切断，只留混响尾巴与三个钢琴单音（呼吸） |
| 25–26 | 72–78 s | 开场动机再现，莲花绽放时钟音上行琶音，推向 78 s 重拍 |
| 27–37 | 78–111 s | D → A/C# → Bm7 → Gmaj7 主旋律，Anime 段加入钟音八度叠奏与拨弦 |
| 38–40 | 111–120 s | 终止在 Dmaj9，开场动机收尾 |

## 构建

```sh
python3 -m http.server 8123 --bind 127.0.0.1 &          # 本目录
pip install numpy scipy pillow fonttools pyloudnorm imageio-ffmpeg
python3 tools/fetch_fonts.py                            # 修改文案后需重跑
python3 tools/compose_music.py "$FFMPEG"                # dist/music.wav, assets/music.m4a
NODE_PATH=$(npm root -g) node tools/render.cjs stills 12.5,85   # 单帧检查 → dist/stills/
FFMPEG=$FFMPEG NODE_PATH=$(npm root -g) node tools/render.cjs video --fps 60 --workers 4
python3 tools/mux.py "$FFMPEG"                          # → dist/lotus-v7-teaser.mp4
```

`FFMPEG` 需带 libx264（`imageio-ffmpeg` 自带的静态版即可）；渲染使用 Playwright 的 Chromium。

## 史实依据

| 节点 | 出处 |
| --- | --- |
| GAN | Goodfellow et al., *Generative Adversarial Nets*, 2014 |
| alignDRAW | Mansimov et al., *Generating Images from Captions with Attention*, 2015（32×32） |
| Text-to-Image GAN | Reed et al., *Generative Adversarial Text to Image Synthesis*, 2016（64×64） |
| DDPM | Ho, Jain & Abbeel, *Denoising Diffusion Probabilistic Models*, 2020（T = 1000） |
| CLIP / DALL·E | Radford et al.; Ramesh et al., 2021 |
| Latent Diffusion / Stable Diffusion | Rombach et al., 2021–22（下采样因子 8）；Stable Diffusion 权重 2022 年 8 月公开 |
| DiT | Peebles & Xie, *Scalable Diffusion Models with Transformers*, 2022 预印本 / ICCV 2023 |
| MMDiT · Rectified Flow | Esser et al., *Scaling Rectified Flow Transformers for High-Resolution Image Synthesis*, 2024；同年 FLUX.1 为 12B 参数 |

产品描述取自 Lotus AI Lab 官网文案（`AutoHandling2027/lotus/index.html`）：Realistic V7 为 diffusion transformer、重点在 skin / light / material；Anime Diffusion V7 为 "higher floor"、house style、its own look。片中未引用任何未公开的基准数字。

## 素材

`assets/img/` 中四张图为模型样张：`anime-*` 由 Lotus Anime Diffusion V7 生成，`realistic-*` 由 Lotus Realistic V7 生成。历史段的像素化、模糊、噪声、潜空间、线稿等效果均由同一张 Realistic 样张在浏览器中实时处理得到，属于示意。
