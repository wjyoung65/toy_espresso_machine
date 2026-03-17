// Respond to a pulse on A0 to start or stop playing one of five sounds.
// Implemented using pin change interrupt (PCINT) on A0 to avoid missing
// pulses. Sound is played using the Adafruit Waveshield, which requires
// their WaveHC library https://github.com/adafruit/WaveHC. This file was
// initially based on one of their examples.
// 
// Pulse duration meanings:
// Duration  Signal       Arduino action
// 50ms      Grind start  Play grind sound, loop until stop
// 100ms     Water ready  Play water sound, loop until stop
// 150ms     Milk start   Play milk sound, loop until stop
// 200ms     Steam start  Play steam sound, loop until stop
// 250ms     Coffee       Play coffee sound, loop until stop
// 300ms     Stop         Stop whatever is playing

#include "WaveUtil.h"
#include "WaveHC.h"

SdReader card;    // This object holds the information for the card
FatVolume vol;    // This holds the information for the partition on the card
FatReader root;   // This holds the information for the filesystem on the card
FatReader f;      // This holds the information for the file we're playing

WaveHC wave;      // This is the only wave (audio) object, since we will only play one at a time

const int pulsePin = A0;      // pulse input from micro:bit pin0

volatile unsigned long pulseStart = 0;
volatile unsigned long pulseWidth = 0;
volatile bool pulseReady = false;

// Interrupt service routine: measure how long the pulse is held high
ISR(PCINT1_vect) {
  if (digitalRead(pulsePin) == HIGH) {
    pulseStart = micros();
  } else {
    pulseWidth = micros() - pulseStart;
    pulseReady = true;
  }
}

// Return the number of bytes currently free in RAM
int getFreeRam(void)
{
  extern int  __bss_end; 
  extern int  *__brkval; 
  int free_memory; 
  if((int)__brkval == 0) {
    free_memory = ((int)&free_memory) - ((int)&__bss_end); 
  }
  else {
    free_memory = ((int)&free_memory) - ((int)__brkval); 
  }
  return free_memory; 
} 

void sdErrorCheck(void)
{
  if (!card.errorCode()) return;
  putstring("\n\rSD I/O error: ");
  Serial.print(card.errorCode(), HEX);
  putstring(", ");
  Serial.println(card.errorData(), HEX);
  while(1);
}

void setup() {
  // set up serial port
  Serial.begin(9600);
  
  putstring("Free RAM: ");       // This can help with debugging, running out of RAM is bad
  Serial.println(getFreeRam());  // if this is under 150 bytes it may spell trouble!
  
  // Set the output pins for the DAC control. This pins are defined in the library
  pinMode(2, OUTPUT);
  pinMode(3, OUTPUT);
  pinMode(4, OUTPUT);
  pinMode(5, OUTPUT);

  pinMode(pulsePin, INPUT);      // pulse input from micro:bit
  PCICR  |= (1 << PCIE1);      // enable PCINT1 group (A0-A5)
  PCMSK1 |= (1 << PCINT8);     // enable specifically A0
 
  //  if (!card.init(true)) { //play with 4 MHz spi if 8MHz isn't working for you
  if (!card.init()) {         //play with 8 MHz spi (default faster!)  
    putstring_nl("Card init. failed!");  // Something went wrong, lets print out why
    sdErrorCheck();
    while(1);                            // then 'halt' - do nothing!
  }
  
  // enable optimize read - some cards may timeout. Disable if you're having problems
  card.partialBlockRead(true);
 
  // Now we will look for a FAT partition!
  uint8_t part;
  for (part = 0; part < 5; part++) {     // we have up to 5 slots to look in
    if (vol.init(card, part)) 
      break;                             // we found one, lets bail
  }
  if (part == 5) {                       // if we ended up not finding one  :(
    putstring_nl("No valid FAT partition!");
    sdErrorCheck();      // Something went wrong, lets print out why
    while(1);                            // then 'halt' - do nothing!
  }
  
  // Lets tell the user about what we found
  putstring("Using partition ");
  Serial.print(part, DEC);
  putstring(", type is FAT");
  Serial.println(vol.fatType(),DEC);     // FAT16 or FAT32?
  
  // Try to open the root directory
  if (!root.openRoot(vol)) {
    putstring_nl("Can't open root dir!"); // Something went wrong,
    while(1);                             // then 'halt' - do nothing!
  }
  
  // Whew! We got past the tough parts.
  putstring_nl("Ready!");
}

// Play a sound file, looping until a 300ms stop signal is received
void playsound(char *name) {
  playfile(name);
  while (true) {
    if (!wave.isplaying) {
      playfile(name);  // loop
    }
    if (pulseReady) {
      noInterrupts();
      unsigned long captured = pulseWidth;
      pulseReady = false;
      interrupts();
      if (captured >= 275000 && captured <= 325000) {  // ~300ms = stop
        wave.stop();
        Serial.println("Stop");
        break;
      }
    }
  }
}

void loop() {
  if (!pulseReady) return;
  noInterrupts();
  unsigned long captured = pulseWidth;
  pulseReady = false;
  interrupts();

  if (captured < 25000 || captured > 325000) return;

  Serial.print("Pulse (us): ");
  Serial.println(captured);

  if (captured < 75000)
    playsound("grinding.wav");  // 50ms = grind start
  else if (captured < 125000)
    playsound("water.wav");         // 100ms = water ready
  else if (captured < 175000)
    playsound("milk.wav");         // 150ms = milk start
  else if (captured < 225000)
    playsound("bubbles.wav");   // 200ms = steam start
  else if (captured < 275000)
    playsound("pouring.wav");   // 250ms = coffee
  // 300ms stop signal is handled inside playsound()
}


void playfile(char *name) {
  // see if the wave object is currently doing something
  if (wave.isplaying) {// already playing something, so stop it!
    wave.stop(); // stop it
  }
  // look in the root directory and open the file
  if (!f.open(root, name)) {
    putstring("Couldn't open file "); Serial.print(name); return;
  }
  // OK read the file and turn it into a wave object
  if (!wave.create(f)) {
    putstring_nl("Not a valid WAV"); return;
  }
  
  // ok time to play! start playback
  wave.play();
}

