#include <sys/types.h>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <errno.h>
#include <string.h>
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <pthread.h>
#include <signal.h>
#include <stdbool.h>

int registrar_log_rpc(const char *usuario, const char *operacion, const char *param1, const char *fecha);

#define MAX_USERS 100
#define MAX_FILES 1000
#define MAX_STRING 256

// Estructura para usuarios
typedef struct {
    char username[MAX_STRING];
    char ip[MAX_STRING];
    int port;
    bool connected;
} User;

// Estructura para archivos publicados
typedef struct {
    char filename[MAX_STRING];
    char description[MAX_STRING];
    char owner[MAX_STRING];
} FileEntry;

// Variables globales del servidor
User users[MAX_USERS];
FileEntry files[MAX_FILES];
int user_count = 0;
int file_count = 0;

pthread_mutex_t users_mutex = PTHREAD_MUTEX_INITIALIZER;
pthread_mutex_t files_mutex = PTHREAD_MUTEX_INITIALIZER;

bool server_running = true;
int sd; // Socket del servidor

// Función readLine proporcionada
ssize_t readLine(int fd, void *buffer, size_t n) {
    ssize_t numRead;
    size_t totRead;
    char *buf;
    char ch;

    if (n <= 0 || buffer == NULL) {
        errno = EINVAL;
        return -1;
    }

    buf = buffer;
    totRead = 0;
    
    for (;;) {
        numRead = read(fd, &ch, 1);
        
        if (numRead == -1) {
            if (errno == EINTR)
                continue;
            else
                return -1;
        } else if (numRead == 0) {
            if (totRead == 0)
                return 0;
            else
                break;
        } else {
            if (ch == '\n' || ch == '\0')
                break;
            if (totRead < n - 1) {
                totRead++;
                *buf++ = ch;
            }
        }
    }
    
    *buf = '\0';
    return totRead;
}

// Manejar señal SIGINT para apagado ordenado

void handle_signal(int sig) {
    if (sig == SIGINT) {
        printf("\ns> Shutdown solicitado. Cerrando servidor...\n");
        server_running = false;
        shutdown(sd, SHUT_RDWR); // fuerza a que accept salga
        close(sd);
    }
}

// Buscar usuario por nombre
int find_user(const char *username) {
    for (int i = 0; i < user_count; i++) {
        if (strcmp(users[i].username, username) == 0) {
            return i;
        }
    }
    return -1;
}

// Buscar archivo por nombre y dueño
int find_file(const char *filename, const char *owner) {
    for (int i = 0; i < file_count; i++) {
        if (strcmp(files[i].filename, filename) == 0 && 
            strcmp(files[i].owner, owner) == 0) {
            return i;
        }
    }
    return -1;
}

// Operación REGISTER
int handle_register(int client_fd, const char *username) {
    pthread_mutex_lock(&users_mutex);
    
    int result;
    if (find_user(username) != -1) {
        result = 1; // Usuario ya existe
    } else if (user_count >= MAX_USERS) {
        result = 2; // Error del sistema
    } else {
        strcpy(users[user_count].username, username);
        users[user_count].connected = false;
        user_count++;
        result = 0; // Éxito
    }
    
    pthread_mutex_unlock(&users_mutex);
    write(client_fd, &result, sizeof(result));
    return result; // Retorna el resultado de la operación, aunque no se use
}

// Operación UNREGISTER
int handle_unregister(int client_fd, const char *username) {
    pthread_mutex_lock(&users_mutex);
    
    int result;
    int user_idx = find_user(username);
    if (user_idx == -1) {
        result = 1; // Usuario no existe
    } else {
        // Eliminar usuario (mover último elemento a esta posición)
        users[user_idx] = users[user_count - 1];
        user_count--;
        
        // Eliminar sus archivos
        pthread_mutex_lock(&files_mutex);
        for (int i = 0; i < file_count; ) {
            if (strcmp(files[i].owner, username) == 0) {
                files[i] = files[file_count - 1];
                file_count--;
            } else {
                i++;
            }
        }
        pthread_mutex_unlock(&files_mutex);
        
        result = 0; // Éxito
    }
    
    pthread_mutex_unlock(&users_mutex);
    write(client_fd, &result, sizeof(result));
    return result;
}

// Operación CONNECT
int handle_connect(int client_fd, const char *username, const char *port_str) {
    pthread_mutex_lock(&users_mutex);
    
    int result;
    int user_idx = find_user(username);
    if (user_idx == -1) {
        result = 1; // Usuario no existe
    } else if (users[user_idx].connected) {
        result = 2; // Ya conectado
    } else {
        // Obtener IP del cliente
        struct sockaddr_in addr;
        socklen_t addr_size = sizeof(struct sockaddr_in);
        getpeername(client_fd, (struct sockaddr *)&addr, &addr_size);
        
        strcpy(users[user_idx].ip, inet_ntoa(addr.sin_addr));
        users[user_idx].port = atoi(port_str);
        users[user_idx].connected = true;
        result = 0; // Éxito
    }
    
    pthread_mutex_unlock(&users_mutex);
    write(client_fd, &result, sizeof(result));
    return result;
}

