#if 1
/*
 * https://m.blog.naver.com/PostView.naver?isHttpsRedirect=true&blogId=dododokim&logNo=221463847309
 * 
*/
#define LOG_OUT 1 // use the log output function
#define FHT_N 256 // set to 256 point fht

#include <FHT.h> // include the library


// 1회에 0.0275초 정도 걸림. 10번에 0.275초 / 20번에 0.55초 / 30번에 0.75 / 40번에 1.1 / 50번에 1.375


//======== Available Constants ========//

const int WA_case = 5;                                            // 가중평균 구간 개수
const int WA_interval[WA_case + 1] = {0, 10, 45, 75, 105, 128};   // 분할 기준 i 값
const float WA_weight[WA_case] = {0.5, 1, 4, 1, 4};               // 구간별 가중치

const int interval_avg = 15;        // 이전 자료를 평균내는 범위
const int interval_clap = 5;        // 박수 직후 다른 소음 무시하는 시간이자, 두번째 박수까지의 최소 시간.
const int interval_silent = 20;     // 박수로 인정받기 위해 조용해야 하는 시간
const int interval_offset = 5;      // 박수소리 평균을 구하는 구간.
const float offset_rate = 0.7;      // 박수소리 평균과 현재 소음의 차이에 곱해주어 offset 강도 조절.


//======== Global Variables Setting ========//
int offset_flexible = 0;      // 넘겨야 하는 diff 기준치 , 배경 소음과 박수 소리에 따라 달라짐. 초기 값은 setup에서 지정.
int offset_mean = 0;          // 박수 소리 주파수 평균 값. 초기 값은 setup에서 지정.
int offset_tmp[interval_offset] = {0, };
int offset_pointer = 0;

int avg_new = 40;
int avg_prev = 40;
int avg_buf = 0;
int avg_tmp[interval_avg] = {0, };
int avg_pointer = 0;

int diff = 0;

int clap_count = 0;
unsigned long interval_tcount = 0;
unsigned long sum = 0;

int state_LED = 0;


//======== Testing Variables ========// 개발중에 써보는 영역 -> 가중평균 변수






//======== Setup ========//
void setup() {
  Serial.begin(115200); // use the serial port
  TIMSK0 = 0; // turn off timer0 for lower jitter
  
  ADCSRA = (1 << ADEN) | 
           (1 << ADSC) |
           (1 << ADATE) |
           (1 << ADPS2) | (1 << ADPS1) | (1 << ADPS0);
  ADMUX = 0x40; // use adc0
  DIDR0 = 0x01; // turn off the digital input for adc0 

  pinMode(LED_BUILTIN, OUTPUT);
  
  for (int i; i < interval_avg; i++) avg_tmp[i] = 50;
  for (int i; i < interval_offset; i++) offset_tmp[i] = 90;
  offset_mean = offset_tmp[1];
  offset_flexible = (offset_tmp[1] - avg_tmp[1]) * offset_rate;
}


//======== Offset Flexible 구하는 부분 ========//
int get_offset_mean(int avg_buf){
  if(offset_pointer == interval_offset) offset_pointer = 0;
  offset_tmp[offset_pointer++] = avg_buf;

  unsigned long sum_array = 0;
  for(int i = 0; i < interval_offset; i++) sum_array += offset_tmp[i];

  return sum_array / interval_offset;
}
  
//======== 이전 소리와 현재 소리의 크기 차이를 구하는 부분 ========//
/*  현재 주파수 크기 평균(avg_new)과 이전 주파수 크 평균(avg_prev) 비교
 *   if 현재 소리가 이전 소리보다 더 크다면, 그 차이를 diff에 할당한다.
 *   else diff = 0 으로 둔다.
 */
void Volume_difference_detect(){
  if (avg_new > avg_prev)
    diff = avg_new - avg_prev;
  else
    diff = 0;
}

//======== 박수 감지 및 카운팅 ========//
/* if diff 가 일정 값 이상인 경우, 
 *    if 앞서 조용했다면, !cmd = 1
 *       그렇다면 박수 횟수 clap_count 를 1로 올리고, cmd도 1로 바꿔준다.(박수 셀 준비) 
 *    else if 셀 준비가 되어있고, and 박수 간의 최소 간격 시간(interval_clap)이 지났다면,
 *      박수를 세고, 박수 간격 카운터(interval_tcount)를 초기화한다.
 *    else 박수 간의 최소 간격 시간(interval_clap) 전에 시끄러운경우
 *      무시하고, 박수 간격 카운터(interval_tcount)를 초기화 해 다시 기다린다.
 */
void Clap_detect(){
  if (diff > offset_flexible) {
    Serial.println("clap!!!!!!!!!!!!!!!!!!!!!!!");
    if (!clap_count){
      clap_count = 1;
      interval_tcount = 0;
    }
    else if (interval_tcount > interval_clap){
      interval_tcount = 0;
      clap_count++;
      if (clap_count == 2) avg_buf = avg_new;
    }
    else if (interval_tcount <= interval_clap)
      interval_tcount = 0;
  }
}

