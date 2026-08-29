import '../models/usuario.dart';

enum EstadoSesion { inicial, cargando, autenticado, noAutenticado }

class AuthState {
  const AuthState({required this.estado, this.usuario, this.error});

  const AuthState.inicial() : this(estado: EstadoSesion.inicial);

  final EstadoSesion estado;
  final Usuario? usuario;
  final String? error;

  bool get estaAutenticado => estado == EstadoSesion.autenticado;

  bool tienePermiso(String codigo) => usuario?.permisos.contains(codigo) ?? false;

  AuthState copyWith({EstadoSesion? estado, Usuario? usuario, String? error}) {
    return AuthState(
      estado: estado ?? this.estado,
      usuario: usuario ?? this.usuario,
      error: error,
    );
  }
}
