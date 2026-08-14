from datetime import datetime
import db
from rag.chat import answer_query


def _parse_fecha(texto: str):
    texto = texto.strip()
    for formato in ("%d/%m/%y", "%d/%m/%Y"):
        try:
            return datetime.strptime(texto, formato)
        except ValueError:
            continue
    return None


def _validar_fecha_pago(session: dict, user_input: str, campo_sesion: str):

    fecha = _parse_fecha(user_input)
    if fecha is None:
        return (
            "❌ No reconozco esa fecha. Escríbela en formato dd/mm/aa "
            "(ej. 10/08/26): ⬇️",
            False,
        )
    if fecha.date() > datetime.now().date():
        return (
            "❌ La fecha no puede ser futura. Indica la fecha real en la "
            "que realizaste el pago (dd/mm/aa): ⬇️",
            False,
        )
    session[campo_sesion] = fecha.strftime("%d/%m/%y")
    return f"📅 Fecha registrada: {session[campo_sesion]}", True


def not_implemented(session: dict) -> str:
    return "🚧 Funcionalidad no disponible por el momento."


_MENSAJE_ESCALAMIENTO = (
    "🧑‍💻 Te voy a conectar con un agente de soporte técnico en vivo.\n"
    "Nuestro horario de atención es de lunes a domingo, de 08:00 a.m. a "
    "10:00 p.m. Si es fuera de ese horario, tu caso quedará registrado "
    "para ser atendido apenas se reanude el horario de atención."
)

_COMANDOS_SALIDA = {"0", "menu", "menú", "salir"}
_COMANDOS_AGENTE = {"agente", "humano", "persona", "asesor"}


def soporte_tecnico_rag(session: dict, user_input: str):
    texto = user_input.strip().lower()

    if texto in _COMANDOS_SALIDA:
        session["soporte_intentos_fallidos"] = 0
        return "Volviendo al menú de soporte. 👋", True

    if texto in _COMANDOS_AGENTE:
        db.insert_escalamiento(consulta=user_input, motivo="solicitud_usuario")
        session["soporte_intentos_fallidos"] = 0
        return _MENSAJE_ESCALAMIENTO, True

    resultado = answer_query(user_input)

    if resultado.resuelto:
        session["soporte_intentos_fallidos"] = 0
        return (
            resultado.respuesta
            + "\n\n¿Te ayudó esto? Puedes seguir preguntando, o escribe "
            "\"agente\" para hablar con soporte humano, o \"0\" para volver "
            "al menú."
        ), False

    intentos = session.get("soporte_intentos_fallidos", 0) + 1
    session["soporte_intentos_fallidos"] = intentos

    if intentos >= 2:
        db.insert_escalamiento(consulta=user_input, motivo="rag_sin_resultado")
        session["soporte_intentos_fallidos"] = 0
        return (
            "😕 No logré encontrar información suficiente para resolver tu "
            "caso. " + _MENSAJE_ESCALAMIENTO
        ), True

    return (
        "😕 No encontré información suficiente para responder eso. "
        "¿Puedes reformular tu pregunta con más detalle? También puedes "
        "escribir \"agente\" para hablar con soporte humano."
    ), False


def ver_saldo_lookup(session: dict, user_input: str) -> str:
    cliente = db.get_cliente_by_email(user_input)

    if cliente is None:
        return (
            "❌ No encontramos ninguna cuenta asociada a ese correo electrónico.\n"
            "Verifica que esté escrito correctamente e intenta de nuevo, "
            "o contacta a un agente."
        )

    return (
        f"👋🏼 Hola {cliente['nombre']}\n"
        f"✅ ¡Tu plan de {cliente['plan']} está ACTIVO!\n\n"
        f"Detalles de tu servicio:\n"
        f"💰 Plan {cliente['plan']}: Por Bs. {cliente['precio_bs']:.2f} "
        f"cada {cliente['ciclo_dias']} Days.\n"
        f"📅 Fecha de renovación: {cliente['fecha_renovacion']}\n"
        f"🛑 Tienes Bs. {cliente['saldo_favor_bs']:.2f}, a favor. "
        f"➡️ ¡Recarga la diferencia del costo de tu plan antes de la fecha "
        f"de renovación para garantizar la continuidad de tu servicio!\n"
        f"ℹ️ Las tarifas se ajustan mensualmente según la tasa del BCV. "
        f"Te recomendamos verificar el monto a pagar durante los primeros "
        f"días de cada mes\n\n"
        f"💡 Ten en cuenta:\n"
        f"- Si registras un 📱N° de Pago Móvil frecuente, tus pagos se "
        f"aplican automáticamente.\n"
        f"- Si recargas con otro número, ¡recuerda confirmar los datos "
        f"aquí: http://bit.ly/46SZ6y8 para aplicarlo al instante!"
    )


