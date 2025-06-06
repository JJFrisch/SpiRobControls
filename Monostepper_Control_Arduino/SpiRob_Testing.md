## SpiRob Testing  
#### After assembling the two cable SpiRob we want to test the limits of the robot and see if it can grab a pen.  


### Max Range of Motion Test in Each Direction  
To the left as shown:


The motor has a limit on how tight of a spiral it can pull the SpiRob into. With my hands I can pull the wire and the SpiRob will continue to bend into its full spiral, but 
the arduino step motor 28BYJ-48 is not capible of enough power. The amount of steps taken till the motor is unable to pull any farther is 3,620 steos.

To the right as shown:  


The right side motor is able to pull the SpiRob farther than the left hand motor. This is likley because the right hand motor is part of a newer kit. 
The amount of steps taken till the motor failed to pull is higher this time at 6633 steps.

The code for these two runs can be found in the Max_Steps file. I used remote command 1 for to pull to the left and remote command 2 to pull to the right.

About the motor: Source https://lastminuteengineers.com/28byj48-stepper-motor-arduino-tutorial/  
The maximum torque of an Arduino step motor 28BYJ-48 is approximately 34.3 mN·m.



### Expirementing with the Amount of Slack

As one motor works as the driving motor and curles the SpiRob in a direction, the other passive motor is responsible for maintaining a level of tension on its wire while simotaniously unspooling 
some of its wire. 

##### 1:0  

##### 1:.1  

##### 1:.3  

##### 1:.5  

##### 1:.7  

##### 1:1  














