# Carpool-Simulation
快车、拼车仿真工程

## Requirements
1. osmnx
2. networkx
3. numpy
4. pandas
5. pickle
6. sklearn
7. gurobipy (important, ILP solver)
8. scipy

- For simplicity, create a new environment using anaconda

## Data Preparation
- 数据我放在交大云盘上了，之后还有。https://jbox.sjtu.edu.cn/l/Foibeb
- 原始数据是纽约曼哈顿岛出租车数据集，目前原始数据和路径字典已经提取好保存成pickle文件了

## Logic
1. 主程序是 [simulation_rs.ipynb](simulation_rs.ipynb)
2. 通过 [network_int.ipynb](network_int.ipynb) 生成路径信息。逻辑是全城用很多结点表示，提取全连通分量，使得全城任意两个点之间可以相互到达。然后通过最短路径算法计算任意两个点之间的最短距离，保存成字典以便后面路径规划使用。
3. 结果处理程序有四个jupyter脚本。
