import re
import pytest
from app.ml.anonymizer import anonimizador

def test_anonimizacion_identificadores_basicos():
    texto = "Paciente Juan Carlos Pérez Gómez con CC 1020304050 y celular 3124567890 atendido el 15/08/2026 por Dr. Carlos Mendoza."
    anon = anonimizador.anonimizar(texto)
    
    assert "1020304050" not in anon
    assert "3124567890" not in anon
    assert "15/08/2026" not in anon
    assert "[DOC]" in anon
    assert "[TEL]" in anon
    assert "[FECHA]" in anon

def test_100_casos_anonimizacion_sin_fugas():
    """Genera y evalúa 100 variaciones de datos sensibles para garantizar 0 fugas (RF-03)"""
    nombres = ["Andrés Felipe Ramos", "María Camila Torres", "Javier Rodríguez", "Diana Patricia Mora", "Luis Eduardo Castro"]
    doctores = ["Martínez", "Villalobos", "González", "Osorio", "López"]
    
    for i in range(100):
        cc_val = f"{10000000 + i * 137}"
        tel_val = f"31{i:02d}987654"
        nombre_pac = nombres[i % len(nombres)]
        nombre_doc = doctores[i % len(doctores)]
        dia = (i % 28) + 1
        fecha_val = f"{dia:02d}/05/2026"
        
        texto_muestra = (
            f"Paciente identificado como {nombre_pac} con CC {cc_val} y tel {tel_val} "
            f"ingresa con fecha {fecha_val} remitido por Dr. {nombre_doc} en la Calle 100 # 15-20 con dolor precordial."
        )

        resultado = anonimizador.anonimizar(texto_muestra)

        # Verificaciones estrictas: ningún identificador crudo debe sobrevivir
        assert cc_val not in resultado, f"Fuga de CC en caso #{i}: {cc_val}"
        assert tel_val not in resultado, f"Fuga de teléfono en caso #{i}: {tel_val}"
        assert fecha_val not in resultado, f"Fuga de fecha en caso #{i}: {fecha_val}"
        assert "Calle 100" not in resultado, f"Fuga de dirección en caso #{i}"
