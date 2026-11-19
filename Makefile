.PHONY: test evaluate run dev lint clean

run:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

test:
	python -m pytest -v tests/

evaluate:
	python scripts/evaluate_model.py

lint:
	ruff check app tests || true

clean:
	rm -rf __pycache__ .pytest_cache data/evaluacion_metricas_reporte.txt
