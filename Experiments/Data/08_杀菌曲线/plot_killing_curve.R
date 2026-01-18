#!/usr/bin/env Rscript
# W菌MOI优化杀菌曲线可视化
# 数据来源: Protocol kinetic-12h_W20260117.csv
# 日期: 2025-01-18

library(tidyverse)
library(scales)

# ============ 数据准备 ============

# 手动输入扣除空白后的OD600数据（从CSV Blank 600部分提取）
# 时间点：每15分钟，共49个读数

time_hours <- seq(0.25, 12.25, by = 0.25)  # 0:14:16 到 12:14:16

# W对照（6个重复取均值）
W_control <- c(0.333, 0.374, 0.401, 0.441, 0.469, 0.497, 0.521, 0.569, 0.620, 0.669,
               0.711, 0.744, 0.779, 0.808, 0.832, 0.857, 0.879, 0.908, 0.940, 0.971,
               0.998, 1.024, 1.053, 1.073, 1.096, 1.122, 1.144, 1.164, 1.186, 1.205,
               1.223, 1.241, 1.259, 1.277, 1.295, 1.313, 1.328, 1.343, 1.356, 1.369,
               1.381, 1.393, 1.406, 1.418, 1.429, 1.441, 1.452, 1.463, 1.475)

# W1 MOI=10 (WP1: B4,C4,D4 均值)
W1_MOI10 <- c(0.266, 0.316, 0.361, 0.414, 0.434, 0.411, 0.364, 0.179, 0.086, 0.091,
              0.101, 0.115, 0.133, 0.151, 0.173, 0.195, 0.223, 0.250, 0.278, 0.307,
              0.335, 0.365, 0.396, 0.426, 0.459, 0.494, 0.530, 0.567, 0.605, 0.647,
              0.693, 0.737, 0.784, 0.831, 0.856, 0.849, 0.863, 0.887, 0.907, 0.928,
              0.949, 0.971, 0.990, 1.010, 1.030, 1.048, 1.069, 1.088, 1.107)

# W1 MOI=1 (WP2: E4,F4,G4 均值)
W1_MOI1 <- c(0.270, 0.322, 0.361, 0.403, 0.445, 0.459, 0.446, 0.330, 0.169, 0.099,
             0.106, 0.116, 0.129, 0.145, 0.165, 0.191, 0.218, 0.251, 0.283, 0.316,
             0.351, 0.388, 0.426, 0.466, 0.510, 0.554, 0.600, 0.648, 0.700, 0.757,
             0.815, 0.869, 0.917, 0.957, 0.987, 1.011, 1.033, 1.050, 1.065, 1.081,
             1.096, 1.110, 1.125, 1.141, 1.157, 1.173, 1.192, 1.208, 1.225)

# W1 MOI=0.1 (WP3: B5,C5,D5 均值)
W1_MOI01 <- c(0.271, 0.319, 0.361, 0.414, 0.452, 0.471, 0.479, 0.510, 0.479, 0.265,
              0.154, 0.149, 0.163, 0.185, 0.221, 0.264, 0.317, 0.369, 0.418, 0.466,
              0.519, 0.564, 0.606, 0.650, 0.694, 0.738, 0.782, 0.828, 0.869, 0.893,
              0.911, 0.925, 0.943, 0.959, 0.972, 0.986, 1.000, 1.016, 1.030, 1.044,
              1.056, 1.069, 1.082, 1.095, 1.109, 1.122, 1.135, 1.150, 1.165)

# W1 MOI=0.01 (WP4: E5,F5,G5 均值)
W1_MOI001 <- c(0.272, 0.317, 0.359, 0.415, 0.448, 0.461, 0.474, 0.497, 0.532, 0.565,
               0.519, 0.342, 0.188, 0.165, 0.173, 0.198, 0.228, 0.262, 0.298, 0.335,
               0.379, 0.424, 0.472, 0.522, 0.574, 0.629, 0.681, 0.738, 0.792, 0.843,
               0.881, 0.916, 0.949, 0.979, 1.007, 1.031, 1.053, 1.076, 1.094, 1.114,
               1.136, 1.158, 1.179, 1.199, 1.218, 1.237, 1.255, 1.270, 1.287)

