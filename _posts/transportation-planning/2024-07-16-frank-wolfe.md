---
title: 基于Frank-Wolfe算法求解交通分配UE模型 #标题
date: 2024-04-10 #日期，如果日期超过当前时间，无法发出，可能会作为定时？
categories: [交通规划, 交通分配] # 文件夹分类
tags: [UE, Frank Wolfe] # 标签
math: true # 启用数学
pin: false # 置顶
authors: [Zuoyu Chai]
---

## 一、用户均衡模型简略介绍

### 1.1 Wardrop 第一原理

- 道路的利用者，都确切知道网络的交通状态，并试图选择最短路径
- 当网络达到平衡状态时，每个 OD 对的各条被使用的路径，行驶时间相等，且行驶时间最短
- 没有被使用的路径的行驶时间大于或等于最小行驶时间

### 1.2 用户均衡模型

满足 Wardrop 第一原理的交通分配模型，称为用户均衡模型。

1956 年 Beckmann 提出了一种满足 Wardrop 第一原理的数学规划模型。模型核心是，交通网络中的用户，都试图选择最短路径，而最终使得被选择的路径的阻抗最小且相等。该数学规划模型为：

### 1.3 BPR 函数

在用户均衡模型中， $t_a$ 为路阻函数，我们一般采用 BPR 函数，即：

$$
t_a\left( x_a \right) =FFT_a*\left[ 1+\alpha *\left( \frac{x_a}{C_a} \right) ^{\beta} \right]
$$

- $FFT_a$  表示最快通过路段 a 的时间
- $\alpha$  常取 0.15，$\beta$  常取 4.0
- $C_a$  表示路段 $a$ 的通行能力
- $x_a$  表示路段 a 的流量

### 1.4 用户均衡模型的积分项

为便于后续求解，我们将 BPR 函数代入 $\int_0^{x_a}{t_a\left( w \right) dw}$  进行积分计算，过程如下 :

$$
\begin{aligned}
\int_0^{x_a}t_a\left(w\right)dw& =\int_0^{x_a}FFT_a*\biggl[1+\alpha\biggl(\frac{w}{C_a}\biggr)^\beta\biggr]dw \\
&=C_a*FFT_a\int_0^{x_a}\biggl[1+\alpha\biggl(\frac w{C_a}\biggr)^\beta\biggr]d \frac w{C_a} \\
&=C_a*FFT_a\int_0^{\frac{x_a}{C_a}}(1+\alpha x^\beta)dx \\
&=C_a*FFT_a*\biggl(x+\frac\alpha{\beta+1}x^{\beta+1}\biggr)\biggr|_0^{\frac{x_a}{C_a}} \\
&=C_a*FFT_a*\biggl[\frac{x_a}{C_a}+\frac{\alpha}{\beta+1}\biggl(\frac{x_a}{C_a}\biggr)^{\beta+1}\biggr] \\
&=FFT_a{\left[x_a+\frac{\alpha C_a}{\beta+1}{\left(\frac{x_a}{C_a}\right)}^{\beta+1}\right]}
\end{aligned}
$$

因此，我们的目标函数为：

$$
\min Z\left( X \right) =\sum_a{FFT_a\left[ x_a+\frac{\alpha C_a}{\beta +1}\left( \frac{x_a}{C_a} \right) ^{\beta +1} \right]}
$$

## 二、Frank Wolfe 算法求解步骤

友情提醒：后面若一时对代码主体逻辑有疑惑，返回看看这部分。

步骤 1：初始化。基于零流图的路阻，依次搜索每一个 OD 对  *r,s*  所对应的最短路径，并将  *r,s*  间的 OD 流量，全部分配到对应的最短路径上，得到初始路段流量  $X_1$ 。

步骤 2：更新路阻。根据 BPR 函数，分别代入每个路段的初始流量，求得阻抗  $W_1$ 。

步骤 3：下降方向。基于阻抗  $W_1$，按照步骤 1 中的方法（最短路全有全无分配），将流量重新分配到对应路径上，得到临时路段流量  ${X_1}^*$ 。

步骤 4：搜索最优步长，并更新流量。采用二分法，搜索最优步长  $step^*$  ，并令

$$X_2=X_1+step^**({X_1}^*-X_1)$$

其中，最优步长满足：

$$\min Z\left[X_1+step^**\left(X_1\right.^*-X_1\right)],step\in(0,1]$$

