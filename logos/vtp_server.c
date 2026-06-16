#ifdef _WIN32
    #define _WIN32_WINNT 0x0600
    #include <winsock2.h>
    #include <ws2tcpip.h>
    #pragma comment(lib, "ws2_32.lib")
#else
    #include <sys/socket.h>
    #include <arpa/inet.h>
    #include <unistd.h>
    #define SOCKET int
    #define INVALID_SOCKET -1
    #define closesocket close
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>

struct VTPIntentPacket {
    unsigned int magic;
    unsigned int seq_num;
    unsigned long long timestamp;
    char intent[16];
    char event[16];
    unsigned char signature[16];
};

struct VTPStateReflection {
    unsigned int magic;
    unsigned int seq_num;
    unsigned int status;
    char active_state[16];
    double mass;
    double energy;
    double entropy;
    double cycle;
    double fee_pool;
    char details[32];
    unsigned char padding[28];
    unsigned char signature[32];
};

// In-memory insulated state database representing the inner garden
double mesh_mass = 100000.0;
double mesh_energy = 50000.0;
double mesh_entropy = 1000.0;
double mesh_cycle = 2000.0;
double fee_pool = 0.0;
char active_state[16] = "Initialize";

int main(int argc, char** argv) {
    int port = (argc > 1) ? atoi(argv[1]) : 5050;

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        printf("WSAStartup Failed.\n");
        return 1;
    }
#endif

    SOCKET server_fd = socket(AF_INET, SOCK_STREAM, 0);
    if (server_fd == INVALID_SOCKET) {
        printf("Socket failed.\n");
        return 1;
    }

    // Set socket reuse option
    int opt = 1;
    setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, (const char*)&opt, sizeof(opt));

    struct sockaddr_in address;
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(port);

    if (bind(server_fd, (struct sockaddr*)&address, sizeof(address)) < 0) {
        printf("Bind failed.\n");
        closesocket(server_fd);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    if (listen(server_fd, 3) < 0) {
        printf("Listen failed.\n");
        closesocket(server_fd);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    printf("[VTP SERVER] Insulated Inner Garden listening on port %d...\n", port);

    while (1) {
        struct sockaddr_in client_addr;
        int addrlen = sizeof(client_addr);
        SOCKET client_sock = accept(server_fd, (struct sockaddr*)&client_addr, &addrlen);
        if (client_sock == INVALID_SOCKET) {
            continue;
        }

        // Receive fixed-size 64-byte Intent Frame
        struct VTPIntentPacket intent;
        memset(&intent, 0, sizeof(intent));
        
        int bytes_read = recv(client_sock, (char*)&intent, sizeof(intent), 0);
        
        // STRICT BOUNDARY PROTECTION: If packet size doesn't match or magic is wrong, disconnect.
        if (bytes_read != sizeof(intent) || intent.magic != 0x56545049) {
            printf("[VTP SERVER] [ALERT] Invalid boundary packet received. Dropping connection to prevent cross-contamination.\n");
            closesocket(client_sock);
            continue;
        }

        printf("[VTP SERVER] Received VTP Intent: %s::%s\n", intent.intent, intent.event);

        struct VTPStateReflection reflection;
        memset(&reflection, 0, sizeof(reflection));
        reflection.magic = 0x56545052;
        reflection.seq_num = intent.seq_num;
        
        // Process transition logic natively inside the inner garden
        // 2-Phase Atomic Rollover and 6.18% platform fee checks:
        double backup_mass = mesh_mass;
        double backup_energy = mesh_energy;
        double backup_entropy = mesh_entropy;
        double backup_cycle = mesh_cycle;
        double backup_fee_pool = fee_pool;

        double required_energy = 50.0; // Base Wh cost for compilation transition
        double required_cycle = 100.0;
        
        // Apply 6.18% fee
        double total_energy = required_energy * 1.0618;
        double total_cycle = required_cycle * 1.0618;
        double energy_fee = required_energy * 0.0618;
        double cycle_fee = required_cycle * 0.0618;

        if (strcmp(intent.event, "scan_tokens") == 0 && strcmp(active_state, "Initialize") == 0) {
            if (mesh_energy >= total_energy && mesh_cycle >= total_cycle) {
                // Deduct resources
                mesh_energy -= total_energy;
                mesh_cycle -= total_cycle;
                
                // Divert fee to pool
                fee_pool += (energy_fee + cycle_fee);
                
                strcpy(active_state, "Lexing");
                reflection.status = 1; // Transitioned
                strcpy(reflection.details, "Transition OK");
            } else {
                // Deficit: Trigger Rollback
                mesh_mass = backup_mass;
                mesh_energy = backup_energy;
                mesh_entropy = backup_entropy;
                mesh_cycle = backup_cycle;
                fee_pool = backup_fee_pool;
                
                reflection.status = 2; // Blocked
                strcpy(reflection.details, "Deficit: Rollback triggered");
            }
        } else if (strcmp(intent.event, "tokens_ready") == 0 && strcmp(active_state, "Lexing") == 0) {
            // Sample transition to Parsing
            strcpy(active_state, "Parsing");
            reflection.status = 1;
            strcpy(reflection.details, "Transition OK");
        } else {
            reflection.status = 2;
            strcpy(reflection.details, "No matching transition rule");
        }

        // Pack reflection status
        strcpy(reflection.active_state, active_state);
        reflection.mass = mesh_mass;
        reflection.energy = mesh_energy;
        reflection.entropy = mesh_entropy;
        reflection.cycle = mesh_cycle;
        reflection.fee_pool = fee_pool;
        
        // Sign package
        for (int i = 0; i < 32; i++) {
            reflection.signature[i] = (unsigned char)(0x55 ^ i);
        }

        printf("[VTP SERVER] Reflecting State delta: State=%s, Status=%d, Details=%s\n", 
               reflection.active_state, reflection.status, reflection.details);
               
        send(client_sock, (const char*)&reflection, sizeof(reflection), 0);
        closesocket(client_sock);
    }

    closesocket(server_fd);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