// Operación DISCONNECT
int handle_disconnect(int client_fd, const char *username) {
    pthread_mutex_lock(&users_mutex);
    
    int result;
    int user_idx = find_user(username);
    if (user_idx == -1) {
        result = 1; // Usuario no existe
    } else if (!users[user_idx].connected) {
        result = 2; // No conectado
    } else {
        users[user_idx].connected = false;
        result = 0; // Éxito
    }
    
    pthread_mutex_unlock(&users_mutex);
    write(client_fd, &result, sizeof(result));
    return result;
}

// Operación PUBLISH
int handle_publish(int client_fd, const char *username, const char *filename, const char *description) {
    pthread_mutex_lock(&users_mutex);
    int user_idx = find_user(username);
    pthread_mutex_unlock(&users_mutex);
    
    int result;
    if (user_idx == -1) {
        result = 1; // Usuario no existe
    } else if (!users[user_idx].connected) {
        result = 2; // Usuario no conectado
    } else {
        pthread_mutex_lock(&files_mutex);
        if (find_file(filename, username) != -1) {
            result = 3; // Archivo ya publicado
        } else if (file_count >= MAX_FILES) {
            result = 4; // Error del sistema
        } else {
            strcpy(files[file_count].filename, filename);
            strcpy(files[file_count].description, description);
            strcpy(files[file_count].owner, username);
            file_count++;
            result = 0; // Éxito
        }
        pthread_mutex_unlock(&files_mutex);
    }
    
    write(client_fd, &result, sizeof(result));
    return result;
}

// Operación DELETE
int handle_delete(int client_fd, const char *username, const char *filename) {
    pthread_mutex_lock(&users_mutex);
    int user_idx = find_user(username);
    pthread_mutex_unlock(&users_mutex);
    
    int result;
    if (user_idx == -1) {
        result = 1; // Usuario no existe
    } else if (!users[user_idx].connected) {
        result = 2; // Usuario no conectado
    } else {
        pthread_mutex_lock(&files_mutex);
        int file_idx = find_file(filename, username);
        if (file_idx == -1) {
            result = 3; // Archivo no publicado
        } else {
            // Eliminar archivo (mover último elemento a esta posición)
            for (int i = file_idx; i < file_count - 1; i++) {
                files[i] = files[i + 1];
            }
            memset(&files[file_count - 1], 0, sizeof(FileEntry));  // Limpieza
            file_count--;
            
            result = 0; // Éxito
        }
        pthread_mutex_unlock(&files_mutex);
    }
    
    write(client_fd, &result, sizeof(result));
    return result;
}

// Operación LIST_USERS
int handle_list_users(int client_fd, const char *username) {
    pthread_mutex_lock(&users_mutex);
    int user_idx = find_user(username);
    pthread_mutex_unlock(&users_mutex);
    
    int result;
    if (user_idx == -1) {
        result = 1; // Usuario no existe
    } else if (!users[user_idx].connected) {
        result = 2; // Usuario no conectado
    } else {
        result = 0; // Éxito
    }
    unsigned char response_code = (unsigned char)result;
    write(client_fd, &response_code, 1);

    
    if (result == 0) {
        // Solo enviar datos si el resultado fue exitoso
        pthread_mutex_lock(&users_mutex);
        
        // Contar usuarios conectados
        int connected_count = 0;
        for (int i = 0; i < user_count; i++) {
            if (users[i].connected) connected_count++;
        }
        
        // Enviar número de usuarios
        char count_str[MAX_STRING];
        snprintf(count_str, MAX_STRING, "%d", connected_count);
        write(client_fd, count_str, strlen(count_str) + 1); // +1 para el null
        
        // Enviar información de cada usuario
        for (int i = 0; i < user_count; i++) {
            if (users[i].connected) {
                write(client_fd, users[i].username, strlen(users[i].username) + 1);
                write(client_fd, users[i].ip, strlen(users[i].ip) + 1);
                
                char port_str[MAX_STRING];
                snprintf(port_str, MAX_STRING, "%d", users[i].port);
                write(client_fd, port_str, strlen(port_str) + 1);
            }
        }
        pthread_mutex_unlock(&users_mutex);
    }
    
    return result;
}

