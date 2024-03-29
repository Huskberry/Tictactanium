# Tictactanium: Haptic Feedback Device for the Audio-Visual Impaired

Tictactanium is a wrist-worn or vest-based noninvasive haptic feedback device designed to make the world more accessible for people with audio and visual impairments. With its cost-effective approach (less than $100), this technology has the potential to open up new avenues for an otherwise marginalized audience.

## Etymology of The Name

**Tictactanium** is a portmanteau blending three distinct elements, each signifying a core aspect of the project's identity and purpose:

1. **Tic** - Derived from the 'tick' of a clock, this part symbolizes the millisecond precision, almost imperceptible moments in time that our device aims to capture and respond to. It reflects our commitment to accuracy and responsiveness in delivering tactile sensations.

2. **Tact** - Short for 'tactile', this segment represents the sense of touch. It is the essence of our project's goal: to create a bridge between the digital and physical worlds, allowing users to experience and interact with digital environments through touch.

3. **Anium** - A nod to the nomenclature often used in the periodic table, it gives a scientific and elemental flavor to the name. It implies that this technology is fundamental, almost elemental, in its approach to enhancing human-computer interaction.

Together, **Tictactanium** encompasses our vision of creating a haptic feedback device that is precise, tactile, and fundamentally innovative, offering an elemental change in how we interact with technology.

## Table of Contents

1. [Visual Application](#visual-application)
2. [Audio Application](#audio-application)
3. [Features](#features)
4. [Technical Description](#technical-description)
5. [Project Setup](#project-setup)
6. [Materials & Circuit Setup](#materials--circuit-setup)
7. [Usage](#usage)
8. [Project Status](#project-status)
9. [License](#license)
10. [Known Bugs](#known-bugs)
11. [Contributions](#contributions)

## Visual Application

Tictactanium utilizes Text-to-Speech (TTS) technology, specifically the [rhasspy/piper](https://github.com/rhasspy/piper) library, to facilitate an adaptable Braille-like experience. It converts text to audio files and processes these through a Fourier Transform algorithm. The resulting frequencies and amplitudes are then translated into PWM signals which activate linear vibrating actuators—making webpages like Wikipedia, textbooks, or blogs accessible without the need for expensive technology.

## Audio Application

For those with hearing impairments, Tictactanium enables a unique auditory experience through controlled skin vibrations on the wrist. In essence, this is a form of sensory substitution.

## Features

- **Affordable**: Cost under $100
- **Accessible**: Designed for people with audio/visual impairments
- **Adaptable**: Can be used for a variety of online resources
- **Sensory Substitution**: Converts audio/visual information into tactile feedback

## Technical Description

The core algorithm takes 16ms chunks of auditory information and applies a Discrete Fourier Transform (DFT) to them. Based on the number of available vibration motors (a minimum of 4 being feasible), the frequencies are binned. Each motor is then activated based on the amplitude of these frequencies. The frequency bands for the motors are not evenly but logarithmically distributed to better match human perception.

For example, a motor that operates between a frequency band of 300 - 900 Hz will not have a noticeable next frequency at 600 Hz but rather at 900 Hz.

## Project setup

```python3 -m venv .venv```

where ```.venv``` is the name of the folder where the virtual environment will be stored.

```source .venv/bin/activate```

```pip install -r requirements.txt```

```python3 main.py --bins 4 --filename "test.wav"```

## Materials & Circuit Setup

### Required Materials

- 4 Linear Resonant Actuators (LRAs) rated for 5V
- 4 N-channel MOSFETs (compatible with 5V gate voltage)
- 4 Diodes (for flyback protection)
- 4 10kΩ resistors (for pull-down)
- Raspberry Pi
- Breadboard
- Jumper wires
- External 3.3V power supply

### Circuit Setup

Detailed steps on setting up the circuit are provided. This includes information on the power supply, MOSFETs, LRAs, diodes, pull-down resistors, and GPIO connections.

[See Full Setup](Setup.md)

## Usage

Since we use the Raspberry Pi's GPIO pins, make sure to select appropriate pins for the setup.

## Project Status

This document will be updated as the project progresses. For now, the code should provide an adequate understanding of the project's functionality. Your suggestions for improvements are most welcome.

## License

This project is licensed under the MIT License. [See License](License.txt)

## Known Bugs

The `dynamic_ceiling()` and `running_mean` functions can cause a consistent vibratory pattern for the first 30 seconds which then dwindles. This is part of the system's noise regulation which needs further refinement.

## Contributions

Feel free to suggest improvements, both for the code and this documentation.
