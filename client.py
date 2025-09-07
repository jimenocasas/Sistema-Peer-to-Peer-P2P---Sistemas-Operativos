from enum import Enum
import argparse
import socket
import threading
import os
import sys
import time
import requests 

class client:

    # ******************** TYPES *********************
    #
    # @brief Return codes for the protocol methods
    class RC(Enum):
        OK = 0
        ERROR = 1
        USER_ERROR = 2

    # ****************** ATTRIBUTES ******************
    _server = None
    _port = -1
    _listen_port = -1
    _listen_socket = None
    _listen_thread = None
    _connected_user = None
    _running = False

    # ******************** METHODS *******************

    #Primero implementamos los métodos de envío y recepción de cadenas, que son utilizados por los demás métodos.
    @staticmethod
    def send_string(sock, message):
        """Envía una cadena terminada en NULL al socket"""
        try:
            message = message + "\0"
            sock.sendall(message.encode())
            return True
        except:
            return False

    @staticmethod
    def read_string(sock):
        """Lee una cadena terminada en NULL del socket"""
        a = bytearray()
        while True:
            msg = sock.recv(1)
            if not msg:
                return None  # Error de conexión
            if msg == b'\0':
                break
            a += msg
        try:
            return a.decode('utf-8')
        except UnicodeDecodeError:
            return None

    @staticmethod
    def get_current_datetime():
        try:
            response = requests.get("http://localhost:8000/fecha")
            if response.status_code == 200:
                return response.text.strip()
            else:
                return None
        except Exception as e:
            print("ERROR AL OBTENER FECHA DEL SERVICIO WEB")
            return None

    
    #Para transferencia de archivos entre clientes (P2P).
    @staticmethod
    def _listen_thread_function():
        try:
            client._listen_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client._listen_socket.bind(('0.0.0.0', client._listen_port))
            client._listen_socket.listen(5)
            
            while client._running:
                conn, addr = client._listen_socket.accept()
                
                # Leer operación
                command = client.read_string(conn)
                if command is None:
                    conn.close()
                    continue
                
                if command == "GET_FILE":
                    # Leer nombre de archivo
                    filename = client.read_string(conn)
                    if filename is None:
                        conn.close()
                        continue
                    
                    # Verificar si el archivo existe
                    if os.path.exists(filename):
                        conn.sendall(bytes([0]))  # Código de éxito
                        
                        # Enviar tamaño del archivo
                        size = os.path.getsize(filename)
                        if not client.send_string(conn, str(size)):
                            conn.close()
                            continue
                        
                        # Enviar contenido del archivo
                        with open(filename, 'rb') as f:
                            conn.sendall(f.read())
                    else:
                        conn.sendall(bytes([1]))  # Archivo no existe
                
                conn.close()
                
        except Exception as e:
            if client._running:
                print(f"Error en hilo de escucha: {str(e)}")
        finally:
            if client._listen_socket:
                client._listen_socket.close()

    #Metodos de la clase cliente para interactuar con el servidor.
    @staticmethod
    def register(user):
        try:
            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando REGISTER
            if not client.send_string(s, "REGISTER"):
                print("REGISTER FAIL")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("REGISTER FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, user):
                print("REGISTER FAIL")
                return client.RC.ERROR
            
            # Recibir respuesta
            response = s.recv(1)
            if not response:
                print("REGISTER FAIL")
                return client.RC.ERROR
            
            response_code = response[0]
            
            if response_code == 0:
                print("REGISTER OK")
                return client.RC.OK
            elif response_code == 1:
                print("USERNAME IN USE")
                return client.RC.USER_ERROR
            else:
                print("REGISTER FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print("REGISTER FAIL")
            return client.RC.ERROR
        finally:
            s.close()

    @staticmethod
    def unregister(user):
        try:
            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando UNREGISTER
            if not client.send_string(s, "UNREGISTER"):
                print("UNREGISTER FAIL")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("UNREGISTER FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, user):
                print("UNREGISTER FAIL")
                return client.RC.ERROR
            
            # Recibir respuesta
            response = s.recv(1)
            if not response:
                print("UNREGISTER FAIL")
                return client.RC.ERROR
            
            response_code = response[0]
            
            if response_code == 0:
                print("UNREGISTER OK")
                return client.RC.OK
            elif response_code == 1:
                print("USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            else:
                print("UNREGISTER FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print("UNREGISTER FAIL")
            return client.RC.ERROR
        finally:
            s.close()


    @staticmethod
    def connect(user):
        try:
            # Buscar puerto libre
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.bind(('', 0))
            client._listen_port = s.getsockname()[1]
            s.close()
            
            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando CONNECT
            if not client.send_string(s, "CONNECT"):
                print("CONNECT FAIL")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("CONNECT FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, user):
                print("CONNECT FAIL")
                return client.RC.ERROR
            
            # Enviar puerto de escucha
            if not client.send_string(s, str(client._listen_port)):
                print("CONNECT FAIL")
                return client.RC.ERROR
            
            # Recibir respuesta
            response = s.recv(1)
            if not response:
                print("CONNECT FAIL")
                return client.RC.ERROR
            
            response_code = response[0]
            
            if response_code == 0:
                # Iniciar hilo de escucha
                client._running = True
                client._listen_thread = threading.Thread(target=client._listen_thread_function)
                client._listen_thread.start()
                client._connected_user = user
                print("CONNECT OK")
                return client.RC.OK
            elif response_code == 1:
                print("CONNECT FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response_code == 2:
                print("USER ALREADY CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("CONNECT FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print("CONNECT FAIL")
            return client.RC.ERROR
        finally:
            s.close()

    @staticmethod
    def disconnect(user):
        try:
            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando DISCONNECT
            if not client.send_string(s, "DISCONNECT"):
                print("DISCONNECT FAIL")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("DISCONNECT FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, user):
                print("DISCONNECT FAIL")
                return client.RC.ERROR
            
            # Recibir respuesta
            response = s.recv(1)
            if not response:
                print("DISCONNECT FAIL")
                return client.RC.ERROR
            
            response_code = response[0]
            
            if response_code == 0:
                # Detener hilo de escucha
                client._running = False
                if client._listen_socket:
                    # Crear conexión ficticia para desbloquear el accept
                    temp_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    temp_socket.connect(('localhost', client._listen_port))
                    temp_socket.close()
                
                if client._listen_thread:
                    client._listen_thread.join()
                
                client._connected_user = None
                print("DISCONNECT OK")
                return client.RC.OK
            elif response_code == 1:
                print("DISCONNECT FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response_code == 2:
                print("DISCONNECT FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("DISCONNECT FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print("DISCONNECT FAIL")
            return client.RC.ERROR
        finally:
            s.close()

    @staticmethod
    def publish(fileName, description):
        try:
            # Verificar si el archivo existe localmente
            if not os.path.exists(fileName):
                print("PUBLISH FAIL, FILE NOT FOUND")
                return client.RC.ERROR
            
            # Comprobar que se pasa una ruta completa
            if not os.path.isabs(fileName):
                print("PUBLISH FAIL, MUST USE ABSOLUTE PATH")
                return client.RC.ERROR
            
            # Extraer solo el nombre del archivo para mostrarlo en LIST_CONTENT
            fileName_base = os.path.basename(fileName)

            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando PUBLISH
            if not client.send_string(s, "PUBLISH"):
                print("PUBLISH FAIL")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("PUBLISH FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, client._connected_user):
                print("PUBLISH FAIL")
                return client.RC.ERROR
            
            # Enviar nombre de archivo
            if not client.send_string(s, fileName_base):
                print("PUBLISH FAIL")
                return client.RC.ERROR
            
            # Enviar descripción
            if not client.send_string(s, description):
                print("PUBLISH FAIL")
                return client.RC.ERROR
            
            # Recibir respuesta
            response = s.recv(1)
            if not response:
                print("PUBLISH FAIL")
                return client.RC.ERROR
            
            response_code = response[0]
            
            if response_code == 0:
                print("PUBLISH OK")
                return client.RC.OK
            elif response_code == 1:
                print("PUBLISH FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response_code == 2:
                print("PUBLISH FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR
            elif response_code == 3:
                print("PUBLISH FAIL, CONTENT ALREADY PUBLISHED")
                return client.RC.USER_ERROR
            else:
                print("PUBLISH FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print("PUBLISH FAIL")
            return client.RC.ERROR
        finally:
            s.close()

    @staticmethod
    def delete(filePath):
        try:
            if not os.path.isabs(filePath):
                print("DELETE FAIL, MUST USE ABSOLUTE PATH")
                return client.RC.ERROR

            if not os.path.exists(filePath):
                print("DELETE FAIL, FILE DOES NOT EXIST LOCALLY")
                return client.RC.ERROR
            
            fileName = os.path.basename(filePath)

            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando DELETE
            if not client.send_string(s, "DELETE"):
                print("DELETE FAIL")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("DELETE FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, client._connected_user):
                print("DELETE FAIL")
                return client.RC.ERROR

            # Enviar nombre de archivo
            if not client.send_string(s, fileName):
                print("DELETE FAIL")
                return client.RC.ERROR
            
            # Recibir respuesta
            response = s.recv(1)
            if not response:
                print("DELETE FAIL")
                return client.RC.ERROR
            
            response_code = response[0]
            
            if response_code == 0:
                print("DELETE OK")
                return client.RC.OK
            elif response_code == 1:
                print("DELETE FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response_code == 2:
                print("DELETE FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR
            elif response_code == 3:
                print("DELETE FAIL, CONTENT NOT PUBLISHED")
                return client.RC.USER_ERROR
            else:
                print("DELETE FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print("DELETE FAIL")
            return client.RC.ERROR
        finally:
            s.close()

    @staticmethod
    def listusers():
        try:
            # Crear socket y conectar al servidor
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))
            
            # Enviar comando LIST_USERS
            if not client.send_string(s, "LIST_USERS"):
                print("LIST_USERS FAIL1")
                return client.RC.ERROR
            
            fecha = client.get_current_datetime()
            if not client.send_string(s, fecha):
                print("DELETE FAIL")
                return client.RC.ERROR

            
            # Enviar nombre de usuario
            if not client.send_string(s, client._connected_user):
                print("LIST_USERS FAIL2")
                return client.RC.ERROR
            
            
            # Recibir respuesta (y parte del número si llega de golpe)
            response = s.recv(2)  # código de estado + posible primer byte del número
            if not response or len(response) < 1:
                print("LIST_USERS FAIL3")
                return client.RC.ERROR

            response_code = response[0]

            # Preparamos buffer restante con cualquier byte extra recibido
            remaining = response[1:] if len(response) > 1 else b''


            if response_code == 0:
                # Leer número de usuarios
                time.sleep(0.05)  # pequeña espera opcional
                num_users = client.read_string_with_buffer(s, remaining)

                if num_users is None:
                    print("LIST_USERS FAIL4")
                    return client.RC.ERROR
                
                

                try:
                    num_users = int(num_users)
                except:
                    print("LIST_USERS FAIL (número inválido)")
                    return client.RC.ERROR

                print("LIST_USERS OK")

                # Recibir información de cada usuario
                for _ in range(num_users):
                    username = client.read_string(s)
                    if username is None:
                        print("LIST_USERS FAIL5")
                        return client.RC.ERROR

                    ip = client.read_string(s)
                    if ip is None:
                        print("LIST_USERS FAIL6")
                        return client.RC.ERROR

                    port = client.read_string(s)
                    if port is None:
                        print("LIST_USERS FAIL7")
                        return client.RC.ERROR

                    print(f"{username} {ip} {port}")

                return client.RC.OK

            
            elif response_code == 1:
                print("LIST_USERS FAIL, USER DOES NOT EXIST")
                return client.RC.USER_ERROR
            elif response_code == 2:
                print("LIST_USERS FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR
            else:
                print("LIST_USERS FAIL")
                return client.RC.ERROR
                
        except Exception as e:
            print(f"Se produjo una excepción: {e}")
            print("LIST_USERS FAIL")
            return client.RC.ERROR
        finally:
            s.close()

    @staticmethod
    def read_string_with_buffer(sock, initial_bytes):
        """Lee una cadena terminada en NULL del socket, usando bytes leídos previamente si los hay"""
        chars = []

        # Procesar los bytes que ya fueron leídos (por ejemplo en s.recv(2))
        for b in initial_bytes:
            if b == 0:
                return ''.join(chars)
            chars.append(chr(b))  # convertir directamente a carácter

        # Leer desde el socket hasta encontrar \0
        while True:
            msg = sock.recv(1)
            if not msg:
                return None
            if msg == b'\0':
                break
            chars.append(msg.decode())

        return ''.join(chars)



    @staticmethod
    def listcontent(user):
        if not client._connected_user:
            print("LIST_CONTENT FAIL, USER NOT CONNECTED")
            return client.RC.ERROR

        if not user:
            print("Syntax error. Usage: LIST_CONTENT <userName>")
            return client.RC.ERROR

        try:

             # Crear socket temporal para esta operación
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((client._server, client._port))

            # Enviar comando
            s.sendall(b"LIST_CONTENT\0")
            fecha = client.get_current_datetime()
            if fecha is None:
                print("LIST_CONTENT FAIL")
                return client.RC.ERROR
            s.sendall(fecha.encode() + b"\0")

            s.sendall(client._connected_user.encode() + b"\0")
            s.sendall(user.encode() + b"\0")

            # Recibir código de respuesta
            response = s.recv(1)
            if not response:
                print("LIST_CONTENT FAIL")
                return client.RC.ERROR

            response_code = response[0]

            if response_code == 0:
                # Leer número de archivos
                num_files = client.read_string(s)
                if num_files is None:
                    print("LIST_CONTENT FAIL")
                    return client.RC.ERROR

                try:
                    num_files = int(num_files.strip())
                except ValueError:
                    print("LIST_CONTENT FAIL (número inválido)")
                    return client.RC.ERROR

                print("LIST_CONTENT OK")

                for i in range(num_files):
                    attempts = 0
                    filename = None
                    while attempts < 3 and filename is None:
                        filename = client.read_string(s)
                        if filename is None:
                            time.sleep(0.05)
                            attempts += 1

                    if filename is None:
                        print(f"LIST_CONTENT FAIL al recibir archivo {i+1}/{num_files}")
                        return client.RC.ERROR

                    print(filename)

                return client.RC.OK

            elif response_code == 2:
                print("LIST_CONTENT FAIL, USER NOT CONNECTED")
            elif response_code == 3:
                print("LIST_CONTENT FAIL, REMOTE USER DOES NOT EXIST")
            elif response_code == 4:
                print("LIST_CONTENT FAIL, USER HAS NO FILES")
                return client.RC.USER_ERROR  # <-- AÑADE ESTE RETURN
            else:
                print("LIST_CONTENT FAIL")

            return client.RC.ERROR

        except Exception as e:
            print("LIST_CONTENT FAIL:", str(e))
            return client.RC.ERROR
        finally:
            s.close()



    @staticmethod
    def getfile(user, remote_FileName, local_FileName):
        from os.path import basename  # Necesario para extraer solo el nombre del archivo

        try:
            # 1. Verificar que el archivo esté publicado por el usuario remoto
            s_check = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s_check.connect((client._server, client._port))
            client.send_string(s_check, "LIST_CONTENT")
            fecha = client.get_current_datetime()
            if not client.send_string(s_check, fecha):
                print("GET_FILE FAIL")
                s_check.close()
                return client.RC.ERROR

            client.send_string(s_check, client._connected_user)
            client.send_string(s_check, user)
            
            response = s_check.recv(1)
            if not response or response[0] != 0:
                print("GET_FILE FAIL, COULD NOT VERIFY FILE")
                s_check.close()
                return client.RC.ERROR

            num_files = client.read_string(s_check)
            if num_files is None:
                print("GET_FILE FAIL, COULD NOT VERIFY FILE")
                s_check.close()
                return client.RC.ERROR

            num_files = int(num_files.strip())
            found = False
            for _ in range(num_files):
                filename = client.read_string(s_check)

                #  CORRECCIÓN: solo comparamos el nombre base, no el path completo
                if filename == basename(remote_FileName):
                    found = True
                    break

            s_check.close()
            if not found:
                print("GET_FILE FAIL, FILE NOT PUBLISHED")
                return client.RC.USER_ERROR

            # 2. Obtener IP y puerto del usuario remoto
            user_info = None
            s_list = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s_list.connect((client._server, client._port))
            client.send_string(s_list, "LIST_USERS")
            fecha = client.get_current_datetime()
            if not client.send_string(s_list, fecha):
                print("GET_FILE FAIL")
                s_list.close()
                return client.RC.ERROR

            client.send_string(s_list, client._connected_user)
            
            response = s_list.recv(1)
            if not response or response[0] != 0:
                print("GET_FILE FAIL")
                s_list.close()
                return client.RC.ERROR
            
            num_users = client.read_string(s_list)
            if num_users is None:
                print("GET_FILE FAIL")
                s_list.close()
                return client.RC.ERROR
            
            found = False
            for _ in range(int(num_users)):
                username = client.read_string(s_list)
                ip = client.read_string(s_list)
                port = client.read_string(s_list)
                if username == user:
                    user_info = (ip, int(port))
                    found = True
                    break

            s_list.close()
            if not found:
                print("GET_FILE FAIL, USER NOT CONNECTED")
                return client.RC.USER_ERROR

            # 3. Conectar al cliente remoto y solicitar el archivo
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((user_info[0], user_info[1]))

            # Enviamos la ruta completa, como pide el enunciado
            client.send_string(s, "GET_FILE")
            client.send_string(s, remote_FileName)

            response = s.recv(1)
            if not response:
                print("GET_FILE FAIL")
                return client.RC.ERROR

            response_code = response[0]
            if response_code == 0:
                size_str = client.read_string(s)
                if size_str is None:
                    print("GET_FILE FAIL")
                    return client.RC.ERROR
                size = int(size_str)

                received = 0
                with open(local_FileName, 'wb') as f:
                    while received < size:
                        data = s.recv(min(4096, size - received))
                        if not data:
                            break
                        f.write(data)
                        received += len(data)

                if received == size:
                    print("GET_FILE OK")
                    return client.RC.OK
                else:
                    if os.path.exists(local_FileName):
                        os.remove(local_FileName)
                    print("GET_FILE FAIL")
                    return client.RC.ERROR

            elif response_code == 1:
                print("GET_FILE FAIL, FILE NOT EXIST")
                return client.RC.USER_ERROR
            else:
                print("GET_FILE FAIL")
                return client.RC.ERROR

        except Exception as e:
            if 'local_FileName' in locals() and os.path.exists(local_FileName):
                os.remove(local_FileName)
            print("GET_FILE FAIL")
            return client.RC.ERROR
        finally:
            if 's' in locals(): s.close()
            if 's_check' in locals(): s_check.close()
            if 's_list' in locals(): s_list.close()



    # *
    # **
    # * @brief Command interpreter for the client. It calls the protocol functions.
    @staticmethod
    def shell():
        while (True):
            try:
                command = input("c> ")
                line = command.split(" ")
                if (len(line) > 0):

                    line[0] = line[0].upper()

                    if (line[0]=="REGISTER"):
                        if (len(line) == 2):
                            client.register(line[1])
                        else:
                            print("Syntax error. Usage: REGISTER <userName>")

                    elif(line[0]=="UNREGISTER"):
                        if (len(line) == 2):
                            client.unregister(line[1])
                        else:
                            print("Syntax error. Usage: UNREGISTER <userName>")

                    elif(line[0]=="CONNECT"):
                        if (len(line) == 2):
                            client.connect(line[1])
                        else:
                            print("Syntax error. Usage: CONNECT <userName>")
                    
                    elif(line[0]=="PUBLISH"):
                        if (len(line) >= 3):
                            # Remove first two words
                            description = ' '.join(line[2:])
                            client.publish(line[1], description)
                        else:
                            print("Syntax error. Usage: PUBLISH <fileName> <description>")

                    elif(line[0]=="DELETE"):
                        if (len(line) == 2):
                            client.delete(line[1])
                        else:
                            print("Syntax error. Usage: DELETE <fileName>")

                    elif(line[0]=="LIST_USERS"):
                        if (len(line) == 1):
                            client.listusers()
                        else:
                            print("Syntax error. Use: LIST_USERS")

                    elif(line[0]=="LIST_CONTENT"):
                        if (len(line) == 2):
                            client.listcontent(line[1])
                        else:
                            print("Syntax error. Usage: LIST_CONTENT <userName>")

                    elif(line[0]=="DISCONNECT"):
                        if (len(line) == 2):
                            client.disconnect(line[1])
                        else:
                            print("Syntax error. Usage: DISCONNECT <userName>")

                    elif(line[0]=="GET_FILE"):
                        if (len(line) == 4):
                            client.getfile(line[1], line[2], line[3])
                        else:
                            print("Syntax error. Usage: GET_FILE <userName> <remote_fileName> <local_fileName>")

                    elif(line[0]=="QUIT"):
                        if (len(line) == 1):
                            if client._connected_user:
                                client.disconnect(client._connected_user)
                            break 
                        else:
                            print("Syntax error. Use: QUIT")
                    else:
                        print("Error: command " + line[0] + " not valid.")
            except Exception as e:
                print("Exception: " + str(e))

    # *
    # * @brief Prints program usage
    @staticmethod
    def usage():
        print("Usage: python3 client.py -s <server> -p <port>")

    # *
    # * @brief Parses program execution arguments
    @staticmethod
    def parseArguments(argv):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', type=str, required=True, help='Server IP')
        parser.add_argument('-p', type=int, required=True, help='Server Port')
        args = parser.parse_args()

        if (args.s is None):
            parser.error("Usage: python3 client.py -s <server> -p <port>")
            return False

        if ((args.p < 1024) or (args.p > 65535)):
            parser.error("Error: Port must be in the range 1024 <= port <= 65535")
            return False
        
        client._server = args.s
        client._port = args.p

        return True


    # ******************** MAIN *********************
    @staticmethod
    def main(argv):
        if (not client.parseArguments(argv)):
            client.usage()
            return

        # Crear socket y conectar al servidor
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((client._server, client._port))

        client.shell()
        s.close()

        print("+++ FINISHED +++")


if __name__=="__main__":
    client.main(sys.argv[1:])