步骤 5：结束条件。如果

$$ \frac{\sqrt{\sum*a{\left( x*{a}^{n+1}-x*{a}^{n} \right) ^2}}}{\sum_a{x*{a}^{n}}}\leqslant \boldsymbol{\epsilon } $$

，则算法结束；否则 n=n+1，转至步骤 2。此处的  𝜀  表示误差阈值，在代码部分用 max_err 表示。

## 三、代码

代码基于 Python 的 NetWorkX 库编写，这样将大大减少我们代码编写的工作量，并且更易于阅读。我们以 SiouxFalls 交通网络为例，进行交通网络构建与流量分配。

### 3.1 导入必要的库

```python
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
from scipy.optimize import minimize_scalar
```

- pandas 用于读取文件、导出结果
- numpy 在计算误差时使用
- networkx 贯穿整个代码
- matplotlib 用于绘制交通网络图
- scipy 在搜索最优步长时用到

### 3.2 构建交通网络

```python
def build_network(Link_path, Node_path):
    # 读取点数据、边数据
    links_df = pd.read_csv(Link_path)
    # 需要注意使用from_pandas_edge，其读取的边的顺序和csv中边的顺序有差异
    G = nx.from_pandas_edgelist(links_df, source='O', target='D', edge_attr=['FFT', 'Capacity'], create_using=nx.DiGraph())
    nx.set_edge_attributes(G, 0, 'flow_temp')
    nx.set_edge_attributes(G, 0, 'flow_real')
    nx.set_edge_attributes(G, 0, 'descent')
    nx.set_edge_attributes(G, nx.get_edge_attributes(G, "FFT"), 'weight')

    # 获取节点位置信息
    nodes_df = pd.read_csv(Node_path)
    node_positions = {}
    for index, row in nodes_df.iterrows():
        node_positions[row['id']] = (row['pos_x'], row['pos_y'])
    # 更新图中节点的位置属性
    nx.set_node_attributes(G, node_positions, 'pos')
    return G
```

- Link_path，表示路网文件路径。下载链接见文末。

- Node_path，表示节点文件路径。

- low_real，表示每次迭代更新后的路段流量或初始化流量，所有路段的 flow_real 组成 ${X_n}$
- flow_temp，所有路段的 flow_temp 组成 ${X_n}^∗$
- descent，表示 flow_temp 与 flow_real 的差值，所有路段的 descent 组成 ${X_n}^∗-{X_n}$
- weight，表示路阻。初始的路阻，由于路段流量都是 0，所以直接用 FFT 表示。后续将用 BPR 函数计算

### 3.3 绘制交通路网图

```python
def draw_network(G):
    pos = nx.get_node_attributes(G, "pos")
    nx.draw(G, pos, with_labels=True, node_size=200, node_color='lightblue', font_size=10, font_weight='bold')
    plt.show()
```

构建交通网络后，我们来看一看这个 SiouxFalls 网络长什么样子吧