void handle_list_content(int client_fd, char *username, char *target_user) {
    printf("s> OPERATION LIST_CONTENT FROM %s\n", username);

    pthread_mutex_lock(&users_mutex);
    int requester_idx = find_user(username);
    int target_idx = find_user(target_user);
    pthread_mutex_unlock(&users_mutex);

    unsigned char response_code = 0;

    if (requester_idx == -1) {
        response_code = 1; // USER DOES NOT EXIST
        write(client_fd, &response_code, 1);
        return;
    }

    if (!users[requester_idx].connected) {
        response_code = 2; // USER NOT CONNECTED
        write(client_fd, &response_code, 1);
        return;
    }

    if (target_idx == -1) {
        response_code = 3; // REMOTE USER DOES NOT EXIST
        write(client_fd, &response_code, 1);
        return;
    }

    // Buscar archivos publicados por target_user
    pthread_mutex_lock(&files_mutex);
    int count = 0;
    for (int i = 0; i < file_count; i++) {
        if (strcmp(files[i].owner, target_user) == 0) {
            count++;
        }
    }

    if (count == 0) {
        response_code = 4; // USER HAS NO FILES
        write(client_fd, &response_code, 1);
        pthread_mutex_unlock(&files_mutex);
        return;
    }

    // Enviar código de éxito
    response_code = 0;
    write(client_fd, &response_code, 1);

    // Enviar número de archivos
    char count_str[MAX_STRING];
    snprintf(count_str, MAX_STRING, "%d", count);
    write(client_fd, count_str, strlen(count_str) + 1);

    // Enviar nombres de archivos
    for (int i = 0; i < file_count; i++) {
        if (strcmp(files[i].owner, target_user) == 0) {
            write(client_fd, files[i].filename, strlen(files[i].filename) + 1);
        }
    }
    pthread_mutex_unlock(&files_mutex);
}






// Función principal para manejar cada cliente
void *handle_client(void *arg) {
    int client_fd = *(int *)arg;
    free(arg); // Liberar memoria asignada para el descriptor del cliente

    char buffer[MAX_STRING];
    char *command, *username, *param1 = NULL, *param2;

    // Leer comando
    if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
        close(client_fd);
        return NULL;
    }
    command = strdup(buffer);

    // Leer fecha
    char fecha[MAX_STRING];
    if (readLine(client_fd, fecha, MAX_STRING) <= 0) {
        free(command);
        close(client_fd);
        return NULL;
    }

    // Imprimir la fecha recibida
    printf("s> [FECHA] %s\n", fecha);

    // Leer parámetros según el comando
    if (strcmp(command, "REGISTER") == 0 || strcmp(command, "UNREGISTER") == 0 || 
        strcmp(command, "DISCONNECT") == 0 || strcmp(command, "LIST_USERS") == 0) {
        
        // Comandos con 1 parámetro (username)
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            close(client_fd);
            return NULL;
        }
        username = strdup(buffer);
        

    } else if (strcmp(command, "DELETE") == 0) {
        // DELETE necesita username y filename
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            close(client_fd);
            return NULL;
        }
        username = strdup(buffer);

        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            free(username);
            close(client_fd);
            return NULL;
        }
        param1 = strdup(buffer); // filename

    } else if (strcmp(command, "LIST_CONTENT") == 0) {
        // LIST_CONTENT necesita username y param1 (target_user)
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            close(client_fd);
            return NULL;
        }
        username = strdup(buffer);
        
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            free(username);
            close(client_fd);
            return NULL;
        }
        param1 = strdup(buffer);
        
    } else if (strcmp(command, "PUBLISH") == 0) {
        // PUBLISH necesita username, filename y description
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            close(client_fd);
            return NULL;
        }
        username = strdup(buffer);
        
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            free(username);
            close(client_fd);
            return NULL;
        }
        param1 = strdup(buffer); // filename
        
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            free(username);
            free(param1);
            close(client_fd);
            return NULL;
        }
        param2 = strdup(buffer); // description
        
    } else if (strcmp(command, "CONNECT") == 0) {
        // CONNECT necesita username y port
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            close(client_fd);
            return NULL;
        }
        username = strdup(buffer);
        
        if (readLine(client_fd, buffer, MAX_STRING) <= 0) {
            free(command);
            free(username);
            close(client_fd);
            return NULL;
        }
        param1 = strdup(buffer); // port
    }

    // Registrar operación en el servidor (después de leer username)
    if (username)
    printf("s> OPERATION %s FROM %s\n", command, username);
    else
    printf("s> OPERATION %s\n", command);

    if (username && command && fecha[0] != '\0') {
        if (param1 && strlen(param1) > 0) {
            if (registrar_log_rpc(username, command, param1, fecha) != 0) {
            fprintf(stderr, "s> ERROR al registrar operación RPC\n");
            }
        }
        else{
            if (registrar_log_rpc(username, command, NULL, fecha) != 0) {
            fprintf(stderr, "s> ERROR al registrar operación RPC\n");
            }
        }    
    }
    

    // Procesar operación
    if (strcmp(command, "REGISTER") == 0) {
        if (username) {
            handle_register(client_fd, username);
        } else {
            printf("s> Error: Falta el nombre de usuario para REGISTER\n");
        }
    }
    else if (strcmp(command, "UNREGISTER") == 0) {
        if (username) {
            handle_unregister(client_fd, username);
        } else {
            printf("s> Error: Falta el nombre de usuario para UNREGISTER\n");
        }
    }
    else if (strcmp(command, "CONNECT") == 0) {
        if (username && param1) { // Se espera el puerto como param1
            handle_connect(client_fd, username, param1);
        } else {
            printf("s> Error: Faltan parámetros para CONNECT\n");
        }
    }
    else if (strcmp(command, "DISCONNECT") == 0) {
        if (username) {
            handle_disconnect(client_fd, username);
        } else {
            printf("s> Error: Falta el nombre de usuario para DISCONNECT\n");
        }
    }
    else if (strcmp(command, "PUBLISH") == 0) {
        if (username && param1 && param2) { // Se esperan nombre de archivo y descripción
            handle_publish(client_fd, username, param1, param2);
        } else {
            printf("s> Error: Faltan parámetros para PUBLISH\n");
        }
    }
    else if (strcmp(command, "DELETE") == 0) {
        if (username && param1) { // Se espera el nombre del archivo como param1
            handle_delete(client_fd, username, param1);
        } else {
            printf("s> Error: Faltan parámetros para DELETE\n");
        }
    }
    else if (strcmp(command, "LIST_USERS") == 0) {
        if (username) {
            handle_list_users(client_fd, username);
        } else {
            printf("s> Error: Falta el nombre de usuario para LIST_USERS\n");
        }
    }
    else if (strcmp(command, "LIST_CONTENT") == 0) {
        if (username && param1) { // Se espera el usuario objetivo como param1
            handle_list_content(client_fd, username, param1);
        } else {
            printf("s> Error: Faltan parámetros para LIST_CONTENT\n");
        }
    }
    else {
        printf("s> Error: Comando no reconocido\n");
    }

    close(client_fd);
    return NULL;
}

