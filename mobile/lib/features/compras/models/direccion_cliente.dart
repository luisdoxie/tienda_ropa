class DireccionCliente {
  const DireccionCliente({
    required this.id,
    required this.clienteId,
    required this.zonaEnvioId,
    required this.alias,
    required this.direccion,
    required this.referencia,
    required this.esPrincipal,
    required this.activo,
  });

  factory DireccionCliente.fromJson(Map<String, dynamic> json) => DireccionCliente(
    id: json['id'] as int,
    clienteId: json['cliente_id'] as int,
    zonaEnvioId: json['zona_envio_id'] as int?,
    alias: json['alias'] as String?,
    direccion: json['direccion'] as String,
    referencia: json['referencia'] as String?,
    esPrincipal: json['es_principal'] as bool,
    activo: json['activo'] as bool,
  );

  final int id;
  final int clienteId;
  final int? zonaEnvioId;
  final String? alias;
  final String direccion;
  final String? referencia;
  final bool esPrincipal;
  final bool activo;

  String get etiqueta => alias?.isNotEmpty == true ? alias! : direccion;
}
