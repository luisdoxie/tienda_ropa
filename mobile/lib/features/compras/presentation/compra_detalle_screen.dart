import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../../core/theme/app_theme.dart';
import '../models/venta.dart';
import '../state/compras_providers.dart';

class CompraDetalleScreen extends ConsumerWidget {
  const CompraDetalleScreen({required this.ventaId, super.key});

  final int ventaId;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final asyncVenta = ref.watch(compraDetalleProvider(ventaId));

    return Scaffold(
      backgroundColor: AppColors.fondo,
      appBar: AppBar(title: const Text('Comprobante')),
      body: asyncVenta.when(
        loading: () => const Center(child: CircularProgressIndicator(color: AppColors.acento)),
        error: (e, s) => const Center(child: Text('No se pudo cargar el comprobante.')),
        data: (venta) => ListView(
          padding: const EdgeInsets.all(AppSpacing.md),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text(venta.codigo, style: const TextStyle(fontWeight: FontWeight.w700, fontSize: 16)),
                        Chip(label: Text(etiquetasEstadoVenta[venta.estado] ?? venta.estado)),
                      ],
                    ),
                    const SizedBox(height: AppSpacing.xs),
                    Text(
                      venta.esEnvioADomicilio ? 'Envío a domicilio' : 'Retiro en sucursal',
                      style: const TextStyle(color: AppColors.textoTenue, fontSize: 13),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: AppSpacing.md),

            for (final linea in venta.detalle) _TarjetaLinea(linea: linea),
            const SizedBox(height: AppSpacing.md),

            Card(
              child: Padding(
                padding: const EdgeInsets.all(AppSpacing.md),
                child: Column(
                  children: [
                    _FilaResumen('Subtotal', venta.subtotal),
                    if (venta.descuento > 0) _FilaResumen('Descuento', -venta.descuento, color: AppColors.exito),
                    if (venta.costoEnvio > 0) _FilaResumen('Envío', venta.costoEnvio),
                    const Divider(),
                    _FilaResumen('Total', venta.total, negrita: true),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FilaResumen extends StatelessWidget {
  const _FilaResumen(this.etiqueta, this.monto, {this.negrita = false, this.color});

  final String etiqueta;
  final double monto;
  final bool negrita;
  final Color? color;

  @override
  Widget build(BuildContext context) {
    final estilo = TextStyle(
      fontWeight: negrita ? FontWeight.w700 : FontWeight.w400,
      fontSize: negrita ? 16 : 14,
      color: color ?? AppColors.texto,
    );
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(etiqueta, style: estilo),
          Text('Bs ${monto.toStringAsFixed(2)}', style: estilo),
        ],
      ),
    );
  }
}

class _TarjetaLinea extends StatelessWidget {
  const _TarjetaLinea({required this.linea});

  final VentaLinea linea;

  @override
  Widget build(BuildContext context) {
    final subtitulo = [
      if (linea.tallaCodigo != null) linea.tallaCodigo!,
      if (linea.colorNombre != null) linea.colorNombre!,
      'x${linea.cantidad}',
    ].join(' · ');

    return Card(
      margin: const EdgeInsets.only(bottom: AppSpacing.sm),
      child: ListTile(
        leading: ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.base),
          child: linea.imagenPrincipal != null
              ? CachedNetworkImage(imageUrl: linea.imagenPrincipal!, width: 48, height: 48, fit: BoxFit.cover)
              : Container(
                  width: 48,
                  height: 48,
                  color: AppColors.fondoAlterno,
                  child: const Icon(Icons.checkroom, color: AppColors.textoTenue),
                ),
        ),
        title: Text(linea.productoNombre ?? 'Prenda', maxLines: 1, overflow: TextOverflow.ellipsis),
        subtitle: Text(subtitulo),
        trailing: Text('Bs ${linea.subtotal.toStringAsFixed(2)}', style: const TextStyle(fontWeight: FontWeight.w600)),
      ),
    );
  }
}
