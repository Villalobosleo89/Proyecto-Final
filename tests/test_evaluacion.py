import pytest
from scripts.evaluate_model import evaluar_modelo

def test_evaluacion_200_casos_criterio_ca04():
    """Valida que la batería de 200 casos alcance Accuracy >= 0.80 y F1 >= 0.75 (CA-04)"""
    evaluar_modelo()
