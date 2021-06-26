/*
* Title : Volume and Frequency Visualizer
* Author : Jihyuk Park
* Date : 2021.06.18
* Reference : http://wiki.openmusiclabs.com/wiki/ArduinoFHT 
*/
import processing.serial.*;

final int N = 256;
final int X_OFFSET  = 40;  // x-distance to left upper corner of window
final int Y_OFFSET  = 60;  // y-distance to left upper corner of window
final int BOT_DIST  = 80;  // distance to bottom line of window
final int COL_WIDTH =  4;  // column width
final int Y_DIST    = 64;  // distance horizontal lines
final int X_DIST    =  5;  // distance verical linesqus
final int Y_MAX     = 256; // y-axis length
final int X_MAX     = (128 + 1) * X_DIST + 1; // x-axis length
final int X_WINDOW  = X_MAX + 2*X_OFFSET;      // window width
final int Y_WINDOW  = Y_MAX+BOT_DIST+Y_OFFSET; // window height
final int X_ENUM    = 10;
enum state { PLAY, PAUSE, REPLAY }

/* Global Variables */ 
color graphColor = color(25, 25, 250);
Serial port;
int volume[] = new int[N];
int frequency[] = new int[N/2];
boolean locked = false;

Queue Q = new Queue();
state STATE = state.PLAY;

/* main function */
void setup(){
  size(726, 792); //  size(X_WINDOW, Y_WINDOW);  // size of window
  noStroke();
  background(0);
  
  println(Serial.list());                        // show available COM-ports
  port = new Serial(this, "COM4", 115200);
  port.buffer(1 + 256 * 2 + 128);                // 1 start-byte + 512 data-bytes + 128 data-bytes
}

/* loop function */
void draw(){ 
  background(0);
  draw_volume_grid();
  draw_freq_grid();
  draw_volume_bar();  
  draw_freq_bar();
}

/* key Input ISR */
void keyPressed() {
  if(keyPressed) { 
    switch (key) {
      case ' ' :
        if (STATE == state.PAUSE) STATE = state.PLAY;
        else                      STATE = state.PAUSE;
        break;
      case 'R' : case 'r' :
        if (STATE == state.REPLAY) STATE = state.PAUSE;
        else                       STATE = state.REPLAY;
        break;
    }

    switch (STATE) {
      case PLAY :
        locked = false;
        break;
      case PAUSE : 
        locked = true;
        break;
      case REPLAY :
        locked = true;
        thread("replay");
        break;
    }
  }
}

/* Own thread for the serial event */
// As serialEvent() is a separated thread from the main thread,
// the I/O interrupt doesn't pause the main thread.
void serialEvent(Serial port){
  if(locked) return;

  if(port.read() == 255){ // read the start byte
    volume = combineBytes( port.readBytes(N * 2) ); // read 512 bytes and combine two bytes into one int
    frequency = int( port.readBytes(N/2) ); // read 128 bytes and form into int
    port.clear();

    Q.push(volume, frequency);
    if(Q.size() >= 20) Q.pop();
  }
}

void replay(){
  Q.pointer = Q.head;
  while(STATE == state.REPLAY){
    volume = Q.read().vol;
    frequency = Q.read().freq;
    delay(10);
    if(Q.pointer == Q.tail) Q.pointer = Q.head; 
  }
  Q.flush();
}

int[] combineBytes(byte byteArr[]){
  int intArr[] = new int[N];
  
  for(int i = 0; i < N; i++){
    int ADCH = byteArr[2*i] & 0xFF;
    int ADCL = byteArr[2*i + 1] & 0xFF;
    intArr[i] = ADCH << 8 | ADCL;
  }
  return intArr;
}

void draw_volume_grid(){
  // vertical lines
  for(int x = X_DIST, count = 0; x <= X_MAX; x += X_DIST){
    if(count % X_ENUM == 0){
      stroke(126);
      line(x + X_OFFSET, Y_OFFSET, x + X_OFFSET, Y_OFFSET + Y_MAX + 10);
      count = 0;
    }
    else{
      stroke(40);
      line(x + X_OFFSET, Y_OFFSET, x + X_OFFSET, Y_OFFSET + Y_MAX);
    }
    count++;
  }

  // horizontal lines
  for(int y = 0; y <= Y_MAX; y += Y_DIST){
    stroke(126);
    line(X_OFFSET, y + Y_OFFSET , X_MAX + X_OFFSET, y + Y_OFFSET);
    textSize(16);
    text( 4*(-y + Y_MAX), 0, y + Y_OFFSET + 6);
  }

  textSize(32);
  fill(graphColor);
  text("Volume Scale Analyser", 215, 40);
  textSize(16);
  text("amplitude", 7, 20);
  text("10bit-value", 7, 40);
  text("--> time (number i) [ms]", X_OFFSET, Y_WINDOW - Y_OFFSET/2);
  text(" time   t ( i ) = i * DURATION_TIME / FHT_N ", 350, Y_WINDOW - Y_OFFSET/2);
}

