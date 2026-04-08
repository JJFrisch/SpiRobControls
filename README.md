# SpiRobControls

<img src="Assets/SpiRob Zheng Lab Logo.png" width="200">


### Quick Abstract

This project implements hardware control and physics-based simulation for a two-cable **[SpiRob](https://doi.org/10.1016/j.device.2024.100646)** — a logarithmic-spiral-shaped soft robot capable of versatile grasping. Two 28BYJ-48 stepper motors tension and release fishing-wire cables that thread through a spiral TPU body, causing it to curl in a controlled direction. This repo covers the full stack: 3D-printed hardware, Arduino motor control sketches, and physics-based simulation environments in MuJoCo and Isaac Lab.

I am working with a two-cable SpiRob. I have the physical system built, including the SpiRob, Arduino 28BYJ-48 stepper motors, a motor holder, and a spool. Wires go through the SpiRob and around the spool. The motors turn the spool and control the SpiRob's movement.


# Components

 - ### The SpiRob Arm
   
![IMG_7711](https://github.com/user-attachments/assets/0837e2b8-34a1-4828-8349-c7bd39dd22cc)
![IMG_7708](https://github.com/user-attachments/assets/fd5c9af3-754a-45e5-a628-6bd4fca264d5)

   
 - ### The Base and Stand

![IMG_7955](https://github.com/user-attachments/assets/a2900732-6b4f-4c79-b37e-c3dc7313f789)

![IMG_7956](https://github.com/user-attachments/assets/f3c369db-63f8-4919-81c2-023af8348746)

![IMG_7957](https://github.com/user-attachments/assets/ae125a1c-d629-4f01-ba3e-97defd598465)

![IMG_7944](https://github.com/user-attachments/assets/9f7b5ae0-e98f-4ad6-b8dd-2201eaa29b3c)


 - ### The Arduino Stepper Motor 28BYJ-48

![IMG_7952](https://github.com/user-attachments/assets/01a597e0-8427-45ba-b5a7-a2811b0426e8)

![IMG_7951](https://github.com/user-attachments/assets/09d7b81a-e778-4405-bfa8-0c598f86fafd)


 - ### The Spools

![image](https://github.com/user-attachments/assets/3744bbee-6153-4e29-9627-d0e1c8eeb5c0)


 - ### The Motor Stands

![IMG_7747](https://github.com/user-attachments/assets/8d18ae8b-3cbf-4ba2-8d24-ba0bfe5bb8ca)


 - ### The Wire

![IMG_7710](https://github.com/user-attachments/assets/2ccf6d8f-2b6d-4903-a922-1057082ab32c)

   
 - ### The Circiut
     - Overview

![IMG_7953](https://github.com/user-attachments/assets/3ed8001d-32db-4f43-98fd-e997c2a4ab82)

![IMG_7721](https://github.com/user-attachments/assets/1d9db685-0a94-4fb3-b1a6-6f870eb35c3d)

     - Parts

![IMG_7954](https://github.com/user-attachments/assets/02e8638a-e66d-4b26-9215-6963f3577e0b)

     
 - ### Arduino Code

   | Sketch | Description |
   |---|---|
   | [`Monostepper_Control_Arduino.ino`](Controls/Monostepper_Control_Arduino/Monostepper_Control_Arduino.ino) | Single-motor step tracking with length-based safety limit |
   | [`IR_Remote_With_Stepper_Motor.ino`](Controls/Monostepper_Control_Arduino/IR_Remote_With_Stepper_Motor/IR_Remote_With_Stepper_Motor.ino) | IR remote + Serial control with auto-retract safety |
   | [`Max_Steps.ino`](Controls/Monostepper_Control_Arduino/Max_Steps/Max_Steps.ino) | Stall-finding experiment (measured physical motor limits) |
   | [`MultiMotor_Controls.ino`](Controls/Monostepper_Control_Arduino/MultiMotor_Controls/MultiMotor_Controls.ino) | Production 3-motor controller with relax-ratio cable coordination |
   | [`Testing_Relax_Ratio.ino`](Controls/Monostepper_Control_Arduino/Testing_Relax_Ratio/Testing_Relax_Ratio.ino) | Experiments to tune the passive-motor slack ratio |
   | [`bipolar_stepper_motor.ino`](Controls/bipolar_stepper_motor/bipolar_stepper_motor.ino) | Bipolar stepper driver test with push buttons |

---

## 🚀 Getting Started

### Hardware Required
- 2× 28BYJ-48 stepper motors + ULN2003 driver boards
- Arduino Uno (or compatible)
- IR remote (NEC protocol, 21-key generic) + VS1838B receiver module
- 3D-printed SpiRob body (TPU-70A), spools, motor mounts, and base — see [`Models/`](Models/)
- Fishing wire

### Wiring
```
Motor 1 ULN2003:  IN1→8  IN2→9  IN3→10  IN4→11
Motor 2 ULN2003:  IN1→4  IN2→5  IN3→6   IN4→7
IR Receiver data: → pin 12
```

### Arduino Library Dependencies
Install via **Arduino IDE → Tools → Manage Libraries**:
- **AccelStepper** by Mike McCauley
- **IRremote** ≥ 4.x by Armin Joachimsmeyer
- **Stepper** (built-in) and **MultiStepper** (built-in with AccelStepper)

### Recommended Upload Order
1. `Monostepper_Control_Arduino.ino` — verify single motor wiring
2. `Max_Steps.ino` — find stall limits of each motor
3. `Testing_Relax_Ratio.ino` — tune passive-motor slack ratio
4. `MultiMotor_Controls.ino` — deploy coordinated two-cable control

---

## 📓 Lab Log

**May 6th, 2025**

Mini SpiRob Testing



https://github.com/user-attachments/assets/26b53d3d-497c-47d8-9731-5240ee73252a






**May 8th, 2025**

We started the print of our full sized SpiRob, testing SpiROb shown for scale. The full model has a 12 hour build time and is made of TPU-70A for flexibility and strength.

![thumbnail_IMG_7640](https://github.com/user-attachments/assets/e35ee814-b298-4bb8-a3fc-6146c4e591f1)

![thumbnail_IMG_7638](https://github.com/user-attachments/assets/9bb93bcb-c744-4a6c-aa65-d33fd86fd921)


Monodirectional Stepper Motor Circuit

![thumbnail_IMG_7642](https://github.com/user-attachments/assets/053f7348-bbb1-4e4f-949f-b7c14ebd4cb8)


Bidirectional Stepper Motor Circuit

![thumbnail_IMG_7641](https://github.com/user-attachments/assets/1ab60ccf-6b08-48b5-9135-00bfea3ea04c)


We ran into an issue with printing using the right nozzle. Switching the TPU fillament to the other nozzle fixed this issue.

https://github.com/user-attachments/assets/064c2381-0a16-4408-b68d-ab61ad8286e9

The updates as shown and described in the commit - first rotary spool test failure -

[![Spool Test Demo](./media/spool-test-thumb.png)](https://drexel0-my.sharepoint.com/:v:/r/personal/jfw69_drexel_edu/Documents/Videos/Clipchamp/Video%20Project%202/Exports/SPIROBS_UPDATE_SPOOL_TEST.mp4?csf=1&web=1&e=miKF8t)

In the next test, we mitigate some of the preliminary mistakes - lose cables around the spoolss, a slightly better anchored "anchor" string to vieew the actuation behavior. Visible actuation but obviously uncontrolled and in need of much refinement:
see below:

[![Spool test Demonstration number 2](https://drexel0-my.sharepoint.com/:v:/r/personal/jfw69_drexel_edu/Documents/Videos/Clipchamp/Video%20Project%204/Exports/SPOOL_TEST_UPDATE_05132025.mp4?csf=1&web=1&e=x9gOBd)


There are a few kinks to sort out -the spools connection to cable and shaft, the wrap around and the control of the actuation. Promising first steps.


# Flaws and Possible Improvements

 - Stronger motors: the Arduino stepper motor 28BYJ-48 does not produce enough torque to fully curl or control the two-cable SpiRob. 
 - We use fishing wire. It is too stretchable a wire which stretches instead of pulling the SpiRob at ends of the domain where tension is high.
 - When printing the SpiRob arm we used too low an infil percent. The structure of the SpiRob sometimes buckles under higher stress.
 - Our robot lacked an elastic core to produce a restoring force towards the initial position. 




For the idea of a SpiRob and the .stl models of both a two and three cable SpiRob,
Credit to Zhanchi Wang, Nikolaos M. Freris, Xi Wei,  
SpiRobs: Logarithmic spiral-shaped robots for versatile grasping across scales,  
Device,
Volume 3, Issue 4,
2025,
100646,
ISSN 2666-9986,
https://doi.org/10.1016/j.device.2024.100646.
(https://www.sciencedirect.com/science/article/pii/S2666998624006033)  
Keywords: soft robots; logarithmic spiral; multi-scale design; bioinspired design and operation
