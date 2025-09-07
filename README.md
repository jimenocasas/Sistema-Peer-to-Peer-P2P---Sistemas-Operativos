# Sistema Peer-to-Peer con Servicio Web y Registro mediante RPC  

## Descripción
Proyecto final de la asignatura de **Sistemas Distribuidos**, centrado en el diseño e implementación de una aplicación distribuida con arquitectura peer-to-peer (P2P). El trabajo integra múltiples tecnologías y fases de desarrollo, con el objetivo de consolidar conocimientos de concurrencia, comunicación en red y diseño modular de sistemas.  

El proyecto se compone de tres partes principales:  

### 1. Cliente-servidor en C y Python  
Se implementó un **servidor multihilo en C** capaz de gestionar múltiples clientes de forma concurrente mediante sockets TCP y sincronización con hilos. El servidor coordina el registro de usuarios, publicación de ficheros, consultas, descargas y desconexiones.  
El **cliente en Python** proporciona una interfaz de línea de comandos, desde la cual los usuarios pueden interactuar con el sistema y realizar operaciones P2P, incluyendo la transferencia directa de ficheros entre clientes.  

### 2. Servicio web en Python (Flask)  
Cada cliente integra un servicio web local que proporciona la fecha y hora actual en formato estandarizado. Esta información se adjunta a todas las operaciones realizadas, garantizando trazabilidad temporal y coherencia en la comunicación con el servidor central.  

### 3. Registro de operaciones mediante RPC (ONC-RPC en C)  
Se desarrolló un **servidor RPC independiente** para registrar en un fichero externo todas las operaciones de los clientes (ej. REGISTER, PUBLISH, DELETE). El servidor principal actúa como cliente RPC, enviando los datos de usuario, operación, parámetros y marca temporal. Esto asegura un registro fiable y centralizado de todas las interacciones.  

## Resultados
El sistema combina **comunicación cliente-servidor, servicios web y procedimientos remotos**, integrando tecnologías heterogéneas (C y Python) en un entorno distribuido. Se verificó su correcto funcionamiento mediante pruebas unitarias y de concurrencia con múltiples clientes, comprobando tanto casos válidos como entradas erróneas.  

El resultado es una aplicación **robusta, modular y extensible**, que simula el funcionamiento real de una red P2P, soporta operaciones concurrentes y asegura la trazabilidad de todas las acciones. Este proyecto permitió aplicar de manera práctica conceptos clave de **sistemas distribuidos, programación en red, sincronización de procesos y diseño de software seguro**.  
