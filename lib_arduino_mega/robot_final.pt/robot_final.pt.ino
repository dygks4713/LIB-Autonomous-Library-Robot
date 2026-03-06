#include <Servo.h>

Servo s[6];
int pins[6] = {4, 7, 9, 10, 13, 15}; 
int startPos[6] = {90, 90, 90, 60, 90, 90}; 
int neutralPos[6] = {90, 120, 180, 55, 100, 90};
int currentPos[6];

int M3_PWM = 8;   int M3_DIR1 = 36; int M3_DIR2 = 37; // 왼쪽 모터
int M4_PWM = 5;   int M4_DIR1 = A4; int M4_DIR2 = A5; // 오른쪽 모터

char lastDriveCmd = 'x'; 

void setup() {
  Serial.begin(115200);
  pinMode(M3_PWM, OUTPUT); pinMode(M3_DIR1, OUTPUT); pinMode(M3_DIR2, OUTPUT);
  pinMode(M4_PWM, OUTPUT); pinMode(M4_DIR1, OUTPUT); pinMode(M4_DIR2, OUTPUT);
  stopMotors();

  for(int i = 0; i < 6; i++) { 
    s[i].attach(pins[i]); 
    currentPos[i] = startPos[i]; 
    s[i].write(currentPos[i]); 
  }
  delay(1000); 
  
  // 초저속 초기화 루프
  bool allReached = false;
  while(!allReached) {
    allReached = true;
    for(int i = 0; i < 6; i++) {
      if (currentPos[i] < neutralPos[i]) { currentPos[i]++; s[i].write(currentPos[i]); allReached = false; }
      else if (currentPos[i] > neutralPos[i]) { currentPos[i]--; s[i].write(currentPos[i]); allReached = false; }
    }
    delay(50);
  }
}

void loop() {
  if (Serial.available() > 0) {
    String input = Serial.readStringUntil('\n');
    input.trim();
    
    // 1. 통합 주행 명령 처리 (v:L_PWM:R_PWM)
    if (input.startsWith("v:")) {
      int firstColon = input.indexOf(':');
      int secondColon = input.indexOf(':', firstColon + 1);
      
      if (secondColon != -1) {
        int lPWM = input.substring(firstColon + 1, secondColon).toInt();
        int rPWM = input.substring(secondColon + 1).toInt();
        driveIndependent(lPWM, rPWM);
      }
    } 
    // 2. 팔 제어 명령 처리 (ID:Angle)
    else if (input.indexOf(':') != -1) {
      int delimiter = input.indexOf(':');
      int id = input.substring(0, delimiter).toInt();
      int target = input.substring(delimiter + 1).toInt();
      if (id >= 1 && id <= 6) moveSmooth(id - 1, constrain(target, 0, 180));
    }
    // 3. 정지 명령
    else if (input == "x") {
      stopMotors();
    }
  }
}

// 좌우 바퀴 독립 제어 함수 (양수: 전진, 음수: 후진)
void driveIndependent(int lp, int rp) {
  // 왼쪽 모터 제어
  if (lp >= 0) { digitalWrite(M3_DIR1, HIGH); digitalWrite(M3_DIR2, LOW); }
  else { digitalWrite(M3_DIR1, LOW); digitalWrite(M3_DIR2, HIGH); }
  analogWrite(M3_PWM, abs(lp));

  // 오른쪽 모터 제어
  if (rp >= 0) { digitalWrite(M4_DIR1, HIGH); digitalWrite(M4_DIR2, LOW); }
  else { digitalWrite(M4_DIR1, LOW); digitalWrite(M4_DIR2, HIGH); }
  analogWrite(M4_PWM, abs(rp));
}

void stopMotors() {
  analogWrite(M3_PWM, 0); analogWrite(M4_PWM, 0);
  digitalWrite(M3_DIR1, LOW); digitalWrite(M3_DIR2, LOW);
  digitalWrite(M4_DIR1, LOW); digitalWrite(M4_DIR2, LOW);
}

void moveSmooth(int idx, int target) {
  int start = currentPos[idx];
  if (start < target) for (int p=start; p<=target; p++) { s[idx].write(p); delay(15); }
  else for (int p=start; p>=target; p--) { s[idx].write(p); delay(15); }
  currentPos[idx] = target;
}