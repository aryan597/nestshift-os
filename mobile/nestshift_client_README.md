# NestShift Client Library

This library provides API and MQTT connectivity for Flutter apps to communicate with the NestShift OS backend.

## Installation

Add to your `pubspec.yaml`:

```yaml
dependencies:
  http: ^1.0.0
  mqtt_client: ^10.0.0
```

Then import the library:

```dart
import 'package:nestshift_client/index.dart';
```

## Usage

### API Client

```dart
final client = NestShiftClient(baseUrl: 'http://localhost:8000');

try {
  final health = await client.getHealth();
  print('API Status: ${health['status']}');

  final devices = await client.getDevices();
  for (var device in devices) {
    print('Device: ${device['name']}');
  }

  await client.controlDevice('light1', 'turn_on');
} on NestShiftApiException catch (e) {
  print('API Error: $e');
}
```

### MQTT Client

```dart
final mqttService = NestShiftMqttService();

await mqttService.connect('localhost', port: 1883);

// Listen to device state changes
mqttService.deviceStates.listen((deviceState) {
  print('Device ${deviceState.id} is ${deviceState.state}');
});

// Listen to sensor readings
mqttService.sensorReadings.listen((reading) {
  print('Sensor ${reading.sensorId}: ${reading.value}');
});

// Listen to tariff updates
mqttService.tariffUpdates.listen((tariff) {
  print('Current price: ${tariff.pricePerKwh}p/kWh');
});

// Clean up
await mqttService.disconnect();
```

## Configuration

- **Development**: Use `http://localhost:8000` for API and `localhost:1883` for MQTT
- **Production**: Use `http://nestshift.local:8000` for API and `nestshift.local:1883` for MQTT

## Error Handling

All API methods throw `NestShiftApiException` on HTTP errors. MQTT connection errors are propagated through the connect method.