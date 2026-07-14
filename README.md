# Description:
This repository was created by Tan Zheng Ying for his capstone project 'A Teaching Aid for Spinal Mobilisation'.
The programs were developed for a prototype of a teaching aid for physiotherapy students to conduct trials for a thesis.
The thesis explored the use of an objective visual feedback tool for improving students' performance in spinal mobilisation.
The teaching aid prototype is an embedded system, consisting of pressure sensors wired to an Arduino Mega 2560 Rev 3 microcontroller.
The microcontroller is wired to a laptop that shows the graphical user interface (GUI), which shows the visual feedback.

# 🚀 Features
- Feature 1: Real-time data processing of sensor inputs
- Feature 2: Responsive graphical user interface (GUI)
- Feature 3: Recording of feedback results in an Excel file

# 🛠️ Built with:
## Python language (TeachingAid_GUI.py):
- Tkinter: creation of GUI interface
- Matplotlib: plotting of figures
- Pandas: data manipulation and analysis
- Serial: accessing serial port
- Time: manipulation of timev values
## C++ language (TeachingAid_sensor_reading.ino):
- math.h: library for mathematical calculations

# 📦 Getting started:
## Prerequisites:
Make sure you have the following:
- Arduino IDE installed in your local machine
- Python IDE (e.g. Visual Studio, PyCharm) installed in your local machine
- Parrallel branches of pressure sensors formed on an electrical circuit (e.g. breadboard, printed circuit board)
## Usage:
1) Form parallel branches of pressure sensors on an electrical circuit, then connect them to the Arduino microcontroller.
2) Connect the microcontroller to a laptop using a USB Type A-to-B cable.
3) Run TeachingAid_sensor_reading.ino on the microcontroller.
4) Run TeachingAid_GUI.py on the laptop.
5) Click on the 'Start Recording' button of the GUI to observe the results.
6) Click on the 'Stop Recording' button of the GUI to stop recording and an Excel file of the results will be produced.
