#if 1
#define LOG_OUT 1
#define FHT_N 256
#include <FHT.h>

const int CLAP_INTERVAL = 5;
const int SILENT_INTERVAL = 10;

/* Global Variables */
uint8_t avg[FHT_N / 2];
int clap_count;
int state;
int cnt;

unsigned long interval_tcount;

/* Variables for check_loud_sound */
int hurdle = 10;
int offset = 10;

/* Moving Average Funtion 
  if n = 0 : avg_0 = fht_log_out
  else :     avg_(n+1) = alpha * fht_log_out + (1 - alpha) * avg_(n)

  Apply 'fht_log_out' to 'avg_(n+1)' only if :
      lower limit < fht_log_out < upper limit
*/
bool check_loud_sound(){
    if(cnt < 3){
        cnt++;
        // simple average
        for(int i = 50; i < FHT_N/2; i++)
            avg[i] = avg[i] == 0 ? fht_log_out[i] : (fht_log_out[i] + avg[i] * (cnt - 1))/cnt; 
        return 0;
    }

    const float alpha = 0.8;
    const float lower = 0.5;
    const float upper = 1.5;

    int upper_signal = 0;

    // bar graph i = 40 at Freq = 1500 Hz
    // i = 50 at Freq = 1875 Hz 
    for(int i = 50; i < FHT_N/2; i++){
        float lower_limit = max(avg[i] - 20, lower * avg[i]);
        float upper_limit = max(avg[i] + 20, upper * avg[i]);

        // move average
        if(fht_log_out[i] > lower_limit && fht_log_out[i] < upper_limit){
            avg[i] = alpha * fht_log_out[i] + (1 - alpha) * avg[i];
        }
        // count up signals over than upper limit
        else if(fht_log_out[i] >= upper_limit){
            upper_signal++;
        }
    }

    Serial.print(upper_signal);  Serial.print(' ');
    Serial.print(hurdle);        Serial.print(' ');
    Serial.print("   state : "); Serial.print(state);
    Serial.print("   count : "); Serial.println(clap_count);
    
    bool isLoudSound = (upper_signal > hurdle); // check the signal if there are more 'upper signals' than the hurdle

    if (isLoudSound) Serial.println("CLAP !!");
    
        
      if (upper_signal < 2)        offset = 10;
      else if (upper_signal <  6)  offset = 8;
      else if (upper_signal < 10)  offset = 8;
      else if (upper_signal < 20)  offset = 8;
      else if (upper_signal < 30)  offset = 6;
      else                         offset = 6;

      hurdle = upper_signal + offset;
    

    return isLoudSound;
}

/* Change the state between 0 and 1 */
void change_state(){
    Serial.println ("=================state changed==================");
    if (!state){
        digitalWrite (LED_BUILTIN, HIGH);
        state = 1;
    }
    else{
        digitalWrite (LED_BUILTIN, LOW);
        state = 0;
    }
}

void detect_double_clap(bool isLoudSound){
    if (isLoudSound){
        if (!clap_count) // 박수가 감지된 적 없다면 박수카운트를 1 올림
            clap_count = 1;
        else if (interval_tcount > CLAP_INTERVAL) // 박수 구간 후에 들리는 소리는 박수로 인정
            clap_count++;
        // 박수 구간 내에 들리는 큰 소리는 무시함 (박수 카운트를 올리지 않음)
        
        interval_tcount = 0; // 큰 소리가 들릴 때 마다 구간 타이머 초기화
    }
    
    if (interval_tcount > SILENT_INTERVAL && clap_count){
        if (clap_count == 2){
            change_state();
            clap_count = 0;
        }
        else if (clap_count > 2)
            clap_count = 0;        
        else if (interval_tcount > 2 * SILENT_INTERVAL) // clap_count == 1 이지만, SILENT 구간의 두 배가 넘는 시간 동안 새로운 박수가 들어오지 않았다면 초기화
            clap_count = 0;
    }
}


void setup(){
    Serial.begin(115200);
    pinMode(LED_BUILTIN, OUTPUT);
    cli();

    TIMSK0 = 0;
    ADCSRA = (1 << ADEN) |
             (1 << ADSC) |
             (1 << ADATE) |
             (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
    ADMUX = 0x40;
    DIDR0 = 0x01;
}

double prev;
double a = 0.7;

void loop(){
    cli();
    for(int i = 0; i < FHT_N; i++){
        while(!(ADCSRA & (1 << ADIF)));

        uint8_t low = ADCL;//ADCL = 1111 0000
        uint8_t high = ADCH;
        ADCSRA |= (1 << ADSC);

        int ADC_IN = (high << 8 | low);

        double crnt = a * prev + (1 - a) * ADC_IN;
        prev = crnt;

        int toSigned = crnt;

        toSigned -= 512;
        toSigned <<= 6;
        fht_input[i] = toSigned;
    }

    fht_window();
    fht_reorder();
    fht_run();
    fht_mag_log();
    sei();

    bool singleClap = check_loud_sound();    
    detect_double_clap(singleClap);

    if (interval_tcount++ > 4294967293){
        interval_tcount = 0;
        clap_count = 0;
    }
}

#endif
