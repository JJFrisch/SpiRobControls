# SpiRobControls

<img src="Assets/SpiRob Zheng Lab Logo.png" width="200">


### Quick Abstract
##### What are we doing? why? Lorem ipsum dolor sit amet, 

I am working with a two cable spirob. I have the physical system build, including the SpiRob, Arduino 28BYJ-84 step motors, a motor holder and a spool. Wires go through the SpiRob and around the spool. The motors turn the spool and control the SpiRob's movement.


# Components

 - ### The SpiRob Arm
   
![IMG_7711](https://github.com/user-attachments/assets/0837e2b8-34a1-4828-8349-c7bd39dd22cc)
![IMG_7708](https://github.com/user-attachments/assets/fd5c9af3-754a-45e5-a628-6bd4fca264d5)

   
 - ### The Base and Stand

![IMG_7955](https://github.com/user-attachments/assets/a2900732-6b4f-4c79-b37e-c3dc7313f789)

![IMG_7956](https://github.com/user-attachments/assets/f3c369db-63f8-4919-81c2-023af8348746)

![IMG_7957](https://github.com/user-attachments/assets/ae125a1c-d629-4f01-ba3e-97defd598465)

![IMG_7944](https://github.com/user-attachments/assets/9f7b5ae0-e98f-4ad6-b8dd-2201eaa29b3c)


 - ### The Ardunio Step Motor 28BJY-48

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
   
   
   
   





**May 6th 20205**

Mini SpiRob Testing



https://github.com/user-attachments/assets/26b53d3d-497c-47d8-9731-5240ee73252a






**May 8th 20205**

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

 - Stronger motors: the arduino step motor 28BJY-48 does not produce enough torque to fully curl or control the two-cable SpiRob. 
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
