class Envio {
  const Envio({
    required this.id,
    required this.ventaId,
    required this.direccionId,
    required this.zonaEnvioId,
    required this.costo,
    required this.estado,
  });

  factory Envio.fromJson(Map<String, dynamic> json) => Envio(
    id: json['id'] as int,
    ventaId: json['venta_id'] as int,
    direccionId: json['direccion_id'] as int,
    zonaEnvioId: json['zona_envio_id'] as int,
    costo: double.parse(json['costo'].toString()),
    estado: json['estado'] as String,
  );

  final int id;
  final int ventaId;
  final int direccionId;
  final int zonaEnvioId;
  final double costo;
  final String estado;
}