![image.png](https://raw.githubusercontent.com/zychai/ImageBed/main/20240711031334.png){:whith="600"}
_交通网络图_

### 3.4 定义 BPR 函数

```python
def BPR(FFT, flow, capacity, alpha=0.15, beta=4.0):
    return FFT * (1 + alpha * (flow / capacity) ** beta)
```

- FTT，表示最快通过时间
- flow，表示路段流量
- capacity，表示路段通行能力
- alpha 和 beta，是 BPR 函数的参数，在此取默认值

### 3.5 初始化路网流量

```python
def all_none_initialize(G, od_df):
    # 这个函数仅使用一次，用于初始化
    # 在零流图上，按最短路全有全无分配，用于更新flow_real
    for _, od_data in od_df.iterrows():
        source = od_data["o"]
        target = od_data["d"]
        demand = od_data["demand"]
        # 计算最短路径
        shortest_path = nx.shortest_path(G, source=source, target=target, weight="weight")
        # 更新路径上的流量
        for i in range(len(shortest_path) - 1):
            u = shortest_path[i]
            v = shortest_path[i + 1]
            G[u][v]['flow_real'] += demand
    # 初始化流量后，更新阻抗
    for _, _, data in G.edges(data=True):
        data['weight'] = BPR(data['FFT'], data['flow_real'], data['Capacity'])
```

- 这个函数仅使用一次，用于初始化。在零流图上，按最短路全有全无分配，用于得到  $X_1$
- od_df 表示 pd.Dataframe 数据格式的 OD 流量信息。

### 3.6 获取 flow_temp，即  ${X_n}^*$

```python
def all_none_temp(G, od_df):
    # 这个是虚拟分配，用于得到flow_temp
    # 每次按最短路分配前，需要先将flow_temp归零
    nx.set_edge_attributes(G, 0, 'flow_temp')
    for _, od_data in od_df.iterrows():
        # 每次更新都得读OD，后面尝试优化这个
        source = od_data["o"]
        target = od_data["d"]
        demand = od_data["demand"]
        # 计算最短路径
        shortest_path = nx.shortest_path(G, source=source, target=target, weight="weight")
        # 更新路径上的流量
        for i in range(len(shortest_path) - 1):
            u = shortest_path[i]
            v = shortest_path[i + 1]
            # 更新流量
            G[u][v]['flow_temp'] += demand
```

### 3.7 获取下降方向 descent，即 ${X_n}^*-X_n$

```python
def get_descent(G):
    for _, _, data in G.edges(data=True):
        data['descent'] = data['flow_temp'] - data['flow_real']
```

### 3.8 定义目标函数

```python
def objective_function(temp_step, G):
    s, alpha, beta = 0, 0.15, 4.0
    for _, _, data in G.edges(data=True):
        x = data['flow_real'] + temp_step * data['descent']
        s += data["FFT"] * (x + alpha * data["Capacity"] / (beta + 1) * (x / data["Capacity"]) ** (beta + 1))
    return s
```

该部分代码，对应本文 1.4 部分的目标函数。

### 3.9 一维搜索最优步长，并更新流量

```python
def update_flow_real(G):
    # 这个函数用于调整流量，即flow_real，并更新weight
    best_step = get_best_step(G)  # 获取最优步长
    for _, _, data in G.edges(data=True):
        # 调整流量，更新路阻
        data['flow_real'] += best_step * data["descent"]
        data['weight'] = BPR(data['FFT'], data['flow_real'], data['Capacity'])

def get_best_step(G, tolerance=1e-4):
    result = minimize_scalar(objective_function, args=(G,), bounds=(0, 1), method='bounded', tol=tolerance)
    return result.x
```

### 3.10 主函数

```python
def main():
    G = build_network("Link.csv", "Node.csv")  # 构建路网
    draw_network(G)  # 绘制交通路网图
    od_df = pd.read_csv("ODPairs.csv")  # 获取OD需求情况
    all_none_initialize(G, od_df)  # 初始化路网流量
    print("初始化流量", list(nx.get_edge_attributes(G, 'flow_real').values()))

    epoch = 0  # 记录迭代次数
    err, max_err = 1, 1e-4  # 分别代表初始值、最大容许误差
    f_list_old = np.array(list(nx.get_edge_attributes(G, 'flow_real').values()))
    while err > max_err:
        epoch += 1
        all_none_temp(G, od_df)  # 全有全无分配，得到flow_temp
        get_descent(G)  # 计算梯度，即flow_temp-flow_real
        update_flow_real(G)  # 先是一维搜索获取最优步长，再调整流量，更新路阻

        # 计算并更新误差err
        f_list_new = np.array(list(nx.get_edge_attributes(G, 'flow_real').values()))  # 这个变量是新的路网流量列表
        d = np.sum((f_list_new - f_list_old) ** 2)
        err = np.sqrt(d) / np.sum(f_list_old)
        f_list_old = f_list_new

    print("均衡流量", list(nx.get_edge_attributes(G, 'flow_real').values()))
    print("迭代次数", epoch)
    # 导出网络均衡流量
    df = nx.to_pandas_edgelist(G)
    df = df[["source", "target", "flow_real"]].sort_values(by=["source", "target"])
    df.to_csv("网络均衡结果.csv", index=False)


if __name__ == '__main__':
    main()
```

- epoch，表示迭代次数
- err，表示误差初始值
- max_err，表示最大容许误差
- f_list_new, f_list_old 分别表示  𝑋𝑛  和 𝑋𝑛−1，用于计算误差

## 四、所用文件

下载链接：[交通分配（UE 模型）](https://link.zhihu.com/?target=https%3A//download.csdn.net/download/m0_61584121/88936726)
