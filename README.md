# bitsheets

Extract music from GB roms and create MIDI files and sheet music.

## Description

This repository contains code to parse GB roms and extract their soundtrack. Currently, a parser for Pokémon Red&Blue is implemented that understands pitch, duration, and loops and ignores control signals (like instrument selection). Score extraction is controlled by specifying the start address and bank offset of the respective track. The addresses and offsets are available in the included config file in the `data` directory. Extracted scores can be converted to [lilypond](http://http://lilypond.org/) notation and subsequently processed into MIDI files or sheet music. Additional utility functions allow playing the extracted music and dumping the score manually to MIDI.

## Examples

The image below shows the first staff of the Route 1 Theme.

![Route 1 sheet music](/img/route_01.png)
