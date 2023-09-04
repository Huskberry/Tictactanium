# Vaibuu
I've been working on a noninvasive haptic feedback device meant to be worn on the wrist. A simple technology for less < $100 (Raspberry Pi is the most expensive component here). It's most useful application is allow people with audio/visual impairments interact with the world.

This is a technology that can usher a new type of audience to the world.

VISUAL: The technology here is use Text to Speech (TTS) to allow a sort of dynamic and adaptable braille system. Imagine a person with blindness accessing @wikipedia, text books or a blog without expensive technology. I'm using [rhasspy/piper](https://github.com/rhasspy/piper) on to generate TTS. I take the text, convert it to a .WAV file (audio) then run the audio through a Fourier Transform algorithm to generate different frequencies and amplitudes, then pass that information to a PWM signal and to linear vibrating actuators (the tiny vibrators in your smartphone)

AUDIO: the technology here is to enable people with hearing impairments to have an auditory experience through controlled vibrations on the skin (wrist).

This is sensory substitution.

## Description
Simply put, this code takes auditory information from the environment, passes 16ms chunks of it through a discrete Fourier Transform, bins the frequencies (depending on the number of vibration motors available; 4 being feasibly minimum) and vibrates those motors depending on the frequency's amplitude. The motors are linear resonant actuators (LRA) similar to those in smartphones..

A motor will always vibrate within the same frequency band. For example, motor 1 will always vibrate at a frequency band between 300 - 900 Hz of sound. The frequency bands are actually not evenly distributed; rather logarithmically distributed. For human hearing, the next percievable and distinguishable frequency from 300 Hz is not really 600 Hz but 900 Hz.

# Connection requirements and schematic
## Materials Needed:
4 Linear Resonant Actuators (LRAs) rated for 5V
4 N-channel MOSFETs (compatible with 5V gate voltage)
4 Diodes (for flyback protection)
4 10kΩ resistors (for pull-down)
Raspberry Pi
Breadboard
Jumper wires
External 5V power supply
## Circuit Setup:
* Power Supply: Connect an external 5V power supply to the breadboard. Make sure to connect the ground of the Raspberry Pi to the ground of the external power supply.
* MOSFETs: Place the 8 N-channel MOSFETs on the breadboard. Connect the source pin of each MOSFET to the ground rail on the breadboard.
* LRAs: Connect one terminal of each LRA to the drain pin of a corresponding MOSFET. Connect the other terminal to the positive rail of the 5V power supply on the breadboard.
* Diodes: Connect a diode in parallel with each LRA. The cathode (the side with the stripe) should be connected to the positive terminal of the LRA, and the anode should be connected to the drain of the corresponding MOSFET. This protects the MOSFET from back EMF.
* Pull-down Resistors: Connect a 10kΩ resistor between the gate of each MOSFET and the ground. This ensures that the MOSFET remains off when the GPIO pin is not actively driving it.
* GPIO to Gate: Connect a GPIO pin from the Raspberry Pi to the gate of each MOSFET. This will be used to control the MOSFET via PWM.

Since we are using GPIO as the bins, we should choose appropriate pins on the Raspberry Pi. 

## PS
I will be adding additional information to this project as time goes by. I hope by reading the code, for now, should provide an idea of what it does. Feel free to suggest improvements (To the documentation as well)

## Known bugs
As the code is running, I've noticed that the first 30 seconds or so have a somewhat consistent vibratory pattern on my wrist. After that, it dwindles. The ```dynamic_ceiling()``` and ```running_mean``` functions are the culprits here. Those two functions are means to regulate the noise from the environment. eg, a hum from a coffee machine in a restraurant may produce a high vibration once detected, then falls to a constant hum (which is undesirable); but as this is noise, the  algorithm should be able to detect that it doesn't have enough variation in frequency to classify as meaninfful sound. So that hum gets drowned out at the expense of the meaningful frequencies being a bit less 'feelable'.