# W2 MOI=10 (WP7: B7,C7,D7 均值)
W2_MOI10 <- c(0.271, 0.315, 0.359, 0.407, 0.438, 0.436, 0.398, 0.234, 0.108, 0.105,
              0.115, 0.131, 0.151, 0.174, 0.199, 0.225, 0.252, 0.280, 0.311, 0.342,
              0.375, 0.410, 0.445, 0.483, 0.523, 0.563, 0.604, 0.650, 0.699, 0.752,
              0.808, 0.856, 0.893, 0.924, 0.950, 0.971, 0.990, 1.008, 1.025, 1.040,
              1.054, 1.068, 1.082, 1.095, 1.108, 1.120, 1.132, 1.146, 1.158)

# W2 MOI=1 (WP8: E7,F7,G7 均值)
W2_MOI1 <- c(0.271, 0.316, 0.360, 0.416, 0.449, 0.467, 0.476, 0.450, 0.307, 0.131,
             0.114, 0.118, 0.128, 0.143, 0.163, 0.187, 0.218, 0.273, 0.339, 0.402,
             0.468, 0.539, 0.611, 0.686, 0.760, 0.833, 0.904, 0.968, 1.015, 1.033,
             1.036, 1.023, 1.015, 1.011, 1.010, 1.012, 1.018, 1.026, 1.037, 1.047,
             1.060, 1.073, 1.087, 1.100, 1.114, 1.129, 1.143, 1.162, 1.176)

# W2 MOI=0.1 (WP5: B6,C6,D6 均值)
W2_MOI01 <- c(0.273, 0.316, 0.356, 0.403, 0.437, 0.434, 0.404, 0.287, 0.120, 0.101,
              0.106, 0.114, 0.125, 0.141, 0.164, 0.197, 0.249, 0.290, 0.316, 0.346,
              0.382, 0.427, 0.481, 0.544, 0.616, 0.693, 0.771, 0.850, 0.924, 0.988,
              1.037, 1.074, 1.104, 1.130, 1.152, 1.174, 1.194, 1.212, 1.229, 1.247,
              1.263, 1.280, 1.296, 1.311, 1.327, 1.343, 1.357, 1.374, 1.390)

# W2 MOI=0.01 (WP6: E6,F6,G6 均值) - 注意G6异常
W2_MOI001 <- c(0.272, 0.316, 0.357, 0.409, 0.441, 0.455, 0.455, 0.388, 0.237, 0.144,
               0.131, 0.132, 0.139, 0.153, 0.175, 0.207, 0.246, 0.287, 0.328, 0.370,
               0.415, 0.468, 0.524, 0.583, 0.646, 0.710, 0.774, 0.842, 0.906, 0.968,
               1.021, 1.068, 1.106, 1.139, 1.168, 1.196, 1.222, 1.246, 1.269, 1.292,
               1.313, 1.334, 1.354, 1.374, 1.395, 1.415, 1.437, 1.460, 1.483)

# 创建数据框
df <- tibble(
  Time = rep(time_hours, 9),
  OD600 = c(W_control, W1_MOI10, W1_MOI1, W1_MOI01, W1_MOI001,
            W2_MOI10, W2_MOI1, W2_MOI01, W2_MOI001),
  Sample = rep(c("W Control",
                 "W1 MOI=10", "W1 MOI=1", "W1 MOI=0.1", "W1 MOI=0.01",
                 "W2 MOI=10", "W2 MOI=1", "W2 MOI=0.1", "W2 MOI=0.01"),
               each = length(time_hours)),
  Phage = rep(c("Control", rep("W1", 4), rep("W2", 4)), each = length(time_hours)),
  MOI = rep(c(NA, 10, 1, 0.1, 0.01, 10, 1, 0.1, 0.01), each = length(time_hours))
)

# 设置因子顺序
df$Sample <- factor(df$Sample, levels = c("W Control",
                                           "W1 MOI=10", "W1 MOI=1", "W1 MOI=0.1", "W1 MOI=0.01",
                                           "W2 MOI=10", "W2 MOI=1", "W2 MOI=0.1", "W2 MOI=0.01"))

# ============ 绘图 ============

