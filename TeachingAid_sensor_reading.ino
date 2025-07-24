/*
Written by Tan Zheng Ying for his capstone project 'A Teaching Aid for Spinal Mobilisation'
NOTE:
-Ensure that the Arduino Mega 2560 microcontroller is connected to the laptop at all times
-Close the GUI window only when there is no recording in progress
*/

#include <math.h>         //Include library for mathematical calculations

#define REF_VOL 5         //Constant for reference voltage (5V)
#define MAX_BITS 1023     //Constant for maximum number of bits in analogue reading
#define ACCELERATION 9.81 //Constant for gravitational acceleration (9.81m/(s^2))

//Assign pins to spine locations
#define L1L A1
#define L1C A2
#define L1R A3
#define L2L A4
#define L2C A5
#define L2R A6
#define L3L A7
#define L3C A8
#define L3R A9
#define L4L A10
#define L4C A11
#define L4R A12
#define L5L A13
#define L5C A14
#define L5R A15

#define NUM_SENSORS 15  //Constant for total number of sensors
#define NUM_READS 3     //Constant for number of readings for each sensor to calculate average

float total_volts;  //Total voltage reading from analogue readings
float avg_volt;     //Average voltage reading
float sensor_volt;  //Sensor's voltage reading
float sensor_force; //Sensor's force reading
int spine_pins[NUM_SENSORS] = {L1L,L1C,L1R, L2L,L2C,L2R, L3L,L3C,L3R, L4L,L4C,L4R, L5L,L5C,L5R};  //Array of pins of each location
float spine_forces[NUM_SENSORS];  //Initialise array of force of each sensor
String allReadings;  //Initialise string of readings to send via serial

void setup() {  
  Serial.begin(9600);
}

void loop() {
  allReadings = "";   //Reset string of force readings
  for (int s=0; s<NUM_SENSORS; s++){            //For each sensor,
    total_volts = 0;                            //reset total voltage to 0
    for (int r=0; r<NUM_READS; r++){                                          //For each analogue reading,
      sensor_volt = (analogRead(spine_pins[s]) / float(MAX_BITS)) * REF_VOL;  //convert bits to voltage
      total_volts += sensor_volt;                                             //add voltage to total voltage
    }
    avg_volt = total_volts / NUM_READS;         //calculate average voltage
    sensor_force = calculateForce(avg_volt, s); //calculate from voltage to force
    spine_forces[s] = sensor_force;             //assign calculated force to an index in the array of forces
  }
  for (int i=0; i<NUM_SENSORS; i++){  //For each force reading,
    allReadings += spine_forces[i];   //append to string
    if (i != (NUM_SENSORS - 1)){  //If it is not the last reading,
      allReadings += ',';         //append comma
    }
  }
  Serial.println(allReadings);        //Send string of force readings via serial communication
  delay(1000);
}

float calculateForce(float voltage, int sensor_index){
  int vertebra = (sensor_index / 3) + 1;  //Find vertebra of lumbar section
  int position = sensor_index % 3;        //Find left (0), centre (1) or right (2) position
  float mass;                             //Initialise variable for mass
  float force;                            //Initialise variable for force
  if (vertebra == 1){         //L1 vertebra
    if (position == 0){       //L1L transfer function
      mass = ((-1.5809) + sqrt(2.49924481 + 0.2656 * voltage)) / 0.1328;
    }
    else if (position == 1){  //L1C transfer function
      mass = ((-1.0657) + sqrt(1.13571649 + 0.5232 * voltage)) / 0.2616;
    }
    else if (position == 2){  //L1R transfer function
      mass = ((-1.0967) + sqrt(1.20275089 + 0.626 * voltage)) / 0.313;
    }
  }
  else if (vertebra == 2){    //L2 vertebra
    if (position == 0){       //L2L transfer function
      mass = 0;//Insert transfer function for L2L (after capstone project)
    }
    else if (position == 1){  //L2C transfer function
      mass = ((0.8635) - sqrt(0.74563225 - 0.5748 * voltage)) / 0.2874;
    }
    else if (position == 2){  //L2R transfer function
      mass = 0;//Insert transfer function for L2R (after capstone project)
    }
  }
  else if (vertebra == 3){    //L3 vertebra
    if (position == 0){       //L3L transfer function
      mass = 0;//Insert transfer function for L3L (after capstone project)
    }
    else if (position == 1){  //L3C transfer function
      mass = ((-0.1506) + sqrt(0.02268036 + 0.1068 * voltage)) / 0.0534;
    }
    else if (position == 2){  //L3R transfer function
      mass = 0;//Insert transfer function for L3R (after capstone project)
    }
  }
  else if (vertebra == 4){    //L4 vertebra
    if (position == 0){       //L4L transfer function
      mass = 0;//Insert transfer function for L4L (after capstone project)
    }
    else if (position == 1){  //L4C transfer function
      mass = ((0.266) - sqrt(0.070756 - 0.0504 * voltage)) / 0.0252;
    }
    else if (position == 2){  //L4R transfer function
      mass = 0;//Insert transfer function for L4R (after capstone project)
    }
  }
  else if (vertebra == 5){    //L5 vertebra
    if (position == 0){       //L5L transfer function
      mass = 0;//Insert transfer function for L5L (after capstone project)
    }
    else if (position == 1){  //L5C transfer function
      mass = ((-0.1774) + sqrt(0.03147076 + 0.2368 * voltage)) / 0.1184;
    }
    else if (position == 2){  //L5R transfer function
      mass = 0;//Insert transfer function for L5R (after capstone project)
    }
  }
  force = mass * ACCELERATION; //Convert mass to force, since transfer function is based on voltage-mass relationship
  return force;                //Return calculated force
}