# Carpool-Simulation
快车、拼车仿真工程，参考论文 [On-demand high-capacity ride-sharing via dynamic trip-vehicle assignment](http://www.alonsomora.com/docs/17-alonsomora-ridesharing-pnas-supplemental.pdf)

**先看主程序，按顺序读懂每个函数操作**

## Requirements
1. osmnx
2. networkx
3. numpy
4. pandas
5. pickle
6. sklearn
7. gurobipy (important, ILP solver)
8. scipy

- Refer to the env file [carpool-simulation.yaml](https://github.com/JiahuiSun/Carpool-Simulation/blob/master/carpool-simulation.yaml). Note: This file is just my environment. You can install packages as you like.

- For simplicity, create a new environment using anaconda

```
conda env create -f carpool-simulation.yml
```

- 配置环境可能遇到各种问题，配合我的环境文件和goole食用

## Data Preparation
- 数据我放在交大云盘上了，之后还有。https://jbox.sjtu.edu.cn/l/Foibeb
1. 原始数据是纽约曼哈顿岛出租车数据集，目前原始数据和路径字典已经提取好保存成pickle文件了，可以直接运行主程序，但可能有问题:-)。

## Logic
1. 主程序是 [simulation_rs2.ipynb]()。逻辑是先读取原始订单数据，生成司机和请求，再计算RR、RV、RTV图。主要是simulation_ridesharing这个函数，之后的结果处理可以不用看。
2. 先通过 [network_int.ipynb]() 生成路径信息。逻辑是全城用很多结点表示，提取全连通分量，使得全城任意两个点之间可以相互到达。然后通过最短路径算法计算任意两个点之间的最短距离，保存成字典以便后面路径规划使用。可以用来学习一下如何生成地图信息。
