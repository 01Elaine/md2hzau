---
title_cn: 基于多模态融合的跌倒检测方法研究
title_en: Research on Fall Detection Method Based on Multi-Modal Fusion
author: 张三
author_en: ZHANGSAN
major: 人工智能
major_en: ARTIFICIAL INTELLIGENCE
instructor: 李四
instructor_en: SI LI
instructor_title: 副教授
instructor_title_en: ASSOCIATE PROFESSOR
student_id: 2021317220XX
class_name: 人工智能2101班
degree: 工学学士学位
date_cn: 二〇二五年六月
date_en: JUNE，2025
signature_date: 2025年6月14日
year: 2025
---

## 摘要

跌倒事件是老年人群体面临的重大安全威胁，准确、及时的跌倒检测对于减少伤亡具有重要意义。传统的单模态检测方法在复杂场景下鲁棒性不足，难以应对光照变化、遮挡等干扰。本文提出一种基于多模态融合的跌倒检测方法，综合利用 RGB 视频、骨骼关键点与惯性传感器三类信号，通过注意力机制对不同模态特征进行自适应加权融合，在公开数据集上取得了 $F_1 = 0.923$ 的检测精度。

实验结果表明，多模态融合策略相比单一模态基线提升了 8.6 个百分点，在遮挡场景下的鲁棒性优势更为显著。本研究为智慧养老场景下的跌倒检测提供了一种实用的技术方案。

**关键词：** 跌倒检测；多模态融合；注意力机制；骨骼关键点；惯性传感器

## Abstract

Fall events pose a major safety threat to the elderly population, and accurate, timely fall detection is essential for reducing casualties. Traditional single-modal detection methods lack robustness in complex scenes and struggle with interference such as illumination changes and occlusion. This paper proposes a multi-modal fusion-based fall detection method that integrates RGB video, skeleton keypoints, and inertial sensor signals. By employing an attention mechanism for adaptive weighted fusion of different modal features, the method achieves an $F_1 = 0.923$ detection accuracy on public datasets.

Experimental results demonstrate that the multi-modal fusion strategy improves performance by 8.6 percentage points over single-modal baselines, with more pronounced robustness advantages in occlusion scenarios. This study provides a practical technical solution for fall detection in smart elderly care environments.

**Keywords:** Fall Detection; Multi-Modal Fusion; Attention Mechanism; Skeleton Keypoints; Inertial Sensors

## 缩略语

- RGB: Red Green Blue
- IMU: Inertial Measurement Unit
- GCN: Graph Convolutional Network
- LSTM: Long Short-Term Memory

## 第1章 绪论

### 1.1 研究背景与意义

随着人口老龄化加剧，跌倒已成为 65 岁以上人群意外伤害死亡的首要原因[1]。据世界卫生组织统计，全球每年约有 68 万人死于跌倒相关伤害[2]。

智能跌倒检测系统能够在跌倒发生后第一时间发出告警，为急救争取宝贵时间。与人工看护相比，自动化检测系统具有全天候、低成本、覆盖范围广等优势，具有重要的应用价值。

### 1.2 国内外研究现状

#### 1.2.1 基于视觉的方法

基于视觉的跌倒检测方法利用摄像头采集的图像或视频信息进行分析。早期工作主要基于背景差分和光流估计[3]，近年来深度学习方法取得了显著进展。

#### 1.2.2 基于传感器的方法

惯性测量单元（IMU）因其低功耗、高采样率的特点被广泛应用于跌倒检测[4]。加速度计和陀螺仪的组合能够有效捕捉运动加速度突变特征。

### 1.3 本文研究内容

本文的主要研究内容包括以下三个方面：

（1）构建多模态数据采集与预处理 pipeline，统一不同来源数据的时间戳对齐策略

（2）设计跨模态注意力融合模块，实现 RGB、骨骼、IMU 三路特征的自适应加权

（3）在公开数据集上进行系统评估，与主流基线方法进行对比实验

### 1.4 论文结构

本文共分为五章。第 2 章介绍相关理论基础；第 3 章详细阐述所提方法；第 4 章报告实验结果；第 5 章总结全文并展望未来工作。

## 第2章 相关理论基础

### 2.1 骨骼关键点估计

骨骼关键点估计是计算机视觉领域的基础任务，旨在从图像中定位人体关节位置。主流方法包括自顶向下（Top-Down）和自底向上（Bottom-Up）两类范式。

本文采用 OpenPose[5] 提取 18 个关键点，包括颈部、肩部、肘部、腕部、髋部、膝部、踝部等关节，坐标归一化到 $[0, 1]$ 范围内。

