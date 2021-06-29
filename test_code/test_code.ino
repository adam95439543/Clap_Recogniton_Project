/*
 * https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=dododokim&logNo=221463847309
 * 
*/
#define LOG_OUT 1 // use the log output function
#define FHT_N 256 // set to 256 point fht

#include <FHT.h> // include the library
uint8_t amplitude[FHT_N * 2];
int state = 0;

void setup() {
  Serial.begin(115200); // use the serial port
  TIMSK0 = 0; // turn off timer0 for lower jitter
  //ADCSRA = 0xe5; // set the adc to free running mode
  ADCSRA = (1 << ADEN) | 
           (1 << ADSC) |
           (1 << ADATE) |
           (1 << ADPS2) | (1 << ADPS1 ) | (1 << ADPS0);
  ADMUX = 0x40; // use adc0
  DIDR0 = 0x01; // turn off the digital input for adc0 

  pinMode(LED_BUILTIN, OUTPUT);
}


void loop() {
    unsigned int peakToPeak = 0;   // peak-to-peak level
    unsigned int signalMax = 0;
    unsigned int signalMin = 1024;
  
    cli();  // UDRE interrupt slows this way down on arduino1.0   
    // 인터럽트를 끄면 micros() 가 제대로 작동하지 않음
    // micros()는 타이머 인터럽트로 카운트업을 하기 때문.
    // ADSRA의 Prescaler factor가 Sampling Rate fs에 영향을 미친다.
    // ADPS = 32  -->  fs = 38400      Ts = 2.6 microS  Ttot = 6666.6 microS
    // ADPS = 64  -->  fs = 2 * 38400  Ts = 1.3 microS  Ttot = 3333.3 microS
    // ADPS = 128 -->  fs = 4 * 38400  Ts = 0.6 microS  Ttot = 1666.6 microS
    
    for (int i = 0 ; i < FHT_N ; i++) { // save 256 samples     
      while(!(ADCSRA & 0x10)); // wait for adc to be ready
      
      // we have to read ADCL first; doing so locks both ADCL
      // and ADCH until ADCH is read.  reading ADCL second would
      // cause the results of each conversion to be discarded,
      // as ADCL and ADCH would be locked when it completed.
      uint8_t low = ADCL;
      uint8_t high = ADCH;
      
      amplitude[2*i] = high;
      amplitude[2*i + 1] = low;
      
      unsigned int ADC_IN = (high << 8 | low) & 0x3FF;
      int k = (high << 8 | low); // 0 <= ADC < 1024
      k -= 512; // form into a signed int
      k <<= 6; // form into a 16b signed int by multipling 2^6
      fht_input[i] = k; // put real data into bins
      
      ADCSRA |= (1 << ADSC); // restart adc

      if(ADC_IN < 1024)
        if(ADC_IN > signalMax) signalMax = ADC_IN;
        else if(ADC_IN < signalMin) signalMin = ADC_IN;
      
    }    

    peakToPeak = signalMax - signalMin;
    
    if(peakToPeak > 120){
      if(state == 0){
        digitalWrite(LED_BUILTIN, HIGH);
        state = 1;
      }
      else{
        digitalWrite(LED_BUILTIN, LOW);
        state = 0;
      }
    }

    fht_window(); // window the data for better frequency response
    fht_reorder(); // reorder the data before doing the fht
    fht_run(); // process the data in the fht
    fht_mag_log(); // take the output of the fht
    sei();
    
    Serial.write(255); // send a start byte for Volume Graph
    Serial.write(amplitude, FHT_N * 2);
    Serial.write(fht_log_out, FHT_N/2); // send out the data

    
}
