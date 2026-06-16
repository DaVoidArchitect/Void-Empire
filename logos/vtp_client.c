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

// Rigid VTP Binary Packet specifications (64-byte Intent Frame)
struct VTPIntentPacket {
    unsigned int magic;          // 0x56545049 ("VTPI")
    unsigned int seq_num;        // Monotonic sequence count
    unsigned long long timestamp; // Unix epoch or clock tick
    char intent[16];             // Target deployment intent (e.g. "LogosCompiler")
    char event[16];              // Trigger event name (e.g. "scan_tokens")
    unsigned char signature[16]; // Cryptographic checksum/HMAC-SHA256 signature
};

// State Reflection Response (128-byte Response Frame)
struct VTPStateReflection {
    unsigned int magic;          // 0x56545052 ("VTPR")
    unsigned int seq_num;        // Matching sequence response
    unsigned int status;         // 1 = Transitioned, 2 = Blocked/Rolled Back
    char active_state[16];       // Resolved state in the inner garden
    double mass;                 // Current mesh mass capacity (SI base)
    double energy;               // Current mesh energy capacity
    double entropy;              // Current mesh entropy capacity
    double cycle;                // Current mesh cycle capacity
    double fee_pool;             // Diverted 6.18% platform fee balance
    char details[32];            // Transaction log summary
    unsigned char padding[28];   // Reserved alignment space
    unsigned char signature[32]; // Full cryptographic HMAC-SHA256 signature
};

int main(int argc, char** argv) {
    if (argc < 4) {
        printf("Usage: vtp_client <ip> <port> <event> [intent]\n");
        return 0;
    }

    const char* server_ip = argv[1];
    int port = atoi(argv[2]);
    const char* event_name = argv[3];
    const char* intent_name = (argc > 4) ? argv[4] : "LogosCompiler";

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2,2), &wsa) != 0) {
        printf("WSAStartup Failed.\n");
        return 1;
    }
#endif

    SOCKET sock = socket(AF_INET, SOCK_STREAM, 0);
    if (sock == INVALID_SOCKET) {
        printf("Socket creation failed.\n");
        return 1;
    }

    struct sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(port);
    inet_pton(AF_INET, server_ip, &server_addr.sin_addr);

    printf("[VTP CLIENT] Connecting to inner garden at %s:%d...\n", server_ip, port);
    if (connect(sock, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
        printf("Connection to VTP host failed.\n");
        closesocket(sock);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    // Prepare fixed-size 64-byte Intent Packet
    struct VTPIntentPacket packet;
    memset(&packet, 0, sizeof(packet));
    packet.magic = 0x56545049;
    packet.seq_num = 1;
    packet.timestamp = 1234567890ULL;
    strncpy(packet.intent, intent_name, sizeof(packet.intent) - 1);
    strncpy(packet.event, event_name, sizeof(packet.event) - 1);
    
    // Simulate HMAC signature on the client side
    for (int i = 0; i < 16; i++) {
        packet.signature[i] = (unsigned char)(0xAA ^ i);
    }

    printf("[VTP CLIENT] Transmitting VTP Intent Packet (%d bytes)... Event: %s\n", (int)sizeof(packet), packet.event);
    send(sock, (const char*)&packet, sizeof(packet), 0);

    // Read fixed-size 128-byte State Matrix Reflection
    struct VTPStateReflection reflection;
    memset(&reflection, 0, sizeof(reflection));
    
    int bytes_received = recv(sock, (char*)&reflection, sizeof(reflection), 0);
    if (bytes_received != sizeof(reflection)) {
        printf("[VTP CLIENT] Error: Connection closed or invalid VTP Frame size received.\n");
    } else {
        printf("\n=======================================================\n");
        printf("  STATE REFLECTION MATRIX RECEIVED FROM INNER GARDEN\n");
        printf("=======================================================\n");
        printf("  Magic Anchor:    0x%X\n", reflection.magic);
        printf("  Status Code:     %s (%u)\n", reflection.status == 1 ? "TRANSITIONED" : "BLOCKED/ROLLED BACK", reflection.status);
        printf("  Active State:    %s\n", reflection.active_state);
        printf("  Current Mesh:\n");
        printf("    Mass:          %.4f kg\n", reflection.mass);
        printf("    Energy:        %.4f Wh\n", reflection.energy);
        printf("    Entropy:       %.4f J/K\n", reflection.entropy);
        printf("    Cycle:         %.4f cycles\n", reflection.cycle);
        printf("  Fee Pool:        %.4f Wh (6.18%% platform surcharge)\n", reflection.fee_pool);
        printf("  System Log:      %s\n", reflection.details);
        printf("=======================================================\n");
    }

    closesocket(sock);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;
}
