class ZonaEnvio {
  const ZonaEnvio({
    required this.id,
    required this.ciudadId,
    required this.nombre,
    required this.anilloDesde,
    required this.anilloHasta,
    required this.tarifaBase,
  });

  factory ZonaEnvio.fromJson(Map<String, dynamic> json) => ZonaEnvio(
    id: json['id'] as int,
    ciudadId: json['ciudad_id'] as int,
    nombre: json['nombre'] as String,
    anilloDesde: json['anillo_desde'] as int?,
    anilloHasta: json['anillo_hasta'] as int?,
    tarifaBase: double.parse(json['tarifa_base'].toString()),
  );

  final int id;
  final int ciudadId;
  final String nombre;
  final int? anilloDesde;
  final int? anilloHasta;
  final double tarifaBase;
}
