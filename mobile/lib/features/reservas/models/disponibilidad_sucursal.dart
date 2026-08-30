class DisponibilidadSucursal {
  const DisponibilidadSucursal({required this.varianteId, required this.sucursalId, required this.cantidadDisponible});

  factory DisponibilidadSucursal.fromJson(Map<String, dynamic> json) => DisponibilidadSucursal(
    varianteId: json['variante_id'] as int,
    sucursalId: json['sucursal_id'] as int,
    cantidadDisponible: json['cantidad_disponible'] as int,
  );

  final int varianteId;
  final int sucursalId;
  final int cantidadDisponible;
}