// 편의를 위한 cmd, clap_count 초기화 함수
void Clear(){
  clap_count = 0;
}

//======== 박수 두번 판단 ========//
/* if 인정 대기시간 (interval_silent)동안 조용했고 and 박수 감지 모드라면, 
 *    if 박수 카운트(Clap_count)가 두번인 경우,
 *       박수 두번으로 인정하고 LED를 켜거나 끈다.
 *       이후 초기화한다.
 *    else 그냥 소음으로 판정, 초기화한다.
 */
void Doubleclap_detect(){
  if (interval_tcount > interval_silent && clap_count){
    if (clap_count == 2) {
      Serial.println ("=================state changed==================");
      offset_mean = get_offset_mean(avg_buf);
      // offset_flexible = (offset_mean - avg_prev) * offset_rate;  루프 속으로 옮김.

      if (!state_LED){
        digitalWrite (LED_BUILTIN, HIGH);
        state_LED = 1;
      }
      else{
        digitalWrite (LED_BUILTIN, LOW);
        state_LED = 0;
      }
      Clear();
    }
    else {
      Clear();
    }
  }
}


//======== 근 0.275*interval_avg s 동안의 소리 크기 평균을 구함 ========//
/* avg_tmp 배열에 돌아가며 가장 최신값을 대입하는 방식으로,
 * n평균 구하고 n초 쉬는 것이 아니라, 실시간으로 근 n초의 평균을 구함
 */

void Average(){
  
  unsigned long sum_tmp = 0;

  if (avg_pointer == interval_avg) avg_pointer = 0;
  avg_tmp[avg_pointer++] = avg_new;

  for (int i = 0; i < interval_avg; i++){
    sum_tmp += avg_tmp[i];
  }
  avg_prev = sum_tmp / interval_avg;
}


//======== FFT Magnitude 가중평균 ========//
void FFT_Weighted_Average(){
  unsigned long sum_tmp = 0;
  int WA_sum = 0;
  for (int k = 0; k < WA_case; k++){
      for (int i = WA_interval[k]; i < WA_interval[k+1]; i++)
          sum_tmp += fht_log_out[i] * WA_weight[k];
          
      WA_sum += (WA_interval[k+1] - WA_interval[k]) * WA_weight[k];
   }    
  avg_new = sum_tmp/WA_sum;

}


void loop() {
    cli();  // UDRE interrupt slows this way down on arduino1.0   
    // 인터럽트를 끄면 micros() 가 제대로 작동하지 않음
    // micros()는 타이머 인터럽트로 카운트업을 하기 때문.
    // ADSRA의 Prescaler factor가 Sampling Rate fs에 영향을 미친다.
    // ADPS = 32  -->  fs = 38400      Ts = 2.6 microS  Ttot = 6666.6 microS
    // ADPS = 64  -->  fs = 2 * 38400  Ts = 1.3 microS  Ttot = 3333.3 microS
    // ADPS = 128 -->  fs = 4 * 38400  Ts = 0.6 microS  Ttot = 1666.6 microS
    
    for (int i = 0 ; i < FHT_N ; i++) { // save 256 samples     
      while(!(ADCSRA & 0x10)); // wait for adc to be ready
      uint8_t low = ADCL;
      uint8_t high = ADCH;
      
      int k = (high << 8 | low); // 0 <= ADC < 1024
      k -= 512; // form into a signed int
      k <<= 6; // form into a 16b signed int by multipling 2^6
      fht_input[i] = k; // put real data into bins
      
      ADCSRA |= (1 << ADSC); // restart adc
    }

    fht_window(); // window the data for better frequency response
    fht_reorder(); // reorder the data before doing the fht
    fht_run(); // process the data in the fht
    fht_mag_log(); // take the output of the fht
    sei();
 
    FFT_Weighted_Average();
    Volume_difference_detect();
    Clap_detect();
    Doubleclap_detect();
    Average();
    
    interval_tcount++;

    if (interval_tcount > 3000){
      interval_tcount = 0;
      Clear();
    }
    
    offset_flexible = (offset_mean - avg_prev) * offset_rate;       // offset_flexible은 avg_prev 에 따라 실시간으로 변해야 하므로, 루프를 돌때마다 실행하도록 수정.
    if (offset_flexible < 20) offset_flexible = 20;                 // offset_mean과 avg_prev의 차이가 너무 작아져서 offset_flexible의 값이 너무 작은 경우, 계속 박수로 인식하는 경우가 생김. 따라서 최솟값으로 20을 정해주었음. 
  Serial.print(offset_mean);
  Serial.print(' ');     
  Serial.print(offset_flexible);
  Serial.print(' ');
  Serial.print(avg_buf);
  Serial.print(' ');
  Serial.print(offset_pointer);
  Serial.print(' ');
  Serial.print(clap_count);
  Serial.print(' ');
  Serial.print(avg_new);
  Serial.print(' ');
  Serial.print(avg_prev);
  Serial.println(' ');
  

  // Serial.println(avg);
}   
#endif
