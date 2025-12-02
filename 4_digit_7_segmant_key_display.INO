// Letters A-G only
byte letters[7][7] = {
  //g, f, a, b, e, d, c
  {1, 1, 1, 1, 1, 0, 1}, // A
  {1, 1, 0, 0, 1, 1, 1}, // b
  {0, 1, 1, 0, 1, 1, 0}, // C
  {1, 0, 0, 1, 1, 1, 1}, // d
  {1, 1, 1, 0, 1, 1, 0}, // E
  {1, 1, 1, 0, 1, 0, 0}, // F
  {1, 1, 1, 0, 1, 1, 1}  // G
};

int segmentPins[] = {2, 3, 4, 5, 6, 7, 8};
int Dpins[] = {12, 11, 10, 9};
int dotPin = 13;

int activeDigit = 0;
int letterToDisplay = 0;
bool isSharp = false;

void setup() {
  Serial.begin(9600); // Initialize serial communication
  
  for (int i = 0; i < 7; i++) {
    pinMode(segmentPins[i], OUTPUT);
  }

  for (int i = 0; i < 4; i++) {
    pinMode(Dpins[i], OUTPUT);
  }
  
  pinMode(dotPin, OUTPUT);
}

void loop() {
  // Check if data is available from Python
  if (Serial.available() > 0) {
    String key = Serial.readStringUntil('\n');
    key.trim(); // Remove whitespace
    
    // Parse the key
    if (key.length() >= 1) {
      char note = key.charAt(0);
      
      // Convert note to letter index (0-6 for A-G)
      switch (note) {
        case 'A': letterToDisplay = 0; break;
        case 'B': letterToDisplay = 1; break;
        case 'C': letterToDisplay = 2; break;
        case 'D': letterToDisplay = 3; break;
        case 'E': letterToDisplay = 4; break;
        case 'F': letterToDisplay = 5; break;
        case 'G': letterToDisplay = 6; break;
      }
      
      // Check if it's sharp
      if (key.length() >= 2 && key.charAt(1) == '#') {
        isSharp = true;
      } else {
        isSharp = false;
      }
    }
  }
  
  // Display the current note
  digitalWrite(Dpins[0], HIGH);
  digitalWrite(Dpins[1], HIGH);
  digitalWrite(Dpins[2], HIGH);
  digitalWrite(Dpins[3], HIGH);
  
  digitalWrite(Dpins[activeDigit], LOW);

  for (int i = 0; i < 7; i++) {
    digitalWrite(segmentPins[i], letters[letterToDisplay][i]);
  }
  
  digitalWrite(dotPin, isSharp ? HIGH : LOW);
}
