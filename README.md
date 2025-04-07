# Motion-Pattern-Recognition-System-Logic
Attached are various software files needed to recreate the Motion Pattern Recognition System. This device is capable of identifying movement based on the acceleration data captured from the microcontroller to a database. An OLED device hosts the information so you do not have to view it solely on the terminal.

Software Setup:
For this project I used the following softwares:
Python (Host code, responsible for handling the data fed from the Arduino IDE / MySQL Database and applying algorithms to classify movement)
Arduino IDE (Responsible for obtanining data from a connected MPU6050 Sensor and displaying results onto an 0.96 Inch, I2C OLED Screen)
MySQL (Database used to group movements together for python to feed into)

Hardware Used:
MPU6050 Sensor
Arduino Uno R4 WiFi
0.96 OLED I2C Display

Connections:
A big thing going for this project was simplicity, the I2C library as you might or might not know, relys on the SDA/SCL Pins to drive inputs on the interface. Simply connect both these pins to the designated inputs that share the same name (connections are shared so if possible, you can use a common node/rail and connect each together). The OLED in my case uses a 5V power input, while the MPU6050 uses a 3v3 input. Lastly connect each to GND.

Finally you can move onto the software aspect
Please note, for the Arduino IDE, you will need to install libraries shown at the top of the file. These are sensor/display specific so be warned if you are using different parts!
Same goes for Python

Software Used:
Arduino IDE
Python (on visual studio code)
MySQL/MySQL Workbench

How to use:
1.Upload the Arduino file to the IDE and connect it with your board. If all is working correctly you'll be able to see movement idenfitied between Idle/Rest/Walk/Run. Some of these parameters might have to be changed depending on your environment so be aware you might just have to tweak values.
2.Upload the MySQL Workbench Queries and keep the software open so that Python can properly read from the database
3.Two python files are included, the one called "test_db_connection" is used to properly read acceleration movement and pair it with a movement keyword (high accel = running). Keep this running to collect data over a time period, once finish press "Crtl+C" to end readings *DO NOT KILL/CLOSE THE TERMINAL* doing so wont register your information to MySQL, please make sure to use Crtl+C!
Finally open the other file called "machine_learned_results", this will obtain the most recent data in a given timeframe (you can edit the timeframe in the code itself) I only put a short timeframe to verify results / connections, but you should see two charts. One denotes periods of where you stopped/started moving. Another is used to show the timeline of movement: rest -> idle -> walk -> run -> walk -> idle for example.
Below are my finished results of the circuit and tables
![TestResults](https://github.com/user-attachments/assets/e2a3c068-3f49-4eb7-aa4b-1b1bfa8500fd)
![MotionSensorConnections](https://github.com/user-attachments/assets/d9954b19-35fb-4762-bb29-dca3d2a841fd)


