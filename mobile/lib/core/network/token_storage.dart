import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// Guarda el JWT en el almacenamiento seguro del dispositivo (Keychain en
/// iOS, EncryptedSharedPreferences/Keystore en Android). Nunca en
/// SharedPreferences en texto plano.
class TokenStorage {
  const TokenStorage();

  static const _claveAccessToken = 'fs_access_token';
  static const _claveRefreshToken = 'fs_refresh_token';

  static const _storage = FlutterSecureStorage();

  Future<void> guardar({required String accessToken, required String refreshToken}) async {
    await _storage.write(key: _claveAccessToken, value: accessToken);
    await _storage.write(key: _claveRefreshToken, value: refreshToken);
  }

  Future<String?> leerAccessToken() => _storage.read(key: _claveAccessToken);

  Future<String?> leerRefreshToken() => _storage.read(key: _claveRefreshToken);

  Future<void> limpiar() async {
    await _storage.delete(key: _claveAccessToken);
    await _storage.delete(key: _claveRefreshToken);
  }
}
