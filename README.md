Para correr el simulador se usa el script dockershell . Tiene un volume montado que es los archivos de simulación. 

para extraer los datos se usa https://docs.omnetpp.org/tutorials/pandas/
En particular el comando: 

 opp_scavetool x *.sca *.vec -o routing.csv

