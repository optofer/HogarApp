#include "esp_camera.h"
#include <WiFi.h>

static const char* WIFI_SSID = "manchitanoa2014";
static const char* WIFI_PASSWORD = "lumbalgia2020";
static const char* SERVER_HOST = "192.168.10.10";
static const uint16_t SERVER_PORT = 8002;
static const char* CAMERA_ID = "cam3";
static const char* CAMERA_TOKEN = "";

static const uint32_t CAPTURE_INTERVAL_MS = 3000;
static const uint32_t WIFI_CONNECT_TIMEOUT_MS = 20000;
static const uint32_t SERVER_TIMEOUT_MS = 10000;
static const framesize_t CAMERA_FRAME_SIZE = FRAMESIZE_VGA;
static const int CAMERA_JPEG_QUALITY = 12;
static const char* BOUNDARY = "----esp32cam-boundary-7MA4YWxkTrZu0gW";

#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM      0
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27

#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       21
#define Y4_GPIO_NUM       19
#define Y3_GPIO_NUM       18
#define Y2_GPIO_NUM        5
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

bool connect_wifi() {
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.printf("Conectando a WiFi SSID=%s\n", WIFI_SSID);
  uint32_t start = millis();
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    if (millis() - start > WIFI_CONNECT_TIMEOUT_MS) {
      Serial.println();
      return false;
    }
  }

  Serial.println();
  return true;
}

bool init_camera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size = CAMERA_FRAME_SIZE;
  config.jpeg_quality = CAMERA_JPEG_QUALITY;
  config.fb_count = 1;
  config.grab_mode = CAMERA_GRAB_LATEST;

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("esp_camera_init fallo: 0x%x\n", err);
    return false;
  }
  return true;
}

void print_runtime_config() {
  Serial.println("Configuracion de emisor ESP32-CAM:");
  Serial.printf("  CAMERA_ID: %s\n", CAMERA_ID);
  Serial.printf("  SERVER: http://%s:%u/api/cam/%s/frame\n", SERVER_HOST, SERVER_PORT, CAMERA_ID);
  Serial.printf("  TOKEN: %s\n", strlen(CAMERA_TOKEN) > 0 ? "habilitado" : "deshabilitado");
  Serial.printf("  CAPTURE_INTERVAL_MS: %lu\n", (unsigned long)CAPTURE_INTERVAL_MS);
}

bool upload_frame(camera_fb_t* fb) {
  WiFiClient client;
  client.setTimeout(SERVER_TIMEOUT_MS / 1000);

  if (!client.connect(SERVER_HOST, SERVER_PORT, SERVER_TIMEOUT_MS)) {
    Serial.println("No se pudo conectar al servidor");
    return false;
  }

  String path = "/api/cam/" + String(CAMERA_ID) + "/frame";
  String head =
      "--" + String(BOUNDARY) + "\r\n"
      "Content-Disposition: form-data; name=\"frame\"; filename=\"frame.jpg\"\r\n"
      "Content-Type: image/jpeg\r\n\r\n";
  String tail = "\r\n--" + String(BOUNDARY) + "--\r\n";
  size_t content_length = head.length() + fb->len + tail.length();

  client.printf("POST %s HTTP/1.1\r\n", path.c_str());
  client.printf("Host: %s:%u\r\n", SERVER_HOST, SERVER_PORT);
  client.println("Connection: close");
  client.println("User-Agent: esp32-cam-sender/1.0");
  client.println("Accept: application/json");
  if (strlen(CAMERA_TOKEN) > 0) {
    client.printf("X-Camera-Token: %s\r\n", CAMERA_TOKEN);
  }
  client.printf("Content-Type: multipart/form-data; boundary=%s\r\n", BOUNDARY);
  client.printf("Content-Length: %u\r\n", (unsigned int)content_length);
  client.println();

  client.print(head);
  client.write(fb->buf, fb->len);
  client.print(tail);

  uint32_t start = millis();
  while (!client.available() && client.connected()) {
    delay(10);
    if (millis() - start > SERVER_TIMEOUT_MS) {
      Serial.println("Timeout esperando respuesta HTTP");
      client.stop();
      return false;
    }
  }

  String status_line = client.readStringUntil('\n');
  status_line.trim();
  Serial.println(status_line);
  Serial.printf("Bytes enviados: %u\n", (unsigned int)fb->len);

  bool ok = status_line.indexOf("200") >= 0;
  while (client.available()) {
    Serial.write(client.read());
  }
  client.stop();
  return ok;
}

void setup() {
  Serial.begin(115200);
  delay(1000);
  print_runtime_config();

  if (!init_camera()) {
    Serial.println("Error inicializando la camara");
    while (true) {
      delay(1000);
    }
  }

  if (!connect_wifi()) {
    Serial.println("No se pudo conectar al WiFi");
  } else {
    Serial.print("WiFi conectado. IP local: ");
    Serial.println(WiFi.localIP());
  }
}

void loop() {
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("Reconectando WiFi...");
    if (!connect_wifi()) {
      delay(2000);
      return;
    }
  }

  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("No se pudo capturar frame");
    delay(CAPTURE_INTERVAL_MS);
    return;
  }

  bool ok = upload_frame(fb);
  esp_camera_fb_return(fb);

  if (!ok) {
    Serial.println("Upload fallido");
  }

  delay(CAPTURE_INTERVAL_MS);
}
