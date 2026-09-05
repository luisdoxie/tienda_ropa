/// POST /envios/cotizar: no persiste nada, solo calcula cuánto costaría el
/// envío del carrito actual a una dirección.
class CotizacionEnvio {
  const CotizacionEnvio({
    required this.zonaEnvioId,
    required this.zonaNombre,
    required this.pesoKg,
    required this.tarifaBase,
    required this.recargoPeso,
    required this.costo,
  });

  factory CotizacionEnvio.fromJson(Map<String, dynamic> json) => CotizacionEnvio(
    zonaEnvioId: json['zona_envio_id'] as int,
    zonaNombre: json['zona_nombre'] as String,
    pesoKg: double.parse(json['peso_kg'].toString()),
    tarifaBase: double.parse(json['tarifa_base'].toString()),
    recargoPeso: double.parse(json['recargo_peso'].toString()),
    costo: double.parse(json['costo'].toString()),
  );

  final int zonaEnvioId;
  final String zonaNombre;
  final double pesoKg;
  final double tarifaBase;
  final double recargoPeso;
  final double costo;
}
