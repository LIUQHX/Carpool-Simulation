st=`date +"%y%m%d_%H%M"`
python main.py 2000 300 600 30 0109 > ${st}.log 2>&1

# for i in 10 20 30 40 50 60
# do
#     st=`date +"%y%m%d_%H%M"`
#     python main.py 2000 300 600 ${i} 0109 > ${st}.log 2>&1
# done

# for i in 0103 0104 0105 0106 0107 0108
# do
#     st=`date +"%y%m%d_%H%M"`
#     python main.py 2000 300 600 30 ${i} > ${st}.log 2>&1
# done
