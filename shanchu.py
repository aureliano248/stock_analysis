import matplotlib
matplotlib.use('Agg')  # 【必须放在 import pyplot 之前】告诉它不要弹窗

import numpy as np
import matplotlib.pyplot as plt

# 1. 设置数据
D = np.linspace(0, 0.5, 100)
Multiplier = 1 + 30 * D**2

# 2. 绘图设置
plt.figure(figsize=(10, 6), dpi=300)
plt.plot(D*100, Multiplier, label='y = 1 + 30 * D^2', color='red', linewidth=2.5)

# 3. 标记关键点
key_points = [0.05, 0.10, 0.20, 0.30, 0.40, 0.50]
for p in key_points:
    val = 1 + 30 * p**2
    plt.scatter(p*100, val, color='blue', zorder=5)
    plt.text(p*100, val + 0.3, f'{val:.2f}x', ha='center', fontsize=10, fontweight='bold')

# 4. 装饰图表
plt.title('Investment Multiplier Strategy (Parabolic)', fontsize=14)
plt.xlabel('Drawdown Percentage (D%)', fontsize=12)
plt.ylabel('Investment Multiplier (Times of Base)', fontsize=12)
plt.grid(True, linestyle='--', alpha=0.6)
plt.xlim(0, 55)
plt.ylim(0, 10)
plt.legend()

# 5. 保存图片
plt.savefig('shanchu.png', bbox_inches='tight')

print("图片已成功保存为 shanchu.png")