void draw_volume_bar(){
  for(int i = 0, count = 0; i < N; i++){
    noStroke();
    fill(graphColor);
    
    rect((i + 1) * X_DIST/2 + X_OFFSET - COL_WIDTH/8, height - BOT_DIST - Y_WINDOW, COL_WIDTH/4, -volume[i]/4);
    if(count % (2 * X_ENUM) == 0){
      text(2 * i, (i + 1) * X_DIST/2 + X_OFFSET - COL_WIDTH/8, height - BOT_DIST - Y_WINDOW + 25);
      count = 0;
    }
    count++;
  }
}

void draw_freq_grid(){
  for(int x = 0 + X_DIST, count = 0; x <= X_MAX; x += X_DIST){
    if(count % X_ENUM == 0){
      stroke(126);
      line(x + X_OFFSET, Y_WINDOW + Y_OFFSET, x + X_OFFSET, Y_WINDOW + Y_MAX + Y_OFFSET + 10);
      count = 0;
    }
    else{
      stroke(40);
      line(x + X_OFFSET, Y_WINDOW + Y_OFFSET, x + X_OFFSET, Y_WINDOW + Y_MAX + Y_OFFSET);
    }
    count++;
  }
  for(int y = 0; y <= Y_MAX; y += Y_DIST){
    line(X_OFFSET, y + Y_WINDOW + Y_OFFSET, X_MAX + X_OFFSET, y + Y_WINDOW +  Y_OFFSET);
    textSize(16);
    text( -y + Y_MAX, 7, y + Y_WINDOW + Y_OFFSET + 6);
  }
  textSize(32);
  fill(graphColor); 
  text("128-Channel Freq. Spectrum Analyser", 115, Y_WINDOW + 40);
  textSize(16);
  text("magnitude", 7, Y_WINDOW + 20);  
  text("(8bit-value)", 7, Y_WINDOW + 40);  
  text("--> channel (number i)", X_OFFSET, 2 * Y_WINDOW-Y_OFFSET/2);
  text(" frequency   f ( i ) = i * SAMPLE_RATE / FHT_N ", 350, 2 * Y_WINDOW-Y_OFFSET/2 );
}

void draw_freq_bar(){
  for(int i = 0, count = 0; i < 128; i++){
    fill(graphColor);
    rect(i * X_DIST + X_OFFSET + X_DIST - COL_WIDTH/2, height - BOT_DIST, COL_WIDTH, -frequency[i]);
    if (count % X_ENUM == 0){ 
      text(i, (i + 1) * X_DIST + X_OFFSET - COL_WIDTH/2, height - BOT_DIST + 25);
      count = 0;
    }
    count++;
  }
}

class Node{
  int vol[] = new int[N];
  int freq[] = new int[N/2];
  Node next;
  
  Node(){
    this.next = null;
  }
  
  Node(int data1[], int data2[]){
    if(data1.length == N && data2.length == N/2){       
      this.vol = data1.clone(); // deep copy
      this.freq = data2.clone();
    }
    else if(data1.length == N/2 && data2.length == N){       
      this.vol = data2.clone(); 
      this.freq = data1.clone();
    }
    this.next = null;
  }
  
  Node(int data1[], int data2[], Node next){
    if(data1.length == N && data2.length == N/2){       
      this.vol = data1.clone(); 
      this.freq = data2.clone();
    }
    else if(data1.length == N/2 && data2.length == N){       
      this.vol = data2.clone(); 
      this.freq = data1.clone();
    }
    this.next = next;         // shallow copy
  }
}

class Queue{
  Node head, tail, current, pointer;
  int index;  // pointer for sequential array elements in the queue
  long count;  // number of nodes
 
  Queue(){ // queue initiallization
    head = null; 
    tail = null; 
    current = null;
    pointer = null;
    index = 0;
    count = 0;
  }

  boolean isEmpty(){
    return head == null && tail == null;
  }

  long size(){
    return count;
  }

  void flush(){
    head = null; 
    tail = null; 
    current = null;
    pointer = null;
    index = 0;
    count = 0;
  }
 
  void push(int data1[], int data2[]){
    Node newNode = new Node(data1, data2);
    count++;
   
    if(this.isEmpty()){       // if queue is empty
      current = newNode;      // allocate the first node
      head = tail = current;  // let the head, tail, and current nodes to point the address of the first node
      //println("first element pushed");
    }
    else{   
      tail.next = newNode;
      tail = newNode;
      //print("push : "); println(count);
    }
  }
 
  void pop(){
    if(this.isEmpty()){           // if queue is empty
      //println("queue is empty");
      return;
    }
    else if(head.next == null){   // if queue has only one element
      head = null; 
      tail = null; 
      current = null;
      count = 0;
    }
    else{                          // if queue has more than two elements
      current = head.next;
      head.next = null;
      head = current;
      count--;
    }
    //println("pop");
  }

  Node read(){
    Node ret = new Node();
    
    if(this.isEmpty()) return ret;
    System.arraycopy(pointer.freq, 0, ret.freq, 0, N/2);

    if(index == 0){
      System.arraycopy(pointer.vol, 0, ret.vol, 0, N);
    }
    else{
      System.arraycopy(pointer.vol, index, ret.vol, 0, N - index);
      if(pointer.next == null) return ret; // "NO NEXT NODE!"
      System.arraycopy(pointer.next.vol, 0, ret.vol, N - index, index);
    }
    

    if(index++ == N - 1){
      index = 0;
      pointer = pointer.next;
    }

    return ret;
  }
}
