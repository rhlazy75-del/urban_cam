#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID  = "HeNg7";
const char* WIFI_PASS  = "heng35700";
const char* SERVER_URL = "http://10.132.250.140:6601/ucs/api/upload";
const char* DEVICE_ID  = "CAM_LEFT";  // ← กล้องซ้าย

#define LED_PIN 4
#define PWDN_GPIO_NUM   32
#define RESET_GPIO_NUM  -1
#define XCLK_GPIO_NUM    0
#define SIOD_GPIO_NUM   26
#define SIOC_GPIO_NUM   27
#define Y9_GPIO_NUM     35
#define Y8_GPIO_NUM     34
#define Y7_GPIO_NUM     39
#define Y6_GPIO_NUM     36
#define Y5_GPIO_NUM     21
#define Y4_GPIO_NUM     19
#define Y3_GPIO_NUM     18
#define Y2_GPIO_NUM      5
#define VSYNC_GPIO_NUM  25
#define HREF_GPIO_NUM   23
#define PCLK_GPIO_NUM   22

unsigned long lastCapture = 0;
int captureCount = 0;

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer   = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM; config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM; config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM; config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM; config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk     = XCLK_GPIO_NUM;
  config.pin_pclk     = PCLK_GPIO_NUM;
  config.pin_vsync    = VSYNC_GPIO_NUM;
  config.pin_href     = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn     = PWDN_GPIO_NUM;
  config.pin_reset    = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  config.frame_size   = FRAMESIZE_VGA;
  config.jpeg_quality = 12;
  config.fb_count     = 1;

  if (esp_camera_init(&config) != ESP_OK) {
    Serial.println("[CAM] เริ่มไม่ได้!");
    return;
  }
  Serial.println("[CAM_LEFT] พร้อมแล้ว");

  WiFi.begin(WIFI_SSID, WIFI_PASS);
  Serial.print("[WiFi] กำลังเชื่อมต่อ");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\n[WiFi] เชื่อมต่อแล้ว: " + WiFi.localIP().toString());
}

void loop() {
  if (millis() - lastCapture > 10000) {
    lastCapture = millis();
    captureCount++;
    captureAndSend();
  }
  if (WiFi.status() != WL_CONNECTED) {
    WiFi.reconnect();
  }
}

void captureAndSend() {
  Serial.println("\n[LEFT-" + String(captureCount) + "] ถ่ายภาพ...");

  digitalWrite(LED_PIN, HIGH);
  delay(100);
  camera_fb_t* fb = esp_camera_fb_get();
  digitalWrite(LED_PIN, LOW);

  if (!fb) {
    Serial.println("[CAM] ถ่ายไม่ได้!");
    return;
  }
  Serial.printf("[CAM] %d bytes (%dx%d)\n", fb->len, fb->width, fb->height);

  HTTPClient http;
  http.begin(SERVER_URL);
  http.setTimeout(15000);

  String boundary = "ESP32Boundary";
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);

  String head = "--" + boundary + "\r\n"
                "Content-Disposition: form-data; name=\"image\"; filename=\"photo.jpg\"\r\n"
                "Content-Type: image/jpeg\r\n\r\n";
  String tail = "\r\n--" + boundary + "\r\n"
                "Content-Disposition: form-data; name=\"device_id\"\r\n\r\n" +
                String(DEVICE_ID) +
                "\r\n--" + boundary + "--\r\n";

  int totalLen = head.length() + fb->len + tail.length();
  uint8_t* buf = (uint8_t*)malloc(totalLen);
  if (!buf) {
    Serial.println("[SEND] RAM ไม่พอ!");
    esp_camera_fb_return(fb);
    return;
  }

  int offset = 0;
  memcpy(buf + offset, head.c_str(), head.length()); offset += head.length();
  memcpy(buf + offset, fb->buf,      fb->len);       offset += fb->len;
  memcpy(buf + offset, tail.c_str(), tail.length());
  esp_camera_fb_return(fb);

  int code = http.POST(buf, totalLen);
  free(buf);

  if (code == 201) {
    Serial.println("[SEND] ส่งสำเร็จ! ✓");
  } else {
    Serial.println("[SEND] ส่งไม่ได้: " + String(code));
  }
  http.end();
}
