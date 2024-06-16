import os
import subprocess
import tempfile
import base64
from flask import Flask, request, jsonify

app = Flask(__name__)

PRIVATE_KEY_PATH = os.getenv('PRIVATE_KEY_PATH')
RUT_EMISOR = os.getenv('RUT_EMISOR')
RAZON_SOCIAL_EMISOR = os.getenv('RAZON_SOCIAL_EMISOR')
FOLIOS_DESDE = os.getenv('FOLIOS_DESDE')
FOLIOS_HASTA = os.getenv('FOLIOS_HASTA')
FRMA_ALGORITMO = os.getenv('FRMA_ALGORITMO')
port = int(os.environ.get('PORT', 3000))

@app.route('/sign', methods=['POST'])
def sign_document():
    data = request.get_json()

    # Validar y extraer datos
    try:
        tipo_documento = data['tipoDocumento']
        folio = data['folio']
        fecha_emision = data['fechaEmision']
        rut_receptor = data['rutReceptor']
        razon_social_receptor = data['razonSocialReceptor']
        monto_total = data['montoTotal']
        detalle_1 = data['detalle1']
    except KeyError:
        return jsonify({'error': 'Invalid data format'}), 400

    fecha = "2003-09-04"
    fecha_hora = "2003-09-08T12:28:31"

    # Formatear el mensaje
    message = (
        f"<DD><RE>{RUT_EMISOR}</RE><TD>{tipo_documento}</TD>"
        f"<F>{folio}</F><FE>{fecha_emision}</FE>"
        f"<RR>{rut_receptor}</RR><RSR>{razon_social_receptor}</RSR>"
        f"<MNT>{monto_total}</MNT><IT1>{detalle_1}</IT1>"
        f"<CAF version=\"1.0\"><DA><RE>{RUT_EMISOR}</RE>"
        f"<RS>{RAZON_SOCIAL_EMISOR}</RS><TD>{tipo_documento}</TD>"
        f"<RNG><D>{FOLIOS_DESDE}</D><H>{FOLIOS_HASTA}</H></RNG><FA>{fecha}</FA>"
        f"<RSAPK><M>0a4O6Kbx8Qj3K4iWSP4w7KneZYeJ+g/prihYtIEolKt3cykSxl1zO8vSXu397QhTmsX7SBEudTUx++2zDXBhZw==</M>"
        f"<E>Aw==</E></RSAPK><IDK>100</IDK></DA>"
        f"<FRMA algoritmo=\"SHA1withRSA\">{FRMA_ALGORITMO}</FRMA>"
        f"</CAF><TSTED>{fecha_hora}</TSTED></DD>"
    )

    # Crear archivo temporal para el mensaje
    with tempfile.NamedTemporaryFile(delete=False) as temp_msg_file:
        temp_msg_file.write(message.encode())
        temp_msg_file_path = temp_msg_file.name

    # Crear archivo temporal para el mensaje sin saltos de línea
    temp_msg_no_newlines_path = tempfile.mktemp()

    try:
        # Leer el archivo y eliminar saltos de línea y retornos de carro
        with open(temp_msg_file_path, 'r') as infile, open(temp_msg_no_newlines_path, 'w') as outfile:
            for line in infile:
                outfile.write(line.replace('\n', '').replace('\r', ''))

        # Crear archivo temporal para la firma
        temp_sig_file_path = tempfile.mktemp()

        # Generar firma
        subprocess.run(['openssl', 'dgst', '-sha1', '-sign', PRIVATE_KEY_PATH, '-out', temp_sig_file_path,
                        temp_msg_no_newlines_path], check=True)

        # Leer y convertir la firma a base64
        with open(temp_sig_file_path, 'rb') as sig_file:
            signature = base64.b64encode(sig_file.read()).decode()

    finally:
        # Limpiar archivos temporales
        os.remove(temp_msg_file_path)
        os.remove(temp_msg_no_newlines_path)
        os.remove(temp_sig_file_path)

    return jsonify({'signature': signature})


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=port)