def nro_cliente_lookup(session: dict, user_input: str) -> str:
    cliente = db.get_cliente_by_email(user_input)

    if cliente is None:
        return (
            "❌ No encontramos ninguna cuenta asociada a ese correo electrónico.\n"
            "Verifica que esté escrito correctamente e intenta de nuevo, "
            "o contacta a un agente."
        )

    return (
        f"¡Listo! Aquí tienes el dato que necesitas.\n"
        f"Tu N° de Cliente es el siguiente: ➡️ {cliente['numero_cliente']}\n\n"
        f"💡 Recuerda que con este número puedes realizar tus renovaciones "
        f"de forma rápida en cualquiera de nuestros canales de pago y "
        f"bancos aliados."
    )



def reportar_pago_identificar(session: dict, user_input: str):
    cliente = db.get_cliente_by_email(user_input)

    if cliente is None:
        return (
            "❌ No encontramos ninguna cuenta asociada a ese correo electrónico. "
            "Verifica que esté escrito correctamente e intenta de nuevo: ⬇️",
            False,
        )

    session["reporte_pago_email"] = cliente["email"]
    session["reporte_pago_numero_cliente"] = cliente["numero_cliente"]
    return f"👋🏼 Hola {cliente['nombre']}, ya identificamos tu cuenta."


def pago_movil_telefono(session: dict, user_input: str) -> str:
    session["reporte_pago_telefono"] = user_input
    return f"📱 Teléfono registrado: {user_input}"


def pago_movil_fecha(session: dict, user_input: str):
    return _validar_fecha_pago(session, user_input, "reporte_pago_fecha")


def pago_movil_monto(session: dict, user_input: str) -> str:
    email = session.pop("reporte_pago_email", "-")
    numero_cliente = session.pop("reporte_pago_numero_cliente", "-")
    telefono = session.pop("reporte_pago_telefono", "-")
    fecha = session.pop("reporte_pago_fecha", "-")

    db.insert_pago_reportado(
        email=email,
        numero_cliente=numero_cliente,
        canal="pago_movil",
        dato_identificador=telefono,
        fecha_pago=fecha,
        monto_bs=user_input,
    )

    return (
        f"✅ ¡Listo! Registramos tu reporte de pago (simulado):\n"
        f"📱 Pago Móvil desde: {telefono}\n"
        f"📅 Fecha del pago: {fecha}\n"
        f"💰 Monto: Bs. {user_input}\n\n"
        f"En breve validaremos tu pago y actualizaremos tu saldo. "
        f"¡Gracias por tu reporte!"
    )


def transferencia_datos(session: dict, user_input: str) -> str:
    session["reporte_pago_datos"] = user_input
    return f"🏦 Datos registrados: {user_input}"


def transferencia_fecha(session: dict, user_input: str):
    return _validar_fecha_pago(session, user_input, "reporte_pago_fecha")


def transferencia_monto(session: dict, user_input: str) -> str:
    email = session.pop("reporte_pago_email", "-")
    numero_cliente = session.pop("reporte_pago_numero_cliente", "-")
    datos = session.pop("reporte_pago_datos", "-")
    fecha = session.pop("reporte_pago_fecha", "-")

    db.insert_pago_reportado(
        email=email,
        numero_cliente=numero_cliente,
        canal="transferencia",
        dato_identificador=datos,
        fecha_pago=fecha,
        monto_bs=user_input,
    )

    return (
        f"✅ ¡Listo! Registramos tu reporte de pago (simulado):\n"
        f"🏦 Transferencia: {datos}\n"
        f"📅 Fecha del pago: {fecha}\n"
        f"💰 Monto: Bs. {user_input}\n\n"
        f"En breve validaremos tu pago y actualizaremos tu saldo. "
        f"¡Gracias por tu reporte!"
    )


REGISTRY = {
    "not_implemented": not_implemented,
}

INPUT_REGISTRY = {
    "ver_saldo_lookup": ver_saldo_lookup,
    "nro_cliente_lookup": nro_cliente_lookup,
    "reportar_pago_identificar": reportar_pago_identificar,
    "pago_movil_telefono": pago_movil_telefono,
    "pago_movil_fecha": pago_movil_fecha,
    "pago_movil_monto": pago_movil_monto,
    "transferencia_datos": transferencia_datos,
    "transferencia_fecha": transferencia_fecha,
    "transferencia_monto": transferencia_monto,
    "soporte_tecnico_rag": soporte_tecnico_rag,
}