# 颜色方案
colors <- c("W Control" = "black",
            "W1 MOI=10" = "#E41A1C", "W1 MOI=1" = "#377EB8",
            "W1 MOI=0.1" = "#4DAF4A", "W1 MOI=0.01" = "#984EA3",
            "W2 MOI=10" = "#FF7F00", "W2 MOI=1" = "#FFFF33",
            "W2 MOI=0.1" = "#A65628", "W2 MOI=0.01" = "#F781BF")

# 图1: 全部样本
p1 <- ggplot(df, aes(x = Time, y = OD600, color = Sample)) +
  geom_line(linewidth = 0.8) +
  scale_color_manual(values = colors) +
  scale_x_continuous(breaks = seq(0, 12, by = 2)) +
  labs(title = "Killing Curve: W1 & W2 Phages vs W Strain (EcAZ-1)",
       subtitle = "MOI Optimization Experiment | 37°C, Continuous Shaking",
       x = "Time (hours)",
       y = expression(OD[600]),
       color = "Sample") +
  theme_bw(base_size = 12) +
  theme(legend.position = "right",
        plot.title = element_text(face = "bold"))

ggsave("killing_curve_all.png", p1, width = 10, height = 6, dpi = 300)

# 图2: W1噬菌体分面图
df_W1 <- df %>% filter(Phage %in% c("Control", "W1"))
p2 <- ggplot(df_W1, aes(x = Time, y = OD600, color = Sample)) +
  geom_line(linewidth = 1) +
  scale_color_manual(values = colors) +
  scale_x_continuous(breaks = seq(0, 12, by = 2)) +
  labs(title = "W1 Phage Killing Curve at Different MOIs",
       x = "Time (hours)",
       y = expression(OD[600]),
       color = "Sample") +
  theme_bw(base_size = 12) +
  theme(legend.position = "right")

ggsave("killing_curve_W1.png", p2, width = 9, height = 5, dpi = 300)

# 图3: W2噬菌体分面图
df_W2 <- df %>% filter(Phage %in% c("Control", "W2"))
p3 <- ggplot(df_W2, aes(x = Time, y = OD600, color = Sample)) +
  geom_line(linewidth = 1) +
  scale_color_manual(values = colors) +
  scale_x_continuous(breaks = seq(0, 12, by = 2)) +
  labs(title = "W2 Phage Killing Curve at Different MOIs",
       x = "Time (hours)",
       y = expression(OD[600]),
       color = "Sample") +
  theme_bw(base_size = 12) +
  theme(legend.position = "right")

ggsave("killing_curve_W2.png", p3, width = 9, height = 5, dpi = 300)

# 图4: 并排比较（分面）
df_phage <- df %>% filter(Phage != "Control")
df_phage$MOI_label <- factor(paste0("MOI = ", df_phage$MOI),
                              levels = c("MOI = 10", "MOI = 1", "MOI = 0.1", "MOI = 0.01"))

p4 <- ggplot() +
  geom_line(data = df %>% filter(Sample == "W Control"),
            aes(x = Time, y = OD600), color = "gray40", linewidth = 0.8, linetype = "dashed") +
  geom_line(data = df_phage,
            aes(x = Time, y = OD600, color = Phage), linewidth = 1) +
  facet_wrap(~MOI_label, nrow = 1) +
  scale_color_manual(values = c("W1" = "#E41A1C", "W2" = "#377EB8")) +
  scale_x_continuous(breaks = seq(0, 12, by = 3)) +
  labs(title = "Comparison of W1 vs W2 at Each MOI",
       subtitle = "Dashed line: W strain control (no phage)",
       x = "Time (hours)",
       y = expression(OD[600]),
       color = "Phage") +
  theme_bw(base_size = 11) +
  theme(legend.position = "bottom",
        strip.background = element_rect(fill = "lightblue"))

ggsave("killing_curve_comparison.png", p4, width = 12, height = 4, dpi = 300)

cat("图表已保存:\n")
cat("  - killing_curve_all.png (全部样本)\n")
cat("  - killing_curve_W1.png (W1噬菌体)\n")
cat("  - killing_curve_W2.png (W2噬菌体)\n")
cat("  - killing_curve_comparison.png (W1 vs W2比较)\n")