### 2.2 注意力机制

注意力机制（Attention Mechanism）最早由 Bahdanau 等人[6]在神经机器翻译中提出，其核心思想是对输入序列中不同位置赋予不同权重。对于多模态融合，注意力权重可形式化为：

$$
\alpha_i = \frac{\exp(e_i)}{\sum_{j=1}^{M} \exp(e_j)}, \quad e_i = f(h_i)
$$

其中 $M$ 为模态数量，$h_i$ 为第 $i$ 个模态的特征向量，$f(\cdot)$ 为打分函数。

### 2.3 多模态融合策略

多模态融合可在特征级（Feature-level）或决策级（Decision-level）进行。本文采用特征级融合，通过注意力权重对各模态特征进行加权求和，获得统一的融合表示。

## 第3章 方法设计

### 3.1 整体框架

如图所示，本文方法由三个特征提取分支和一个融合模块组成：

![Overall Architecture of the Proposed Multi-Modal Fall Detection Method](figures/fig_architecture.png)
**图3-1** 多模态跌倒检测整体框架 | Overall Architecture of the Proposed Method

- RGB 分支：基于 ResNet-50 提取空间外观特征
- 骨骼分支：基于图卷积网络（GCN）提取结构特征
- IMU 分支：基于 LSTM 提取时序动态特征

两路分支对比如子图所示：

![RGB Feature Extraction Branch](figures/fig_architecture.png)
![Skeleton Feature Extraction Branch](figures/fig_architecture.png)
**图3-2** RGB 与骨骼特征提取分支对比 | Comparison of RGB and Skeleton Feature Extraction Branches

### 3.2 跨模态注意力融合

设三路特征分别为 $\mathbf{f}_v \in \mathbb{R}^{512}$、$\mathbf{f}_s \in \mathbb{R}^{256}$、$\mathbf{f}_a \in \mathbb{R}^{128}$，经线性投影统一到 $d=256$ 维后，注意力融合计算如下：

$$
\mathbf{f}_{fused} = \sum_{i \in \{v,s,a\}} \alpha_i \cdot \mathbf{W}_i \mathbf{f}_i
$$

其中权重 $\{\alpha_i\}$ 由 Softmax 归一化的打分函数给出。

跨模态注意力融合的具体流程见算法1：

```algorithm
\caption{跨模态注意力融合}
\KwIn{三路特征 $\mathbf{f}_v, \mathbf{f}_s, \mathbf{f}_a$，投影矩阵 $\{\mathbf{W}_i\}$}
\KwOut{融合特征 $\mathbf{f}_{fused}$}
\For{$i \in \{v, s, a\}$}{
  $\tilde{\mathbf{f}}_i \leftarrow \mathbf{W}_i \mathbf{f}_i$\tcp*{线性投影到公共空间}
  $e_i \leftarrow \mathbf{w}^\top \tilde{\mathbf{f}}_i$\tcp*{打分}
}
$\{\alpha_i\} \leftarrow \mathrm{Softmax}(\{e_i\})$\;
$\mathbf{f}_{fused} \leftarrow \sum_i \alpha_i \cdot \tilde{\mathbf{f}}_i$\;
\Return{$\mathbf{f}_{fused}$}
```

### 3.3 损失函数

训练采用带类别权重的二分类交叉熵损失：

$$
\mathcal{L} = -\sum_{n} \left[ w_1 y_n \log \hat{y}_n + w_0 (1-y_n) \log(1-\hat{y}_n) \right]
$$

## 第4章 实验结果

### 4.1 数据集与实验设置

本文在 UR Fall Detection[7] 和 FDD[8] 两个公开数据集上进行评估。数据集划分采用 7:1:2 的训练/验证/测试比例，使用 Adam 优化器，初始学习率 $1 \times 10^{-4}$，批大小 32。

### 4.2 主要结果

**表4-1** 在 UR Fall Detection 数据集上与基线方法的比较 | Comparison with Baselines on UR Fall Detection Dataset

| 方法 | 精确率 | 召回率 | $F_1$ | 准确率 |
|------|--------|--------|--------|--------|
| CNN-LSTM | 0.871 | 0.853 | 0.862 | 0.889 |
| ST-GCN | 0.884 | 0.876 | 0.880 | 0.901 |
| IMU-only | 0.862 | 0.841 | 0.851 | 0.878 |
| **本文方法** | **0.931** | **0.915** | **0.923** | **0.941** |

