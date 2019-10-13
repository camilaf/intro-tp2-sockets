# 75.43 Introducción a Sistemas Distribuidos
## Trabajo Práctico 2

El objetivo del trabajo práctico es implementar un sistema de almacenamiento de archivos en la nube utilizando los protocolos de capa de transporte TCP y UDP. Este repositorio facilita a los grupos un esqueleto con los comandos que el sistema debe exponer.

## Comandos

Este repositorio expone los 3 comandos descriptos en el enunciado del TP, con todos los parametros requeridos.
A continuación se listan algunos ejemplos para correr los comandos utilizando los dos protocolos.

### Iniciando el servidor

    ./start-server --protocol tcp -H 127.0.0.1 -P 8080 --storage-dir ./storage
    ./start-server --protocol udp -H 127.0.0.1 -P 8080 --storage-dir ./storage

### Subiendo un archivo

    ./upload-file --protocol tcp -H 127.0.0.1 -P 8080 --src ./files/test.txt --name first-upload.txt
    ./upload-file --protocol udp -H 127.0.0.1 -P 8080 --src ./files/test.txt --name first-upload.txt

### Descargando un archivo

    ./download-file --protocol tcp -H 127.0.0.1 -P 8080 --name first-upload.txt --dst ./output/first-file.txt
    ./download-file --protocol udp -H 127.0.0.1 -P 8080 --name first-upload.txt --dst ./output/first-file.txt

## Simulando la red

Para poder simular distintas condiciones de red vamos a utilizar la herramienta [comcast](https://github.com/tylertreat/comcast). En el repo de comcast van a encontrar las instrucciones de instalación. La herramienta esta escrita en [Go](https://golang.org/doc/), por lo que van a tener que instalar Go primero.

En nuestro caso, vamos a simular una tasa de perdida de paquetes del 10% para poder ver como se comportan las distintas soluciones. Para hacer esto, corremos:

    comcast --device=lo0 --packet-loss=10%

Una vez que terminamos con la simulación, debemos correr el siguiente comando para desactivar las reglas setteadas:

    comcast --stop
