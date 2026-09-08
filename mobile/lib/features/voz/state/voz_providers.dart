import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../../core/network/providers.dart';
import '../data/voz_repository.dart';

final vozRepositoryProvider = Provider<VozRepository>((ref) => VozRepository(ref.watch(dioProvider)));
