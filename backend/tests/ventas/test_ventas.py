import datetime as dt

import pytest

from tests.conftest import crear_cajero


def _proxima_fecha_con_dia_semana(dia_semana: int) -> dt.date:
    base = dt.date.today() + dt.timedelta(days=7)
    delta = (dia_semana - base.isoweekday()) % 7
    return base + dt.timedelta(days=delta)


@pytest.fixture()
def contexto(client, admin_headers, db_session):
    cat = client.post("/api/v1/categorias", json={"nombre": "Camisas Venta"}, headers=admin_headers).json()
    talla = client.post("/api/v1/tallas", json={"codigo": "M", "orden": 1}, headers=admin_headers).json()
    color = client.post("/api/v1/colores", json={"nombre": "Azul Venta"}, headers=admin_headers).json()
    producto = client.post(
        "/api/v1/productos",
        json={
            "codigo": "VTA-1",
            "nombre": "Camisa venta",
            "categoria_id": cat["id"],
            "precio_base": "100.00",
            "tallas_ids": [talla["id"]],
            "colores_ids": [color["id"]],
        },
        headers=admin_headers,
    ).json()
    variantes = client.get(f"/api/v1/productos/{producto['id']}/variantes", headers=admin_headers).json()
    variante_id = variantes[0]["id"]

    ciudad = client.post(
        "/api/v1/ciudades", json={"nombre": "Santa Cruz Venta", "departamento": "Santa Cruz"}, headers=admin_headers
    ).json()
    sucursal = client.post(
        "/api/v1/sucursales",
        json={"ciudad_id": ciudad["id"], "codigo": "SUC-VTA", "nombre": "Sucursal Venta", "direccion": "Av. 1"},
        headers=admin_headers,
    ).json()
    sucursal_id = sucursal["id"]

    # Stock inicial: 10 unidades a costo 10.
    client.post(
        "/api/v1/inventario/movimientos",
        json={
            "variante_id": variante_id,
            "sucursal_id": sucursal_id,
            "tipo_movimiento_codigo": "recepcion",
            "cantidad": 10,
            "costo_unitario": "10.00",
        },
        headers=admin_headers,
    )

    cajero_headers = crear_cajero(client, admin_headers, db_session, sucursal_id=sucursal_id)

    return {
        "producto_id": producto["id"],
        "categoria_id": cat["id"],
        "variante_id": variante_id,
        "sucursal_id": sucursal_id,
        "cajero_headers": cajero_headers,
    }


def _stock(client, headers, ctx):
    return client.get(
        f"/api/v1/inventario/stock/{ctx['variante_id']}/{ctx['sucursal_id']}", headers=headers
    ).json()


def _payload_presencial(ctx, cantidad=1):
    return {
        "sucursal_id": ctx["sucursal_id"],
        "detalle": [{"variante_id": ctx["variante_id"], "cantidad": cantidad}],
    }


def _pagar_en_caja(client, headers, venta_id, *, metodo="qr", monto_recibido=None):
    payload = {"venta_id": venta_id, "metodo_pago": metodo}
    if monto_recibido is not None:
        payload["monto_recibido"] = monto_recibido
    return client.post("/api/v1/pagos/caja", json=payload, headers=headers)


# ---- venta descuenta stock (recién al confirmarse el pago, P5.2) ----------------------


def test_venta_presencial_descuenta_stock(client, admin_headers, contexto):
    disponible_antes = _stock(client, admin_headers, contexto)["cantidad_disponible"]

    respuesta = client.post(
        "/api/v1/ventas/presencial", json=_payload_presencial(contexto, cantidad=3), headers=contexto["cajero_headers"]
    )
    assert respuesta.status_code == 201
    venta = respuesta.json()
    assert venta["canal"] == "presencial"
    assert venta["estado"] == "pendiente_pago"
    assert venta["subtotal"] == "300.00"
    assert venta["total"] == "300.00"

    # Reservado, pero todavía NO descontado físicamente: el pago no se
    # confirmó todavía.
    stock_pendiente = _stock(client, admin_headers, contexto)
    assert stock_pendiente["cantidad_disponible"] == disponible_antes - 3
    assert stock_pendiente["cantidad_fisica"] == 10

    pago = _pagar_en_caja(client, contexto["cajero_headers"], venta["id"])
    assert pago.status_code == 201

    stock_pagado = _stock(client, admin_headers, contexto)
    assert stock_pagado["cantidad_fisica"] == 7
    assert stock_pagado["cantidad_reservada"] == 0
    assert stock_pagado["cantidad_disponible"] == disponible_antes - 3

    venta_pagada = client.get(f"/api/v1/ventas/{venta['id']}/comprobante", headers=admin_headers).json()
    assert venta_pagada["estado"] == "pagada"


