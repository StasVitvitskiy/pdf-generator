import base64
import io
import json
import os
from typing import Dict

import requests
from PIL import Image
from flask import Flask, render_template, request, url_for
import pdfkit
import qrcode


app = Flask(__name__)

INFURA_HOST = 'https://ipfs.infura.io'
INFURA_PORT = '5001'


def get_qr_code(url: str) -> str:
    logo = Image.open('static/logo.png')

    # taking base width
    base_width = 80

    # adjust image size
    aspect_ratio = (base_width / float(logo.size[0]))
    height = int((float(logo.size[1]) * float(aspect_ratio)))
    logo = logo.resize((base_width, height), Image.ANTIALIAS)
    qr_code = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H
    )

    qr_code.add_data(url)
    qr_code.make()

    # adding color to QR code
    qr_img = qr_code.make_image()

    # set size of QR code
    pos = ((qr_img.size[0] - logo.size[0]) // 2,
           (qr_img.size[1] - logo.size[1]) // 2)
    qr_img.paste(logo, pos)

    output = io.BytesIO()
    qr_img.save(output, 'PNG')

    result = base64.b64encode(output.getvalue()).decode()
    output.close()

    return result


def upload_pdf(pdf: bytes) -> Dict:
    response = requests.post(
        url=f'{INFURA_HOST}:{INFURA_PORT}/api/v0/add',
        files={
            'file': pdf
        },
    )

    if response.status_code == 200:
        result_data = response.json()
        pdf_hash = result_data['Hash']
        return {'url': f'{INFURA_HOST}/ipfs/{pdf_hash}'}

    return {'url': None}


@app.route('/generate_pdf/')
def generate_pdf() -> Dict:
    input_data = request.args.to_dict()
    params = json.loads(input_data.get('params') or "") or []
    qr_code_url = input_data.get('qr_code_url')

    if qr_code_url:
        qr_code_image = get_qr_code(qr_code_url)
    else:
        qr_code_image = None

    empty_block_url = url_for("static", filename='blank.png', _external=True)

    rendered_template = render_template(
        'index.html',
        artist_name=input_data.get('artist_name', ''),
        artist_born=f"(b.{input_data.get('artist_born', '')})" if input_data.get('artist_born', '') else "",
        artwork_name=input_data.get('artwork_name', ''),
        artwork_creation_year=f", {input_data.get('artwork_creation_year', '')}"
        if input_data.get('artwork_creation_year', '') else "",
        sign_url=input_data.get('sign_url', empty_block_url),
        params=params,
        artwork_preview_url=input_data.get(
            'artwork_preview_url',
            empty_block_url
        ),
        qr_code=f'data:image/png;base64, {qr_code_image}' if qr_code_image else empty_block_url,
    )
    pdfkit.from_string(rendered_template, "certificate.pdf")
    pdf = pdfkit.from_string(rendered_template, False)

    return upload_pdf(pdf)


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 3000))
    app.run(debug=False, host='0.0.0.0', port=port)
