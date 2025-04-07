#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>

// OLED display configuration
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET    -1  // Reset pin # (or -1 if sharing Arduino reset pin)
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// MPU6050 sensor (using Adafruit library)
Adafruit_MPU6050 mpu;

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("MPU6050 and OLED Test");
  
  // Initialize I2C
  Wire.begin();
  
  // Initialize OLED
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3C for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for(;;); // Don't proceed, loop forever
  }
  
  // Clear the display buffer
  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 0);
  display.println("MPU6050 & OLED Test");
  display.display();
  delay(2000);
  
  // Initialize MPU6050
  Serial.println("Initializing MPU6050...");
  if (!mpu.begin()) {
    Serial.println("Could not find a valid MPU6050 sensor, check wiring!");
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println("MPU6050 not found!");
    display.display();
    while (1) {
      delay(10);
    }
  }
  
  // Configure MPU6050
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  mpu.setGyroRange(MPU6050_RANGE_500_DEG);
  mpu.setFilterBandwidth(MPU6050_BAND_21_HZ);
  
  Serial.println("MPU6050 initialized successfully!");
}

void loop() {
  // Read accelerometer and gyroscope values
  sensors_event_t a, g, temp;
  mpu.getEvent(&a, &g, &temp);
  
  // Print to serial monitor
  Serial.print("Accel: ");
  Serial.print(a.acceleration.x);
  Serial.print(" ");
  Serial.print(a.acceleration.y);
  Serial.print(" ");
  Serial.print(a.acceleration.z);
  Serial.print(" | Gyro: ");
  Serial.print(g.gyro.x);
  Serial.print(" ");
  Serial.print(g.gyro.y);
  Serial.print(" ");
  Serial.println(g.gyro.z);
  
  // Display on OLED
  display.clearDisplay();
  display.setCursor(0, 0);
  display.println("MPU6050 Readings:");
  
  display.setCursor(0, 16);
  display.print("Accel X: ");
  display.println(a.acceleration.x);
  
  display.setCursor(0, 24);
  display.print("Accel Y: ");
  display.println(a.acceleration.y);
  
  display.setCursor(0, 32);
  display.print("Accel Z: ");
  display.println(a.acceleration.z);
  
  display.setCursor(0, 48);
  display.print("Gyro X: ");
  display.println(g.gyro.x);
  
  display.setCursor(0, 56);
  display.print("Gyro Y: ");
  display.println(g.gyro.y);
  
  display.display();
  
  delay(100);  // Update every 100ms
}