实验结果表明，本文方法在所有指标上均优于对比基线，$F_1$ 较最优基线提升了 4.3 个百分点。

### 4.3 消融实验

为验证各模态的贡献，进行消融实验，结果如下：

**表4-2** 消融实验结果 | Ablation Study Results

| 配置 | $F_1$ | $\Delta F_1$ |
|------|--------|--------------|
| RGB only | 0.862 | — |
| + 骨骼 | 0.891 | +0.029 |
| + IMU | 0.905 | +0.043 |
| + 注意力融合 | **0.923** | **+0.061** |

## 第5章 总结与展望

### 5.1 工作总结

本文提出了一种基于多模态融合的跌倒检测方法，主要贡献包括：

（1）设计了跨模态注意力融合模块，实现三路异构特征的自适应整合

（2）在两个公开数据集上验证了方法有效性，$F_1$ 达到 0.923

（3）消融实验证明了注意力机制的必要性，单独去除任一模态均导致性能下降

### 5.2 未来展望

未来工作将从以下方向继续探索：

- 引入轻量化网络结构，降低边缘设备部署成本
- 扩展到多人场景的跌倒检测
- 研究隐私保护条件下的视频分析方案

## 参考文献

```bibtex
@article{ref1,
  author  = {World Health Organization},
  title   = {Falls},
  year    = {2021},
  url     = {https://www.who.int/news-room/fact-sheets/detail/falls}
}

@article{ref2,
  author  = {Montero-Odasso, Manuel and others},
  title   = {World guidelines for falls prevention and management for older adults},
  journal = {Age and Ageing},
  year    = {2022},
  volume  = {51},
  number  = {9}
}

@article{ref3,
  author  = {Vishwakarma, Dinesh Kumar and Rawat, Priti and Kapoor, Rajkumar},
  title   = {A review of background subtraction algorithms for video surveillance},
  journal = {Multimedia Tools and Applications},
  year    = {2013},
  volume  = {67},
  pages   = {1--29}
}

@article{ref4,
  author  = {Casilari, Eduardo and Santoyo-Ram{\'o}n, Jos{\'e}-Antonio and Cano-Garc{\'i}a, Jos{\'e}-Manuel},
  title   = {Analysis of public datasets for wearable fall detection systems},
  journal = {Sensors},
  year    = {2017},
  volume  = {17},
  number  = {7}
}

@inproceedings{ref5,
  author    = {Cao, Zhe and Simon, Tomas and Wei, Shih-En and Sheikh, Yaser},
  title     = {{OpenPose}: Realtime Multi-Person 2D Pose Estimation using Part Affinity Fields},
  booktitle = {CVPR},
  year      = {2017}
}

@inproceedings{ref6,
  author    = {Bahdanau, Dzmitry and Cho, Kyunghyun and Bengio, Yoshua},
  title     = {Neural Machine Translation by Jointly Learning to Align and Translate},
  booktitle = {ICLR},
  year      = {2015}
}

@article{ref7,
  author  = {Kwolek, Bogdan and Kepski, Michal},
  title   = {Human fall detection on embedded platform using depth maps and wireless accelerometer},
  journal = {Computer Methods and Programs in Biomedicine},
  year    = {2014},
  volume  = {117},
  pages   = {489--501}
}

@inproceedings{ref8,
  author    = {Adhikari, Karan and Bouchachia, Hamid and Nait-Charif, Hammadi},
  title     = {Activity recognition for indoor fall detection using convolutional neural network},
  booktitle = {VISAPP},
  year      = {2017}
}
```

## 附录

### 主要实验环境配置

| 配置项 | 参数 |
|--------|------|
| 操作系统 | Ubuntu 20.04 LTS |
| GPU | NVIDIA RTX 3090 (24 GB) |
| 深度学习框架 | PyTorch 1.13.1 |
| Python 版本 | 3.9.7 |

## 致谢

本科四年的学习生活即将画上句点，值此毕业论文完成之际，谨向所有给予我帮助与支持的人致以诚挚的谢意。

首先，衷心感谢我的指导老师在课题选定、方案设计以及论文撰写过程中给予的悉心指导。老师严谨的治学态度和对科研的热情深深影响了我，受益终身。

感谢实验室的各位同学在日常讨论中提供的宝贵建议，感谢数据采集阶段参与实验的志愿者，没有你们的支持，本研究难以完成。

最后，感谢我的家人在四年学习中给予的无私支持与鼓励，是你们的陪伴让我得以走完这段充实的旅程。