int main(int argc, char *argv[]) {

    struct sockaddr_in server_addr, client_addr;
    socklen_t client_len;
    int port;
    pthread_t thread_id;

    // Manejar señal SIGINT para apagado ordenado
    signal(SIGINT, handle_signal);

    // Verificar argumentos
    if (argc != 3 || strcmp(argv[1], "-p") != 0) {
        fprintf(stderr, "Debes de introducir: %s -p <port>\n", argv[0]);
        exit(1);
    }

    port = atoi(argv[2]);
    if (port < 1024 || port > 65535) {
        fprintf(stderr, "El puerto debe de estar entre 1024 y 65535\n");
        exit(1);
    }

    // Crear socket
    sd = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);
    if (sd < 0) {
        perror("Error en el socket");
        exit(1);
    }

    // Configurar dirección del servidor
    memset(&server_addr, 0, sizeof(server_addr));
    server_addr.sin_family = AF_INET;
    server_addr.sin_addr.s_addr = INADDR_ANY;
    server_addr.sin_port = htons(port);

    // Reutilizar dirección del socket, en caso de que el puerto esté en uso
    int val = 1;
    if (setsockopt(sd, SOL_SOCKET, SO_REUSEADDR, (char *)&val, sizeof(int)) < 0) {
        perror("Error in setsockopt");
        close(sd);
        exit(1);
    }

    // Enlazar socket
    if (bind(sd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
        perror("Error en bind");
        close(sd);
        exit(1);
    }

    // Escuchar conexiones
    if (listen(sd, 10) < 0) {
        perror("Error en listen");
        close(sd);
        exit(1);
    }

    printf("s> init server %s:%d\n", inet_ntoa(server_addr.sin_addr), port);

    // Bucle principal de aceptación de conexiones
while (server_running) {
    client_len = sizeof(client_addr);

    // Asignar memoria dinámica para el descriptor del cliente
    int *client_sd = malloc(sizeof(int));
    if (client_sd == NULL) {
        perror("Error asignando memoria para client_sd");
        continue;
    }

    *client_sd = accept(sd, (struct sockaddr *)&client_addr, &client_len);
    if (*client_sd < 0) {
        perror("Error en accept");
        free(client_sd); // Liberar memoria si ocurre un error
        continue;
    }

    // Crear hilo para manejar cliente
    if (pthread_create(&thread_id, NULL, handle_client, client_sd) != 0) {
        perror("Error creando hilo");
        close(*client_sd); // Cerrar el socket del cliente en caso de error
        free(client_sd);   // Liberar memoria
    } else {
        pthread_detach(thread_id); // Separar el hilo para que se limpie automáticamente al finalizar
    }
}

    // Limpieza antes de salir
    close(sd);
    printf("Servidor desconectado\n");
    return 0;
}