# SDN_LB_Multiple_Controller
TA Load Balancing untuk multiple controller pada SDN berbasis switches group dan distributed decision

Cara run TA ini :
1.  install rabitmq pada localhost
2.  install mysql
3.  install mininet 
4.  install hping3
5.  install pox controller
6.  install python2.7
7.  buka folder forwarding dalam pox controller
    >cd pox/pox/forwarding
8.  masukan file forwarding.l2_learning_nxl_c1 dan forwarding.l2_learning_nxl_c2 ke folder forwarding
9.  kembali ke folder sebelumnya
    >cd ..
10. jalankan script ini untuk menginisiasi controller 1
    >./pox.py forwarding.l2_learning_nxl_c1 openflow.of_01 --port=6633
11. jalankan script ini pada terminal yang berbeda untuk menginsiasi controller 2 
    >./pox.py forwarding.l2_learning_nxl_c1 openflow.of_01 --port=6634
12. letakan file TAv1.py dan Testing.py pada folder yang sama 
13. jalankan syntax ini untuk menjalankan topology
    >python Testing.py
14. pada terminal h1/h2/h3 jalankan syntax ini untuk menggenerate paket
    >hping3 10.0.0.4 -S -V -i u5000
15. silahkan buka terminal controller untuk melihat perubahan packet pada switch
