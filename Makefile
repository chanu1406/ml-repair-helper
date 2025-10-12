.PHONY: env data train api ui test format

env:
	conda env create -f environment.yml

data:
	@echo "Data steps are project-specific. Use DVC to pull or add datasets."

train:
	@echo "Run training scripts under ml/models/ (not implemented in scaffold)."

api:
	uvicorn backend.app.main:app --reload

ui:
	streamlit run frontend/streamlit_app.py

test:
	pytest -q

format:
	black .
