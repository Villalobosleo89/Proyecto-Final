import re

class AnonimizadorClinico:
    """
    Capa de anonimización según Ley 1581 de 2012 (RF-03).
    Sustituye identificadores directos por marcadores estables:
    [PACIENTE], [MEDICO], [DOC], [TEL], [FECHA], [DIRECCION].
    """

    def __init__(self):
        pass

    def anonimizar(self, texto: str) -> str:
        if not texto:
            return ""

        texto_anon = texto

        # 1. Fechas (dd/mm/aaaa, aaaa-mm-dd, o dd de mes de aaaa)
        texto_anon = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[FECHA]', texto_anon)
        texto_anon = re.sub(r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b', '[FECHA]', texto_anon)
        texto_anon = re.sub(
            r'\b\d{1,2}\s+de\s+(?:enero|febrero|marzo|abril|mayo|junio|julio|agosto|septiembre|octubre|noviembre|diciembre)(?:\s+de\s+\d{2,4})?\b',
            '[FECHA]', texto_anon, flags=re.IGNORECASE
        )

        # 2. Direcciones colombianas
        texto_anon = re.sub(
            r'\b(?:calle|carrera|cra|cll|diagonal|diag|transversal|tv|avenida|av\.?)\s+\d+[a-zA-Z]?\s*(?:#|no\.?|numero)\s*\d+[a-zA-Z]?[-.\s]*\d+\b',
            '[DIRECCION]', texto_anon, flags=re.IGNORECASE
        )

        # 3. Nombres de médicos y profesionales
        texto_anon = re.sub(
            r'\b(?:dr(?:\.|\s+)|dra(?:\.|\s+)|medico(?:\s+tratante)?)\s*[:#]?\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+){1,3})',
            'Dr. [MEDICO]', texto_anon, flags=re.IGNORECASE
        )

        # 4. Nombres de pacientes
        texto_anon = re.sub(
            r'\b(?:paciente(?:\s+identificado\s+como)?|nombre(?:\s+del\s+paciente)?|usuario|sr(?:\.|\s+)|sra(?:\.|\s+)|don|dona)\s*[:#]?\s+([A-ZÁÉÍÓÚÑa-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑa-záéíóúñ]+){1,3})',
            'Paciente [PACIENTE]', texto_anon, flags=re.IGNORECASE
        )

        # 5. Teléfonos explícitos o celulares colombianos (empiezan por 3 con 10 dígitos)
        texto_anon = re.sub(
            r'\b(?:tel(?:efono)?|cel(?:ular)?|movil)\s*[:#.-]?\s*[\d\s-]{7,15}\b',
            '[TEL]', texto_anon, flags=re.IGNORECASE
        )
        texto_anon = re.sub(r'\b(?:\+?57\s*)?3\d{2}[-.\s]?\d{3}[-.\s]?\d{4}\b', '[TEL]', texto_anon)

        # 6. Documentos de identidad explícitos y números de 7 a 10 dígitos
        texto_anon = re.sub(
            r'\b(?:c\.?c\.?|cedula(?:\s+de\s+ciudadania)?|t\.?i\.?|tarjeta\s+de\s+identidad|c\.?e\.?|pasaporte|rut|doc(?:umento)?)\s*[:#.-]?\s*\d{6,12}\b',
            '[DOC]', texto_anon, flags=re.IGNORECASE
        )
        texto_anon = re.sub(r'\b\d{7,10}\b', '[DOC]', texto_anon)

        return texto_anon

anonimizador = AnonimizadorClinico()
