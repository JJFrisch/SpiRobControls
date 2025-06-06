# 3D Printer Troubleshooting Guide 

Many of these solutions were presented by this article: [7 Most Common Problems with a 3D Printer \- How to Fix \- 3D Printerly](https://3dprinterly.com/7-most-common-problems-with-a-3d-printer-how-to-fix/). Many of the solutions were arrived at by trial and error or by reading the printer manuals.

# Filament Welding in the Extruder

## What Happens:

Most of the time filament welding occurs when using flexible filaments like TPU, and sometimes even PLA. The material can soften unevenly if left in a hotend after a print is paused or fails. This might lead to the filament fusing inside the heat break or throat. Once cooled, the filament becomes stuck, making it impossible to extrude but possible to extract. 

## Symptoms:

- Manual extrusion is blocked even at the correct temperature  
- The extrusion/retraction gear still turns but will not pull down the filament, while it will retract the filament

## Fixes:

Try a cold pull by heating the hotend to the printing temperature for the filament. Then, wait 30-60 seconds to let it soften and hopefully attach to the stuck filament. Reduce the temperature to around half the printing temperature and manually pull the filament out. If it comes out with a bulbous shaped tip the blockage is likely cleared. Unfortunately if this doesn’t work the next step may have to be disassemble the hotend. Turn off and cool down the printer. Disassemble the nozzle area and use a thin needle to push out the clogged filament.

# Thermal Expansion Mismatch

## What Happens: 

PLA and TPU expand and contract at different rates, so when dual printing sometimes there can be issues. When these materials are bonded (e.g., PLA shell with TPU infill), internal stresses may cause the print to warp, separate, or crack as it cools unevenly across the print..

## Symptoms: 

- Visible delamination between layers, especially horizontally where different materials meet.   
- PLA cracking at the TPU seam  
- Corners lifting despite proper adhesion in other cases

## Solution:

Make sure to use compatible print settings for both of the materials. For PLA and TPU, use a PLA temperature on the higher side and for TPU use a temperature on the lower side so they're closer in range.   
You may also want to improve the bonding geometry. Avoid using a thin PLA shell over the more flexible TPU core because it creates a lot of shell tension as they cool. Instead use a design with mechanical joints to lock them together or print alternating stripes or lattice interlocks. (No, I don't know how to do this. I tried and failed and chose to go another route without dual material printing, but there are videos on the topic\!)

# Bed Leveling / First Layer Adhesion

Sometimes when fixing other issues I change the bed leveling and it quickly becomes an annoying problem. 

## What Happens:

Incorrect bed leveling or nozzle height can result in poor first layer adhesion. If the nozzle is too high, the filament won't stick. When it is too low it can get overly squished. These variances can lead to failed prints. If the bed is tilted towards one of the corners, builds will turn out uneven or malformed.

## Symptoms:

- Gaps between extrusion lines  
- Squished or rippled first layer   
- Warping or lifting mid-print  
- Adhesion varies across print bed

## Solution:

There is a very detailed step by step process for re-leveling the printing bed. Dr. Zheng has a manual in the drawer beneath the printer with the instructions. The instructions might look arduous (and they are) but it's worth your time in failed prints\!

# Faulty Extrusion

There are three kinds of faulty extrusion I’ve encountered in the past month: Under-Extrusion, Over-Extrusion, and Inconsistent Extrusion.

# Under-Extrusion

## What Happens: 

Under-extrusion may occur due to a clogged nozzle, stripped filament, or a weak extruder motor. This leads to filament not being pushed through consistently, affecting print quality. 

## Symptoms: 

- Gaps in walls or infill  
- Clicking or grinding sounds from the extruder  
- Bite marks or flattening on filament (hard to see sometimes)  
- Thin or uneven extrusion lines


# Over-Extrusion (Blobs and Stringing) 

## What Happens:

Too much filament is extruded during printing. This may result from incorrect steps/mm, an excessively high flow rate, or printing with too high a nozzle temperature. 

## Symptoms: 

- Blobs at the start and end of extrusion paths  
- Filament oozes or drools during travel moves  
- Overfilled walls or softened, gummy surfaces 

# Inconsistent Extrusion 

## What Happens: 

Misalignment in the filament path causes friction and inconsistent feed. Take out the filament and reinsert.

## Symptoms: 

- Irregular layer lines  
- Small gaps in walls or the prints  
- Uneven or poor surface quality  
- Extruder tension issues

