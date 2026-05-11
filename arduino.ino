#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ตั้งค่า 
const char* WIFI_SSID = "HeNg7";
const char* WIFI_PASS = "heng35700";

// --- Pin สำหรับ AI-Thinker ESP32-CAM ---
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

WebServer server(80);

// ------------------------------------------------
void capture() {
  camera_fb_t* fb = esp_camera_fb_get();

  if (!fb) {
    server.send(500, "text/plain", "Camera capture failed");
    return;
  }

  server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
  server.send_P(200, "image/jpeg", (char*)fb->buf, fb->len);

  esp_camera_fb_return(fb);
}

// ------------------------------------------------
bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0       = Y2_GPIO_NUM;
  config.pin_d1       = Y3_GPIO_NUM;
  config.pin_d2       = Y4_GPIO_NUM;
  config.pin_d3       = Y5_GPIO_NUM;
  config.pin_d4       = Y6_GPIO_NUM;
  config.pin_d5       = Y7_GPIO_NUM;
  config.pin_d6       = Y8_GPIO_NUM;
  config.pin_d7       = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;

  // ตั้งค่าความละเอียด
  if (psramFound()) {
    config.frame_size   = FRAMESIZE_VGA;  // 640*480(ถ้ามี PSRAM)
    config.jpeg_quality = 10;              // 0-63 ยิ่งน้อยยิ่งคมชัด
    config.fb_count     = 2;
  } else {
    config.frame_size   = FRAMESIZE_SVGA;  // 800x600 (ถ้าไม่มี PSRAM)
    config.jpeg_quality = 12;
    config.fb_count     = 1;
  }

  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed: 0x%x\n", err);
    return false;
  }
  return true;
}

// ------------------------------------------------
void setup() {
  Serial.begin(115200);
  Serial.println("\nStarting...");

  // Init กล้อง
  if (!initCamera()) {
    Serial.println("Camera init failed! Restarting...");
    delay(3000);
    ESP.restart();
  }
  Serial.println("Camera ready ✅");

  // เชื่อมต่อ WiFi
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected ✅");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Route
  server.on("/capture", HTTP_GET, capture);
  server.begin();
  Serial.println("Server started ✅");
  Serial.printf("Capture URL: http://%s/capture\n", WiFi.localIP().toString().c_str());
}

// ------------------------------------------------
void loop() {
  server.handleClient();
}
