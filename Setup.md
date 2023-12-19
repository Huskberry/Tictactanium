# Circuit Setup:
* Power Supply: Connect an external 3.3V power supply to the breadboard. Make sure to connect the ground of the Raspberry Pi to the ground of the external power supply.
* MOSFETs: Place the 8 N-channel MOSFETs on the breadboard. Connect the source pin of each MOSFET to the ground rail on the breadboard.
* LRAs: Connect one terminal of each LRA to the drain pin of a corresponding MOSFET. Connect the other terminal to the positive rail of the 5V power supply on the breadboard.
* Diodes: Connect a diode in parallel with each LRA. The cathode (the side with the stripe) should be connected to the positive terminal of the LRA, and the anode should be connected to the drain of the corresponding MOSFET. This protects the MOSFET from back EMF.
* Pull-down Resistors: Connect a 10kΩ resistor between the gate of each MOSFET and the ground. This ensures that the MOSFET remains off when the GPIO pin is not actively driving it.
* GPIO to Gate: Connect a GPIO pin from the Raspberry Pi to the gate of each MOSFET. This will be used to control the MOSFET via PWM.

Since we are using GPIO as the bins, we should choose appropriate pins on the Raspberry Pi. See `motor_pins = [5,6,13,19]  # Replace with your GPIO pin numbers`. 
