import 'package:flutter/material.dart';

class HorarioSucursal {
  const HorarioSucursal({required this.diaSemana, required this.horaApertura, required this.horaCierre});

  factory HorarioSucursal.fromJson(Map<String, dynamic> json) => HorarioSucursal(
    diaSemana: json['dia_semana'] as int,
    horaApertura: json['hora_apertura'] as String,
    horaCierre: json['hora_cierre'] as String,
  );

  // 1=lunes ... 7=domingo (DateTime.weekday usa la misma convención).
  final int diaSemana;
  final String horaApertura; // "HH:MM:SS"
  final String horaCierre;

  TimeOfDay get apertura => _aTimeOfDay(horaApertura);
  TimeOfDay get cierre => _aTimeOfDay(horaCierre);

  static TimeOfDay _aTimeOfDay(String hhmmss) {
    final partes = hhmmss.split(':');
    return TimeOfDay(hour: int.parse(partes[0]), minute: int.parse(partes[1]));
  }
}
