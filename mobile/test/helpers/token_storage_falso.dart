import 'package:mobile/core/network/token_storage.dart';

/// Doble en memoria de TokenStorage para tests: el real usa
/// flutter_secure_storage, que necesita un canal de plataforma que no
/// existe en `flutter test`.
class TokenStorageFalso extends TokenStorage {
  String? accessToken;
  String? refreshToken;
  int vecesLimpiado = 0;

  @override
  Future<void> guardar({required String accessToken, required String refreshToken}) async {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
  }

  @override
  Future<String?> leerAccessToken() async => accessToken;

  @override
  Future<String?> leerRefreshToken() async => refreshToken;

  @override
  Future<void> limpiar() async {
    accessToken = null;
    refreshToken = null;
    vecesLimpiado++;
  }
}
