# Proyecto Final - Sistemas Distribuidos (Curso 2024/2025)

## Nombre del Proyecto
Sistema P2P distribuido con registro temporal de operaciones mediante servicio web y servidor RPC.

## Estructura del proyecto

```
PRACTICA_FINAL/
|├── client.py                # Cliente en Python (controla las operaciones del usuario)
|├── server.c                # Servidor en C que gestiona conexiones y tuplas
|├── servidor_web.py         # Servicio web Flask que proporciona fecha y hora
|├── proxy_rpc.c             # Cliente RPC que contacta con el servidor RPC para registrar logs
|├── server_rpc.c            # Servidor RPC que guarda logs en logs.txt
|├── claves_rpc.x            # Definición de la interfaz RPC con rpcgen
|├── makefile                # Compilador automático de todos los componentes
|├── logs.txt                # Fichero generado con el log de operaciones
```

## Requisitos previos

- Linux o WSL (Windows Subsystem for Linux)
- Python 3 con Flask:

```
pip3 install flask
```
- Librerías de desarrollo RPC:

```
sudo apt update
sudo apt install libtirpc-dev -y

```

## Compilación del sistema
Desde el directorio principal `PRACTICA_FINAL/`, ejecutar:

```
make clean
make
```
Esto genera:
- `server` (Servidor principal)
- `servidor_rpc` (Servidor de logs RPC)
- Archivos generados automáticamente por `rpcgen` a partir de `claves_rpc.x`
---

## Ejecución del sistema (en terminales separadas)

### 1. Ejecutar el **servidor RPC**
Este servidor recibe logs de operaciones:
```
./servidor_rpc
```
Esto crea/actualiza el fichero `logs.txt` donde se almacenarán (Día Hora) Usuario --> Acción 

### 2. Ejecutar el **servidor web** de fecha
En otra terminal:
```
python3 servidor_web.py
```
servidor web disponible para registrar el momento en el que se lleva a cabo la acción pertinente.

### 3. Ejecutar el **servidor principal**
En otra terminal:
```
./server -p 8080
```

### 4. Ejecutar el **cliente Python** (se ejecuta esto en una terminal nueva por cada cliente)
```
python3 client.py -s localhost -p 8080
```

### UNA VEZ REALIZADOS TODOS ESTOS PROCESOS, EL SISTEMA ESTARÁ DISPONIBLE PARA REALIZAR CUALQUIER OPERACIÓN