# ---- no se puede vender más de lo disponible ------------------------------------------


def test_no_se_puede_vender_mas_de_lo_disponible(client, contexto):
    respuesta = client.post(
        "/api/v1/ventas/presencial",
        json=_payload_presencial(contexto, cantidad=999),
        headers=contexto["cajero_headers"],
    )
    assert respuesta.status_code == 409

    # No debe haber quedado ningún movimiento aplicado: el stock sigue igual.
    stock = _stock(client, contexto["cajero_headers"], contexto)
    assert stock["cantidad_disponible"] == 10


# ---- costo congelado -------------------------------------------------------------------


def test_costo_congelado_no_cambia_con_recepcion_posterior(client, admin_headers, contexto):
    """El "Revisar" del enunciado: vender, después recibir a otro costo, y
    confirmar que el margen histórico de la primera venta no se movió.
    El costo recién se congela al confirmarse el pago (P5.2), no al crear
    la venta -- por eso el pago va antes de leer costo_unitario."""
    respuesta = client.post(
        "/api/v1/ventas/presencial", json=_payload_presencial(contexto, cantidad=2), headers=contexto["cajero_headers"]
    )
    venta_id = respuesta.json()["id"]
    _pagar_en_caja(client, contexto["cajero_headers"], venta_id)

    comprobante = client.get(f"/api/v1/ventas/{venta_id}/comprobante", headers=admin_headers).json()
    costo_congelado = comprobante["detalle"][0]["costo_unitario"]
    assert costo_congelado == "10.0000"  # costo_promedio de la recepción inicial

    # Nueva recepción a un costo bien distinto: sube el costo_promedio actual.
    client.post(
        "/api/v1/inventario/movimientos",
        json={
            "variante_id": contexto["variante_id"],
            "sucursal_id": contexto["sucursal_id"],
            "tipo_movimiento_codigo": "recepcion",
            "cantidad": 10,
            "costo_unitario": "50.00",
        },
        headers=admin_headers,
    )
    stock = _stock(client, admin_headers, contexto)
    assert stock["costo_promedio"] != "10.0000"  # el promedio actual sí cambió

    # El comprobante de la venta ya hecha no se recalcula: mismo costo de antes.
    comprobante_de_nuevo = client.get(f"/api/v1/ventas/{venta_id}/comprobante", headers=admin_headers).json()
    assert comprobante_de_nuevo["detalle"][0]["costo_unitario"] == costo_congelado


# ---- venta desde reserva libera lo reservado -------------------------------------------


def test_venta_desde_reserva_libera_stock_reservado(client, admin_headers, cliente_headers, contexto, db_session):
    # Horario de atención + reserva del cliente.
    dia = _proxima_fecha_con_dia_semana(3)
    client.post(
        f"/api/v1/sucursales/{contexto['sucursal_id']}/horarios",
        json={"dia_semana": 3, "hora_apertura": "08:00:00", "hora_cierre": "20:00:00"},
        headers=admin_headers,
    )
    reserva = client.post(
        "/api/v1/reservas",
        json={
            "sucursal_id": contexto["sucursal_id"],
            "fecha_visita": dia.isoformat(),
            "hora_visita_desde": "10:00:00",
            "hora_visita_hasta": "11:00:00",
            "detalle": [{"variante_id": contexto["variante_id"], "cantidad": 2}],
        },
        headers=cliente_headers,
    ).json()
    reserva_id = reserva["id"]

    stock_reservado = _stock(client, admin_headers, contexto)
    assert stock_reservado["cantidad_reservada"] == 2
    assert stock_reservado["cantidad_disponible"] == 8  # 10 físicas - 2 reservadas

    # Staff: preparar -> confirmar llegada -> seleccionar (compra las 2).
    client.put(f"/api/v1/reservas/{reserva_id}/preparar", headers=admin_headers)
    client.put(f"/api/v1/reservas/{reserva_id}/confirmar-llegada", headers=admin_headers)
    seleccion = client.put(
        f"/api/v1/reservas/{reserva_id}/seleccion",
        json={"lineas": [{"variante_id": contexto["variante_id"], "seleccionada": True}]},
        headers=admin_headers,
    ).json()
    assert seleccion["estado"] == "completada"

    # Sigue reservado (todavía no se vendió, solo se decidió comprarlo).
    stock_tras_seleccion = _stock(client, admin_headers, contexto)
    assert stock_tras_seleccion["cantidad_reservada"] == 2
    assert stock_tras_seleccion["cantidad_fisica"] == 10

    venta = client.post(
        "/api/v1/ventas/presencial",
        json={"sucursal_id": contexto["sucursal_id"], "reserva_id": reserva_id},
        headers=contexto["cajero_headers"],
    ).json()
    assert venta["reserva_id"] == reserva_id
    assert venta["estado"] == "pendiente_pago"
    assert len(venta["detalle"]) == 1
    assert venta["detalle"][0]["cantidad"] == 2

    # Crear la venta todavía no toca el stock: sigue reservado (por la
    # reserva original), nada descontado físicamente hasta que se pague.
    stock_tras_venta = _stock(client, admin_headers, contexto)
    assert stock_tras_venta["cantidad_reservada"] == 2
    assert stock_tras_venta["cantidad_fisica"] == 10

    # Pagar es lo que libera lo reservado Y descuenta físicamente.
    pago = _pagar_en_caja(client, contexto["cajero_headers"], venta["id"])
    assert pago.status_code == 201

    stock_final = _stock(client, admin_headers, contexto)
    assert stock_final["cantidad_reservada"] == 0
    assert stock_final["cantidad_fisica"] == 8
    assert stock_final["cantidad_disponible"] == 8


