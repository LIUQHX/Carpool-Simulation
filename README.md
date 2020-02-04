# Carpool-Simulation
快车、拼车仿真

## Requirements
1. osmnx
2. networkx
3. numpy
4. pandas
5. pickle
6. sklearn
7. scipy
8. gurobipy (important, ILP solver)

- 配置环境
  - 创建新环境，直接安装osmnx，其他的库除了gurobipy就全有了；
  ```
  conda create -n ridesharing python=3.7
  conda install osmnx -c conda-forge
  ```
  - https://www.gurobi.com/free-trial/ 网上申请gurobipy这个库的免费版license；
  - 安装gurobipy；
  ```
  conda config --add channels http://conda.anaconda.org/gurobi
  conda install gurobi
  ```
  - 生成密钥，你的电脑就可以使用这个库了
  ```
  grbgetkey 6942793e-1bcc-11ea-a76c-0a7c4f30bdbe
  ```

## Data Preparation
- 数据使用纽约曼哈顿出租车数据集，组账号服务器上有；交大云盘上有预处理后的结果。https://jbox.sjtu.edu.cn/l/Foibeb
- 预处理结果包括：订单数据保存成pickle文件，曼哈顿路网已经提取好保存成pickle文件；

NOTE: 不一定非要保存成这种格式，根据需要进行保存

## Logic
1. 主程序是 [simulation_rs.ipynb](simulation_rs.ipynb)；初始化参数，按照时间顺序分单；地图路径提前处理好了；具体操作看代码；
2. 通过 [network_int.ipynb](network_int.ipynb) 生成路径信息。城市的路网图用OSMnx获取，用networkx处理，提取最大的全连通分量，使得全城任意两个点之间可以相互到达；然后通过最短路径算法计算出任意两个点之间的最短距离，保存成字典以便分单时的路径规划使用；
3. 其他jupyter脚本都是分析结果的。
