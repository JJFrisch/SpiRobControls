# SpiRobControls


### Quick Abstract
##### What are we doing? why? Lorem ipsum dolor sit amet, 

I am working with a two cable spirob. I have the physical system build, including the SpiRob, Arduino 28BYJ-84 step motors, a motor holder and a spool. Wires go through the SpiRob and around the spool. The motors turn the spool and control the SpiRob's movement. My goal is to simulate its movement and use reinforcement learning to teach it to pick up different objects. A possible extension would be to add a camera and teach it to catch thrown objects.



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


