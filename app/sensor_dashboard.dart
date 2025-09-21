// lib/widgets/sensor_dashboard.dart
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class SensorDashboard extends StatefulWidget {
  @override
  _SensorDashboardState createState() => _SensorDashboardState();
}

class _SensorDashboardState extends State<SensorDashboard> {
  Map<String, dynamic> _sensorData = {};

  Future<void> _fetchData() async {
    final response = await http.get(Uri.parse('https://api.gard.za/sensor-data'));
    setState(() {
      _sensorData = json.decode(response.body);
    });
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        GaugeChart(
          value: _sensorData['soil_moisture']?.toDouble() ?? 0,
          maxValue: 100,
          title: 'Soil Moisture',
        ),
        // Add more sensor visualizations
      ],
    );
  }
}