# ---- promociones ------------------------------------------------------------------------


def test_promocion_vigente_aplica_descuento(client, admin_headers, contexto):
    hoy = dt.date.today()
    r = client.post(
        "/api/v1/promociones",
        json={
            "nombre": "20% en camisas",
            "tipo": "porcentaje",
            "valor": "20",
            "fecha_inicio": (hoy - dt.timedelta(days=1)).isoformat(),
            "fecha_fin": (hoy + dt.timedelta(days=1)).isoformat(),
            "alcances": [{"categoria_id": contexto["categoria_id"]}],
        },
        headers=admin_headers,
    )
    assert r.status_code == 201

    venta = client.post(
        "/api/v1/ventas/presencial", json=_payload_presencial(contexto, cantidad=1), headers=contexto["cajero_headers"]
    ).json()
    assert venta["detalle"][0]["descuento_unitario"] == "20.00"
    assert venta["subtotal"] == "100.00"
    assert venta["descuento"] == "20.00"
    assert venta["total"] == "80.00"


# ---- devolución reingresa stock ----------------------------------------------------------


def test_devolucion_reingresa_stock(client, admin_headers, contexto):
    venta = client.post(
        "/api/v1/ventas/presencial", json=_payload_presencial(contexto, cantidad=4), headers=contexto["cajero_headers"]
    ).json()
    venta_detalle_id = venta["detalle"][0]["id"]
    _pagar_en_caja(client, contexto["cajero_headers"], venta["id"])  # sin pagar, no hay nada físico que devolver

    disponible_tras_venta = _stock(client, admin_headers, contexto)["cantidad_disponible"]

    devolucion = client.post(
        "/api/v1/devoluciones",
        json={"venta_id": venta["id"], "motivo": "Talle incorrecto", "detalle": [{"venta_detalle_id": venta_detalle_id, "cantidad": 1}]},
        headers=contexto["cajero_headers"],
    )
    assert devolucion.status_code == 201
    assert devolucion.json()["estado"] == "aprobada"

    disponible_tras_devolucion = _stock(client, admin_headers, contexto)["cantidad_disponible"]
    assert disponible_tras_devolucion == disponible_tras_venta + 1


def test_devolucion_no_puede_superar_lo_vendido(client, contexto):
    venta = client.post(
        "/api/v1/ventas/presencial", json=_payload_presencial(contexto, cantidad=2), headers=contexto["cajero_headers"]
    ).json()
    venta_detalle_id = venta["detalle"][0]["id"]
    _pagar_en_caja(client, contexto["cajero_headers"], venta["id"])

    respuesta = client.post(
        "/api/v1/devoluciones",
        json={"venta_id": venta["id"], "detalle": [{"venta_detalle_id": venta_detalle_id, "cantidad": 3}]},
        headers=contexto["cajero_headers"],
    )
    assert respuesta.status_code == 400


# ---- carrito y venta digital --------------------------------------------------------------


def test_venta_digital_desde_carrito_lo_vacia(client, admin_headers, cliente_headers, contexto):
    client.post(
        "/api/v1/carrito", json={"variante_id": contexto["variante_id"], "cantidad": 2}, headers=cliente_headers
    )
    carrito = client.get("/api/v1/carrito", headers=cliente_headers).json()
    assert len(carrito["detalle"]) == 1

    venta = client.post(
        "/api/v1/ventas/digital",
        json={"sucursal_id": contexto["sucursal_id"], "costo_envio": "15.00"},
        headers=cliente_headers,
    )
    assert venta.status_code == 201
    cuerpo = venta.json()
    assert cuerpo["canal"] == "digital"
    assert cuerpo["costo_envio"] == "15.00"
    assert cuerpo["total"] == "215.00"  # 200 subtotal + 15 envío

    carrito_despues = client.get("/api/v1/carrito", headers=cliente_headers).json()
    assert carrito_despues["detalle"] == []
